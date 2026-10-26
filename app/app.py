"""Rastro Layer: the demo.

A domain selector (app/dominios.yaml): oncology is drawn here; the other domains,
with dominio.py and their configuration file.

Oncology tabs:
  Preguntar          a question in natural language; the answer brings the source of
                     each column and a "¿cómo lo supe?" with the query
  Con y sin Rastro   the 20 evaluation questions, answered by the LLM alone,
                     with direct SQL and with Rastro

It starts with docker compose up and opens at http://localhost:8501
"""

import json
import os
import sys
from pathlib import Path

import base64
import re

import pandas as pd
import psycopg
import requests
import sqlparse
import streamlit as st
import yaml

sys.path.insert(0, "/layer")
sys.path.insert(0, "/layer/eval")

import answer  # noqa: E402
from run import NAMES, normalize, score  # noqa: E402
import dominio  # noqa: E402  (the screens of the other domains and what they share with oncology)
from dominio import ayuda, tabla, warm_up  # noqa: E402  (the «?» icons, the tables with long text and the warm-up)
import idioma  # noqa: E402  (the interface language: Spanish by default, English on request)
from idioma import t  # noqa: E402

EVAL = Path("/layer/eval")
SOURCE_LABEL = {"aact": "AACT", "chembl": "ChEMBL", "openfda": "openFDA", "mesh": "MeSH",
                "rastro": "enlace Rastro"}
# Where each source lives: 🐘 Postgres (SQL) and 🕸️ GraphDB. The full MeSH is in GraphDB;
# Ontop uses a copy of its hierarchy in Postgres.
STORAGE = {"aact": "🐘", "chembl": "🐘", "openfda": "🐘", "mesh": "🕸️🐘", "rastro": "🐘"}
STORAGE_NOTE = {
    "aact": "en Postgres",
    "chembl": "en Postgres",
    "openfda": "en Postgres",
    "mesh": "completo en GraphDB, con búsqueda de texto; su jerarquía, copiada en Postgres",
    "rastro": "en Postgres",
}


def label(source):
    return f"{STORAGE.get(source, '')} {SOURCE_LABEL.get(source, source)}".strip()

st.set_page_config(page_title="Rastro", page_icon="/app/logo.svg", layout="wide")


# --- Data ----------------------------------------------------------

@st.cache_data
def questions():
    return yaml.safe_load((EVAL / "questions.yaml").read_text())["questions"]


@st.cache_data
def saved():
    return json.loads((EVAL / "results.json").read_text())


@st.cache_data
def unified_columns():
    """From the R2RML mappings: which different columns end up in the same concept."""
    import collections

    import rdflib

    rr = rdflib.Namespace("http://www.w3.org/ns/r2rml#")
    g = rdflib.Graph().parse("/mappings/rastro.r2rml.ttl")
    schema_name = {"aact": "AACT", "chembl": "ChEMBL", "openfda": "openFDA", "mesh": "MeSH",
                   "linking": "enlaces de Rastro", "rastro_meta": "registro de fuentes"}
    entity_name = {"drug": "Fármaco", "trial": "Ensayo", "sponsor": "Sponsor", "target": "Target",
                   "2026": "Condición (descriptor de MeSH)"}

    def table(tm):
        lt = g.value(tm, rr.logicalTable)
        text = str(g.value(lt, rr.tableName) or g.value(lt, rr.sqlQuery))
        found = re.search(r"FROM\s+([\w.]+)", text, re.I)
        return found.group(1) if found else text

    def column(t, c):
        schema, name = t.split(".", 1)
        return f"`{name}.{c}` ({schema_name.get(schema, schema)})"

    entities, attributes = collections.defaultdict(set), collections.defaultdict(set)
    for tm in g.subjects(rdflib.RDF.type, rr.TriplesMap):
        t = table(tm)
        templates = [g.value(g.value(tm, rr.subjectMap), rr.template)]
        for pom in g.objects(tm, rr.predicateObjectMap):
            om = g.value(pom, rr.objectMap)
            templates.append(g.value(om, rr.template))
            if g.value(om, rr.column):
                attributes[str(g.value(pom, rr.predicate)).split("#")[-1]].add(column(t, g.value(om, rr.column)))
        for tpl in filter(None, templates):
            key = str(tpl).rstrip("/").split("{")[0].rstrip("/").rsplit("/", 1)[-1]
            entities[key].add(column(t, re.findall(r"\{(\w+)\}", str(tpl))[0]))

    lines = ["| Concepto en Rastro | Columnas de las fuentes que lo forman |", "|---|---|"]
    lines += [f"| **{entity_name.get(k, k)}** | {', '.join(sorted(v))} |"
              for k, v in entities.items() if len(v) > 1]
    lines += [f"| atributo **:{k}** | {', '.join(sorted(v))} |" for k, v in attributes.items() if len(v) > 1]
    return "\n".join(lines)


@st.cache_data
def faq():
    return yaml.safe_load(Path("/app/faq.yaml").read_text())


@st.cache_data
def plain():
    return yaml.safe_load(Path("/app/preguntas-simples.yaml").read_text()) or {}


def show_plain(question_id, simple=True):
    """The question in simple words and what each term means, for someone outside the domain.
    In business mode the selector already shows the simple version: only the terms go here."""
    entry = plain().get(question_id)
    if not entry:
        return
    if simple:
        st.info(f"**En palabras simples:** {entry['simple']}")
    terms = entry.get("terms", {})
    if terms:
        with st.expander("¿Qué significa " + ", ".join(terms) + "?"):
            st.markdown("\n".join(f"- **{term}:** {meaning}" for term, meaning in terms.items()))


@st.cache_data
def explanations():
    return yaml.safe_load((EVAL / "explanations.yaml").read_text()) or {}


@st.cache_data
def sources():
    columns, rows = answer.run_sparql_table("""
        PREFIX oncologia: <https://w3id.org/rastro/oncologia#>
        SELECT ?id ?name ?license WHERE { ?s a oncologia:DataSource ; oncologia:name ?name ; oncologia:license ?license .
          BIND (STRAFTER(STR(?s), "/source/") AS ?id) }""")
    # rastro_meta.source has the sources of every domain: here go the oncology ones
    return {r[0]: {"name": r[1], "license": r[2]} for r in rows if r[0] in STORAGE}


def admin():
    return psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                           f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")


@st.cache_data
def scores():
    data = saved()["questions"]
    totals = {k: 0 for k in NAMES}
    per_question = {}
    with admin() as conn:
        for q in questions():
            entry = data[q["id"]]
            per_question[q["id"]] = {k: score(q, entry["reference"], entry[k]["answer"], conn)
                                     for k in NAMES if k in entry}
            for k, ok in per_question[q["id"]].items():
                totals[k] += ok
    return totals, per_question


