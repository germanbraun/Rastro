"""One mark for a link's review status, the same everywhere in the app: an automatic rule with its evidence, a
correction an AI assistant reviewed that still waits for a person, or a correction a person confirmed with a document.
"""
import idioma

AI = "a confirmar por una persona"   # linking/*/correcciones.csv: how an AI-reviewed correction says it waits for a person


def status(rule, evidence=""):
    """«regla», «ia» or «persona», from the link's rule and evidence. A reviewed correction («corrección revisada …»)
    is confirmed by a person when it names its document; otherwise an AI assistant reviewed it."""
    rule, text = str(rule or "").lower(), f"{rule or ''} {evidence or ''}".lower()
    if AI in text:
        return "ia"
    if "revisad" in rule:
        return "persona" if "documento" in text else "ia"
    return "regla"


def label(key):
    return idioma.t(f"enlaces.{key}")


def add_status(frame, rule="regla"):
    """The table with a «Estado» column first, when it has a rule column; the evidence is «evidencia» or «texto»."""
    if rule not in frame.columns:
        return frame
    evidence = next((frame[c] for c in ("evidencia", "texto") if c in frame.columns), [""] * len(frame))
    marks = [label(status(r, e)) for r, e in zip(frame[rule], evidence)]
    return frame.assign(**{label("column"): marks})[[label("column"), *frame.columns]]


def column_help():
    """The legend, as the help of the «Estado» column."""
    import streamlit as st
    return {label("column"): st.column_config.TextColumn(help=label("legend"))}
