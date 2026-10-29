"""«Armá tu capa semántica»: a sketch of the wizard (docs/customer-deployment.md, section 3), to discuss and try ideas.

Nothing here connects, stores or calls a model: each step says what the agent would have done, what the person
decides, where that piece already exists in the app (app/wizard.yaml), and shows it with the demo's real pieces, read
only: its sources, the approved question closest to what you type, its dictionary, its doubtful links, its quality
rules and the method's state. It asks for no password and takes no files.
"""
import base64
import re
from pathlib import Path

import pandas as pd
import streamlit as st

import idioma
from dominio import common, faq, method_view, review_view, sources_view

EXAMPLE_DOMAIN = "energia"   # the demo's pieces serve as the example of each step


def steps():
    return idioma.localized("/app/wizard.yaml")["pasos"]


def example_cfg():
    return common.load_config(f"/app/dominios/{EXAMPLE_DOMAIN}.yaml")


def show():
    st.info(idioma.t("wizard.sketch"))
    with st.expander(idioma.t("wizard.requirements_title")):
        st.markdown(idioma.t("wizard.requirements"))
    all_steps = steps()
    i = min(st.session_state.get("wizard_step", 0), len(all_steps) - 1)
    st.markdown(" → ".join(f"**{n + 1} · {s['titulo']}**" if n == i else f"{n + 1} · {s['titulo']}"
                           for n, s in enumerate(all_steps)))
    step = all_steps[i]
    st.subheader(step["titulo"])
    agent, person = st.columns(2)
    with agent.container(border=True):
        st.markdown(idioma.t("wizard.agent"))
        st.markdown(step["agente"])
    with person.container(border=True):
        st.markdown(idioma.t("wizard.person"))
        st.markdown(step["persona"])
    try:
        EXAMPLES[step["id"]]()
    except Exception:   # noqa: BLE001 - a sketch: an example that cannot be read now is said, not shown as an error
        st.caption(idioma.t("wizard.example_unavailable"))
    st.caption(idioma.t("wizard.today", where=step["hoy"]))
    back, _, forward = st.columns([2, 3, 2])
    if i > 0 and back.button(idioma.t("dominio.show_demo.back"), key="wizard_back"):
        st.session_state["wizard_step"] = i - 1
        st.rerun()
    if i < len(all_steps) - 1 and forward.button(idioma.t("dominio.show_demo.next"), type="primary", key="wizard_next"):
        st.session_state["wizard_step"] = i + 1
        st.rerun()


def show_sources():
    """Several sources: each one added to a list (kept only in this session), and what an inspection would show."""
    added = st.session_state.setdefault("wizard_sources", [])
    labels = {k: idioma.t(f"wizard.kind_{k}") for k in ("database", "files", "api")}
    kind = st.radio(idioma.t("wizard.source_kind"), list(labels), horizontal=True, format_func=labels.get,
                    key="wizard_kind")
    with st.form("wizard_source_form", clear_on_submit=True, border=True):
        if kind == "database":
            engine, host = st.columns([1, 2])
            engine_value = engine.selectbox(idioma.t("wizard.engine"), ["PostgreSQL", "SQL Server", "Oracle", "MySQL"])
            host_value = host.text_input(idioma.t("wizard.host"), placeholder="db.empresa.internal:5432")
            name, user = st.columns(2)
            database = name.text_input(idioma.t("wizard.database"))
            user.text_input(idioma.t("wizard.user"), placeholder="rastro_readonly")
            st.caption(idioma.t("wizard.no_password"))
            described = f"{engine_value} · {host_value or '—'}/{database or '—'}"
        elif kind == "files":
            st.file_uploader(idioma.t("wizard.files"), disabled=True)
            st.caption(idioma.t("wizard.files_note"))
            described = idioma.t("wizard.kind_files")
        else:
            url = st.text_input(idioma.t("wizard.api"), placeholder="https://datos.ejemplo.gob.ar/api/...")
            described = url or "—"
        if st.form_submit_button(idioma.t("wizard.add_source")):
            added.append({idioma.t("wizard.col_kind"): labels[kind], idioma.t("wizard.col_source"): described})
    if added:
        st.markdown(idioma.t("wizard.added", n=len(added)))
        common.tabla(pd.DataFrame(added), key="wizard_added")
        if st.button(idioma.t("wizard.clear_sources"), key="wizard_clear"):
            added.clear()
            st.rerun()
    if st.button(idioma.t("wizard.inspect"), key="wizard_inspect"):
        st.session_state["wizard_inspected"] = True
    if st.session_state.get("wizard_inspected"):
        entries = example_cfg().get("fuentes_detalle", [])
        records = sources_view.load_records(tuple(e["id"] for e in entries))
        rows = []
        for e in entries:
            record = records.get(e["id"])
            if not record:
                continue
            schemas = e.get("esquemas")
            tables = [t for t in record["tables"] if not schemas or t[0].split(".")[0] in schemas]
            rows.append({idioma.t("wizard.col_source"): e.get("nombre") or record["name"],
                         idioma.t("wizard.col_tables"): len(tables),
                         idioma.t("wizard.col_rows"): idioma.number(sum(t[1] for t in tables)),
                         idioma.t("wizard.col_loaded"): max((t[3] for t in tables), default="—")})
        st.markdown(idioma.t("wizard.found"))
        common.tabla(pd.DataFrame(rows), key="wizard_found")