def llm_status():
    """Is there an LLM for free-form questions?"""
    if answer.PROVIDER == "ollama":
        try:
            requests.get(f"{answer.OLLAMA}/api/tags", timeout=3).raise_for_status()
            return True, f"Ollama · {answer.MODEL}"
        except requests.RequestException:
            return False, f"Ollama no responde en {answer.OLLAMA}"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True, f"Claude API · {answer.MODEL}"
    return False, "Sin LLM configurado"


LINK_METHODS = {
    "regex": "con expresiones regulares sobre el texto de las intervenciones",
    "substring": "por pedazos del nombre dentro del texto de las intervenciones",
    "ilike": "con comodines (ILIKE) y nombres escritos a mano en la query",
    "exact": "por nombre exacto en ChEMBL",
}


def link_method(query):
    """How a direct SQL query identifies a drug, or None if it does not."""
    if re.search(r"regexp_replace|~ \(|\\m", query):
        return "regex"
    if re.search(r"position\(|strpos|LIKE '%' \|\|", query, re.I):
        return "substring"
    if re.search(r"ilike", query, re.I):
        return "ilike"
    if re.search(r"synonyms|pref_name", query, re.I):
        return "exact"
    return None


def friendly_error(error):
    """The database error, with a simple explanation if it is a known one."""
    if "statement timeout" in error:
        return ("La consulta superó el límite de 60 segundos y la base la canceló. "
                f"Error original: {error.strip()}")
    return error.strip()


def pretty(query, approach):
    if approach in "BD":
        return sqlparse.format(query, reindent=True, keyword_case="upper", indent_width=2)
    return query.strip()


def last_ok_query(entry, approach):
    ok = [a for a in entry.get(approach, {}).get("attempts", []) if a["error"] is None]
    return ok[-1]["query"] if ok else None


# --- Show an answer -----------------------------------------------

RULES = {
    "nombre": "por su nombre o un sinónimo de ChEMBL",
    "alias": "por un alias que declaró el sponsor",
    "combinación": "como parte de una combinación",
    "régimen": "por un régimen conocido, como FOLFOX",
    "palabras": "por su nombre dentro de un texto más largo",
}
RASTRO_PREFIX = "PREFIX oncologia: <https://w3id.org/rastro/oncologia#>\n"
PROV_PREFIX = "PREFIX prov: <http://www.w3.org/ns/prov#>\n"
EVIDENCE_SUMMARY = RASTRO_PREFIX + """SELECT ?name ?rule (COUNT(?link) AS ?n) WHERE {{
  VALUES ?name {{ {names} }}
  ?link a oncologia:DrugLink ; oncologia:linkDrug ?drug ; oncologia:linkRule ?rule . ?drug oncologia:name ?name .
}} GROUP BY ?name ?rule"""
EVIDENCE_EXAMPLES = RASTRO_PREFIX + PROV_PREFIX + """SELECT ?name ?nct ?text ?matched ?rule WHERE {{
  VALUES ?name {{ {names} }}
  ?link a oncologia:DrugLink ; oncologia:linkDrug ?drug ; oncologia:linkTrial ?trial ;
        oncologia:interventionText ?text ; oncologia:matchedText ?matched ; oncologia:linkRule ?rule ;
        prov:wasDerivedFrom <https://w3id.org/rastro/source/aact> .
  ?drug oncologia:name ?name . ?trial oncologia:nctId ?nct .
  FILTER (?rule != "nombre")
}} LIMIT 400"""


EVIDENCE_ONE = RASTRO_PREFIX + PROV_PREFIX + """SELECT ?textoDelSponsor ?coincidioCon ?regla ?derivaDe ?generadoPor WHERE {{
  ?enlace a prov:Entity ; oncologia:linkTrial ?ensayo ; oncologia:linkDrug ?farmaco ;
          oncologia:interventionText ?textoDelSponsor ; oncologia:matchedText ?coincidioCon ; oncologia:linkRule ?regla ;
          prov:wasDerivedFrom ?derivaDe ; prov:wasGeneratedBy ?generadoPor .
  ?ensayo oncologia:nctId "{nct}" . ?farmaco oncologia:name "{name}" .
}}"""
NAMES_OF = {
    "https://w3id.org/rastro/source/aact": "AACT (ClinicalTrials.gov)",
    "https://w3id.org/rastro/source/chembl": "ChEMBL",
    "https://w3id.org/rastro/activity/entity-linking": "el entity linking de Rastro",
}


def evidence_of(nct, name):
    """A link's evidence, requested with PROV-O. One row per source it derives from."""
    query = EVIDENCE_ONE.format(nct=nct, name=name)
    _, rows = answer.run_sparql_table(query)
    if not rows:
        return query, []
    text, matched, rule, _, activity = rows[0]
    derived = ", ".join(NAMES_OF.get(r[3], r[3]) for r in rows)
    table = [
        {"Propiedad": "es un", "Vocabulario": "PROV-O", "Valor": "prov:Entity (lo deduce la ontología)"},
        {"Propiedad": "texto del sponsor", "Vocabulario": "Rastro", "Valor": text},
        {"Propiedad": "coincidió con", "Vocabulario": "Rastro", "Valor": matched},
        {"Propiedad": "regla", "Vocabulario": "Rastro", "Valor": rule},
        {"Propiedad": "deriva de (prov:wasDerivedFrom)", "Vocabulario": "PROV-O", "Valor": derived},
        {"Propiedad": "generado por (prov:wasGeneratedBy)", "Vocabulario": "PROV-O",
         "Valor": NAMES_OF.get(activity, activity)},
    ]
    return query, table


@st.cache_data
def drug_names():
    with admin() as conn:
        return {r[0] for r in conn.execute("SELECT pref_name FROM linking.drug WHERE pref_name IS NOT NULL")}


def answer_drugs(rows):
    """The drugs an answer names, in the order they appear."""
    names = []
    for row in rows:
        for v in row:
            if isinstance(v, str) and v in drug_names() and v not in names:
                names.append(v)
    return names


@st.cache_data
def evidence_summary(names):
    """Per drug: in how many trials it was recognized and what share by its name (PROV-O)."""
    values = " ".join(json.dumps(n) for n in names)
    _, rows = answer.run_sparql_table(EVIDENCE_SUMMARY.format(names=values))
    totals, by_name = {}, {}
    for name, rule, n in rows:
        totals[name] = totals.get(name, 0) + int(n)
        if rule == "nombre":
            by_name[name] = int(n)
    return {name: f"{total} ensayos · {round(100 * by_name.get(name, 0) / total)} % por nombre"
            for name, total in totals.items()}


