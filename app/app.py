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

import pandas as pd
import psycopg
import requests
import streamlit as st
import yaml

sys.path.insert(0, "/layer")
sys.path.insert(0, "/layer/eval")

import answer  # noqa: E402
from run import NAMES, score  # noqa: E402

EVAL = Path("/layer/eval")
SOURCE_LABEL = {"aact": "AACT", "chembl": "ChEMBL", "openfda": "openFDA", "mesh": "MeSH",
                "rastro": "enlace Rastro"}

st.set_page_config(page_title="Rastro Layer", page_icon="🔎", layout="wide")


# --- Datos ---------------------------------------------------------

@st.cache_data
def questions():
    return yaml.safe_load((EVAL / "questions.yaml").read_text())["questions"]


@st.cache_data
def saved():
    return json.loads((EVAL / "results.json").read_text())


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


def last_ok_query(entry, approach):
    ok = [a for a in entry.get(approach, {}).get("attempts", []) if a["error"] is None]
    return ok[-1]["query"] if ok else None


# --- Mostrar una respuesta ----------------------------------------

def show_answer(query, columns, rows, note=None):
    used, col_sources = answer.column_sources(query)

    st.markdown("**Fuentes que usó esta respuesta:** "
                + " · ".join(f"`{SOURCE_LABEL.get(s, s)}`" for s in used))
    if not rows:
        st.info("La consulta no devolvió resultados.")
    else:
        headers = [f"{c} · {', '.join(SOURCE_LABEL.get(s, s) for s in col_sources.get(c, []))}"
                   for c in columns]
        st.dataframe(pd.DataFrame(rows, columns=headers), hide_index=True, use_container_width=True)
        st.caption(f"{len(rows)} fila{'s' if len(rows) != 1 else ''}. "
                   "Cada columna dice de qué fuente sale.")

    with st.expander("¿Cómo lo supe?"):
        if note:
            st.caption(note)
        st.markdown("**La query que escribió el LLM sobre la ontología de Rastro:**")
        st.code(query, language="sparql")
        st.markdown("**Fuentes usadas:**")
        info = sources()
        for s in used:
            if s == "rastro":
                st.markdown("- **Enlace de Rastro**: ensayo → fármaco, resuelto por nombre, alias y "
                            "sinónimos de ChEMBL (98-99 % de precisión revisada a mano)")
            elif s in info:
                st.markdown(f"- **{info[s]['name']}** · licencia: {info[s]['license']}")
        if "openfda" in used:
            st.caption("Los eventos adversos son conteos de reportes espontáneos de FAERS: "
                       "no son frecuencias clínicas y pueden incluir duplicados.")


# --- Pantalla ------------------------------------------------------

st.title("Rastro Layer")
st.markdown("Preguntas de negocio sobre ensayos de oncología, fármacos y eventos adversos, "
            "respondidas sobre **cuatro fuentes públicas integradas**, diciendo de dónde viene cada dato.")

available, status = llm_status()
with st.sidebar:
    st.subheader("LLM")
    st.markdown(("🟢 " if available else "⚪ ") + status)
    if not available:
        st.caption("Las preguntas de ejemplo funcionan igual: usan las queries ya guardadas. "
                   "Para preguntas libres, configurar ANTHROPIC_API_KEY u Ollama (ver layer/README.md).")
    st.subheader("Fuentes")
    for info in sources().values():
        st.markdown(f"**{info['name']}**  \n{info['license']}")

ask_tab, compare_tab = st.tabs(["Preguntar", "Con y sin Rastro"])

with ask_tab:
    mode = st.radio("¿Qué querés preguntar?", ["Una pregunta de ejemplo", "Mi propia pregunta"],
                    horizontal=True, label_visibility="collapsed")
    if mode == "Una pregunta de ejemplo":
        options = {q["question"]: q for q in questions()}
        chosen = st.selectbox("Pregunta", list(options))
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
    n = len(questions())
    st.markdown("El mismo LLM respondió las mismas 20 preguntas de tres formas. "
                "Una respuesta es correcta si un número está a menos del 5 % del valor real, "
                "o si una lista coincide en al menos un 80 %.")
    cols = st.columns(3)
    help_text = {"A": "Sin acceso a datos: responde con lo que sabe.",
                 "B": "Escribe SQL sobre las tablas de las fuentes, tal como se cargaron.",
                 "C": "Escribe SPARQL sobre la ontología de Rastro."}
    for col, k in zip(cols, NAMES):
        col.metric(NAMES[k], f"{totals[k]} de {n}", help=help_text[k])
    st.caption("Las diferencias entre SQL directo y Rastro se revisaron con ensayos reales: "
               "ver layer/eval/adjudication.md.")

    options = {q["question"]: q for q in questions()}
    chosen = st.selectbox("Pregunta ", list(options))
    q = options[chosen]
    entry = saved()["questions"][q["id"]]

    def fmt(value):
        if value is None:
            return "sin respuesta"
        if isinstance(value, list):
            return ", ".join(value[:12]) + (f" y {len(value) - 12} más" if len(value) > 12 else "")
        return f"{value:,.0f}" if value >= 10 else f"{value:.1f}"

    st.markdown(f"**Respuesta correcta:** {fmt(entry['reference'])}")
    cols = st.columns(3)
    for col, k in zip(cols, NAMES):
        with col:
            ok = per_question[q["id"]].get(k)
            st.markdown(f"#### {NAMES[k]}")
            st.markdown(("✅ " if ok else "❌ ") + fmt(entry[k]["answer"]))
            query = last_ok_query(entry, k)
            if query:
                attempts = len(entry[k]["attempts"])
                st.caption(f"Query de {len(query):,} caracteres · "
                           f"{attempts} intento{'s' if attempts != 1 else ''}")
                st.code(query, language="sql" if k == "B" else "sparql")
            elif k == "A":
                st.caption("Respondió de memoria, sin consultar datos.")
