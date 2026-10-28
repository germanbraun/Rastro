"""Protect model selection, artifact freshness and actual tree-path fidelity."""
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

import alternative
import modelo


@pytest.fixture
def inputs():
    rng = np.random.default_rng(12)
    n = 48
    b = pd.DataFrame({'idpozo': [str(i) for i in range(n)], 'grupo': ['A'] * n, 'area': ['X'] * n,
                      'inicio': pd.to_datetime(['2022-01-01'] * 20 + ['2023-01-01'] * 10 +
                                               ['2024-01-01'] * 10 + ['2025-01-01'] * 8),
                      'gas': rng.uniform(10, 100, n)})
    for col in modelo.VARIABLES['B']['numeros']:
        b[col] = rng.uniform(1, 100, n)
    a = b.rename(columns=dict(zip(['grupo', *modelo.VARIABLES['B']['numeros']],
                                  ['empresa', *modelo.VARIABLES['A']['numeros']]))).copy()
    return a, b


def test_artifact_checks_all_inputs_and_code(inputs, monkeypatch):
    _, b = inputs
    monkeypatch.setattr(alternative, 'code_fingerprint', lambda: 'same')
    artifact = {'code_sha256': 'same', 'input_sha256': alternative.input_fingerprint(b)}
    assert alternative.compatible(artifact, b.iloc[::-1])
    changed = b.copy()
    changed.loc[0, 'etapas'] += 1
    assert not alternative.compatible(artifact, changed)
    changed = b.copy()
    changed['s'] = ['https://example.org/source'] * len(b)
    assert not alternative.compatible(artifact, changed)
    monkeypatch.setattr(alternative, 'code_fingerprint', lambda: 'new')
    assert not alternative.compatible(artifact, b)


def test_selection_does_not_use_2025_targets(inputs, monkeypatch):
    a, b = inputs
    monkeypatch.setattr(alternative, 'LABELS', {'rf': 'Forest', 'other': 'Other'})
    monkeypatch.setattr(alternative, 'specs', lambda: {
        'rf': RandomForestRegressor(n_estimators=5, max_depth=2, random_state=1),
        'other': RandomForestRegressor(n_estimators=5, max_depth=3, random_state=2)})
    monkeypatch.setattr(alternative, 'first_path', lambda *args: {'steps': [], 'leaf': 0.})
    first = alternative.generate(a, b)
    changed_a, changed_b = a.copy(), b.copy()
    changed_a.loc[changed_a.inicio >= modelo.PRUEBA, 'gas'] += 1000
    changed_b.loc[changed_b.inicio >= modelo.PRUEBA, 'gas'] += 1000
    second = alternative.generate(changed_a, changed_b)
    assert first['selected'] == second['selected']
    assert first['candidates'] == second['candidates']
    assert first['test_2025'] != second['test_2025']
    np.testing.assert_allclose([p['prediction'] for p in first['predictions']],
                               [p['prediction'] for p in second['predictions']], rtol=0, atol=1e-10)


def test_first_forest_path_reaches_actual_leaf():
    x = pd.DataFrame({'etapas': [1., 2., 3., 4., 5., 6.]})
    forest = RandomForestRegressor(n_estimators=3, max_depth=2, random_state=42).fit(x.to_numpy(), [2, 4, 6, 8, 10, 12])
    for i in range(len(x)):
        path = alternative.first_path(forest, x.iloc[i], 'rf')
        np.testing.assert_allclose(path['leaf'], forest.estimators_[0].predict(x.iloc[[i]].to_numpy())[0])


def test_actual_tree_labels_render_from_domain_yaml(monkeypatch):
    from pathlib import Path
    import yaml
    from xml.etree import ElementTree
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / 'app'))
    monkeypatch.syspath_prepend(str(root / 'layer'))
    from extensions.energia.lab_alternative import tree_svg
    ui = yaml.safe_load((root / 'app/dominios/energia.yaml').read_text())['alternative_lab']
    path = {'steps': [{'feature': 'etapas', 'value': 53., 'threshold': 30., 'operator': '<', 'yes': False},
                      {'feature': 'grupo=A & B', 'value': 1., 'threshold': .5, 'operator': '≤', 'yes': False}], 'leaf': .1}
    svg = tree_svg(path, ui)
    tree = ElementTree.fromstring(svg)
    text = ''.join(tree.itertext())
    assert 'No' in text and 'Sí' in text and 'A & B' in text
    assert ui['leaf'] in text


@pytest.mark.parametrize('prediction,ridge,observed,status,errors', [
    (54., 60., 53., 'better', (1., 7.)),
    (58., 54., 53., 'worse', (5., 1.)),
    (50., 56., 53., 'tie', (3., 3.)),
    (53., 54., 53., 'better', (0., 1.)),
])
def test_well_accuracy_compares_distance_to_observed(monkeypatch, prediction, ridge, observed, status, errors):
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / 'app'))
    monkeypatch.syspath_prepend(str(root / 'layer'))
    from extensions.energia.lab_alternative import compare_errors
    result, error, baseline = compare_errors(prediction, ridge, observed)
    assert result == status
    assert (error, baseline) == errors