@st.cache_data
def evidence_examples(names, limit=5):
    """Examples of non-obvious links: the sponsor text is not the drug name."""
    values = " ".join(json.dumps(n) for n in names)
    _, rows = answer.run_sparql_table(EVIDENCE_EXAMPLES.format(names=values))
    picked, seen_rules, seen_drugs = [], set(), set()
    for name, nct, text, matched, rule in rows:   # first, a different rule and drug each time
        if text.strip().lower() != matched.lower() and rule not in seen_rules and name not in seen_drugs:
            picked.append((name, nct, text, rule))
            seen_rules.add(rule)
            seen_drugs.add(name)
    for name, nct, text, matched, rule in rows:   # then, fill up
        if len(picked) >= limit:
            break
        if text.strip().lower() != matched.lower() and (name, nct, text, rule) not in picked:
            picked.append((name, nct, text, rule))
    return picked[:limit]


TEXT_QUESTION = Path("/layer/textos/detenidos-pulmon.json")


def show_text_question():
    """A question over texts, step by step (GraphRAG grounded in the graph): the graph picks the trials
    with an exact query, an AI assistant summarizes only their reasons citing each trial, it can be
    checked, and the reason becomes a fact in the graph. The summary is saved; the texts are read live."""
    from dominio import text_step
    item = json.loads(TEXT_QUESTION.read_text())
    st.markdown("**1 · La pregunta → 2 · El grafo elige → 3 · La IA lee solo eso → 4 · El resumen, con citas "
                "→ 5 · Comprobar → 6 · El texto pasa a ser dato**", help=ayuda("texto"))
    text_step(1, "La pregunta")
    st.info(f"**{item['simple']}**")
    if TECH:
        st.caption("Formulación técnica: " + item["pregunta"])
    if st.button("Responder", type="primary", key="text_answer"):
        st.session_state["text_shown"] = True
    if not st.session_state.get("text_shown"):
        return
    query = Path(item["consulta"]).read_text()
    _, rows = answer.run_sparql_table(query)
    texts = {nct: (status, drugs, why) for nct, status, drugs, why in rows}
    graph_part, _, ai_part = item["como"].partition("Un asistente de IA")

    text_step(2, "El grafo elige, con una consulta exacta",
              "No es una búsqueda por palabras: la consulta usa la jerarquía de enfermedades de MeSH y la clase "
              "«inhibidor de quinasa» que deduce Rastro, así que trae exactamente esos ensayos.")
    st.markdown(graph_part.strip())
    st.metric("Ensayos elegidos por el grafo", len(texts))
    with st.expander("La consulta SPARQL que elige los ensayos", expanded=TECH):
        st.caption("Pide conceptos del diccionario, no palabras: por eso trae exactamente estos ensayos, siempre los mismos.")
        st.code(query, language="sparql")

    text_step(3, "La IA lee solo esos textos", "El asistente de IA no busca nada por su cuenta: recibe estos motivos y ninguno más.")
    st.markdown(("Un asistente de IA" + ai_part).strip() if ai_part else f"Un asistente de IA leyó solo los {len(texts)} motivos.")
    with st.expander(f"Los {len(texts)} motivos que leyó, tal como los escribió cada sponsor"):
        tabla(pd.DataFrame([{"Ensayo": f"https://clinicaltrials.gov/study/{nct}", "Fármacos": d.lower(),
                             "Motivo escrito": w} for nct, (_, d, w) in sorted(texts.items())]),
              hide_index=True, use_container_width=True,
              column_config={"Ensayo": st.column_config.LinkColumn(display_text=r"study/(.*)")})

    text_step(4, "El resumen, con citas")
    for group in item["motivos"]:
        links = ", ".join(f"[{nct}](https://clinicaltrials.gov/study/{nct})" for nct in group["ensayos"])
        st.markdown(f"- **{group['motivo']}** · {len(group['ensayos'])} ensayos. {group['detalle']}  \n"
                    f"<small>Cita: {links}</small>", unsafe_allow_html=True)

    text_step(5, "Comprobar", "Cada grupo cita sus ensayos: se abren en ClinicalTrials.gov y se lee el motivo original.")
    st.markdown(f"Cada grupo cita sus ensayos, con el enlace a ClinicalTrials.gov; en el paso 3 está el motivo "
                f"original de cada uno. Resumen guardado el {item['fecha']}; los motivos se leen en vivo.")

    text_step(6, "El texto pasa a ser dato",
              "Cuando el texto se puede clasificar con reglas, el motivo queda como un hecho del grafo, con su evidencia "
              "(PROV-O), y se cuenta con una consulta exacta, sin IA.")
    facts_query = Path("/ontology/queries/cq11.rq").read_text()
    _, facts = answer.run_sparql_table(facts_query)
    tabla(pd.DataFrame([{"Motivo": m, "Ensayos": int(n)} for m, n in facts]), hide_index=True,
          use_container_width=True)
    st.caption("Cada motivo es un hecho del grafo, clasificado con reglas a partir del texto del sponsor y "
               "con su evidencia. Un ensayo puede tener varios motivos. Las reglas aciertan 9 de cada 10 en "
               "una muestra revisada por un asistente de IA.")
    if TECH:
        with st.expander("El conteo, sobre el motivo clasificado (oncologia:stopReason, con su evidencia en oncologia:StopReasonLink)"):
            st.code(facts_query, language="sparql")


# «¿Por qué este número?» in oncology: how a row's drug was recognized in the trials
DRUG_WHY = {
    "titulo": "Cómo reconoció Rastro {valor} en los ensayos",
    "explica": "Cada ensayo escribe el fármaco a su manera (una marca, un código, una combinación). Rastro lo reconoció "
               "una vez, con una regla, y guardó qué escribió el ensayo y con qué coincidió. Algunos ejemplos no obvios:",
    "query": """SELECT ?ensayo ?texto ?coincidio ?regla WHERE {
  ?d oncologia:name "{valor}" .
  ?l a oncologia:DrugLink ; oncologia:linkDrug ?d ; oncologia:linkTrial/oncologia:nctId ?ensayo ;
     oncologia:interventionText ?texto ; oncologia:matchedText ?coincidio ; oncologia:linkRule ?regla .
  FILTER (LCASE(?texto) != LCASE("{valor}"))
} LIMIT 12""",
    "nodo": "{ensayo}", "detalle": "«{coincidio}»", "flecha": "lo prueba",
    "columnas": {"ensayo": "Ensayo", "texto": "Qué escribió el ensayo", "coincidio": "Con qué coincidió", "regla": "Regla"},
}


