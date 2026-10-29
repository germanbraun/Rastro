"""«Método» (technical view): where a domain stands in each step of the method, read from the evidence that already
exists (docs/method.md). Nothing is computed here: each step says what is there, whether something waits for a person
and who approves it. The wizard's skeleton, read-only.
"""
import json
import re

import pandas as pd
import streamlit as st
import yaml

import answer
import idioma

from . import common, review_view, sources_view

DONE, WAITING, MISSING = "✅", "🟡", "—"


def _json(path):
    return json.loads(path.read_text()) if path and path.exists() else None


def _count(path, pattern):
    return len(re.findall(pattern, path.read_text())) if path and path.exists() else 0


def steps(domain, app_cfg, loads, root=None):
    """One row per step: (step key, status, what is there). loads: each source registered in Rastro → its latest load
    date (None if never loaded); a term source that is not registered (Rastro's links, a model) is not counted."""
    root = root or answer.ROOT
    reg = answer.DOMAINS[domain]
    method = reg.get("method", {})
    t = idioma.t
    rows = []

    evaluation = method.get("evaluation") or {}
    folder = root / evaluation["folder"] if evaluation else None
    questions_file = (folder / ("eval/questions.yaml" if evaluation.get("harness") == "current" else "questions.yaml")
                      if folder else None)
    questions = yaml.safe_load(questions_file.read_text()) if questions_file and questions_file.exists() else None
    n_questions = len(questions.get("questions", questions)) if isinstance(questions, dict) else len(questions or [])
    rows.append(("questions", DONE if n_questions else MISSING, t("dominio.method.questions", n=n_questions)))

    sources = [s for s in reg.get("term_sources", {}) if s in loads]
    loaded = {s: loads.get(s) for s in sources if loads.get(s)}
    last = max(loaded.values(), default="—")
    rows.append(("sources", DONE if sources and len(loaded) == len(sources) else WAITING if loaded else MISSING,
                 t("dominio.method.sources", loaded=len(loaded), n=len(sources), last=last)))

    ontology = root / reg["ontology"] if reg.get("ontology") else None
    rows.append(("dictionary", DONE if ontology and ontology.exists() else MISSING,
                 t("dominio.method.dictionary", classes=_count(ontology, r"\ba owl:Class\b"),
                   properties=_count(ontology, r"\ba owl:(?:Object|Datatype)Property\b"))))

    mapping = root / method["mapping"] if method.get("mapping") else None
    maps = _count(mapping, r"\ba rr:TriplesMap\b")
    rows.append(("mapping", DONE if maps else MISSING, t("dominio.method.mapping", maps=maps)))

    linker = method.get("linker") or {}
    declared = [root / p for p in linker.get("corrections", []) if (root / p).exists()]
    reviewable = review_view.files(domain, root)
    waiting = len(review_view.pending(reviewable))
    corrections = sum(len(review_view.read(p)[1]) for p in declared)
    # A corrections file with its own confirmation column (not a «motivo»): its pending rows count, but the app does
    # not review them yet
    other = sum(1 for p in declared if p not in reviewable for row in review_view.read(p)[1]
                if row.get("human_confirmation", "").strip().lower() in ("", "pending"))
    rows.append(("links", MISSING if not linker else WAITING if waiting or other else DONE,
                 t("dominio.method.links", corrections=corrections, waiting=waiting)
                 + (" " + t("dominio.method.links_other", n=other) if other else "")))

    quality = _json(root / method["quality"]["result"]) if method.get("quality") else None
    rows.append(("quality", DONE if quality else MISSING,
                 t("dominio.method.quality", rules=len(quality["reglas"]), date=quality["fecha"],
                   failing=sum(r["fallas"] for r in quality["reglas"])) if quality else t("dominio.method.not_built")))

    result = _json(folder / "resultados.json") if folder else None
    if result:
        from method import publication_errors
        correct = (result.get("totals", {}).get("C") or {}).get("correct", "—")
        pending = bool(publication_errors(reg, root))
        rows.append(("evaluate", WAITING if pending else DONE,
                     t("dominio.method.evaluate", correct=correct, n=len(result.get("questions", {})),
                       date=result.get("date", "—"))
                     + (" " + t("dominio.method.references_pending") if pending else "")))
    else:
        rows.append(("evaluate", MISSING, t("dominio.method.not_built")))

    validated = len(common.validated_questions(app_cfg)) if app_cfg else 0
    shown = len((app_cfg or {}).get("preguntas", []))
    rows.append(("show", DONE if shown and validated == shown else WAITING if shown else MISSING,
                 t("dominio.method.show", validated=validated, n=shown)))

    tests = root / method["change_tests"] if method.get("change_tests") else None
    recorded = sorted(p.stem for p in tests.glob("*.json")) if tests and tests.exists() else []
    rows.append(("maintain", DONE if recorded else MISSING,
                 t("dominio.method.maintain", tests=", ".join(recorded) or "—")))
    return rows


def show_method(cfg):
    domain = cfg["domain"]
    st.markdown(idioma.t("dominio.method.intro"))
    reg = answer.DOMAINS[domain]
    sources = tuple(s for s in reg.get("term_sources", {}) if s != "rastro")
    records = sources_view.load_records(sources) if sources else {}   # only the sources registered in Rastro
    loads = {s: max((t[3] for t in r["tables"]), default=None) for s, r in records.items()}
    rows = steps(domain, cfg, loads)
    headers = [idioma.t(f"dominio.method.col_{c}") for c in ("step", "status", "evidence", "approves")]
    table = pd.DataFrame([dict(zip(headers, (idioma.t(f"dominio.method.step_{key}"), status, evidence,
                                             idioma.t(f"dominio.method.approves_{key}"))))
                          for key, status, evidence in rows])
    common.tabla(table, key=f"{domain}_method")
    st.caption(idioma.t("dominio.method.legend"))
