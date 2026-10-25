"""Select and export an alternative gas model; runtime readers need no tree libraries."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import modelo

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / 'data/cache/gas-alternative/model.json'
ALGORITHMS = {'rf': 'Random Forest', 'xgb': 'XGBoost', 'lgbm': 'LightGBM'}
LABELS = {**ALGORITHMS, **{f'{name}_direct': label for name, label in ALGORITHMS.items()}}
INPUT_COLUMNS = ['idpozo', 'inicio', 'grupo', 'area', 'pct', *modelo.FRACTURA_B, 'profundidad',
                 'gas', 'fracCargada', 's', 'fr', 'st', 'tr', 'reglaNombre', 'reglaSocio']


def input_fingerprint(frame):
    rows = []
    for _, row in frame.sort_values('idpozo').iterrows():
        values = []
        for column in INPUT_COLUMNS:
            value = row.get(column)
            if pd.isna(value):
                value = None
            elif isinstance(value, (pd.Timestamp, np.datetime64)):
                value = pd.Timestamp(value).isoformat()
            elif isinstance(value, (int, float, np.number)):
                value = round(float(value), 6)
            else:
                value = str(value)
            values.append(value)
        rows.append(values)
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def code_fingerprint():
    files = [Path(__file__), Path(modelo.__file__), Path(__file__).with_name('thesis_pipeline.py'),
             Path(__file__).with_name('compare_trees.py')]
    return hashlib.sha256(b''.join(path.read_bytes() for path in files)).hexdigest()


def compatible(artifact, frame):
    return artifact.get('code_sha256') == code_fingerprint() and artifact.get('input_sha256') == input_fingerprint(frame)


def specs():
    from thesis_pipeline import model_specs
    return model_specs()


def fit(frame, path, name, cutoff):
    from compare_trees import design
    train = frame.inicio < cutoff
    variables = modelo.VARIABLES[path]
    x = design(frame, variables['categorias'], variables['numeros'], train)
    estimator = specs()[name.removesuffix('_direct')]
    target = frame.loc[train, 'gas'].to_numpy()
    direct = name.endswith('_direct')
    estimator.fit(x.loc[train].to_numpy(), target if direct else np.log1p(target * 1000))
    output = estimator.predict(x.to_numpy())
    predictions = output if direct else np.expm1(output) / 1000
    if not np.isfinite(predictions).all():
        raise ValueError('Nonfinite alternative predictions')
    return estimator, x, predictions


def score(actual, predicted):
    return {'mae': float(np.abs(actual - predicted).mean()), 'r2': modelo.r2(predicted, actual)}


def first_path(estimator, x, name):
    """A real first-tree path, explicitly not an explanation of the full ensemble."""
    name = name.removesuffix('_direct')
    values = x.to_numpy()
    features = list(x.index)
    steps = []
    if name in ('rf', 'xgb'):
        values = values.astype(np.float32)
    if name == 'rf':
        tree = estimator.estimators_[0].tree_
        node = 0
        while tree.children_left[node] != tree.children_right[node]:
            feature = tree.feature[node]
            yes = bool(values[feature] <= tree.threshold[node])
            steps.append({'feature': features[feature], 'value': float(values[feature]),
                          'threshold': float(tree.threshold[node]), 'operator': '≤', 'yes': yes})
            node = tree.children_left[node] if yes else tree.children_right[node]
        leaf = float(tree.value[node, 0, 0])
    elif name == 'xgb':
        node = json.loads(estimator.get_booster().get_dump(dump_format='json')[0])
        while 'leaf' not in node:
            feature = int(node['split'][1:])
            yes = bool(values[feature] < node['split_condition'])
            steps.append({'feature': features[feature], 'value': float(values[feature]),
                          'threshold': float(node['split_condition']), 'operator': '<', 'yes': yes})
            node = next(child for child in node['children'] if child['nodeid'] == node['yes' if yes else 'no'])
        leaf = float(node['leaf'])
    else:
        node = estimator.booster_.dump_model()['tree_info'][0]['tree_structure']
        while 'split_feature' in node:
            if node['decision_type'] != '<=':
                raise ValueError('Unsupported first-tree decision')
            feature = node['split_feature']
            yes = bool(values[feature] <= node['threshold'])
            steps.append({'feature': features[feature], 'value': float(values[feature]),
                          'threshold': float(node['threshold']), 'operator': '≤', 'yes': yes})
            node = node['left_child' if yes else 'right_child']
        leaf = float(node['leaf_value'])
    return {'steps': steps, 'leaf': leaf}


def generate(a, b):
    candidates = []
    validation = b.loc[b.inicio < modelo.PRUEBA].reset_index(drop=True)
    for name in LABELS:
        folds = []
        for year in (2023, 2024):
            frame = validation.loc[validation.inicio < pd.Timestamp(year + 1, 1, 1)].reset_index(drop=True)
            test = frame.inicio >= pd.Timestamp(year, 1, 1)
            _, _, pred = fit(frame, 'B', name, pd.Timestamp(year, 1, 1))
            folds.append({'year': year, 'train': int((~test).sum()), 'test': int(test.sum()),
                          **score(frame.loc[test, 'gas'].to_numpy(), pred[test])})
        candidates.append({'name': name, 'label': LABELS[name], 'validation': folds,
                           'target_transform': 'direct' if name.endswith('_direct') else 'log',
                           'selection_mae': float(np.mean([fold['mae'] for fold in folds]))})
    selected = min(candidates, key=lambda c: (c['selection_mae'], c['name']))['name']
    evaluation = []
    fitted = {}
    for name in LABELS:
        estimator, x, pred = fit(b, 'B', name, modelo.PRUEBA)
        test = b.inicio >= modelo.PRUEBA
        evaluation.append({'name': name, 'label': LABELS[name],
                           'target_transform': 'direct' if name.endswith('_direct') else 'log',
                           **score(b.loc[test, 'gas'].to_numpy(), pred[test])})
        if name == selected:
            fitted = {'estimator': estimator, 'x': x, 'pred': pred}
    _, _, raw_pred = fit(a, 'A', selected, modelo.PRUEBA)
    ridge = modelo.modelos(a, b)
    test = b.inicio >= modelo.PRUEBA
    rows = []
    for i, row in b.loc[test].iterrows():
        rows.append({'idpozo': str(row.idpozo), 'prediction': float(fitted['pred'][i]), 'actual': float(row.gas),
                     'raw_prediction': float(raw_pred[i]), 'ridge_prediction': float(ridge['B']['pred'][i]),
                     'path': first_path(fitted['estimator'], fitted['x'].loc[i], selected),
                     'records': {key: None if pd.isna(row.get(key)) else str(row[key]) for key in ['s', 'fr', 'st', 'tr']}})
    return {'created_utc': datetime.now(timezone.utc).isoformat(), 'code_sha256': code_fingerprint(),
            'input_sha256': input_fingerprint(b), 'selected': selected, 'selected_label': LABELS[selected],
            'target_transform': 'direct' if selected.endswith('_direct') else 'log',
            'selection_rule': 'minimum_mean_annual_mae_2023_2024', 'candidates': candidates,
            'test_2025': evaluation, 'train': int((~test).sum()), 'test': int(test.sum()),
            'ridge_test': score(b.loc[test, 'gas'].to_numpy(), ridge['B']['pred'][test]),
            'raw_test': score(a.loc[test, 'gas'].to_numpy(), raw_pred[test]), 'predictions': rows}


def main():
    a, b = modelo.preparar(modelo.sql_local(modelo.SQL_GAS), modelo.sql_local(modelo.SQL_A),
                           modelo.sparql_local(modelo.SPARQL_B))
    assert a.idpozo.equals(b.idpozo)
    np.testing.assert_allclose(a.gas, b.gas, rtol=0, atol=.00050001)
    result = generate(a, b)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    report = {k: v for k, v in result.items() if k != 'predictions'}
    (ROOT / 'docs/experiments/gas-alternative/results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