def words(text):
    return set(re.findall(r"\w{4,}", text.lower()))


def show_questions():
    """You write a question; the closest approved question of the demo shows how it was defined (word overlap, no
    model)."""
    question = st.text_input(idioma.t("wizard.your_question"), placeholder=idioma.t("wizard.question_placeholder"),
                             key="wizard_question")
    if not question:
        return
    approved = common.validated_questions(example_cfg())
    item = max(approved, key=lambda q: len(words(question) & words(q["simple"] + " " + q["tecnica"])))
    st.markdown(idioma.t("wizard.closest"))
    st.info(f"**{common.md(item['simple'])}**")
    st.caption(idioma.t("wizard.defined_as") + common.md(item["tecnica"]))
    if item.get("terminos"):
        st.markdown("\n".join(f"- **{common.md(t)}:** {common.md(m)}" for t, m in faq.glossary(item["terminos"])))


def show_dictionary():
    diagram = Path(f"/app/{(example_cfg().get('diagrama') or {}).get('archivo', '')}.svg")
    st.markdown(idioma.t("wizard.dictionary_example"))
    st.markdown(f'<img src="data:image/svg+xml;base64,{base64.b64encode(diagram.read_bytes()).decode()}" '
                'style="width:100%;background:#fff;border-radius:12px;padding:8px">', unsafe_allow_html=True)


def show_links():
    waiting = review_view.pending(review_view.files(EXAMPLE_DOMAIN))
    st.markdown(idioma.t("wizard.links_example", n=len(waiting)))
    for _, _, row in waiting[:3]:
        with st.container(border=True):
            shown = [v for k, v in row.items() if v and k != "motivo"]
            st.markdown(" → ".join(f"**{common.md(v)}**" for v in shown))
            st.caption(common.md(row["motivo"]))


def show_quality():
    quality = common.read_json(example_cfg()["calidad"]["archivo"])
    st.markdown(idioma.t("wizard.quality_example", date=quality["fecha"]))
    common.tabla(pd.DataFrame([{idioma.t("wizard.col_rule"): r["nombre"],
                                idioma.t("wizard.col_failing"): r["fallas"]} for r in quality["reglas"]]),
                 key="wizard_quality")


def show_results():
    cfg = example_cfg()
    st.markdown(idioma.t("wizard.results_example"))
    rows = method_view.steps(EXAMPLE_DOMAIN, cfg, {})
    common.tabla(pd.DataFrame([{idioma.t("dominio.method.col_step"): idioma.t(f"dominio.method.step_{k}"),
                                idioma.t("dominio.method.col_status"): s} for k, s, _ in rows]), key="wizard_results")


def show_publish():
    st.markdown(idioma.t("wizard.publish_example"))
    st.code("infra/customer/install.sh <dominio>", language="bash")


EXAMPLES = {"fuentes": show_sources, "preguntas": show_questions, "diccionario": show_dictionary,
            "uniones": show_links, "calidad": show_quality, "resultados": show_results, "publicar": show_publish}
