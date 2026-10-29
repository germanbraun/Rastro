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
from . import sources_view
from . import chat_view
from . import extension


def render(cfg_path, tech):
    common.warm_up()
    cfg = common.load_config(cfg_path)
    domain = cfg["domain"]
    ext = extension.load(cfg)
    if ext and ext.has_own_screen():   # a domain older than the template keeps its own screen
        ext.show_screen(tech)
        return
    evaluation = common.read_json(cfg["evaluacion"]) if cfg.get("evaluacion") else {}
    changes = common.read_json(cfg["cambio"]) if cfg.get("cambio") else {}
    questions = common.validated_questions(cfg)
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
        # What each source is and what to watch out for, in both views, when the domain describes its sources
        if cfg.get("fuentes_detalle") and st.button(idioma.t("dominio.sources.title"), key=f"{domain}_sources_open",
                                                    use_container_width=True):
            with service_guard():
                sources_view.sources_dialog(cfg, tech)

    # «Por qué confiar» needs a measured evaluation or quality rules; a domain with neither does not show the tab
    # The business view has four tabs at most: the demo, asking, why trust and Rastro Lab; «Paso a paso» goes inside
    # «Por qué confiar». The technical view adds it and the frequent questions as tabs, and «Bajo el capó»
    # (console, dictionary, links and mappings). Each tab has a fixed internal name; only its label is translated
    has_trust = bool(cfg.get("tarjetas") or cfg.get("calidad"))
    example_tab = bool(cfg.get("ejemplo_integracion")) and (tech or not has_trust)
    names = (["demo"] if cfg.get("demo") else []) + ["ask"] + (["trust"] if has_trust else []) \
        + (["model"] if ext and ext.has_tab() else []) + (["example"] if example_tab else []) \
        + (["faq", "hood"] if tech else [])
    labels = {name: cfg["ejemplo_integracion"]["titulo"] if name == "example" else idioma.t(f"dominio.render.tab_{name}")
              for name in names}
    # Only the open section is drawn: Streamlit draws every st.tabs panel on every click, and «Por qué confiar» and
    # Rastro Lab are most of the page. The radio is styled as tabs (show_sections)
    open_tab = show_sections(names, labels, key=f"{domain}_tab")
    if open_tab == "demo":
        with service_guard():
            answers.show_demo(cfg, tech)
    elif open_tab == "example":
        with service_guard():
            answers.show_integration_example(cfg["ejemplo_integracion"], domain, tech, ext=ext)
    elif open_tab == "hood":
        with service_guard():
            hood.under_the_hood(domain, cfg.get("diagrama", {}).get("archivo"), cfg.get("calidad"))
    elif open_tab == "ask":
        with service_guard():
            show_ask(cfg, tech, domain, questions)
    elif open_tab == "trust":
        if cfg.get("ejemplo_integracion") and not example_tab:
            with st.expander(idioma.t("dominio.render.walkthrough", title=cfg["ejemplo_integracion"]["titulo"],
                                            header=cfg["ejemplo_integracion"].get("encabezado", ""))), service_guard():
                answers.show_integration_example(cfg["ejemplo_integracion"], domain, tech, ext=ext)
        trust_view.trust(cfg, tech, evaluation, changes)
    elif open_tab == "faq":
        faq.domain_faq(cfg, tech)
    elif open_tab == "model":
        with service_guard():
            ext.show_tab(tech)


def show_sections(names, labels, key):
    """The screen's sections as tabs: a horizontal radio styled like st.tabs, so only the open one is drawn."""
    st.markdown(f"""<style>
    .st-key-{key} div[role=radiogroup] {{gap:0;border-bottom:1px solid rgba(49,51,63,.2);flex-wrap:wrap}}
    .st-key-{key} div[role=radiogroup] label {{margin:0;padding:.5rem 1rem;border-bottom:2px solid transparent}}
    .st-key-{key} div[role=radiogroup] label > div:first-child {{display:none}}
    .st-key-{key} div[role=radiogroup] label:has(input:checked) {{border-bottom-color:#ff4b4b;color:#ff4b4b}}
    .st-key-{key} div[role=radiogroup] label:has(input:checked) p {{color:#ff4b4b}}
    </style>""", unsafe_allow_html=True)
    with st.container(key=key):
        return st.radio(idioma.t("dominio.render.sections"), names, format_func=labels.get, horizontal=True,
                        label_visibility="collapsed", key=f"{key}_open")


def show_ask(cfg, tech, domain, questions):
    """«Preguntar»: an example question, a question over texts, a claim to check, outside data or a free question."""
    # Fixed internal names for the modes; the radio shows (and returns) their labels
    mode_labels = {"example": idioma.t("dominio.render.mode_example"), "chat": idioma.t("dominio.render.mode_chat"),
                   "text": idioma.t("dominio.render.mode_text"),
                   "claims": (cfg.get("afirmaciones") or {}).get("titulo"), "external": (cfg.get("externo") or {}).get("titulo")}
    # Checking a claim and outside data are rarer: only in the technical view
    # The chat is how a free question is asked: it remembers the conversation and checks its numbers (chat_view)
    modes = ["example", "chat"] + (["text"] if cfg.get("texto") else []) \
        + (["claims"] if cfg.get("afirmaciones") and tech else []) + (["external"] if cfg.get("externo") and tech else [])
    by_label = {mode_labels[m]: m for m in modes}
    mode = by_label.get(st.radio(idioma.t("dominio.render.mode_label"), list(by_label), help=common.ayuda("modo"),
                                 horizontal=True, label_visibility="visible", key=f"{domain}_mode"))
    if mode in ("chat", "text"):   # what each one is for, so the two kinds of AI answer are not confused
        st.markdown(idioma.t(f"dominio.render.purpose_{mode}"))
        if tech:
            st.caption(idioma.t(f"dominio.render.purpose_{mode}_tech"))
    if mode == "chat":
        chat_view.show_chat(cfg, tech)
    elif mode == "text":
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
