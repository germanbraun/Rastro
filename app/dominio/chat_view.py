"""«Conversar con los datos»: a chat over the domain's business dictionary (layer/chat.py), in Preguntar.

Each answer is in words, with its data and evidence below (the same view as a free question), and any number the
answer says that is not in its result is flagged. It is how a free question is asked in every domain; its example
is the domain's «ejemplo_libre».
"""
from pathlib import Path

import streamlit as st
import yaml

import answer
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
            # A toggle, not an expander: the answer's own evidence is an expander, and Streamlit does not nest them
            if st.toggle(idioma.t("dominio.chat.data"), key=f"{cfg['domain']}_chat_data_{index}"):
                if tech:
                    st.code(turn["query"], language="sparql")
                answers.show_answer(cfg, tech, turn["query"], turn["columns"], turn["rows"],
                                    note=idioma.t("dominio.render.attempts", n=len(turn["attempts"])),
                                    where=f"chat{index}")


def recorded_next(domain, history):
    """With the recorded conversations (RASTRO_PROVIDER=replay), the questions that have a recorded answer now: the
    first one of every conversation or, once one is under way, its next question. Each is asked as written."""
    path = Path(answer.__file__).parent / domain / "chat" / "conversaciones.yaml"
    if not path.exists():
        return []
    asked = [turn["question"] for turn in history]
    nexts = []
    for conversation in yaml.safe_load(path.read_text())["conversations"]:
        questions = [turn["question"] for turn in conversation["turns"]]
        if questions[:len(asked)] == asked and len(asked) < len(questions):
            nexts.append(questions[len(asked)])
    return nexts


def recorded_buttons(domain, history, key):
    """The recorded questions as buttons, so the demo asks them exactly as recorded. Returns the one clicked."""
    if idioma.lang() != "es":
        st.caption(idioma.t("dominio.chat.recorded_spanish"))
        return None
    options = recorded_next(domain, history)
    if not options:
        st.caption(idioma.t("dominio.chat.recorded_done"))
        return None
    st.caption(idioma.t("dominio.chat.recorded"))
    chosen = None
    for i, option in enumerate(options):
        if st.button(option, key=f"{key}_recorded_{len(history)}_{i}"):
            chosen = option
    return chosen


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
    failed = st.session_state.pop(f"{key}_failed", None)   # (question, error) of a turn the model did not answer
    if failed:
        common.model_failed(failed[1], tech, question=failed[0])
    example = cfg.get("ejemplo_libre") or idioma.t("dominio.chat.placeholder")
    question = st.chat_input(example, key=f"{key}_input")
    if answer.PROVIDER == "replay":
        question = recorded_buttons(domain, history, key) or question
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"), st.spinner(idioma.t("dominio.chat.thinking")):
            try:
                history.append(chat.turn(question, history, domain, idioma.lang()))
            except Exception as error:  # noqa: BLE001 - any model failure is said in plain words, not as a trace
                st.session_state[f"{key}_failed"] = (question, common.error_text(error))
        st.rerun()