def show_answer(query, columns, rows, note=None):
    used, col_sources = answer.column_sources(query)
    drugs = answer_drugs(rows) if rows and "oncologia:testsDrug" in query else []
    info = sources()

    if TECH:
        st.markdown("**Fuentes que usó esta respuesta:** " + " · ".join(f"`{label(s)}`" for s in used), help=ayuda("fuentes_respuesta"))
    else:
        st.markdown("**Fuentes:** " + ", ".join(info[s]["name"] for s in used if s in info), help=ayuda("fuentes_respuesta"))
    if not rows:
        st.info("La consulta no devolvió resultados.")
    else:
        headers = ([f"{c} · {', '.join(label(s) for s in col_sources.get(c, []))}" for c in columns]
                   if TECH else list(columns))
        table = pd.DataFrame(rows, columns=headers)
        if drugs:
            summary = evidence_summary(tuple(drugs))
            names = [next((v for v in row if v in summary), None) for row in rows]
            column = "Cómo lo reconoce Rastro, en todos sus ensayos" if TECH else "Cómo lo reconoció Rastro"
            table[column] = [summary.get(n, "") for n in names]
        import logos  # each company's (sponsor's) favicon
        table, logo_config = logos.with_logos(table, list(columns))
        tabla(table, hide_index=True, use_container_width=True, column_config=logo_config)
        if drugs:   # «¿Por qué este número?»: how Rastro recognized that drug in the trials
            drug_column = next(c for i, c in enumerate(columns) if any(r[i] in drugs for r in rows))
            dominio.show_why("oncologia", DRUG_WHY | {"columna": drug_column}, list(columns), [list(r) for r in rows])
        if TECH:
            st.caption(f"{len(rows)} fila{'s' if len(rows) != 1 else ''}. Cada columna dice de qué fuente sale."
                       + (" La evidencia de cada enlace está en «¿De dónde sale la respuesta?»." if drugs else ""))
        else:
            st.caption(f"{len(rows)} fila{'s' if len(rows) != 1 else ''}."
                       + (" La evidencia está en «¿De dónde sale la respuesta?»." if drugs else ""))

    with st.expander("¿De dónde sale la respuesta?"):
        if not TECH:
            st.markdown("**Dónde buscó Rastro:**")
            for s in used:
                if s == "rastro":
                    st.markdown("- **Los fármacos de cada ensayo**, que Rastro reconoce una vez en el texto "
                                "del ensayo y revisa")
                elif s in info:
                    st.markdown(f"- **{info[s]['name']}** · licencia: {info[s]['license']}")
            if "openfda" in used:
                st.caption("Los eventos adversos son reportes que llegan a la FDA, no porcentajes de riesgo.")
            if drugs:
                st.markdown("**Cómo reconoció cada fármaco.** Algunos ejemplos: lo que escribió quien registró "
                            "el ensayo, y qué fármaco es.")
                for name, nct, text, rule in evidence_examples(tuple(drugs)):
                    st.markdown(f"- «{text}» → **{name.lower()}**, {RULES.get(rule, rule)} · "
                                f"[{nct}](https://clinicaltrials.gov/study/{nct})")
                st.caption("Cada respuesta se puede auditar: abrí el ensayo y comprobalo.")
            st.caption("Para ver la consulta y el SQL, active «Ver detalles técnicos» en la barra lateral.")
            return
        if note:
            st.caption(note)
        st.markdown("**1. La consulta que escribió el LLM**, sobre los conceptos de Rastro (SPARQL):")
        st.code(query, language="sparql")
        st.markdown("**2. El SQL que Rastro generó y ejecutó en Postgres** (lo traduce Rastro "
                    "con los mapeos; los datos no se copian a otro lado):")
        sql = None
        try:
            sql = pretty(answer.ontop_sql(query), "B")
            st.code(sql, language="sql")
        except requests.RequestException:
            st.caption("No se pudo obtener el SQL de esta consulta.")
        # the «Explicame la consulta» button is the same in every domain
        dominio.explain(query, sql, "oncologia")
        st.markdown("**3. Las fuentes:**")
        info = sources()
        for s in used:
            if s == "rastro":
                st.markdown(f"- {STORAGE['rastro']} **Enlace de Rastro**: ensayo → fármaco, resuelto "
                            "por nombre, alias y sinónimos de ChEMBL (98-99 % de precisión "
                            f"en una muestra) · {STORAGE_NOTE['rastro']}")
            elif s in info:
                st.markdown(f"- {STORAGE[s]} **{info[s]['name']}** · licencia: {info[s]['license']}"
                            f" · {STORAGE_NOTE[s]}")
        if "openfda" in used:
            st.caption("Los eventos adversos son conteos de reportes espontáneos de FAERS: "
                       "no son frecuencias clínicas y pueden incluir duplicados.")
        drugs = answer_drugs(rows) if rows and "oncologia:testsDrug" in query else []
        if drugs:
            st.markdown("**4. La evidencia de los enlaces ensayo → fármaco.** Cada enlace guarda qué "
                        "escribió el sponsor, con qué coincidió y con qué regla. Algunos ejemplos no obvios:")
            for name, nct, text, rule in evidence_examples(tuple(drugs)):
                st.markdown(f"- «{text}» → **{name.lower()}**, {RULES.get(rule, rule)} · "
                            f"[{nct}](https://clinicaltrials.gov/study/{nct})")
            examples = evidence_examples(tuple(drugs))
            if examples:
                name, nct, text, _ = examples[0]
                query, table = evidence_of(nct, name)
                st.markdown(f"La evidencia está en el grafo, descrita con **PROV-O** (el estándar del W3C "
                            f"para procedencia), así que cualquier consulta puede pedirla. Por ejemplo, esta "
                            f"pide la evidencia del enlace entre {nct} y {name.lower()}: de qué deriva "
                            f"(`prov:wasDerivedFrom`) y qué lo generó (`prov:wasGeneratedBy`):")
                st.code(query, language="sparql")
                tabla(pd.DataFrame(table), hide_index=True, use_container_width=True)
                st.caption("La consulta de la respuesta no necesita PROV-O: usa `oncologia:testsDrug`. La procedencia "
                           "se pide aparte, como acá. «?enlace a prov:Entity» no está en ningún mapeo: Rastro "
                           "lo deduce de la ontología, donde un enlace es un tipo de entidad PROV. Cualquiera "
                           "puede auditarlo abriendo el ensayo.")


# --- Screen --------------------------------------------------------

idioma.init()   # before any text, so the first lines are already in the chosen language

