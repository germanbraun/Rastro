"""Rastro Layer: la demo.

Dos pestañas:
  Preguntar          una pregunta en lenguaje natural; la respuesta trae la fuente de
                     cada columna y un "¿cómo lo supe?" con la query
  Con y sin Rastro   las 20 preguntas de la evaluación, respondidas por el LLM solo,
                     con SQL directo y con Rastro

Se levanta con docker compose up y se abre en http://localhost:8501
"""

import json
import os
import sys
from pathlib import Path

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

EVAL = Path("/layer/eval")
SOURCE_LABEL = {"aact": "AACT", "chembl": "ChEMBL", "openfda": "openFDA", "mesh": "MeSH",
                "rastro": "enlace Rastro"}
# Dónde vive cada fuente: 🐘 Postgres (SQL) y 🕸️ GraphDB. MeSH completo está en GraphDB;
# Ontop usa una copia de su jerarquía en Postgres.
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

st.set_page_config(page_title="Rastro Layer", page_icon="🔎", layout="wide")


# --- Datos ---------------------------------------------------------

@st.cache_data
def questions():
    return yaml.safe_load((EVAL / "questions.yaml").read_text())["questions"]


@st.cache_data
def saved():
    return json.loads((EVAL / "results.json").read_text())


@st.cache_data
def explanations():
    return yaml.safe_load((EVAL / "explanations.yaml").read_text()) or {}


@st.cache_data
def sources():
    columns, rows = answer.run_sparql_table("""
        PREFIX : <https://w3id.org/rastro/ontology#>
        SELECT ?id ?name ?license WHERE { ?s a :DataSource ; :name ?name ; :license ?license .
          BIND (STRAFTER(STR(?s), "/source/") AS ?id) }""")
    return {r[0]: {"name": r[1], "license": r[2]} for r in rows}


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
    """¿Hay un LLM para preguntas libres?"""
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
    """Cómo una query de SQL directo identifica un fármaco, o None si no lo hace."""
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
    """El error de la base, con una explicación simple si es uno conocido."""
    if "statement timeout" in error:
        return ("La consulta superó el límite de 60 segundos y la base la canceló. "
                f"Error original: {error.strip()}")
    return error.strip()


def pretty(query, approach):
    if approach == "B":
        return sqlparse.format(query, reindent=True, keyword_case="upper", indent_width=2)
    return query.strip()


def last_ok_query(entry, approach):
    ok = [a for a in entry.get(approach, {}).get("attempts", []) if a["error"] is None]
    return ok[-1]["query"] if ok else None


# --- Mostrar una respuesta ----------------------------------------

def show_answer(query, columns, rows, note=None):
    used, col_sources = answer.column_sources(query)

    st.markdown("**Fuentes que usó esta respuesta:** " + " · ".join(f"`{label(s)}`" for s in used))
    if not rows:
        st.info("La consulta no devolvió resultados.")
    else:
        headers = [f"{c} · {', '.join(label(s) for s in col_sources.get(c, []))}" for c in columns]
        st.dataframe(pd.DataFrame(rows, columns=headers), hide_index=True, use_container_width=True)
        st.caption(f"{len(rows)} fila{'s' if len(rows) != 1 else ''}. "
                   "Cada columna dice de qué fuente sale.")

    with st.expander("¿Cómo lo supe?"):
        if note:
            st.caption(note)
        st.markdown("**1. La consulta que escribió el LLM**, sobre los conceptos de Rastro (SPARQL):")
        st.code(query, language="sparql")
        st.markdown("**2. El SQL que Rastro generó y ejecutó en Postgres** (lo traduce Ontop "
                    "con los mapeos; los datos no se copian a otro lado):")
        try:
            st.code(pretty(answer.ontop_sql(query), "B"), language="sql")
        except requests.RequestException:
            st.caption("Ontop no devolvió la traducción.")
        st.markdown("**3. Las fuentes:**")
        info = sources()
        for s in used:
            if s == "rastro":
                st.markdown(f"- {STORAGE['rastro']} **Enlace de Rastro**: ensayo → fármaco, resuelto "
                            "por nombre, alias y sinónimos de ChEMBL (98-99 % de precisión revisada "
                            f"a mano) · {STORAGE_NOTE['rastro']}")
            elif s in info:
                st.markdown(f"- {STORAGE[s]} **{info[s]['name']}** · licencia: {info[s]['license']}"
                            f" · {STORAGE_NOTE[s]}")
        if "openfda" in used:
            st.caption("Los eventos adversos son conteos de reportes espontáneos de FAERS: "
                       "no son frecuencias clínicas y pueden incluir duplicados.")


