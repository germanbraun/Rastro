"""Where a visit starts: the problem in three measured numbers, two cards, «Ver la demo» (today's app, oil and gas
first) and «Armá tu capa semántica» (a sketch of the wizard, app/wizard.py), and a call to talk about a pilot.
«?inicio=demo» opens the demo directly, for a presentation.

The numbers are the demo domain's «portada» (its YAML): read now from where they are measured (a contrast card, the
change test, the correction test), never typed. If one cannot be read, the page shows without them.
"""
import os

import streamlit as st

import contraste
import idioma
from dominio import answers, common

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


def numbers(cfg):
    """The values the start page's texts name: {<question>[…]} from its contrast card, {cambio[b_broken]} from the
    change test and {correccion[lugares]} from the correction test."""
    portada = cfg["portada"]
    item = next(q for q in cfg["preguntas"] if q["id"] == portada["pregunta"])
    changes = common.read_json(cfg["cambio"])
    trust = contraste.trust_numbers(cfg, {}, changes, {}, lambda v: idioma.number(v, 0))
    return {portada["pregunta"]: answers.card_numbers(item["antes_despues"], cfg["domain"]),
            "cambio": {"b_broken": trust["b_broken"]},
            "correccion": {"lugares": common.read_json(cfg["correccion"]).get("lugares_sin_rastro", "—")}}


def show_numbers(cfg):
    """The problem in three numbers, from the demo domain; nothing if they cannot be read now."""
    try:
        values = numbers(cfg)
        figures = [(f["valor"].format(**values), f["texto"].format(**values)) for f in cfg["portada"]["cifras"]]
    except Exception:   # noqa: BLE001 - a service down or a missing measurement: the start page still shows
        return
    st.markdown(idioma.t("inicio.problem"))
    for column, (value, text) in zip(st.columns(len(figures)), figures):
        with column.container(border=True):
            st.markdown(f"### {value}")
            st.caption(text)


@st.dialog(" ", width="large")
def pilot_dialog():
    st.subheader(idioma.t("inicio.pilot_title"))
    st.markdown(idioma.t("inicio.pilot_text"))
    contact = os.environ.get("RASTRO_CONTACT")   # an email, set in .env; without it, no contact line
    if contact:
        st.link_button(idioma.t("inicio.pilot_write"), f"mailto:{contact}?subject=Rastro", type="primary")


def show_start(cfg):
    """The start page; cfg is the demo domain's configuration (the first in app/dominios.yaml)."""
    if cfg.get("portada"):
        show_numbers(cfg)
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
    _, middle, _ = st.columns([1, 2, 1])
    if middle.button(idioma.t("inicio.pilot_button"), key="inicio_pilot", use_container_width=True):
        pilot_dialog()


def back_button():
    """In the sidebar: back to the start page."""
    st.button(idioma.t("inicio.back"), key="inicio_back", on_click=go, args=("start",), use_container_width=True)
