"""Rastro: the app's frame. It knows no domain.

The logo, the language, the view switch (business or «Ver detalles técnicos») and the domain selector; each domain
(app/dominios.yaml) is drawn by the shared template (app/dominio/) from its configuration file, plus the code its
extension adds (app/extensions/<name>/).

It starts with docker compose up and opens at http://localhost:8501
"""

import base64
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, "/layer")

import dominio  # noqa: E402  (a domain's screen from its configuration)
from dominio import ayuda  # noqa: E402  (the «?» icons)
import enlaces  # noqa: E402  (one mark for a link's review status)
import idioma  # noqa: E402  (the interface language: Spanish by default, English on request)
import inicio  # noqa: E402  (the start page: the demo or the wizard's sketch)
import wizard  # noqa: E402  (a sketch of the wizard, to discuss)
from idioma import t  # noqa: E402

st.set_page_config(page_title="Rastro", page_icon="/app/logo.svg", layout="wide")
idioma.init()   # before any text, so the first lines are already in the chosen language

st.markdown('<img src="data:image/svg+xml;base64,' + base64.b64encode(Path("/app/logo-horizontal.svg").read_bytes()).decode()
            + '" style="height:56px;margin:8px 0 4px 0" alt="Rastro">', unsafe_allow_html=True)
st.markdown(f"**{t('app.tagline')}**")
st.markdown(t("app.what"))

# Where the visit starts: the start page with its two cards, the demo (today's app) or the wizard's sketch
PLACE = inicio.place()
if PLACE != "demo":
    with st.sidebar:
        idioma.selector()
        if PLACE == "wizard":
            inicio.back_button()
    if PLACE == "start":
        inicio.show_start()
    else:
        wizard.show()
    st.stop()
st.caption(t("app.how_to_read", marks=" · ".join(enlaces.label(k) for k in ("regla", "ia", "persona"))))

# A new domain is listed from the start (method.py new-domain) with «preguntas: []» and stays hidden until it has a
# question; a domain with a screen of its own (oncology) has no «preguntas» key and always shows
DOMAINS = [d for d in idioma.localized("/app/dominios.yaml")
           if (dominio.load_config(d["config"]) or {}).get("preguntas", True)]
with st.sidebar:
    # The demo is the first domain; the others show with «Ver detalles técnicos», as proof that the same Rastro
    # works for other data
    idioma.selector()
    inicio.back_button()
    TECH = st.toggle(t("app.technical"), value=False, help=t("app.technical_help"))
    DOMAIN = (st.radio(t("app.domain"), DOMAINS, format_func=lambda d: d["name"], key="domain", help=ayuda("dominio"))
              if TECH else DOMAINS[0])
    st.caption(t("app.sidebar.code"))
dominio.render(DOMAIN["config"], TECH)
