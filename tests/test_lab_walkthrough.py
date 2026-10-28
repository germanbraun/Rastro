"""Exercise saved-run drift detection, precision and data-status semantics."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "layer"))
from extensions.gas_lab.lab_walkthrough import FACTORS, GROUPS, compare_run, same_inputs, value_status
import modelo


@pytest.fixture
def example():
    frame = pd.DataFrame({
        "idpozo": ["1", "2", "3", "4"],
        "inicio": pd.to_datetime(["2024-01-01", "2024-02-01", "2025-02-01", "2025-03-01"]),
        "grupo": ["A", "B", "A", "B"], "area": ["X", "Y", "X", "Y"],
        "pct": [50., 60., 50., np.nan], "rama": [1500., 2000., 1700., 2200.],
        "etapas": [20., 30., 25., 35.], "arena": [1000., 2000., 1500., 2500.],
        "agua": [10000., 20000., 15000., 25000.], "presion": [8000., 9000., 8500., 9500.],
        "profundidad": [2000., 2100., 2050., np.nan], "gas": [40., 60., 50., 70.],
        "fracCargada": pd.to_datetime(["2024-01-01", "2024-01-01", "2025-04-01", "2025-05-01"]),
        "reglaNombre": ["normalizado"] * 3 + ["corrección revisada"],
        "reglaSocio": ["texto"] * 3 + ["corrección revisada con documento"],
        "fracRegla": ["normalizado"] * 4,
        **{key: [f"https://example.org/{key}/{i}" for i in range(4)] for key in ("s", "fr", "st", "tr")},
    })
    fitted = modelo.entrenar(frame, **modelo.VARIABLES["B"])
    inputs = frame.rename(columns={"grupo": "operadora", "area": "concesion", "pct": "participacion"}).copy()
    inputs["de_prueba"] = inputs.inicio >= modelo.PRUEBA
    predictions = frame[["idpozo", "s", "fr", "st", "tr"]].rename(columns={
        "s": "inicio_iri", "fr": "fractura_iri", "st": "socio_iri", "tr": "trayectoria_iri"})
    predictions["gas"] = np.round(fitted["pred"], 3)
    contributions = pd.DataFrame([
        {"idpozo": row.idpozo, "factor": FACTORS[group],
         "aporte": round(float(fitted["aportes"].loc[i, variables].sum()), 3)}
        for i, row in frame.iterrows() for group, variables in GROUPS.items()])
    snapshot = {"run": {"version": "same"}, "inputs": inputs,
                "predictions": predictions, "contributions": contributions}
    return frame, fitted, snapshot


def test_matching_snapshot_and_real_contributions(example):
    frame, fitted, snapshot = example
    result = compare_run(frame, fitted, "3", snapshot, "same")
    assert result["state"] == "matched" and all(result["checks"].values())


def test_other_training_well_changed_even_when_selected_prediction_matches(example):
    frame, fitted, snapshot = example
    snapshot["inputs"].loc[0, "etapas"] += 1
    result = compare_run(frame, fitted, "3", snapshot, "same")
    assert not result["checks"]["inputs"]
    assert result["checks"]["prediction"]
    assert result["state"] == "different"


@pytest.mark.parametrize("part", ["version", "contributions", "records", "prediction"])
def test_equal_inputs_do_not_hide_other_drift(example, part):
    frame, fitted, snapshot = example
    if part == "version":
        snapshot["run"]["version"] = "old"
    elif part == "contributions":
        snapshot["contributions"].loc[snapshot["contributions"].idpozo == "3", "aporte"] += .1
    elif part == "records":
        snapshot["predictions"].loc[2, "fractura_iri"] = "https://example.org/other"
    else:
        snapshot["predictions"].loc[2, "gas"] += 1
    result = compare_run(frame, fitted, "3", snapshot, "same")
    assert result["checks"]["inputs"]
    assert not result["checks"][part]
    assert result["state"] == "different"


def test_saved_precision_and_missingness(example):
    frame, _, snapshot = example
    snapshot["inputs"].loc[0, "rama"] += .0004
    snapshot["inputs"].loc[0, "profundidad"] += .04
    assert same_inputs(frame, snapshot["inputs"])
    snapshot["inputs"].loc[3, "participacion"] = 0
    assert not same_inputs(frame, snapshot["inputs"])


def test_missing_run_or_selected_prediction_is_not_a_match(example):
    frame, fitted, snapshot = example
    assert compare_run(frame, fitted, "3", None, "same")["state"] == "missing"
    snapshot["predictions"] = snapshot["predictions"].iloc[:2]
    assert not compare_run(frame, fitted, "3", snapshot, "same")["checks"]["prediction"]


def test_status_keeps_imputation_late_arrival_and_human_review_separate(example):
    frame, _, _ = example
    assert value_status(frame.iloc[2], "rama") == ["observed", "late"]
    # A stake corrected with a document was verified by a person; an AI-reviewed company-name correction is pending.
    assert value_status(frame.iloc[3], "pct") == ["imputed"]
    assert value_status(frame.iloc[3], "grupo") == ["observed", "pending"]
    assert "pending" not in value_status(frame.iloc[3], "rama")
    assert value_status(frame.iloc[3], "profundidad") == ["imputed"]
    assert pd.isna(frame.iloc[3].pct), "Status must not replace the original missing value"


def test_every_model_input_has_exactly_one_explanation_group():
    grouped = [variable for variables in GROUPS.values() for variable in variables]
    assert sorted(grouped) == sorted(modelo.VARIABLES['B']['categorias'] + modelo.VARIABLES['B']['numeros'])


@pytest.mark.parametrize('run_id', ['captured-run', ''])
def test_audit_uses_captured_run_without_refetching_latest(run_id):
    from streamlit.testing.v1 import AppTest
    script = f'''
import dominio
from extensions.gas_lab import lab
from unittest.mock import patch
example = {{'aviso': 'Datos de prueba', 'selector': 'Paso',
 'ui': {{'run_missing': 'Sin corrida publicada'}}, 'pasos': [{{'titulo': 'Auditar', 'contenido': 'Evidencia',
 'consultas': [{{'titulo': 'Resultado', 'sparql':
   'SELECT ?value WHERE {{ VALUES ?run {{ <https://example.org/{{corrida_publicada}}> }} '
   'VALUES ?well {{ <https://example.org/{{registro_ejemplo}}> }} }}'}}] * 2}}]}}
def query(text, domain):
    assert '<https://example.org/captured-run>' in text
    assert '<https://example.org/21>' in text
    return ['value'], [[1]]
with patch.object(lab, 'published_snapshot', side_effect=AssertionError('Must not select a different run')), \\
     patch.object(dominio.common, 'run', side_effect=query):
    dominio.show_integration_example(example, 'energia', False, record='21', run_id={run_id!r})
'''
    app = AppTest.from_string(script).run(timeout=15)
    assert not app.exception, [error.message for error in app.exception]
    assert len(app.dataframe) == (2 if run_id else 0)
    assert len(app.info) == (0 if run_id else 1)


def test_calculation_renders_inside_walkthrough_expander(example):
    import yaml
    from streamlit.testing.v1 import AppTest
    frame, fitted, _ = example
    config = yaml.safe_load((Path(__file__).resolve().parents[1] / 'app/dominios/energia.yaml').read_text())['ejemplo_lab']

    def page(frame, fitted, config):
        import streamlit as st
        from extensions.gas_lab import lab
        from unittest.mock import patch
        with patch.object(lab, 'datos', return_value=(frame, frame, None, {'B': fitted})), \
             patch.object(lab, 'show_source_evidence', side_effect=lambda *args, **kwargs: st.caption('Source panel')):
            with st.expander('Lab walkthrough'):
                lab.show_calculation(pozo='3', config=config)

    app = AppTest.from_function(page, args=(frame, fitted, config)).run(timeout=15)
    assert not app.exception, [error.message for error in app.exception]
    assert len(app.dataframe) == 2
    assert len(app.expander) == 1
