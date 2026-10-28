"""Rastro Layer: the demo.

A domain selector (app/dominios.yaml): oncology is drawn here; the other domains,
with the dominio package (app/dominio/) and their configuration file.

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
import enlaces  # noqa: E402  (one mark for a link's review status)
import dominio  # noqa: E402  (the screens of the other domains and what they share with oncology)
from dominio import ayuda, tabla, warm_up  # noqa: E402  (the «?» icons, the tables with long text and the warm-up)
import idioma  # noqa: E402  (the interface language: Spanish by default, English on request)
from idioma import t  # noqa: E402

EVAL = Path("/layer/eval")
SOURCE_LABEL = {"aact": "AACT", "chembl": "ChEMBL", "openfda": "openFDA", "mesh": "MeSH"}
# Where each source lives: 🐘 Postgres (SQL) and 🕸️ GraphDB. The full MeSH is in GraphDB;
# Ontop uses a copy of its hierarchy in Postgres.
STORAGE = {"aact": "🐘", "chembl": "🐘", "openfda": "🐘", "mesh": "🕸️🐘", "rastro": "🐘"}
STORAGE_NOTE = {   # keys of app/textos/app.yaml
    "aact": "app.sources.note_postgres",
    "chembl": "app.sources.note_postgres",
    "openfda": "app.sources.note_postgres",
    "mesh": "app.sources.note_mesh",
    "rastro": "app.sources.note_postgres",
}


def label(source):
    name = t("app.sources.rastro_link") if source == "rastro" else SOURCE_LABEL.get(source, source)
    return f"{STORAGE.get(source, '')} {name}".strip()

st.set_page_config(page_title="Rastro", page_icon="/app/logo.svg", layout="wide")


# --- Data ----------------------------------------------------------

@st.cache_data
def questions():
    return yaml.safe_load((EVAL / "questions.yaml").read_text())["questions"]


@st.cache_data
def saved():
    return json.loads((EVAL / "results.json").read_text())


@st.cache_data
def unified_columns(language):
    """From the R2RML mappings: which different columns end up in the same concept (language is the cache key)."""
    import collections

    import rdflib

    rr = rdflib.Namespace("http://www.w3.org/ns/r2rml#")
    g = rdflib.Graph().parse("/mappings/rastro.r2rml.ttl")
    schema_name = {"aact": "AACT", "chembl": "ChEMBL", "openfda": "openFDA", "mesh": "MeSH",
                   "linking": t("app.columns.links"), "rastro_meta": t("app.columns.registry")}
    entity_name = {"drug": t("app.columns.drug"), "trial": t("app.columns.trial"), "sponsor": "Sponsor",
                   "target": "Target", "2026": t("app.columns.condition")}

    def table(tm):
        lt = g.value(tm, rr.logicalTable)
        text = str(g.value(lt, rr.tableName) or g.value(lt, rr.sqlQuery))
        found = re.search(r"FROM\s+([\w.]+)", text, re.I)
        return found.group(1) if found else text

    def column(source_table, c):
        schema, name = source_table.split(".", 1)
        return f"`{name}.{c}` ({schema_name.get(schema, schema)})"

    entities, attributes = collections.defaultdict(set), collections.defaultdict(set)
    for tm in g.subjects(rdflib.RDF.type, rr.TriplesMap):
        source_table = table(tm)
        templates = [g.value(g.value(tm, rr.subjectMap), rr.template)]
        for pom in g.objects(tm, rr.predicateObjectMap):
            om = g.value(pom, rr.objectMap)
            templates.append(g.value(om, rr.template))
            if g.value(om, rr.column):
                attributes[str(g.value(pom, rr.predicate)).split("#")[-1]].add(column(source_table, g.value(om, rr.column)))
        for tpl in filter(None, templates):
            key = str(tpl).rstrip("/").split("{")[0].rstrip("/").rsplit("/", 1)[-1]
            entities[key].add(column(source_table, re.findall(r"\{(\w+)\}", str(tpl))[0]))

    lines = [t("app.columns.header"), "|---|---|"]
    lines += [f"| **{entity_name.get(k, k)}** | {', '.join(sorted(v))} |"
              for k, v in entities.items() if len(v) > 1]
    lines += [f"| {t('app.columns.attribute')} **:{k}** | {', '.join(sorted(v))} |" for k, v in attributes.items() if len(v) > 1]
    return "\n".join(lines)


def faq():
    return idioma.localized("/app/faq.yaml")


def plain():
    return idioma.localized("/app/preguntas-simples.yaml") or {}


def show_plain(question_id, simple=True):
    """The question in simple words and what each term means, for someone outside the domain.
    In business mode the selector already shows the simple version: only the terms go here."""
    entry = plain().get(question_id)
    if not entry:
        return
    if simple:
        st.info(t("app.plain.simple", text=entry["simple"]))
    terms = entry.get("terms", {})
    if terms:
        with st.expander(t("app.plain.meaning", terms=", ".join(terms))):
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
            return False, t("app.llm.no_ollama", url=answer.OLLAMA)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True, f"Claude API · {answer.MODEL}"
    return False, t("app.llm.none")


def link_method(query):
    """How a direct SQL query identifies a drug (its text: app.link_methods.<method>), or None if it does not."""
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
        return t("app.errors.timeout", error=error.strip())
    return error.strip()


def pretty(query, approach):
    if approach in "BD":
        return sqlparse.format(query, reindent=True, keyword_case="upper", indent_width=2)
    return query.strip()


def last_ok_query(entry, approach):
    ok = [a for a in entry.get(approach, {}).get("attempts", []) if a["error"] is None]
    return ok[-1]["query"] if ok else None


def approach_name(k):
    """The evaluation's name of each approach (run.NAMES), in the interface's language."""
    return t(f"app.approach.name_{k}")


# --- Show an answer -----------------------------------------------

# The link rules as the data writes them, and the key of their text in app/textos/app.yaml
RULES = {"nombre": "name", "alias": "alias", "combinación": "combination", "régimen": "regimen", "palabras": "words"}


def rule_text(rule):
    return t(f"app.rules.{RULES[rule]}") if rule in RULES else rule
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
}


def name_of(iri):
    if iri == "https://w3id.org/rastro/activity/entity-linking":
        return t("app.evidence.entity_linking")
    return NAMES_OF.get(iri, iri)


def evidence_of(nct, name):
    """A link's evidence, requested with PROV-O. One row per source it derives from."""
    query = EVIDENCE_ONE.format(nct=nct, name=name)
    _, rows = answer.run_sparql_table(query)
    if not rows:
        return query, []
    text, matched, rule, _, activity = rows[0]
    derived = ", ".join(name_of(r[3]) for r in rows)
    lines = [("is_a", "PROV-O", t("app.evidence.is_a_value")), ("sponsor_text", "Rastro", text),
             ("matched", "Rastro", matched), ("rule", "Rastro", rule), ("derived", "PROV-O", derived),
             ("generated", "PROV-O", name_of(activity))]
    table = [{t("app.evidence.col_property"): t(f"app.evidence.{key}"), t("app.evidence.col_vocabulary"): vocabulary,
              t("app.evidence.col_value"): value} for key, vocabulary, value in lines]
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
def evidence_summary(names, language):
    """Per drug: in how many trials it was recognized and what share by its name (PROV-O); language is the cache key."""
    values = " ".join(json.dumps(n) for n in names)
    _, rows = answer.run_sparql_table(EVIDENCE_SUMMARY.format(names=values))
    totals, by_name = {}, {}
    for name, rule, n in rows:
        totals[name] = totals.get(name, 0) + int(n)
        if rule == "nombre":
            by_name[name] = int(n)
    return {name: t("app.evidence.summary", total=total, pct=round(100 * by_name.get(name, 0) / total))
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
    st.markdown(t("app.text.steps"), help=ayuda("texto"))
    text_step(1, t("app.text.question"))
    st.info(f"**{item['simple']}**")
    if TECH:
        st.caption(t("app.ask.tech_wording") + item["pregunta"])
    if st.button(t("app.ask.answer"), type="primary", key="text_answer"):
        st.session_state["text_shown"] = True
    if not st.session_state.get("text_shown"):
        return
    query = Path(item["consulta"]).read_text()
    _, rows = answer.run_sparql_table(query)
    texts = {nct: (status, drugs, why) for nct, status, drugs, why in rows}
    graph_part, _, ai_part = item["como"].partition("Un asistente de IA")

    text_step(2, t("app.text.step2_title"), t("app.text.step2_help"))
    st.markdown(graph_part.strip())
    st.metric(t("app.text.picked"), len(texts))
    with st.expander(t("app.text.query_expander"), expanded=TECH):
        st.caption(t("app.text.query_caption"))
        st.code(query, language="sparql")

    text_step(3, t("app.text.step3_title"), t("app.text.step3_help"))
    # the saved summary is data: its «como» text stays as it was written
    st.markdown(("Un asistente de IA" + ai_part).strip() if ai_part else t("app.text.ai_fallback", n=len(texts)))
    trial = t("app.text.col_trial")
    with st.expander(t("app.text.reasons_expander", n=len(texts))):
        tabla(pd.DataFrame([{trial: f"https://clinicaltrials.gov/study/{nct}", t("app.text.col_drugs"): d.lower(),
                             t("app.text.col_reason"): w} for nct, (_, d, w) in sorted(texts.items())]),
              hide_index=True, use_container_width=True,
              column_config={trial: st.column_config.LinkColumn(display_text=r"study/(.*)")})

    text_step(4, t("app.text.step4_title"))
    for group in item["motivos"]:
        links = ", ".join(f"[{nct}](https://clinicaltrials.gov/study/{nct})" for nct in group["ensayos"])
        st.markdown(t("app.text.group", reason=group["motivo"], n=len(group["ensayos"]), detail=group["detalle"],
                      links=links), unsafe_allow_html=True)

    text_step(5, t("app.text.step5_title"), t("app.text.step5_help"))
    st.markdown(t("app.text.step5_body", date=item["fecha"]))

    text_step(6, t("app.text.step6_title"), t("app.text.step6_help"))
    facts_query = Path("/ontology/queries/cq11.rq").read_text()
    _, facts = answer.run_sparql_table(facts_query)
    tabla(pd.DataFrame([{t("app.text.col_class"): m, t("app.text.col_trials"): int(n)} for m, n in facts]),
          hide_index=True, use_container_width=True)
    st.caption(t("app.text.facts_caption"))
    if TECH:
        with st.expander(t("app.text.count_expander")):
            st.code(facts_query, language="sparql")


# «¿Por qué este número?» in oncology: how a row's drug was recognized in the trials. Its texts are in
# app/textos/app.yaml (drug_why() fills them in the current language); {valor} is filled by dominio.show_why.
DRUG_WHY = {
    "query": """SELECT ?ensayo ?texto ?coincidio ?regla WHERE {
  ?d oncologia:name "{valor}" .
  ?l a oncologia:DrugLink ; oncologia:linkDrug ?d ; oncologia:linkTrial/oncologia:nctId ?ensayo ;
     oncologia:interventionText ?texto ; oncologia:matchedText ?coincidio ; oncologia:linkRule ?regla .
  FILTER (LCASE(?texto) != LCASE("{valor}"))
} LIMIT 12""",
    "nodo": "{ensayo}", "detalle": "«{coincidio}»",
}


def drug_why():
    return DRUG_WHY | {"titulo": t("app.why.title"), "explica": t("app.why.explains"), "flecha": t("app.why.arrow"),
                       "columnas": {"ensayo": t("app.why.col_trial"), "texto": t("app.why.col_text"),
                                    "coincidio": t("app.why.col_matched"), "regla": t("app.why.col_rule")}}


def show_answer(query, columns, rows, note=None):
    used, col_sources = answer.column_sources(query)
    drugs = answer_drugs(rows) if rows and "oncologia:testsDrug" in query else []
    info = sources()

    if TECH:
        st.markdown(t("app.answer.sources_used") + " · ".join(f"`{label(s)}`" for s in used), help=ayuda("fuentes_respuesta"))
    else:
        st.markdown(t("app.answer.sources") + ", ".join(info[s]["name"] for s in used if s in info),
                    help=ayuda("fuentes_respuesta"))
    if not rows:
        st.info(t("app.answer.no_results"))
    else:
        headers = ([f"{c} · {', '.join(label(s) for s in col_sources.get(c, []))}" for c in columns]
                   if TECH else list(columns))
        table = pd.DataFrame(rows, columns=headers)
        if drugs:
            summary = evidence_summary(tuple(drugs), idioma.lang())
            names = [next((v for v in row if v in summary), None) for row in rows]
            column = t("app.answer.col_recognized_tech") if TECH else t("app.answer.col_recognized")
            table[column] = [summary.get(n, "") for n in names]
        tabla(table, hide_index=True, use_container_width=True)
        if drugs:   # «¿Por qué este número?»: how Rastro recognized that drug in the trials
            drug_column = next(c for i, c in enumerate(columns) if any(r[i] in drugs for r in rows))
            dominio.show_why("oncologia", drug_why() | {"columna": drug_column}, list(columns), [list(r) for r in rows])
        shown_rows = t("app.answer.rows_one" if len(rows) == 1 else "app.answer.rows_many", n=len(rows))
        if TECH:
            st.caption(shown_rows + t("app.answer.rows_tech_tail")
                       + (t("app.answer.evidence_tech_hint") if drugs else ""))
        else:
            st.caption(shown_rows + "." + (t("app.answer.evidence_hint") if drugs else ""))

    with st.expander(t("app.answer.where_from")):
        if not TECH:
            st.markdown(t("app.answer.where_looked"))
            for s in used:
                if s == "rastro":
                    st.markdown(t("app.answer.rastro_drugs"))
                elif s in info:
                    st.markdown(t("app.answer.source_line", name=info[s]["name"], license=info[s]["license"]))
            if "openfda" in used:
                st.caption(t("app.answer.adverse_note"))
            if drugs:
                st.markdown(t("app.answer.how_recognized"))
                for name, nct, text, rule in evidence_examples(tuple(drugs)):
                    st.markdown(f"- «{text}» → **{name.lower()}**, {rule_text(rule)} · "
                                f"[{nct}](https://clinicaltrials.gov/study/{nct})")
                st.caption(t("app.answer.audit"))
            st.caption(t("app.answer.tech_hint"))
            return
        if note:
            st.caption(note)
        st.markdown(t("app.answer.step_query"))
        st.code(query, language="sparql")
        st.markdown(t("app.answer.step_sql"))
        sql = None
        try:
            sql = pretty(answer.ontop_sql(query), "B")
            st.code(sql, language="sql")
        except requests.RequestException:
            st.caption(t("app.answer.no_sql"))
        # the «Explicame la consulta» button is the same in every domain
        dominio.explain(query, sql, "oncologia")
        st.markdown(t("app.answer.step_sources"))
        info = sources()
        for s in used:
            if s == "rastro":
                st.markdown(t("app.answer.tech_rastro_line", storage=STORAGE["rastro"], note=t(STORAGE_NOTE["rastro"])))
            elif s in info:
                st.markdown(t("app.answer.tech_source_line", storage=STORAGE[s], name=info[s]["name"],
                              license=info[s]["license"], note=t(STORAGE_NOTE[s])))
        if "openfda" in used:
            st.caption(t("app.answer.adverse_tech_note"))
        drugs = answer_drugs(rows) if rows and "oncologia:testsDrug" in query else []
        if drugs:
            st.markdown(t("app.answer.step_evidence"))
            for name, nct, text, rule in evidence_examples(tuple(drugs)):
                st.markdown(f"- «{text}» → **{name.lower()}**, {rule_text(rule)} · "
                            f"[{nct}](https://clinicaltrials.gov/study/{nct})")
            examples = evidence_examples(tuple(drugs))
            if examples:
                name, nct, text, _ = examples[0]
                query, table = evidence_of(nct, name)
                st.markdown(t("app.answer.prov_intro", nct=nct, name=name.lower()))
                st.code(query, language="sparql")
                tabla(pd.DataFrame(table), hide_index=True, use_container_width=True)
                st.caption(t("app.answer.prov_caption"))


# --- Screen --------------------------------------------------------

idioma.init()   # before any text, so the first lines are already in the chosen language

st.markdown('<img src="data:image/svg+xml;base64,' + base64.b64encode(Path("/app/logo-horizontal.svg").read_bytes()).decode()
            + '" style="height:56px;margin:8px 0 4px 0" alt="Rastro">', unsafe_allow_html=True)
st.markdown(f"**{t('app.tagline')}**")
st.markdown(t("app.what"))
st.caption(t("app.how_to_read", marks=" · ".join(enlaces.label(k) for k in ("regla", "ia", "persona"))))

# Domains: oncology has its screen in this file; the others are drawn with the dominio package
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
    st.caption(t("app.sidebar.code"))
if DOMAIN.get("config"):
    dominio.render(DOMAIN["config"], TECH)
    st.stop()

with st.sidebar:
    if TECH:
        st.subheader("LLM", help=ayuda("llm"))
        st.markdown(("🟢 " if available else "⚪ ") + status)
        if not available:
            st.caption(t("app.sidebar.examples_work"))
        st.subheader(t("app.sidebar.sources"), help=ayuda("fuentes_barra"))
        for key, info in sources().items():
            st.markdown(f"{STORAGE.get(key, '')} **{info['name']}**  \n<small>{info['license']}</small>",
                        unsafe_allow_html=True)
        st.caption("🐘 Postgres · 🕸️ GraphDB")
    else:
        st.caption(t("app.sidebar.public_data"))

ask_tab, trust_tab, faq_tab, *hood_tab = st.tabs([t("app.tabs.ask"), t("app.tabs.trust"), t("app.tabs.faq")]
                                                + ([t("app.tabs.hood")] if TECH else []))
if hood_tab:
    # «Bajo el capó» is the same in the three domains
    with hood_tab[0]:
        dominio.under_the_hood("oncologia", "ontologia")
FAQ_HINT = t("app.trust.faq_hint")

# The radio keeps fixed values (the Spanish names); each one's label is app.ask.mode_<id>
MODES = {"Una pregunta de ejemplo": "example", "Una pregunta sobre textos": "texts", "Mi propia pregunta": "own"}

with ask_tab:
    mode = MODES[st.radio(t("app.ask.mode"), list(MODES), format_func=lambda m: t(f"app.ask.mode_{MODES[m]}"),
                          horizontal=True, label_visibility="visible", help=ayuda("modo"))]
    if mode == "texts":
        show_text_question()
    elif mode == "example":
        # 🧾 marks the questions whose answer brings the evidence of each link (PROV-O)
        def ask_label(q):
            linked = "oncologia:testsDrug" in (last_ok_query(saved()["questions"][q["id"]], "C") or "")
            text = plain().get(q["id"], {}).get("simple", q["question"])   # the same question in both views
            return ("🧾 " if linked else "") + text

        options = {ask_label(q): q for q in questions()}
        chosen = st.selectbox(t("app.ask.question"), list(options), key="ask_question", help=t("app.ask.question_help"))
        if TECH:
            st.caption(t("app.ask.tech_wording") + options[chosen]["question"])
        show_plain(options[chosen]["id"], simple=False)
        query = last_ok_query(saved()["questions"][options[chosen]["id"]], "C")
        # The answer is kept so «¿Por qué?» can pick a drug without losing it
        if st.button(t("app.ask.answer"), type="primary"):
            st.session_state["shown"] = (chosen, query, *answer.run_sparql_table(query))
        if st.session_state.get("shown", (None,))[0] == chosen:
            _, query, columns, rows = st.session_state["shown"]
            show_answer(query, columns, rows, note=t("app.ask.saved_note"))
    else:
        question = st.text_area(t("app.ask.question"), placeholder=t("app.ask.placeholder"), help=ayuda("propia"))
        if st.button(t("app.ask.answer"), type="primary", disabled=not available or not question.strip()):
            with st.spinner(t("app.ask.spinner")):
                result = answer.ask_rastro(question)
            if result.get("sin_datos"):
                st.warning(t("app.ask.no_data", reason=result["sin_datos"]))
            elif result["query"] is None:
                st.error(t("app.ask.no_query"))
                st.code(result["attempts"][-1]["error"] if result["attempts"] else "")
            else:
                show_answer(result["query"], result["columns"], result["rows"],
                            note=t("app.ask.attempts", n=len(result["attempts"])))
        if not available:
            st.info(t("app.ask.need_llm"))

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
    return idioma.number(value) if value == int(value) else f"{value:.1f}"


def same_answers(values):
    keys = {json.dumps(sorted(v), ensure_ascii=False) if isinstance(v, list) else json.dumps(v) for v in values}
    return len(keys) == 1


def audit_card():
    """The «Cada respuesta se puede auditar» card, with the measured coverage (layer/evidencia.py)."""
    p = Path("/layer/eval/evidencia.json")
    if not p.exists():
        return t("app.trust.audit_yes"), t("app.trust.audit_yes_detail")
    e = json.loads(p.read_text())
    return (t("app.trust.audit_pct", pct=f"{100 * e['enlaces_con_evidencia'] / e['enlaces']:.0f}"),
            t("app.trust.audit_detail", links=idioma.number(e["enlaces"]), with_source=e["columnas_con_fuente"],
              columns=e["columnas"]))


with trust_tab:
    data = saved()["questions"]
    st.markdown(t("app.trust.title"), help=ayuda("confiar"))
    st.caption(t("app.trust.caption"))
    cards = st.columns(3)
    for col, (title, value, compare, tip) in zip(cards, [
            (t("app.trust.card_same"), t("app.trust.card_same_value"), t("app.trust.card_same_without"),
             "tarjeta_consistencia"),
            (t("app.trust.card_change"), t("app.trust.card_change_value"), t("app.trust.card_change_without"),
             "tarjeta_cambio"),
            (t("app.trust.card_audit"), *audit_card(), "tarjeta_auditar")]):
        with col.container(border=True):
            st.markdown(f"**{title}**", help=ayuda(tip))
            st.markdown(f'<p style="font-size:2.4rem;line-height:1.1;margin:0">{value}</p>',
                        unsafe_allow_html=True)
            st.caption(compare)
    # The three tests, kept apart: in the technical view, one tab each, so that picking a question
    # in one test does not seem to change the others
    if TECH:
        trust_correct, trust_same, trust_change = st.tabs([t("app.trust.tab_correct"), t("app.trust.tab_same"),
                                                           t("app.trust.tab_change")])
    with trust_same if TECH else st.expander(t("app.trust.see_answers")):
        st.caption(t("app.same.caption"))
        approaches = {"B": t("app.approach.without"), "D": t("app.approach.links"), "C": t("app.approach.with")}
        if not TECH:
            del approaches["D"]
        question_column = t("app.same.col_question")
        table = []
        for row in consistency():
            line = {question_column: plain().get(row["id"], {}).get("simple", row["texts"][0])}
            for k, title in approaches.items():
                values = row["answers"][k]
                line[title] = ("✅ " if same_answers(values) else "❌ ") + " · ".join(short_answer(v) for v in values)
            table.append(line)
        tabla(pd.DataFrame(table), hide_index=True, use_container_width=True,
                     column_config={question_column: st.column_config.TextColumn(width="medium")})
        st.caption(t("app.same.legend"))
        rows = consistency()
        picked = st.selectbox(t("app.same.pick"),
                              [plain().get(r["id"], {}).get("simple", r["texts"][0]) for r in rows],
                              key="consistency_question")
        row = rows[[plain().get(r["id"], {}).get("simple", r["texts"][0]) for r in rows].index(picked)]
        asked = t("app.same.col_asked")
        detail = [{asked: text, **{title: short_answer(row["answers"][k][i]) for k, title in approaches.items()}}
                  for i, text in enumerate(row["texts"])]
        tabla(pd.DataFrame(detail), hide_index=True, use_container_width=True,
                     column_config={asked: st.column_config.TextColumn(width="large")})
        if TECH:
            with trust_correct:
                st.markdown(t("app.correct.title"))
                totals, per_question = scores()
                data = saved()["questions"]
                n = len(questions())
                st.markdown(t("app.correct.intro"))
                cols = st.columns(len(NAMES))
                for col, k in zip(cols, NAMES):
                    col.metric(approach_name(k), f"{totals[k]}/{n}")
                    col.caption(t(f"app.correct.help_{k}"))
                st.info(t("app.correct.info") + FAQ_HINT)
                with st.expander(t("app.correct.how"), expanded=True):
                    svg = base64.b64encode(Path("/app/como-funciona.svg").read_bytes()).decode()
                    st.markdown(f'<img src="data:image/svg+xml;base64,{svg}" style="width:100%">',
                                unsafe_allow_html=True)

                st.subheader(t("app.correct.per_question"))
                st.caption(t("app.correct.retry_caption"))

                def option_label(q):
                    retried = len(data[q["id"]]["B"]["attempts"]) > 1
                    return ("🔁 " if retried else "") + q["question"]

                options = {option_label(q): q for q in questions()}
                chosen = st.selectbox(t("app.ask.question"), list(options), label_visibility="collapsed",
                                      key="compare_question")
                q = options[chosen]
                show_plain(q["id"])
                entry = data[q["id"]]

                def fmt(value):
                    if value is None:
                        return t("app.correct.no_answer")
                    if isinstance(value, list):
                        return ", ".join(value[:12]) + (t("app.correct.and_more", n=len(value) - 12)
                                                        if len(value) > 12 else "")
                    return f"{value:,.0f}" if value >= 10 else f"{value:.1f}"

                def why_wrong(k):
                    custom = explanations().get(q["id"], {}).get(k)
                    if custom:
                        return custom
                    ref, got = entry["reference"], entry[k]["answer"]
                    if got is None:
                        return t("app.correct.no_query")
                    if q["kind"] == "número":
                        gap = abs(got - ref) / abs(ref) * 100 if ref else 100
                        prefix = t("app.correct.memory_number") if k == "A" else ""
                        return t("app.correct.number_wrong", prefix=prefix, got=fmt(got), ref=fmt(ref), gap=f"{gap:.0f}")
                    with admin() as conn:
                        ref_set = normalize(ref, q["items"], conn)
                        got_set = normalize(got, q["items"], conn)
                    hits = len(ref_set & got_set)
                    prefix = t("app.correct.memory_list") if k == "A" else ""
                    return (t("app.correct.list_wrong", prefix=prefix, hits=hits, total=len(ref_set))
                            + (t("app.correct.list_extra", n=len(got_set - ref_set)) if got_set - ref_set else "."))

                st.markdown(t("app.correct.right_answer", answer=fmt(entry["reference"])))
                cols = st.columns(len(NAMES))
                for col, k in zip(cols, NAMES):
                    with col:
                        ok = per_question[q["id"]].get(k)
                        st.markdown(f"#### {approach_name(k)}")
                        st.markdown(("✅ " if ok else "❌ ") + fmt(entry[k]["answer"]))
                        if not ok:
                            st.warning(t("app.correct.why_failed") + why_wrong(k))
                        query = last_ok_query(entry, k)
                        if k == "A":
                            st.caption(t("app.correct.memory"))
                            continue
                        if k == "B" and query and link_method(query):
                            st.caption(t("app.correct.method_b", method=t(f"app.link_methods.{link_method(query)}")))
                        if k == "D" and query and "linking." in query:
                            st.caption(t("app.correct.method_d"))
                        if k == "C" and query and "oncologia:testsDrug" in query:
                            st.caption(t("app.correct.method_c"))
                        if query:
                            shown = pretty(query, k)
                            attempts = len(entry[k]["attempts"])
                            seconds = entry[k].get("seconds")
                            st.caption(t("app.correct.lines", n=len(shown.splitlines()))
                                       + (f" · {seconds:.1f} s" if seconds is not None else "")
                                       + t("app.correct.attempts_one" if attempts == 1 else "app.correct.attempts_many",
                                           n=attempts))
                            st.code(shown, language="sql" if k in "BD" else "sparql")
                            history = entry[k]["attempts"]
                            if len(history) > 1:
                                with st.expander(t("app.correct.attempts_expander", n=len(history))):
                                    st.caption(t("app.correct.attempts_caption"))
                                    for i, attempt in enumerate(history, start=1):
                                        if attempt["error"]:
                                            st.markdown(t("app.correct.attempt_failed", i=i))
                                            st.error(friendly_error(attempt["error"]))
                                        else:
                                            st.markdown(t("app.correct.attempt_ok", i=i))
                                        st.code(pretty(attempt["query"], k), language="sql" if k in "BD" else "sparql")
                            if k == "C":
                                with st.expander(t("app.correct.sql_expander")):
                                    st.caption(t("app.correct.sql_caption"))
                                    try:
                                        st.code(pretty(answer.ontop_sql(query), "B"), language="sql")
                                    except requests.RequestException:
                                        st.caption(t("app.answer.no_sql"))

# Change scenarios: results measured with layer/cambio/cambio.sh registrar. Their title and what happens are in
# app/textos/app.yaml (app.change.scenario_<id> and app.change.what_<id>)
CHANGES = {
    "valores": {
        "sql": "UPDATE aact.studies SET overall_status = initcap(overall_status);",
        "before": "valores", "after": "valores-arreglado",
        "fix": ("SELECT nct_id, brief_title, phase, overall_status, start_date, why_stopped",
                "SELECT nct_id, brief_title, phase, upper(overall_status) AS overall_status, start_date, why_stopped"),
    },
    "renombrar": {
        "sql": "ALTER TABLE aact.studies RENAME COLUMN overall_status TO status;",
        "before": "renombrar", "after": "renombrar-arreglado",
        "fix": ("SELECT nct_id, brief_title, phase, overall_status, start_date, why_stopped",
                "SELECT nct_id, brief_title, phase, status AS overall_status, start_date, why_stopped"),
    },
}
# The scenario radio keeps fixed values (the Spanish names); each one's label is app.change.scenario_<id>
SCENARIOS = {"Cambia cómo se escribe un valor": "valores", "Cambia el nombre de una columna": "renombrar",
             "Cambia una definición de negocio": "definicion", "Se suma una fuente: Wikidata": "wikidata"}
STATUS = {"✅": "app.change.status_same", "🟡": "app.change.status_silent", "❌": "app.change.status_error"}


def change_names():
    return {"B": t("app.approach.direct"), "D": t("app.approach.links"), "C": "Rastro"}


def change_summary(totals):
    return " · ".join(f"{v} {t(STATUS[s]) if s in STATUS else s}"
                      for s, v in sorted(totals.items(), key=lambda x: x[0] != "✅"))


with trust_tab:
    with trust_change if TECH else st.expander(t("app.change.see")):
        st.caption(t("app.change.caption") + (t("app.change.caption_tech") if TECH else ""))
        change_labels = change_names()
        names = change_labels if TECH else {"B": t("app.approach.without"), "C": t("app.approach.with")}
        scenario_names = [name for name, scenario in SCENARIOS.items() if TECH or scenario != "wikidata"]
        scenario = SCENARIOS[st.radio(t("app.change.scenario"), scenario_names,
                                      format_func=lambda name: t(f"app.change.scenario_{SCENARIOS[name]}"),
                                      horizontal=True, label_visibility="visible", help=ayuda("escenario"))]
        if scenario in CHANGES:
            change = CHANGES[scenario]
            recorded = json.loads(Path("/layer/cambio/resultado.json").read_text())
            before, after = recorded[change["before"]], recorded[change["after"]]
            st.markdown(t(f"app.change.what_{scenario}"))
            if TECH:
                st.code(change["sql"], language="sql")
            st.markdown(t("app.change.before"))
            for col, k in zip(st.columns(len(names)), names):
                col.metric(names[k], f"{before['totals'][k].get('✅', 0)}/20")
                col.caption(change_summary(before["totals"][k]))
            if before["totals"]["C"].get("❌", 0) > before["totals"]["B"].get("❌", 0):
                st.caption(t("app.change.fails_loud_tech") if TECH else t("app.change.fails_loud"))
            if "Control de vocabulario" in before["vocabulary"] and "🟡" in before["vocabulary"]:
                st.warning(t("app.change.warns") + dominio.check_text(before["vocabulary"]))
            if TECH:
                st.markdown(t("app.change.fix_tech"))
                st.code(f"- {change['fix'][0]}\n+ {change['fix'][1]}", language="diff")
            else:
                st.markdown(t("app.change.fix"))
            st.markdown(t("app.change.after"))
            for col, k in zip(st.columns(len(names)), names):
                col.metric(names[k], f"{after['totals'][k].get('✅', 0)}/20")
                col.caption(change_summary(after["totals"][k]) if k == "C" else
                            change_summary(after["totals"][k]) + t("app.change.rewrite"))
            if TECH:
                with st.expander(t("app.change.affected")):
                    rows = [{t("app.same.col_question"): data[qid]["question"],
                             **{change_labels[k]: before["cells"][qid][k] for k in change_labels}}
                            for qid in before["cells"]
                            if any(not before["cells"][qid][k].startswith("✅") for k in change_labels)]
                    tabla(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.info(t("app.change.info_tech") if TECH else t("app.change.info"))
        elif scenario == "definicion" and not TECH:
            st.markdown(t("app.change.definition"))
            cols = st.columns(2)
            cols[0].metric(t("app.change.targeted_drugs"), "188", t("app.change.delta", delta="+32", before="156"))
            cols[1].metric(t("app.change.targeted_trials"), "547", t("app.change.delta", delta="+211", before="336"))
            st.info(t("app.change.definition_info"))
        elif scenario == "definicion":
            st.markdown(t("app.change.definition_tech"))
            st.code("oncologia:KinaseInhibitor    rdfs:subClassOf oncologia:TargetedTherapy .\n"
                    "oncologia:MonoclonalAntibody rdfs:subClassOf oncologia:TargetedTherapy .", language="turtle")
            st.markdown(t("app.change.definition_sql"))
            st.code("SELECT DISTINCT v1.chembl_id, v3.pref_name\n"
                    "FROM linking.drug_class v1,\n"
                    "     (VALUES ('KinaseInhibitor'), ('MonoclonalAntibody')) AS v2 (v0m0),\n"
                    "     linking.drug v3\n"
                    "WHERE v1.class = v2.v0m0 AND v1.chembl_id = v3.chembl_id", language="sql")
            st.markdown(t("app.change.hormone"))
            st.code("oncologia:HormoneTherapy rdfs:subClassOf oncologia:TargetedTherapy .", language="turtle")
            cols = st.columns(2)
            cols[0].metric(t("app.change.targeted_drugs"), "188", t("app.change.delta", delta="+32", before="156"))
            cols[1].metric(t("app.change.targeted_trials"), "547", t("app.change.delta", delta="+211", before="336"))
            st.info(t("app.change.definition_tech_info"))
        else:
            st.markdown(t("app.change.wikidata"))
            table = pd.read_csv("/layer/externo/resultado-2026-10-17.csv").rename(columns={
                "farmaco": t("app.change.wikidata_drug"), "ensayos": t("app.change.wikidata_trials"),
                "trata_segun_wikidata": t("app.change.wikidata_treats")})
            tabla(table.fillna("—"), hide_index=True, use_container_width=True)
            st.caption(t("app.change.wikidata_caption"))
            with st.expander(t("app.change.wikidata_query")):
                st.code(Path("/layer/externo/wikidata.rq").read_text(), language="sparql")
            st.info(t("app.change.wikidata_info"))

with trust_tab:
    with st.expander(t("app.trust.example")):
        st.markdown(t("app.trust.example_body"))
        st.caption(t("app.trust.example_caption"))

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
        "unified_columns": unified_columns(idioma.lang()),
    }
    # the questions that apply to every case, and then the oncology ones
    dominio.show_faq("oncologia", [(i["question"], i["answer"].format(**numbers), i.get("tecnico", False)) for i in faq()],
                     TECH, [("arquitectura-oncologia", t("app.faq.architecture")), ("ontologia", t("app.faq.ontology"))],
                     t("app.faq.diagram_title"))