st.markdown('<img src="data:image/svg+xml;base64,' + base64.b64encode(Path("/app/logo-horizontal.svg").read_bytes()).decode()
            + '" style="height:56px;margin:8px 0 4px 0" alt="Rastro">', unsafe_allow_html=True)
st.markdown(f"**{t('app.tagline')}**")

# Domains: oncology has its screen in this file; the others are drawn with dominio.py
# from their configuration (app/dominios.yaml)
DOMAINS = idioma.localized("/app/dominios.yaml")
available, status = llm_status()
warm_up()   # the domains' example questions, in the background
with st.sidebar:
    # The demo is oil and gas; the other two cases show with «Ver detalles técnicos», as proof that the
    # same Rastro works for other data
    idioma.selector()
    TECH = st.toggle(t("app.technical"), value=False, help=t("app.technical_help"))
    DOMAIN = (st.radio(t("app.domain"), DOMAINS, format_func=lambda d: d["name"], key="domain", help=ayuda("dominio"))
              if TECH else DOMAINS[0])
if DOMAIN.get("config"):
    dominio.render(DOMAIN["config"], TECH)
    st.stop()

with st.sidebar:
    if TECH:
        st.subheader("LLM", help=ayuda("llm"))
        st.markdown(("🟢 " if available else "⚪ ") + status)
        if not available:
            st.caption("Las preguntas de ejemplo funcionan igual.")
        st.subheader("Fuentes", help=ayuda("fuentes_barra"))
        for key, info in sources().items():
            st.markdown(f"{STORAGE.get(key, '')} **{info['name']}**  \n<small>{info['license']}</small>",
                        unsafe_allow_html=True)
        st.caption("🐘 Postgres · 🕸️ GraphDB")
    else:
        st.caption("Datos públicos de oncología: ensayos clínicos (AACT), fármacos (ChEMBL), "
                   "efectos adversos (openFDA) y enfermedades (MeSH).")

ask_tab, trust_tab, faq_tab, *hood_tab = st.tabs(["Preguntar", "Por qué confiar", "Preguntas frecuentes"]
                                                + (["Bajo el capó"] if TECH else []))
if hood_tab:
    # «Bajo el capó» is the same in the three domains
    with hood_tab[0]:
        dominio.under_the_hood("oncologia", "ontologia")
FAQ_HINT = "Para dudas, consulte la pestaña **Preguntas frecuentes**."

with ask_tab:
    mode = st.radio("Tipo de pregunta",
                    ["Una pregunta de ejemplo", "Una pregunta sobre textos", "Mi propia pregunta"],
                    horizontal=True, label_visibility="visible", help=ayuda("modo"))
    if mode == "Una pregunta sobre textos":
        show_text_question()
    elif mode == "Una pregunta de ejemplo":
        # 🧾 marks the questions whose answer brings the evidence of each link (PROV-O)
        def ask_label(q):
            linked = "oncologia:testsDrug" in (last_ok_query(saved()["questions"][q["id"]], "C") or "")
            text = plain().get(q["id"], {}).get("simple", q["question"])   # the same question in both views
            return ("🧾 " if linked else "") + text

        options = {ask_label(q): q for q in questions()}
        chosen = st.selectbox("Pregunta", list(options), key="ask_question",
                              help="🧾 La respuesta muestra cómo reconoció Rastro cada fármaco: se puede auditar.")
        if TECH:
            st.caption("Formulación técnica: " + options[chosen]["question"])
        show_plain(options[chosen]["id"], simple=False)
        query = last_ok_query(saved()["questions"][options[chosen]["id"]], "C")
        # The answer is kept so «¿Por qué?» can pick a drug without losing it
        if st.button("Responder", type="primary"):
            st.session_state["shown"] = (chosen, query, *answer.run_sparql_table(query))
        if st.session_state.get("shown", (None,))[0] == chosen:
            _, query, columns, rows = st.session_state["shown"]
            show_answer(query, columns, rows,
                        note="La query la escribió el LLM durante la evaluación y quedó guardada; "
                             "se ejecuta ahora, en vivo, sobre los datos.")
    else:
        question = st.text_area("Pregunta", placeholder="Por ejemplo: ¿qué fármacos contra KRAS "
                                "se prueban en ensayos de cáncer de páncreas?", help=ayuda("propia"))
        if st.button("Responder", type="primary", disabled=not available or not question.strip()):
            with st.spinner("El LLM está escribiendo la query..."):
                result = answer.ask_rastro(question)
            if result.get("sin_datos"):
                st.warning(f"Rastro no tiene ese dato: {result['sin_datos']}")
            elif result["query"] is None:
                st.error("El LLM no logró una query que funcione en tres intentos.")
                st.code(result["attempts"][-1]["error"] if result["attempts"] else "")
            else:
                show_answer(result["query"], result["columns"], result["rows"],
                            note=f"Intentos: {len(result['attempts'])}.")
        if not available:
            st.info("Para preguntas libres hace falta un LLM. Mientras tanto, pueden usarse las preguntas de ejemplo.")

@st.cache_data
def consistency():
    """The 10 questions of the consistency test: the 4 ways of asking and the answers of
    each approach (layer/consistencia/). Version 0 is the original evaluation question."""
    folder = Path("/layer/consistencia")
    paraphrases = yaml.safe_load((folder / "parafrasis.yaml").read_text())
    data = saved()["questions"]
    rows = []
    for qid, others in paraphrases.items():
        texts = [data[qid]["question"]] + others
        answers = {}
        for k in "BDC":
            answers[k] = [data[qid].get(k, {}).get("answer")]
            for n in range(1, len(others) + 1):
                path = folder / "respuestas" / f"{qid}-{n}-{k}.json"
                answers[k].append(json.loads(path.read_text()).get("answer") if path.exists() else None)
        rows.append({"id": qid, "texts": texts, "answers": answers})
    return rows


