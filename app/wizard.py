"""«Armá tu capa semántica»: a sketch of the wizard (docs/customer-deployment.md, section 3), to discuss and try ideas.

Nothing here connects, stores or calls a model: each step says what the agent would have done, what the person
decides, and where that piece already exists in the app (app/wizard.yaml). The first screen, «Tus fuentes», has the
form a customer would fill in; «Inspeccionar» shows, as an example, what Rastro found in the demo's own sources (read
from Rastro's load records, like «Las fuentes de datos»). It asks for no password and takes no files.
"""
import pandas as pd
import streamlit as st

import idioma
from dominio import common, sources_view

EXAMPLE_DOMAIN = "energia"   # the demo's sources serve as the example of what an inspection finds


def steps():
    return idioma.localized("/app/wizard.yaml")["pasos"]


def show():
    st.info(idioma.t("wizard.sketch"))
    all_steps = steps()
    i = min(st.session_state.get("wizard_step", 0), len(all_steps) - 1)
    st.markdown(" → ".join(f"**{n + 1} · {s['titulo']}**" if n == i else f"{n + 1} · {s['titulo']}"
                           for n, s in enumerate(all_steps)))
    step = all_steps[i]
    st.subheader(step["titulo"])
    if step["id"] == "fuentes":
        show_sources()
    agent, person = st.columns(2)
    with agent.container(border=True):
        st.markdown(idioma.t("wizard.agent"))
        st.markdown(step["agente"])
    with person.container(border=True):
        st.markdown(idioma.t("wizard.person"))
        st.markdown(step["persona"])
    st.caption(idioma.t("wizard.today", where=step["hoy"]))
    back, _, forward = st.columns([2, 3, 2])
    if i > 0 and back.button(idioma.t("dominio.show_demo.back"), key="wizard_back"):
        st.session_state["wizard_step"] = i - 1
        st.rerun()
    if i < len(all_steps) - 1 and forward.button(idioma.t("dominio.show_demo.next"), type="primary", key="wizard_next"):
        st.session_state["wizard_step"] = i + 1
        st.rerun()


def show_sources():
    """The first screen: the form to add a source, and what an inspection would show (the demo's sources)."""
    labels = {k: idioma.t(f"wizard.kind_{k}") for k in ("database", "files", "api")}
    kind = st.radio(idioma.t("wizard.source_kind"), list(labels), horizontal=True, format_func=labels.get,
                    key="wizard_kind")
    if kind == "database":
        engine, host = st.columns([1, 2])
        engine.selectbox(idioma.t("wizard.engine"), ["PostgreSQL", "SQL Server", "Oracle", "MySQL"], key="wizard_engine")
        host.text_input(idioma.t("wizard.host"), placeholder="db.empresa.internal:5432", key="wizard_host")
        name, user = st.columns(2)
        name.text_input(idioma.t("wizard.database"), key="wizard_db")
        user.text_input(idioma.t("wizard.user"), placeholder="rastro_readonly", key="wizard_user")
        st.caption(idioma.t("wizard.no_password"))
    elif kind == "files":
        st.file_uploader(idioma.t("wizard.files"), disabled=True, key="wizard_files")
        st.caption(idioma.t("wizard.files_note"))
    else:
        st.text_input(idioma.t("wizard.api"), placeholder="https://datos.ejemplo.gob.ar/api/...", key="wizard_api")
    if st.button(idioma.t("wizard.inspect"), key="wizard_inspect"):
        st.session_state["wizard_inspected"] = True
    if st.session_state.get("wizard_inspected"):
        cfg = common.load_config(f"/app/dominios/{EXAMPLE_DOMAIN}.yaml")
        entries = cfg.get("fuentes_detalle", [])
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
