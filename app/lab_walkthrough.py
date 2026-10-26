"""Pure input-status and saved-run comparisons for the Lab walkthrough."""

import numpy as np
import pandas as pd

# Stored fields, current DataFrame columns, and the precision used by publicar().
INPUT_FIELDS = {
    "operadora": ("grupo", None), "concesion": ("area", None),
    "participacion": ("pct", .00050001),
    **{name: (name, .00050001) for name in ("rama", "etapas", "arena", "agua", "presion", "gas")},
    "profundidad": ("profundidad", .05000001),
}
GROUPS = {
    "location": ["grupo", "area", "pct"],
    "fracture": ["rama", "etapas", "arena", "agua", "presion"],
    "depth": ["profundidad"],
}
PENDING_RULE = "corrección revisada"   # linking/energia/links.sql: a company-name correction reviewed by an AI assistant
FACTORS = {
    "location": "La concesión con su operadora y socios",
    "fracture": "Cómo se fracturó el pozo",
    "depth": "La profundidad del pozo",
}


def value_status(row, variable):
    """Availability today is separate from historical arrival and human link review."""
    flags = ["imputed" if pd.isna(row[variable]) else "observed"]
    if variable in GROUPS["fracture"]:
        loaded = row.get("fracCargada")
        if pd.notna(loaded) and pd.Timestamp(loaded).to_period("M") > pd.Timestamp(row.inicio).to_period("M"):
            flags.append("late")
    # Only company-name corrections wait for a person: they come from linking/energia/correcciones.csv, reviewed by an
    # AI assistant. Stake corrections («… con documento») were verified by a person with a document, and the
    # fracturing report's company-name rule says who reported it, not whether its values are right.
    if variable == "grupo" and row.get("reglaNombre") == PENDING_RULE:
        flags.append("pending")
    return flags


def same_inputs(current, stored):
    """Compare every well, preserving missingness and persisted numeric precision."""
    if stored.empty or current.idpozo.duplicated().any() or stored.idpozo.duplicated().any():
        return False
    a = current.assign(idpozo=current.idpozo.astype(str)).set_index("idpozo").sort_index()
    b = stored.assign(idpozo=stored.idpozo.astype(str)).set_index("idpozo").sort_index()
    if not a.index.equals(b.index):
        return False
    if not (pd.to_datetime(a.inicio).dt.strftime("%Y-%m-%d") ==
            pd.to_datetime(b.inicio).dt.strftime("%Y-%m-%d")).all():
        return False
    if not ((pd.to_datetime(a.inicio) >= pd.Timestamp("2025-01-01")) == b.de_prueba).all():
        return False
    for saved, (live, tolerance) in INPUT_FIELDS.items():
        if tolerance is None:
            if not a[live].fillna("").astype(str).equals(b[saved].fillna("").astype(str)):
                return False
        else:
            x = pd.to_numeric(a[live], errors="raise").to_numpy(dtype=float)
            y = pd.to_numeric(b[saved], errors="raise").to_numpy(dtype=float)
            if not np.isclose(x, y, rtol=0, atol=tolerance, equal_nan=True).all():
                return False
    return True


def compare_run(current, fitted, well, snapshot, version):
    """Never equate a live fit with a published run using just its displayed total."""
    if snapshot is None:
        return {"state": "missing", "checks": {}}
    row = current[current.idpozo.astype(str) == str(well)].iloc[0]
    stored = snapshot["predictions"]
    selected = stored[stored.idpozo.astype(str) == str(well)]
    checks = {"version": snapshot["run"]["version"] == version,
              "inputs": same_inputs(current, snapshot["inputs"])}
    if len(selected) != 1:
        checks.update(prediction=False, contributions=False, records=False)
    else:
        saved = selected.iloc[0]
        i = current.index.get_loc(row.name)
        live_prediction = float(fitted["pred"][i])
        checks["prediction"] = bool(np.isfinite(live_prediction) and
                                    np.isclose(live_prediction, float(saved.gas), rtol=0, atol=.00050001))
        contributions = snapshot["contributions"]
        contributions = contributions[contributions.idpozo.astype(str) == str(well)]
        amounts = dict(zip(contributions.factor, contributions.aporte))
        checks["contributions"] = len(contributions) == len(FACTORS) and set(amounts) == set(FACTORS.values()) and all(
            np.isclose(float(fitted["aportes"].loc[row.name, GROUPS[g]].sum()), float(amounts[factor]),
                       rtol=0, atol=.00050001) for g, factor in FACTORS.items())
        def identity(value):
            return "" if pd.isna(value) else str(value)
        checks["records"] = all(identity(row[live]) == identity(saved[saved_name]) for live, saved_name in
                                [("s", "inicio_iri"), ("fr", "fractura_iri"),
                                 ("st", "socio_iri"), ("tr", "trayectoria_iri")])
    checks = {key: bool(value) for key, value in checks.items()}
    return {"state": "matched" if all(checks.values()) else "different", "checks": checks}
