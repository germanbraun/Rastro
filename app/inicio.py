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
        figures = [(f["valor"].format(**values), f.get("etiqueta", ""), f["texto"].format(**values))
                   for f in cfg["portada"]["cifras"]]
    except Exception:   # noqa: BLE001 - a service down or a missing measurement: the start page still shows
        return
    st.markdown(idioma.t("inicio.problem"))
    for column, (value, label, text) in zip(st.columns(len(figures)), figures):
        with column.container(border=True):
            st.markdown(f'<div style="font-size:2.1rem;font-weight:700;color:#2F6FB5;line-height:1.1">{value}</div>'
                        f'<div style="font-weight:600;color:#14213D;margin:2px 0 6px">{label}</div>',
                        unsafe_allow_html=True)
            st.caption(text)


def measured(cfg):
    """The two numbers the savings estimate takes from the demo: the share of queries a renamed column broke (change
    test) and the places a corrected value lives without Rastro (correction test)."""
    trust = contraste.trust_numbers(cfg, {}, common.read_json(cfg["cambio"]), {}, str)
    return {"broken": trust["b_broken"] / trust["b_answerable"], "b": trust["b_broken"], "n": trust["b_answerable"],
            "places": common.read_json(cfg["correccion"])["lugares_sin_rastro"]}


def show_savings(cfg):
    """«¿Cuánto ahorraría tu equipo?»: an estimate with the visitor's assumptions and the demo's two measured numbers;
    the formula is shown, and nothing here is presented as a measurement."""
    try:
        m = measured(cfg)
    except Exception:   # noqa: BLE001 - without the measurements, no estimate
        return
    t = idioma.t
    with st.expander(t("inicio.savings_title")):
        st.caption(t("inicio.savings_intro"))
        a, b = st.columns(2)
        queries = a.number_input(t("inicio.savings_queries"), 1, 10000, 40, key="sav_queries")
        changes = a.number_input(t("inicio.savings_changes"), 0, 365, 6, key="sav_changes")
        fix_hours = a.number_input(t("inicio.savings_fix_hours"), 0.0, 100.0, 2.0, 0.5, key="sav_fix")
        corrections = b.number_input(t("inicio.savings_corrections"), 0, 1000, 12, key="sav_corr")
        place_hours = b.number_input(t("inicio.savings_place_hours"), 0.0, 100.0, 0.5, 0.25, key="sav_place")
        rate = b.number_input(t("inicio.savings_rate"), 0, 1000, 60, 5, key="sav_rate")
        st.caption(t("inicio.savings_measured", b=m["b"], n=m["n"], broken=idioma.number(100 * m["broken"], 0),
                     places=m["places"]))
        without = changes * queries * m["broken"] * fix_hours + corrections * m["places"] * place_hours
        with_rastro = changes * fix_hours + corrections * place_hours   # one line per change, one place per correction
        saved = without - with_rastro
        x, y, z = st.columns(3)
        x.metric(t("inicio.savings_without"), f"{idioma.number(without, 0)} h")
        y.metric(t("inicio.savings_with"), f"{idioma.number(with_rastro, 0)} h")
        z.metric(t("inicio.savings_saved"), f"US$ {idioma.number(saved * rate, 0)}")
        st.caption(t("inicio.savings_formula"))


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
    st.markdown(f"### {idioma.t('inicio.choose')}")
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
    if cfg.get("portada"):
        show_savings(cfg)


def back_button():
    """In the sidebar: back to the start page."""
    st.button(idioma.t("inicio.back"), key="inicio_back", on_click=go, args=("start",), use_container_width=True)