def short_answer(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        return str(len(value))
    return f"{value:,.0f}".replace(",", ".") if value == int(value) else f"{value:.1f}"


def same_answers(values):
    keys = {json.dumps(sorted(v), ensure_ascii=False) if isinstance(v, list) else json.dumps(v) for v in values}
    return len(keys) == 1


def audit_card():
    """The «Cada respuesta se puede auditar» card, with the measured coverage (layer/evidencia.py)."""
    p = Path("/layer/eval/evidencia.json")
    if not p.exists():
        return "Sí", "Con la evidencia de cada fármaco"
    e = json.loads(p.read_text())
    return (f"{100 * e['enlaces_con_evidencia'] / e['enlaces']:.0f} %",
            f"de los {e['enlaces']:,} ".replace(",", ".") + "enlaces ensayo → fármaco guardan su texto, su regla y su "
            f"fuente; y {e['columnas_con_fuente']} de {e['columnas']} columnas de las respuestas dicen de qué fuente salen.")


with trust_tab:
    data = saved()["questions"]
    st.markdown("### Por qué confiar", help=ayuda("confiar"))
    st.caption("El mismo asistente de IA, sin Rastro (escribe SQL sobre las bases tal como vienen) y con Rastro.")
    cards = st.columns(3)
    for col, (title, value, compare, tip) in zip(cards, [
            ("La misma pregunta, la misma respuesta", "10 de 10", "Sin Rastro: 1 de 10", "tarjeta_consistencia"),
            ("Si una base cambia, se arregla con", "1 línea", "Sin Rastro: reescribir 5 consultas", "tarjeta_cambio"),
            ("Cada respuesta se puede auditar", *audit_card(), "tarjeta_auditar")]):
        with col.container(border=True):
            st.markdown(f"**{title}**", help=ayuda(tip))
            st.markdown(f'<p style="font-size:2.4rem;line-height:1.1;margin:0">{value}</p>',
                        unsafe_allow_html=True)
            st.caption(compare)
    # The three tests, kept apart: in the technical view, one tab each, so that picking a question
    # in one test does not seem to change the others
    if TECH:
        trust_correct, trust_same, trust_change = st.tabs(["1 · Correctas (20 preguntas)",
                                                           "2 · Misma respuesta de 4 formas (10 preguntas)",
                                                           "3 · Cuando una base cambia (las 20 preguntas)"])
    with trust_same if TECH else st.expander("Ver las 40 respuestas"):
        st.caption("10 preguntas, cada una hecha de 4 formas con el mismo significado.")
        approaches = {"B": "Sin Rastro", "D": "SQL + enlaces", "C": "Con Rastro"} if TECH else \
                     {"B": "Sin Rastro", "C": "Con Rastro"}
        table = []
        for row in consistency():
            line = {"Pregunta": plain().get(row["id"], {}).get("simple", row["texts"][0])}
            for k, title in approaches.items():
                values = row["answers"][k]
                line[title] = ("✅ " if same_answers(values) else "❌ ") + " · ".join(short_answer(v) for v in values)
            table.append(line)
        tabla(pd.DataFrame(table), hide_index=True, use_container_width=True,
                     column_config={"Pregunta": st.column_config.TextColumn(width="medium")})
        st.caption("✅ la misma respuesta las 4 veces · ❌ cambió según cómo se preguntó. En las preguntas que "
                   "piden una lista, el número es cuántos nombres devolvió.")
        rows = consistency()
        picked = st.selectbox("Ver las 4 formas de una pregunta",
                              [plain().get(r["id"], {}).get("simple", r["texts"][0]) for r in rows],
                              key="consistency_question")
        row = rows[[plain().get(r["id"], {}).get("simple", r["texts"][0]) for r in rows].index(picked)]
        detail = [{"Cómo se preguntó": text,
                   **{title: short_answer(row["answers"][k][i]) for k, title in approaches.items()}}
                  for i, text in enumerate(row["texts"])]
        tabla(pd.DataFrame(detail), hide_index=True, use_container_width=True,
                     column_config={"Cómo se preguntó": st.column_config.TextColumn(width="large")})
        if TECH:
            with trust_correct:
                st.markdown("##### Detalle técnico: las cuatro formas, pregunta por pregunta")
                totals, per_question = scores()
                data = saved()["questions"]
                n = len(questions())
                st.markdown("El mismo LLM respondió las mismas 20 preguntas de cuatro formas:")
                cols = st.columns(len(NAMES))
                help_text = {"A": "Sin datos: responde de memoria.",
                             "B": "SQL sobre las tablas de las fuentes; resuelve los cruces por su cuenta.",
                             "D": "SQL sobre las mismas tablas más los enlaces de Rastro: la línea de base justa.",
                             "C": "Consulta sobre los conceptos de Rastro; los cruces ya están resueltos."}
                for col, k in zip(cols, NAMES):
                    col.metric(NAMES[k], f"{totals[k]}/{n}")
                    col.caption(help_text[k])
                st.info("Con los enlaces de Rastro, el SQL acierta igual: la precisión viene de la integración "
                        "hecha una vez. La capa semántica suma que esa integración se mantiene en un solo "
                        "lugar, dice de dónde sale cada dato y se conecta con datos de afuera. " + FAQ_HINT)
                with st.expander("Cómo responde cada forma", expanded=True):
                    svg = base64.b64encode(Path("/app/como-funciona.svg").read_bytes()).decode()
                    st.markdown(f'<img src="data:image/svg+xml;base64,{svg}" style="width:100%">',
                                unsafe_allow_html=True)

                st.subheader("Pregunta por pregunta")
                st.caption("🔁 marca las preguntas en las que el SQL directo necesitó más de un intento.")

                def option_label(q):
                    retried = len(data[q["id"]]["B"]["attempts"]) > 1
                    return ("🔁 " if retried else "") + q["question"]

                options = {option_label(q): q for q in questions()}
                chosen = st.selectbox("Pregunta", list(options), label_visibility="collapsed", key="compare_question")
                q = options[chosen]
                show_plain(q["id"])
                entry = data[q["id"]]

                def fmt(value):
                    if value is None:
                        return "sin respuesta"
                    if isinstance(value, list):
                        return ", ".join(value[:12]) + (f" y {len(value) - 12} más" if len(value) > 12 else "")
                    return f"{value:,.0f}" if value >= 10 else f"{value:.1f}"

                def why_wrong(k):
                    custom = explanations().get(q["id"], {}).get(k)
                    if custom:
                        return custom
                    ref, got = entry["reference"], entry[k]["answer"]
                    if got is None:
                        return "No logró una consulta que funcione."
                    if q["kind"] == "número":
                        gap = abs(got - ref) / abs(ref) * 100 if ref else 100
                        prefix = "Respondió de memoria, sin acceso a los datos: " if k == "A" else ""
                        return f"{prefix}dijo {fmt(got)} y la cifra real es {fmt(ref)} (un {gap:.0f} % de diferencia)."
                    with admin() as conn:
                        ref_set = normalize(ref, q["items"], conn)
                        got_set = normalize(got, q["items"], conn)
                    hits = len(ref_set & got_set)
                    prefix = "Nombró de memoria los más conocidos: " if k == "A" else ""
                    return (f"{prefix}coincide en {hits} de los {len(ref_set)} correctos"
                            + (f" y agrega {len(got_set - ref_set)} que no corresponden." if got_set - ref_set else "."))

                st.markdown(f"**Respuesta correcta:** {fmt(entry['reference'])}")
                cols = st.columns(len(NAMES))
                for col, k in zip(cols, NAMES):
                    with col:
                        ok = per_question[q["id"]].get(k)
                        st.markdown(f"#### {NAMES[k]}")
                        st.markdown(("✅ " if ok else "❌ ") + fmt(entry[k]["answer"]))
                        if not ok:
                            st.warning("**¿Por qué falló?** " + why_wrong(k))
                        query = last_ok_query(entry, k)
                        if k == "A":
                            st.caption("Respondió de memoria, sin consultar datos.")
                            continue
                        if k == "B" and query and link_method(query):
                            st.caption(f"Para reconocer los fármacos, los buscó {LINK_METHODS[link_method(query)]}.")
                        if k == "D" and query and "linking." in query:
                            st.caption("Para reconocer los fármacos usó las tablas de enlaces de Rastro.")
                        if k == "C" and query and "oncologia:testsDrug" in query:
                            st.caption("Para reconocer los fármacos usó el enlace de Rastro: el mismo en todas "
                                       "las preguntas.")
                        if query:
                            shown = pretty(query, k)
                            attempts = len(entry[k]["attempts"])
                            seconds = entry[k].get("seconds")
                            st.caption(f"{len(shown.splitlines())} líneas"
                                       + (f" · {seconds:.1f} s" if seconds is not None else "")
                                       + f" · {attempts} intento{'s' if attempts != 1 else ''}")
                            st.code(shown, language="sql" if k in "BD" else "sparql")
                            history = entry[k]["attempts"]
                            if len(history) > 1:
                                with st.expander(f"🔁 Ver los {len(history)} intentos hasta dar con el resultado"):
                                    st.caption("Cada vez que una query falló, el LLM recibió el error y "
                                               "escribió otra. Hasta tres intentos, igual para SQL y para Rastro.")
                                    for i, attempt in enumerate(history, start=1):
                                        if attempt["error"]:
                                            st.markdown(f"**Intento {i}: ❌ falló**")
                                            st.error(friendly_error(attempt["error"]))
                                        else:
                                            st.markdown(f"**Intento {i}: ✅ funcionó**")
                                        st.code(pretty(attempt["query"], k), language="sql" if k in "BD" else "sparql")
                            if k == "C":
                                with st.expander("El SQL que Rastro generó a partir de esta consulta"):
                                    st.caption("Rastro traduce la consulta a SQL sobre Postgres usando los "
                                               "mapeos. Comparalo con el que el LLM tuvo que escribir a mano: "
                                               "los cruces ya resueltos son tablas simples.")
                                    try:
                                        st.code(pretty(answer.ontop_sql(query), "B"), language="sql")
                                    except requests.RequestException:
                                        st.caption("No se pudo obtener el SQL de esta consulta.")

# Change scenarios: results measured with layer/cambio/cambio.sh registrar
CHANGES = {
    "Cambia cómo se escribe un valor": {
        "what": "AACT publica una versión nueva y los estados pasan de TERMINATED a Terminated.",
        "sql": "UPDATE aact.studies SET overall_status = initcap(overall_status);",
        "before": "valores", "after": "valores-arreglado",
        "fix": ("SELECT nct_id, brief_title, phase, overall_status, start_date, why_stopped",
                "SELECT nct_id, brief_title, phase, upper(overall_status) AS overall_status, start_date, why_stopped"),
    },
    "Cambia el nombre de una columna": {
        "what": "AACT publica una versión nueva y la columna del estado del ensayo cambia de nombre.",
        "sql": "ALTER TABLE aact.studies RENAME COLUMN overall_status TO status;",
        "before": "renombrar", "after": "renombrar-arreglado",
        "fix": ("SELECT nct_id, brief_title, phase, overall_status, start_date, why_stopped",
                "SELECT nct_id, brief_title, phase, status AS overall_status, start_date, why_stopped"),
    },
}
CHANGE_NAMES = {"B": "SQL directo", "D": "SQL + enlaces", "C": "Rastro"}
STATUS = {"✅": "igual", "🟡": "distintas, sin aviso", "❌": "con error"}


def change_summary(totals):
    return " · ".join(f"{v} {STATUS.get(s, s)}" for s, v in sorted(totals.items(), key=lambda x: x[0] != "✅"))


with trust_tab:
    with trust_change if TECH else st.expander("Ver los escenarios de cambio"):
        st.caption("Qué pasa con las 20 preguntas de ejemplo, todas juntas, cuando una base cambia."
                   + (" Se reproduce en vivo con `layer/cambio/cambio.sh`." if TECH else ""))
        names = CHANGE_NAMES if TECH else {"B": "Sin Rastro", "C": "Con Rastro"}
        scenario = st.radio("Escenario", list(CHANGES) + ["Cambia una definición de negocio"]
                            + (["Se suma una fuente: Wikidata"] if TECH else []),
                            horizontal=True, label_visibility="visible", help=ayuda("escenario"))
        if scenario in CHANGES:
            change = CHANGES[scenario]
            recorded = json.loads(Path("/layer/cambio/resultado.json").read_text())
            before, after = recorded[change["before"]], recorded[change["after"]]
            st.markdown(change["what"])
            if TECH:
                st.code(change["sql"], language="sql")
            st.markdown("**Antes de arreglar nada:**")
            for col, k in zip(st.columns(len(names)), names):
                col.metric(names[k], f"{before['totals'][k].get('✅', 0)}/20")
                col.caption(change_summary(before["totals"][k]))
            if before["totals"]["C"].get("❌", 0) > before["totals"]["B"].get("❌", 0):
                st.caption("Rastro falla más, y todo junto: la primera consulta con error deja la conexión "
                           "con la base en error y arrastra a las demás. Falla en voz alta, y se arregla en un lugar."
                           if TECH else "Con Rastro falla todo junto y en voz alta, y se arregla en un solo lugar.")
            if "Control de vocabulario" in before["vocabulary"] and "🟡" in before["vocabulary"]:
                st.warning("Rastro avisa: " + before["vocabulary"].replace("🟡 Control de vocabulario: ", ""))
            if TECH:
                st.markdown("**El arreglo en Rastro: una línea del mapeo**")
                st.code(f"- {change['fix'][0]}\n+ {change['fix'][1]}", language="diff")
            else:
                st.markdown("**El arreglo en Rastro:** una línea, en la traducción de esa base al diccionario "
                            "de negocio.")
            st.markdown("**Después del arreglo:**")
            for col, k in zip(st.columns(len(names)), names):
                col.metric(names[k], f"{after['totals'][k].get('✅', 0)}/20")
                col.caption(change_summary(after["totals"][k]) if k == "C" else
                            change_summary(after["totals"][k]) + ". Hay que encontrar y reescribir cada consulta.")
            if TECH:
                with st.expander("Las preguntas afectadas"):
                    rows = [{"Pregunta": data[qid]["question"],
                             **{CHANGE_NAMES[k]: before["cells"][qid][k] for k in CHANGE_NAMES}}
                            for qid in before["cells"]
                            if any(not before["cells"][qid][k].startswith("✅") for k in CHANGE_NAMES)]
                    tabla(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.info("Con SQL, cada consulta sabe cómo se llaman las columnas y cómo se escriben los valores, "
                    "aunque use las tablas de enlaces. En Rastro ese conocimiento está en un solo lugar: "
                    "el mapeo. Una capa de vistas SQL también lo centralizaría; la capa semántica suma la "
                    "procedencia y los datos de afuera." if TECH else
                    "Sin Rastro, cada consulta sabe cómo se llaman las columnas y cómo se escriben los valores: "
                    "si la base cambia, hay que encontrar y arreglar cada una. Con Rastro, eso está en un solo lugar.")
        elif scenario == "Cambia una definición de negocio" and not TECH:
            st.markdown("«Terapia dirigida» está definida una sola vez, en el **diccionario de negocio**: los "
                        "inhibidores de quinasa y los anticuerpos monoclonales lo son. Si el negocio decide que "
                        "la terapia hormonal también cuenta, es una línea más, y todas las preguntas cambian a la vez:")
            cols = st.columns(2)
            cols[0].metric("Fármacos que son terapia dirigida", "188", "+32 (antes, 156)")
            cols[1].metric("Ensayos de fase 3 de cáncer de mama con terapia dirigida", "547", "+211 (antes, 336)")
            st.info("Sin Rastro, esa definición vive dentro de cada consulta. Con Rastro, en un solo lugar.")
        elif scenario == "Cambia una definición de negocio":
            st.markdown("«Terapia dirigida» no está en ninguna tabla ni en ningún mapeo. Está definida en "
                        "la **ontología**, en dos líneas: los inhibidores de quinasa y los anticuerpos "
                        "monoclonales son terapias dirigidas. Rastro lo deduce al responder.")
            st.code("oncologia:KinaseInhibitor    rdfs:subClassOf oncologia:TargetedTherapy .\n"
                    "oncologia:MonoclonalAntibody rdfs:subClassOf oncologia:TargetedTherapy .", language="turtle")
            st.markdown("El SQL que genera Rastro para «fármacos que son terapia dirigida»: nadie lo escribió.")
            st.code("SELECT DISTINCT v1.chembl_id, v3.pref_name\n"
                    "FROM linking.drug_class v1,\n"
                    "     (VALUES ('KinaseInhibitor'), ('MonoclonalAntibody')) AS v2 (v0m0),\n"
                    "     linking.drug v3\n"
                    "WHERE v1.class = v2.v0m0 AND v1.chembl_id = v3.chembl_id", language="sql")
            st.markdown("**Si el negocio decide que la terapia hormonal también cuenta, es una línea más:**")
            st.code("oncologia:HormoneTherapy rdfs:subClassOf oncologia:TargetedTherapy .", language="turtle")
            cols = st.columns(2)
            cols[0].metric("Fármacos que son terapia dirigida", "188", "+32 (antes, 156)")
            cols[1].metric("Ensayos de fase 3 de cáncer de mama con terapia dirigida", "547", "+211 (antes, 336)")
            st.info("Todas las preguntas que dicen «terapia dirigida» cambian a la vez, sin tocar SQL ni "
                    "consultas. Con SQL, esa definición vive en cada consulta, o en una vista que hay que "
                    "mantener. En Rastro vive en el modelo, documentada, y el LLM la lee.")
        else:
            st.markdown("Una consulta une, en vivo, **Rastro**, **MeSH** y **Wikidata**: para cada fármaco "
                        "anti-HER2, qué enfermedades trata según Wikidata. No se carga nada: Rastro y "
                        "Wikidata comparten el identificador del fármaco (ChEMBL ID).")
            table = pd.read_csv("/layer/externo/resultado-2026-10-17.csv").rename(columns={
                "farmaco": "Fármaco", "ensayos": "Ensayos de cáncer de mama",
                "trata_segun_wikidata": "Trata, según Wikidata"})
            tabla(table.fillna("—"), hide_index=True, use_container_width=True)
            st.caption("Afatinib (pulmón) y vandetanib (tiroides) están aprobados para otros cánceres y se "
                       "prueban en mama: un dato que ninguna de las cuatro fuentes de Rastro tiene. "
                       "Resultado guardado el 17 oct 2026; la consulta en vivo tarda unos 10 segundos.")
            with st.expander("La consulta: tres grafos en una"):
                st.code(Path("/layer/externo/wikidata.rq").read_text(), language="sparql")
            st.info("Con SQL, sumar una fuente de otra organización es cargarla y mantener una copia. "
                    "Con identificadores compartidos, se consulta en el lugar.")

with trust_tab:
    with st.expander("Ver un ejemplo de evidencia"):
        st.markdown("«Adjuvant Systemic Therapy» → **trastuzumab emtansina**, porque el sponsor lo declaró así "
                    "([NCT07421141](https://clinicaltrials.gov/study/NCT07421141)).")
        st.caption("En cada respuesta con fármacos (marcadas con 🧾), «¿De dónde sale la respuesta?» muestra ejemplos como "
                   "este. Cada ensayo se puede abrir y comprobar.")

with faq_tab:
    data = saved()["questions"]
    methods = [link_method(q) for q in (last_ok_query(e, "B") for e in data.values()) if q]
    numbers = {
        "reinvented": sum(m is not None for m in methods),
        "n_methods": len({m for m in methods if m}),
        "secs_b": f"{sum(e['B'].get('seconds', 0) for e in data.values()):.0f}",
        "secs_c": f"{sum(e['C'].get('seconds', 0) for e in data.values()):.0f}",
        "retries_b": sum(len(e["B"]["attempts"]) > 1 for e in data.values()),
        "retries_c": sum(len(e["C"]["attempts"]) > 1 for e in data.values()),
        "unified_columns": unified_columns(),
    }
    # the questions that apply to every case, and then the oncology ones
    dominio.show_faq("oncologia", [(i["question"], i["answer"].format(**numbers), i.get("tecnico", False)) for i in faq()],
                     TECH, [("arquitectura-oncologia", "De las fuentes del dominio a una capa semántica."),
                            ("ontologia", "Los conceptos de negocio que lee el LLM, en lugar de las tablas.")], "ontología")
