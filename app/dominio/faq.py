"""«Preguntas frecuentes» and the glossary."""

import base64
from pathlib import Path

import streamlit as st

import idioma

from . import common


def glossary(terms):
    """(term, meaning) pairs. The Spanish file keys each meaning by its term; an English overlay may give an entry as
    {term, text}, so the term itself is translated too."""
    return [(m["term"], m["text"]) if isinstance(m, dict) else (t, m) for t, m in terms.items()]


def domain_faq(cfg, tech):
    diagram = cfg.get("diagrama", {})
    show_faq(cfg["domain"], [(i["pregunta"], common.md(i["respuesta"]), i.get("tecnico", False)) for i in cfg.get("faq", [])],
             tech, [(f"arquitectura-{cfg['domain']}", idioma.t("dominio.render.architecture_caption")),
                    (diagram.get("archivo"), idioma.t("dominio.render.dictionary_caption", title=diagram.get("titulo")))],
             diagram.get("titulo", idioma.t("dominio.render.dictionary")))


@st.dialog(" ", width="large")
def faq_dialog(cfg):
    st.subheader(idioma.t("dominio.render.tab_faq"))
    domain_faq(cfg, False)


def general_faq():
    return idioma.localized("/app/faq-general.yaml")


def domain_name(domain):
    return next((d["name"] for d in idioma.localized("/app/dominios.yaml") if d["id"] == domain), domain)


def show_faq(domain, specific, tech, diagrams, diagram_title="diccionario"):
    """The frequent questions: first those that apply to every case, then this case's.
    specific is a list of (question, answer, technical)."""
    general = general_faq()

    def block(items):
        for question, answer_text in items:
            with st.expander(question):
                st.markdown(answer_text)

    st.markdown(idioma.t("dominio.show_faq.all_cases"))
    block([(i["pregunta"], common.md(i["respuesta"])) for i in general if not i.get("tecnico")])
    st.markdown(idioma.t("dominio.show_faq.this_case", name=domain_name(domain)))
    block([(q, a) for q, a, t in specific if not t])
    if not tech:
        st.caption(idioma.t("dominio.show_faq.more_technical"))
        return
    st.markdown(idioma.t("dominio.show_faq.technical_all"))
    block([(i["pregunta"], common.md(i["respuesta"])) for i in general if i.get("tecnico")])
    st.markdown(idioma.t("dominio.show_faq.technical_case", name=domain_name(domain)))
    with st.expander(idioma.t("dominio.show_faq.architecture", title=diagram_title)):
        for name, caption in diagrams:
            if not name or not Path(f"/app/{name}.svg").exists():
                continue
            st.caption(caption)
            image = base64.b64encode(Path(f"/app/{name}.svg").read_bytes()).decode()
            st.markdown(f'<img src="data:image/svg+xml;base64,{image}" style="width:100%;margin-bottom:24px">',
                        unsafe_allow_html=True)
    block([(q, a) for q, a, t in specific if t])
