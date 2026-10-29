"""«Uniones para confirmar»: a person confirms or rejects the corrections an AI assistant reviewed (Por qué confiar).

The corrections are the domain's reviewed CSVs (`method.linker.corrections` in layer/dominios.yaml) that keep a
«motivo»; a row waits for a person while its motivo says so (enlaces.AI). Confirming rewrites that sentence with who
confirmed it, when and with which document, so the link shows as confirmed by a person (enlaces.status). Rejecting
moves the row to <file>-rechazadas.csv with who, when and why. Either reaches the answers when Rastro is rebuilt
(the domain's linker, then its Ontop); a rejection changes the data, so the saved answers are measured again.
"""
import csv
import datetime
import io
from pathlib import Path

import streamlit as st

import answer
import enlaces
import idioma

from . import common

AI_SENTENCE = "Revisado por un asistente de IA, a confirmar por una persona."


def files(domain, root=None):
    """The domain's reviewed corrections that keep a reason («motivo»)."""
    root = root or answer.ROOT
    paths = (answer.DOMAINS[domain].get("method", {}).get("linker") or {}).get("corrections", [])
    return [root / p for p in paths if (root / p).exists() and "motivo" in (root / p).open().readline()]


def read(path):
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        return reader.fieldnames, list(reader)


def write(path, fields, rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(out.getvalue())


def pending(paths):
    """(path, row index, row) for every correction that still waits for a person."""
    return [(path, i, row) for path in paths for i, row in enumerate(read(path)[1]) if enlaces.AI in row["motivo"]]


def confirm(path, index, person, document, today=None):
    """The person confirms the correction, with the document it rests on."""
    if not (person.strip() and document.strip()):
        raise ValueError("A confirmation needs who confirms and the document")
    fields, rows = read(path)
    date = (today or datetime.date.today()).strftime("%d/%m/%Y")
    said = f"Confirmado por {person.strip()} el {date}, con este documento: {document.strip()}."
    motivo = rows[index]["motivo"]
    rows[index]["motivo"] = motivo.replace(AI_SENTENCE, said) if AI_SENTENCE in motivo else f"{motivo} {said}"
    write(path, fields, rows)


def reject(path, index, person, reason, today=None):
    """The person rejects the correction: it leaves the file and is kept, with who, when and why, next to it."""
    if not (person.strip() and reason.strip()):
        raise ValueError("A rejection needs who rejects and why")
    fields, rows = read(path)
    row = rows.pop(index)
    write(path, fields, rows)
    rejected = path.with_name(path.stem + "-rechazadas.csv")
    old_fields, old_rows = read(rejected) if rejected.exists() else (fields + ["rechazado_por", "fecha", "razon"], [])
    date = (today or datetime.date.today()).strftime("%d/%m/%Y")
    write(rejected, old_fields, old_rows + [{**row, "rechazado_por": person.strip(), "fecha": date, "razon": reason.strip()}])


def show_review(cfg, tech):
    """The corrections waiting for a person, each with its evidence, to confirm (with a document) or reject."""
    domain = cfg["domain"]
    waiting = pending(files(domain))
    done = st.session_state.pop(f"{domain}_review_done", None)   # the last action, shown once
    if done:
        st.success(done)
    if not waiting:
        return
    with st.expander(idioma.t("dominio.review.title", n=len(waiting)), expanded=bool(done)):
        st.caption(idioma.t("dominio.review.intro"))
        person = st.text_input(idioma.t("dominio.review.person"), key=f"{domain}_review_person")
        for n, (path, index, row) in enumerate(waiting):
            with st.container(border=True):
                shown = {k: v for k, v in row.items() if k != "motivo" and v}
                st.markdown(" → ".join(f"**{common.md(v)}**" for v in shown.values()))
                st.caption(enlaces.label("ia") + " · " + common.md(row["motivo"]))
                key = f"{domain}_review_{path.stem}_{index}"
                document = st.text_input(idioma.t("dominio.review.document"), key=f"{key}_doc")
                yes, no = st.columns(2)
                if yes.button(idioma.t("dominio.review.confirm"), key=f"{key}_yes", disabled=not (person and document)):
                    confirm(path, index, person, document)
                    st.session_state[f"{domain}_review_done"] = idioma.t("dominio.review.confirmed")
                    st.rerun()
                reason = no.text_input(idioma.t("dominio.review.reason"), key=f"{key}_why", label_visibility="collapsed",
                                       placeholder=idioma.t("dominio.review.reason"))
                if no.button(idioma.t("dominio.review.reject"), key=f"{key}_no", disabled=not (person and reason)):
                    reject(path, index, person, reason)
                    st.session_state[f"{domain}_review_done"] = idioma.t("dominio.review.rejected")
                    st.rerun()
        if tech:
            linker = (answer.DOMAINS[domain]["method"].get("linker") or {}).get("service")
            ontop = (answer.DOMAINS[domain]["method"].get("ontop") or {}).get("service")
            st.caption(idioma.t("dominio.review.rebuild", linker=linker, ontop=ontop))