# --- Pantalla ------------------------------------------------------

st.title("Rastro Layer")
st.markdown("Preguntas de negocio sobre ensayos de oncología, fármacos y eventos adversos, "
            "respondidas sobre **cuatro fuentes públicas integradas**, diciendo de dónde viene cada dato.")

available, status = llm_status()
with st.sidebar:
    st.subheader("Qué es Rastro")
    st.markdown("Una capa que integra fuentes públicas de oncología y las describe con "
                "conceptos de negocio. Un LLM pregunta sobre esos conceptos en lugar de "
                "adivinar cómo se cruzan las tablas, y cada respuesta dice de dónde viene.")
    st.subheader("LLM")
    st.markdown(("🟢 " if available else "⚪ ") + status)
    if not available:
        st.caption("Las preguntas de ejemplo funcionan igual: usan las queries ya guardadas. "
                   "Para preguntas libres, configurar ANTHROPIC_API_KEY u Ollama (ver layer/README.md).")
    st.subheader("Fuentes")
    for key, info in sources().items():
        st.markdown(f"{STORAGE.get(key, '')} **{info['name']}**  \n{info['license']}  \n"
                    f"<small>{STORAGE_NOTE.get(key, '')}</small>", unsafe_allow_html=True)
    st.caption("🐘 Postgres (SQL) · 🕸️ GraphDB (grafo). Las consultas de Rastro corren en vivo "
               "sobre Postgres a través de Ontop, que traduce cada pregunta a SQL.")

ask_tab, compare_tab = st.tabs(["Preguntar", "Con y sin Rastro"])

with ask_tab:
    with st.expander("Cómo funciona", expanded=True):
        st.markdown(
            "1. **Escribís una pregunta** como la harías a un analista.\n"
            "2. **El LLM la traduce a una consulta** sobre la ontología de Rastro: un mapa de "
            "conceptos de negocio (ensayo, fármaco, target, sponsor, evento adverso) que ya sabe "
            "cómo se conectan las fuentes.\n"
            "3. **Rastro la ejecuta en vivo** sobre las cuatro fuentes, sin copiarlas: AACT "
            "(ensayos), ChEMBL (fármacos y targets), openFDA (eventos adversos) y MeSH "
            "(enfermedades y sus subtipos).\n"
            "4. **Ves la respuesta con su procedencia**: qué fuentes usó y de dónde sale cada "
            "columna. En «¿Cómo lo supe?» está la consulta exacta.")
    mode = st.radio("¿Qué querés preguntar?", ["Una pregunta de ejemplo", "Mi propia pregunta"],
                    horizontal=True, label_visibility="collapsed")
    if mode == "Una pregunta de ejemplo":
        options = {q["question"]: q for q in questions()}
        chosen = st.selectbox("Pregunta", list(options), key="ask_question")
        query = last_ok_query(saved()["questions"][options[chosen]["id"]], "C")
        if st.button("Responder", type="primary"):
            columns, rows = answer.run_sparql_table(query)
            show_answer(query, columns, rows,
                        note="La query la escribió el LLM durante la evaluación y quedó guardada; "
                             "se ejecuta ahora, en vivo, sobre los datos.")
    else:
        question = st.text_area("Pregunta", placeholder="Por ejemplo: ¿qué fármacos contra KRAS "
                                "se prueban en ensayos de cáncer de páncreas?")
        if st.button("Responder", type="primary", disabled=not available or not question.strip()):
            with st.spinner("El LLM está escribiendo la query..."):
                result = answer.ask_rastro(question)
            if result["query"] is None:
                st.error("El LLM no logró una query que funcione en tres intentos.")
                st.code(result["attempts"][-1]["error"] if result["attempts"] else "")
            else:
                show_answer(result["query"], result["columns"], result["rows"],
                            note=f"Intentos: {len(result['attempts'])}.")
        if not available:
            st.info("Para preguntas libres hace falta un LLM. Mientras tanto, probá las preguntas de ejemplo.")

