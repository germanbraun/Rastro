"""Where a visit starts: a start page with two cards, «Ver la demo» (today's app, oil and gas first) and «Armá tu capa
semántica» (a sketch of the wizard, app/wizard.py). «?inicio=demo» opens the demo directly, for a presentation.
"""
import streamlit as st

import idioma

PLACES = ("start", "demo", "wizard")
# Both cards as tall as the taller one, at any width: every level inside each column fills it, and the button sits at
# the bottom of its card (scoped to the cards' own container)
SAME_HEIGHT = """<style>
.st-key-inicio_cards [data-testid=stColumn] [data-testid=stVerticalBlockBorderWrapper],
.st-key-inicio_cards [data-testid=stColumn] [data-testid=stVerticalBlock],
.st-key-inicio_cards [data-testid=stColumn] > div > div,
.st-key-inicio_cards [data-testid=stVerticalBlockBorderWrapper] > div {height: 100%}
.st-key-inicio_cards [data-testid=stHorizontalBlock] {align-items: stretch}
.st-key-inicio_cards [data-testid=stColumn] [data-testid=stElementContainer]:last-child {margin-top: auto}
</style>"""


def place():
    """Where this visit is: set once from the address (?inicio=demo|wizard), then by the cards and «← Inicio»."""
    if "inicio" not in st.session_state:
        asked = st.query_params.get("inicio")
        st.session_state["inicio"] = asked if asked in PLACES else "start"
    return st.session_state["inicio"]


def go(where):
    st.session_state["inicio"] = where


def show_start():
    st.markdown(idioma.t("inicio.choose"))
    st.markdown(SAME_HEIGHT, unsafe_allow_html=True)
    demo, wizard = st.container(key="inicio_cards").columns(2, gap="large")
    with demo.container(border=True):
        st.subheader(idioma.t("inicio.demo_title"))
        st.markdown(idioma.t("inicio.demo_text"))
        st.button(idioma.t("inicio.demo_button"), type="primary", key="inicio_demo", on_click=go, args=("demo",),
                  use_container_width=True)
    with wizard.container(border=True):
        st.subheader(idioma.t("inicio.wizard_title"))
        st.markdown(idioma.t("inicio.wizard_text"))
        st.button(idioma.t("inicio.wizard_button"), key="inicio_wizard", on_click=go, args=("wizard",),
                  use_container_width=True)


def back_button():
    """In the sidebar: back to the start page."""
    st.button(idioma.t("inicio.back"), key="inicio_back", on_click=go, args=("start",), use_container_width=True)
