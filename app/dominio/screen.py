"""A domain's whole screen (render): the tabs, in the business or the technical view."""

from contextlib import contextmanager
from pathlib import Path

import requests
import streamlit as st

import answer
import idioma

from . import common
from . import answers
from . import hood
from . import trust_view
from . import faq
from . import extension


def render(cfg_path, tech):
    common.warm_up()
    cfg = common.load_config(cfg_path)
    domain = cfg["domain"]
    evaluation = common.read_json(cfg["evaluacion"]) if cfg.get("evaluacion") else {}
    changes = common.read_json(cfg["cambio"]) if cfg.get("cambio") else {}
    questions = common.validated_questions(cfg)
    ext = extension.load(cfg)
    if not questions:
        st.info(idioma.t("dominio.render.no_questions"))
        return
    if answer.DOMAINS[domain].get("method", {}).get("lifecycle") and cfg.get("tarjetas"):
        from method import publication_errors
        if publication_errors(answer.DOMAINS[domain], answer.ROOT):
            cfg = {**cfg, "tarjetas": None, "demo": None}
            st.caption(idioma.t("dominio.render.pending_review"))

    with st.sidebar:
        if tech:
            available, status = common.llm_status()
            st.subheader("LLM", help=common.ayuda("llm"))
            st.markdown(("🟢 " if available else "⚪ ") + status)
            st.subheader(idioma.t("dominio.render.sources"), help=common.ayuda("fuentes_barra"))
            with service_guard():
                for info in common.sources(domain).values():
                    st.markdown(f"🐘 **{info['name']}**  \n<small>{info['license']}</small>", unsafe_allow_html=True)
        else:
            st.caption(common.md(cfg["resumen"]))
            # In the business view the frequent questions open from here, not from a tab of their own
            if st.button(idioma.t("dominio.render.tab_faq"), key=f"{domain}_faq_open", use_container_width=True):
                faq.faq_dialog(cfg)

    # «Por qué confiar» needs a measured evaluation or quality rules; a domain with neither does not show the tab
    # The business view has four tabs at most: the demo, asking, why trust and Rastro Lab; «Paso a paso» goes inside
    # «Por qué confiar». The technical view adds it and the frequent questions as tabs, and «Bajo el capó»
    # (console, dictionary, links and mappings). Each tab has a fixed internal name; only its label is translated
    has_trust = bool(cfg.get("tarjetas") or cfg.get("calidad"))
    example_tab = bool(cfg.get("ejemplo_integracion")) and (tech or not has_trust)
    names = (["demo"] if cfg.get("demo") else []) + ["ask"] + (["trust"] if has_trust else []) \
        + (["lab"] if ext and ext.has_tab() else []) + (["example"] if example_tab else []) \
        + (["faq", "hood"] if tech else [])
    labels = [cfg["ejemplo_integracion"]["titulo"] if name == "example" else idioma.t(f"dominio.render.tab_{name}")
              for name in names]
    tabs = dict(zip(names, st.tabs(labels)))
    ask_tab, trust_tab = tabs["ask"], tabs.get("trust")
    if cfg.get("demo"):
        with tabs["demo"], service_guard():
            answers.show_demo(cfg, tech)
    if example_tab:
        with tabs["example"], service_guard():
            answers.show_integration_example(cfg["ejemplo_integracion"], domain, tech, ext=ext)
    if tech:
        with tabs["hood"], service_guard():
            hood.under_the_hood(domain, cfg.get("diagrama", {}).get("archivo"), cfg.get("calidad"))

    with ask_tab, service_guard():
        # Fixed internal names for the modes; the radio shows (and returns) their labels
        mode_labels = {"example": idioma.t("dominio.render.mode_example"), "text": idioma.t("dominio.render.mode_text"),
                       "claims": (cfg.get("afirmaciones") or {}).get("titulo"), "external": (cfg.get("externo") or {}).get("titulo"),
                       "free": idioma.t("dominio.render.mode_free")}
        # Checking a claim and outside data are rarer: only in the technical view
        modes = ["example"] + (["text"] if cfg.get("texto") else []) \
            + (["claims"] if cfg.get("afirmaciones") and tech else []) + (["external"] if cfg.get("externo") and tech else [])
        by_label = {mode_labels[m]: m for m in modes + ["free"]}
        mode = by_label.get(st.radio(idioma.t("dominio.render.mode_label"), list(by_label), help=common.ayuda("modo"),
                                     horizontal=True, label_visibility="visible", key=f"{domain}_mode"))
        if mode == "text":
            answers.show_text_question(cfg, tech)
        elif mode == "external":
            answers.show_external(cfg, tech)
        elif mode == "claims":
            answers.show_claims(cfg, tech)
        elif mode == "example":
            # The same question in both views; the technical one adds its precise wording below
            options = {q["simple"]: q for q in questions}
            chosen = st.selectbox(idioma.t("dominio.render.question"), list(options), key=f"{domain}_question",
                                  help=common.ayuda("pregunta"))
            item = options[chosen]
            if tech:
                st.caption(idioma.t("dominio.render.tech_wording") + common.md(item["tecnica"]))
                if item.get("nivel"):   # what «validated» rests on: invariants, or independent references
                    st.caption(idioma.t("dominio.render.level_independent" if item["nivel"] == "independent"
                                        else "dominio.render.level_technical"))
            if item.get("terminos"):
                terms = faq.glossary(item["terminos"])
                with st.expander(idioma.t("dominio.render.terms", terms=", ".join(t for t, _ in terms))):
                    st.markdown("\n".join(f"- **{common.md(t)}:** {common.md(m)}" for t, m in terms))
            query = Path(item["query"]).read_text()
            if st.button(idioma.t("dominio.render.answer"), type="primary", key=f"{domain}_answer"):
                st.session_state[f"{domain}_shown"] = (chosen, query, *common.run(query, domain))
            shown = st.session_state.get(f"{domain}_shown", (None,))
            if shown[0] == chosen:
                _, query, columns, rows = shown
                if item.get("antes_despues"):
                    answers.before_after(item["antes_despues"], domain)
                answers.show_answer(cfg, tech, query, columns, rows, item,
                            note=idioma.t("dominio.render.live_note"))
        else:
            available, _ = common.llm_status()
            question = st.text_area(idioma.t("dominio.render.question"), placeholder=cfg.get("ejemplo_libre", ""),
                                    key=f"{domain}_free", help=common.ayuda("propia"))
            if st.button(idioma.t("dominio.render.answer"), type="primary", disabled=not available or not question.strip(),
                         key=f"{domain}_free_answer"):
                with st.spinner(idioma.t("dominio.render.writing")):
                    result = answer.ask_rastro(question, domain, idioma.lang())
                if result.get("sin_datos"):
                    st.warning(idioma.t("dominio.render.no_data", missing=result["sin_datos"]))
                elif result["query"] is None:
                    st.error(idioma.t("dominio.render.failed"))
                else:
                    answers.show_answer(cfg, tech, result["query"], result["columns"], result["rows"],
                                note=idioma.t("dominio.render.attempts", n=len(result["attempts"])))
            if not available:
                st.info(idioma.t("dominio.render.need_llm"))

    if trust_tab:
        with trust_tab:
            if cfg.get("ejemplo_integracion") and not example_tab:
                with st.expander(idioma.t("dominio.render.walkthrough", title=cfg["ejemplo_integracion"]["titulo"],
                                                header=cfg["ejemplo_integracion"].get("encabezado", ""))), service_guard():
                    answers.show_integration_example(cfg["ejemplo_integracion"], domain, tech, ext=ext)
            trust_view.trust(cfg, tech, evaluation, changes)

    if tech:
        with tabs["faq"]:
            faq.domain_faq(cfg, tech)
    # Rastro Lab last: the first time after a data change it trains the model, and the other tabs should not wait
    if "lab" in tabs:
        with tabs["lab"], service_guard():
            ext.show_tab(tech)


@contextmanager
def service_guard():
    """If the service that answers over the data (Ontop) or the database is down, say so in plain words where the
    answer would be, instead of an error trace; the rest of the screen keeps working."""
    import psycopg
    try:
        yield
    except (requests.ConnectionError, requests.Timeout, psycopg.OperationalError) as error:
        what = "database" if isinstance(error, psycopg.OperationalError) else "ontop"
        st.warning(idioma.t("dominio.service_down", what=idioma.t(f"dominio.service_down_{what}")))
        st.caption(idioma.t("dominio.service_down_admin"))