with compare_tab:
    totals, per_question = scores()
    data = saved()["questions"]
    n = len(questions())
    st.markdown("El mismo LLM (Claude Opus 5.5) respondió las mismas 20 preguntas de tres formas:")
    cols = st.columns(3)
    help_text = {"A": "Sin acceso a datos: responde con lo que sabe.",
                 "B": "Escribe SQL sobre las tablas de las fuentes, tal como se cargaron, y "
                      "resuelve por su cuenta cómo se cruzan.",
                 "C": "Escribe una consulta sobre la ontología de Rastro, donde los cruces ya "
                      "están resueltos y revisados."}
    for col, k in zip(cols, NAMES):
        col.metric(NAMES[k], f"{totals[k]} de {n} correctas")
        col.caption(help_text[k])

    # Lo que muestra la comparación, con números medidos sobre las respuestas guardadas
    b_queries = [last_ok_query(e, "B") for e in data.values()]
    methods = [link_method(q) for q in b_queries if q]
    reinvented = sum(m is not None for m in methods)
    n_methods = len({m for m in methods if m})
    secs = {k: sum(e[k].get("seconds", 0) for e in data.values()) for k in ("B", "C")}
    retries = {k: sum(len(e[k]["attempts"]) > 1 for e in data.values()) for k in ("B", "C")}

    st.subheader("Qué muestra esta comparación")
    st.markdown("Con un LLM fuerte, el SQL directo acierta casi tanto como Rastro. "
                "**La diferencia no está en cuántas acierta, sino en cuánto podés confiar "
                "en cada respuesta:**")
    left, right = st.columns(2)
    with left:
        st.markdown(f"**🔁 Cada respuesta define las cosas a su manera.** En {reinvented} de {n} "
                    f"preguntas el SQL directo tuvo que inventar cómo reconocer un fármaco en el "
                    f"texto de los ensayos, y lo hizo de {n_methods} formas distintas. Dos "
                    "respuestas del mismo sistema no son comparables entre sí. Rastro usa siempre "
                    "el mismo enlace, revisado a mano (98-99 % de precisión).")
        st.markdown("**🔇 Sus errores no avisan.** Las dos respuestas incorrectas del SQL directo "
                    "parecen razonables: 488 ensayos en vez de 438. Solo se descubren revisando "
                    "ensayo por ensayo.")
    with right:
        st.markdown(f"**⏱️ Más lento y más frágil.** Las 20 queries del SQL directo tardan "
                    f"{secs['B']:.0f} s en total y {retries['B']} necesitaron un segundo intento; "
                    f"las de Rastro, {secs['C']:.0f} s y {retries['C']} reintentos. El trabajo de "
                    "integrar las fuentes se paga en cada pregunta, en lugar de una sola vez.")
        st.markdown("**🔎 Rastro dice de dónde sale cada dato.** Cada columna trae su fuente y su "
                    "licencia. Con SQL directo, la procedencia queda enterrada en la query.")
    st.subheader("Por qué Rastro acierta")
    st.markdown(
        "No es que el LLM escriba mejor una consulta que otra. **La parte difícil ya estaba "
        "resuelta y revisada antes de que llegara la pregunta.**\n\n"
        "En casi todas las preguntas, lo difícil es saber qué ensayos prueban qué fármaco: AACT "
        "nombra las intervenciones en texto libre («Pembrolizumab 200 mg», «rhuMAb HER2», "
        "«PTK787») y ChEMBL tiene los fármacos con sus nombres y sinónimos.")
    left, right = st.columns(2)
    with left:
        st.markdown(
            "**Sin Rastro**, el LLM resuelve ese enlace dentro de cada consulta, sobre la marcha:\n"
            "- **Lento:** compara cada nombre y sinónimo con el texto de unas 130.000 "
            "intervenciones. Tres consultas superaron el límite de 60 segundos y hubo que "
            "reescribirlas.\n"
            "- **Con huecos que nadie revisa:** buscando pedazos de nombres, «humab» coincidió "
            "con «rhuMAb HER2» (trastuzumab) y contó ensayos que no eran anti-EGFR. Exigiendo el "
            "nombre exacto, perdió «PTK787» (vatalanib).")
    with right:
        st.markdown(
            "**Con Rastro**, ese enlace ya existe:\n"
            "- **Se construyó una vez** con reglas explícitas (palabra entera, gana el nombre más "
            "largo, sin palabras genéricas) y se **revisó a mano: 98-99 % de precisión**.\n"
            "- **La consulta solo nombra conceptos** («ensayo prueba fármaco», «fármaco actúa "
            "sobre target») y Rastro la traduce a uniones simples sobre tablas indexadas. Tarda "
            "décimas de segundo.")
    st.info(
        "**¿Y si al SQL directo le damos las mismas tablas de enlaces?** Probablemente acertaría "
        "casi todas: la precisión viene sobre todo de la integración revisada, no del lenguaje "
        "de consulta. Lo que agrega la capa semántica de Rastro es exponer esa integración como "
        "un **vocabulario de negocio** que se documenta solo, que no cambia si cambian las tablas "
        "de abajo, que es un estándar (lo leen otras herramientas de grafos de conocimiento) y que "
        "lleva la **procedencia de cada dato** incorporada.")

    with st.expander("Cómo se midió"):
        st.markdown("- Una respuesta es correcta si un número está a menos del 5 % del valor real, "
                    "o si una lista coincide en al menos un 80 %.\n"
                    "- Los valores reales salen de consultas escritas a mano sobre Rastro. Como eso "
                    "podría favorecer a Rastro, cada diferencia con el SQL directo se revisó con "
                    "ensayos reales (layer/eval/adjudication.md). Esa revisión encontró errores de "
                    "Rastro, que se corrigieron antes de este resultado.\n"
                    "- Cada respuesta la generó un LLM sin ver las respuestas correctas, con la "
                    "misma consigna y los mismos reintentos para SQL y para Rastro.")

    st.subheader("Pregunta por pregunta")
    st.caption("🔁 marca las preguntas en las que el SQL directo necesitó más de un intento.")

    def option_label(q):
        retried = len(data[q["id"]]["B"]["attempts"]) > 1
        return ("🔁 " if retried else "") + q["question"]

    options = {option_label(q): q for q in questions()}
    chosen = st.selectbox("Pregunta", list(options), label_visibility="collapsed", key="compare_question")
    q = options[chosen]
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
    cols = st.columns(3)
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
            if k == "C" and query and ":testsDrug" in query:
                st.caption("Para reconocer los fármacos usó el enlace de Rastro: el mismo en todas "
                           "las preguntas, revisado a mano.")
            if query:
                shown = pretty(query, k)
                attempts = len(entry[k]["attempts"])
                seconds = entry[k].get("seconds")
                st.caption(f"{len(shown.splitlines())} líneas"
                           + (f" · {seconds:.1f} s" if seconds is not None else "")
                           + f" · {attempts} intento{'s' if attempts != 1 else ''}")
                st.code(shown, language="sql" if k == "B" else "sparql")
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
                            st.code(pretty(attempt["query"], k), language="sql" if k == "B" else "sparql")
                if k == "C":
                    with st.expander("El SQL que Rastro generó a partir de esta consulta"):
                        st.caption("Ontop traduce la consulta a SQL sobre Postgres usando los "
                                   "mapeos. Comparalo con el que el LLM tuvo que escribir a mano: "
                                   "los cruces ya resueltos son tablas simples.")
                        try:
                            st.code(pretty(answer.ontop_sql(query), "B"), language="sql")
                        except requests.RequestException:
                            st.caption("Ontop no devolvió la traducción.")
