"""Read-only comparison of gas models; does not publish or change the demo model."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor

import modelo

SEEDS = (42, 7, 123)
YEARS = (2023, 2024, 2025)


def available_inputs(frame, loaded, columns):
    """Conservative sensitivity: hide the whole aggregate if arrival is late or unknown."""
    result = frame.copy()
    month_end = result.inicio.dt.to_period('M').dt.to_timestamp() + pd.offsets.MonthBegin(1)
    unavailable = loaded.isna() | (loaded >= month_end)
    result.loc[unavailable, columns] = np.nan
    return result, int(unavailable.sum())


def design(frame, categories, numbers, train):
    """Fit means and categorical vocabulary on training rows only."""
    numeric = frame[numbers].astype(float)
    means = numeric.loc[train].mean()
    if means.isna().any():
        raise ValueError('A numeric feature has no training observations')
    cats = pd.get_dummies(frame[categories].astype(str), prefix_sep='=', dtype=float)
    vocabulary = cats.loc[train].columns[cats.loc[train].any()]
    return pd.concat([cats[vocabulary], numeric.fillna(means)], axis=1)


def metrics(actual, predicted):
    return {'mae': float(np.mean(np.abs(actual - predicted))), 'r2': modelo.r2(predicted, actual)}


def compare_fold(frame, path, year):
    end = pd.Timestamp(year + 1, 1, 1)
    frame = frame.loc[frame.inicio < end].reset_index(drop=True)
    train = frame.inicio < pd.Timestamp(year, 1, 1)
    test = ~train
    if train.sum() < 20 or test.sum() < 2:
        raise ValueError(f'Insufficient observations for {year}')
    x = design(frame, **{'categories': modelo.VARIABLES[path]['categorias'],
                        'numbers': modelo.VARIABLES[path]['numeros']}, train=train)
    actual = frame.loc[test, 'gas'].to_numpy()
    ridge = modelo.entrenar(frame, **modelo.VARIABLES[path], prueba=pd.Timestamp(year, 1, 1))
    medians = frame.loc[train].groupby('area').gas.median()
    predictions = {'area_median': frame.loc[test, 'area'].map(medians).fillna(frame.loc[train, 'gas'].median()).to_numpy(),
                   'ridge': ridge['pred'][test]}
    tree = DecisionTreeRegressor(max_depth=2, min_samples_leaf=10, random_state=42)
    tree.fit(x.loc[train], frame.loc[train, 'gas'])
    predictions['small_tree'] = tree.predict(x.loc[test])
    for seed in SEEDS:
        forest = RandomForestRegressor(n_estimators=500, min_samples_leaf=4, random_state=seed, n_jobs=-1)
        forest.fit(x.loc[train], frame.loc[train, 'gas'])
        predictions[f'forest_{seed}'] = forest.predict(x.loc[test])
    result = {'year': year, 'train': int(train.sum()), 'test': int(test.sum()),
              'models': {name: metrics(actual, pred) for name, pred in predictions.items()}}
    if not all(np.isfinite(pred).all() for pred in predictions.values()):
        raise ValueError('Nonfinite predictions')
    # Paired bootstrap describes uncertainty for this cohort; it is not independent external validation.
    delta = np.abs(predictions['ridge'] - actual) - np.abs(predictions['forest_42'] - actual)
    draws = np.random.default_rng(42).choice(delta, size=(10000, len(delta)), replace=True).mean(axis=1)
    result['ridge_minus_forest_mae'] = {'mean': float(delta.mean()),
                                      'bootstrap_95': np.quantile(draws, [.025, .975]).tolist()}
    rows = [{'idpozo': str(frame.loc[test].iloc[i].idpozo), 'actual': float(y),
             **{name: float(pred[i]) for name, pred in predictions.items()}} for i, y in enumerate(actual)]
    return result, rows, tree, list(x.columns)


def draw_tree(tree, features, target, sample=None, well=None):
    """Export this exact small model as SVG, with no plotting dependency."""
    t = tree.tree_
    highlighted = set(tree.decision_path(sample).indices) if sample is not None else set()
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="700" viewBox="0 0 1600 700">',
             '<rect width="1600" height="700" fill="#F7F6F2"/>',
             '<g font-family="sans-serif" text-anchor="middle" fill="#14213D">',
             '<text x="800" y="35" font-size="25">Árbol pequeño · modelo independiente del bosque · gas de meses 2 a 7</text>']
    if sample is not None:
        value = modelo.num(float(tree.predict(sample)[0]), 2)
        parts.append(f'<text x="800" y="65" font-size="19">Pozo {well}: {value} millones de m³ · recorrido resaltado</text>')
    labels = {'rama': 'Rama horizontal (m)', 'etapas': 'Etapas', 'arena': 'Arena (t)',
              'agua': 'Agua (m³)', 'presion': 'Presión (psi)', 'profundidad': 'Profundidad (m)',
              'pct': 'Participación (%)'}

    def visit(node, depth, left, right):
        x, y = (left + right) / 2, 115 + depth * 220
        split = t.children_left[node] != t.children_right[node]
        if split:
            for child, lo, hi, label in [(t.children_left[node], left, x, 'Sí'),
                                         (t.children_right[node], x, right, 'No')]:
                cx = (lo + hi) / 2
                color = '#B36B00' if child in highlighted else '#7A8699'
                parts.append(f'<path d="M{x},{y+42} L{cx},{y+178}" stroke="{color}" stroke-width="3" fill="none"/>')
                parts.append(f'<text x="{(x+cx)/2}" y="{y+110}" font-size="19">{label}</text>')
                visit(child, depth + 1, lo, hi)
        fill = '#FFF0CF' if node in highlighted else 'white'
        parts.append(f'<rect x="{x-185}" y="{y-40}" width="370" height="90" rx="12" fill="{fill}" stroke="#2F6FB5"/>')
        feature = features[t.feature[node]] if split else ''
        name = labels.get(feature, feature)
        if '=' in feature:
            name = feature.replace('area=', 'Concesión = ').replace('grupo=', 'Operadora = ')
            question = f'{name} (0/1) ≤ {t.threshold[node]:.2f}?' if split else ''
        else:
            question = f'{name} ≤ {modelo.num(t.threshold[node], 1)}?' if split else 'Predicción'
        parts.append(f'<text x="{x}" y="{y-10}" font-size="18">{escape(question)}</text>')
        parts.append(f'<text x="{x}" y="{y+18}" font-size="18">{modelo.num(t.value[node,0,0], 2)} millones de m³ · '
                     f'{t.n_node_samples[node]} pozos</text>')
    visit(0, 0, 0, 1600)
    parts.append('<text x="800" y="650" font-size="18">Entrenado antes de 2025 · datos retrospectivos · '
                 'las reglas describen el modelo, no causas físicas.</text></g></svg>')
    target.write_text('\n'.join(parts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/experiments/gas-trees'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    a, b = modelo.preparar(modelo.sql_local(modelo.SQL_GAS), modelo.sql_local(modelo.SQL_A),
                           modelo.sparql_local(modelo.SPARQL_B))
    assert a.idpozo.equals(b.idpozo)
    np.testing.assert_allclose(a.gas, b.gas, rtol=0, atol=0.00050001)
    queries = {'gas': modelo.SQL_GAS, 'raw_features': modelo.SQL_A, 'semantic_features': modelo.SPARQL_B}
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'sklearn': sklearn.__version__,
              'model_version': modelo.version(),
              'model_sha256': hashlib.sha256(Path(modelo.__file__).read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'query_sha256': {k: hashlib.sha256(v.encode()).hexdigest() for k, v in queries.items()},
              'target_max_abs_difference': float(np.max(np.abs(a.gas - b.gas))),
              'target_check_tolerance': 0.00050001, 'input_sha256': {}, 'folds': [], 'settings': {'seeds': SEEDS, 'forest_trees': 500,
              'forest_min_leaf': 4, 'tree_depth': 2, 'tree_min_leaf': 10, 'tuned_on_test': False}}
    cache = Path('data/cache/gas-trees')
    cache.mkdir(parents=True, exist_ok=True)
    for path, frame in [('A', a), ('B', b)]:
        snapshot = frame.to_csv(index=False)
        (cache / f'inputs-{path}.csv').write_text(snapshot)
        report['input_sha256'][path] = hashlib.sha256(snapshot.encode()).hexdigest()
        for regime in ('retrospective', 'hide_late_fracture'):
            data = frame.copy()
            hidden = 0
            if regime == 'hide_late_fracture':
                data, hidden = available_inputs(data, b.fracCargada, modelo.FRACTURA_A if path == 'A' else modelo.FRACTURA_B)
            for year in YEARS:
                result, rows, tree, features = compare_fold(data, path, year)
                result.update(path=path, availability=regime, hidden_fracture_cohort=hidden)
                report['folds'].append(result)
                (cache / f'predictions-{path}-{regime}-{year}.json').write_text(json.dumps(rows, indent=2))
                print(path, regime, year, json.dumps(result['models']), flush=True)
                if path == 'B' and regime == 'retrospective' and year == 2025:
                    x = design(data, modelo.VARIABLES['B']['categorias'],
                               modelo.VARIABLES['B']['numeros'], data.inicio < pd.Timestamp('2025-01-01'))
                    sample = x.loc[data.idpozo == '165404']
                    draw_tree(tree, features, args.output / 'small-tree.svg', sample=sample, well='165404')
    (args.output / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
