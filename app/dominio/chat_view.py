"""«Conversar con los datos»: a chat over the domain's business dictionary (layer/chat.py), in Preguntar.

Each answer is in words, with its data and evidence below (the same view as a free question), and any number the
answer says that is not in its result is flagged. It is how a free question is asked in every domain; its example
is the domain's «ejemplo_libre».
"""
import streamlit as st

import chat
import idioma

from . import answers, common


def show_turn(cfg, tech, turn, index):
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant"):
        if turn.get("sin_datos"):
            st.warning(idioma.t("dominio.chat.no_data", missing=turn["sin_datos"]))
        elif not turn.get("query"):
            st.error(idioma.t("dominio.render.failed"))
        else:
            st.markdown(turn["answer"])
            if turn.get("unsupported"):
                st.warning(idioma.t("dominio.chat.unsupported", numbers=", ".join(turn["unsupported"])))
            with st.expander(idioma.t("dominio.chat.data")):
                if tech:
                    st.code(turn["query"], language="sparql")
                answers.show_answer(cfg, tech, turn["query"], turn["columns"], turn["rows"],
                                    note=idioma.t("dominio.render.attempts", n=len(turn["attempts"])),
                                    where=f"chat{index}")


def show_chat(cfg, tech):
    domain = cfg["domain"]
    key = f"{domain}_chat"
    st.caption(idioma.t("dominio.chat.intro"))
    available, _ = common.llm_status()
    if not available:
        st.info(idioma.t("dominio.render.need_llm"))
        return
    history = st.session_state.setdefault(key, [])
    for index, turn in enumerate(history):
        show_turn(cfg, tech, turn, index)
    if history and st.button(idioma.t("dominio.chat.new"), key=f"{key}_new"):
        history.clear()
        st.rerun()
    example = cfg.get("ejemplo_libre") or idioma.t("dominio.chat.placeholder")
    question = st.chat_input(example, key=f"{key}_input")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"), st.spinner(idioma.t("dominio.chat.thinking")):
            history.append(chat.turn(question, history, domain, idioma.lang()))
        st.rerun()
