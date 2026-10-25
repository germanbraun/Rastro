"""Partial, read-only Q12 comparison; original thesis verification is still required."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor

import modelo
from compare_trees import design, metrics

OUTPUT = Path('docs/experiments/gas-thesis')
CACHE = Path('data/cache/gas-thesis')
COORDINATES = """SELECT idpozo, min(lon) AS lon, min(lat) AS lat
FROM capitulo4.pozo WHERE lon BETWEEN -180 AND 180 AND lat BETWEEN -90 AND 90
GROUP BY idpozo HAVING count(DISTINCT (lon, lat)) = 1"""
SEEDS = (42, 7, 123)
BASE_NUMBERS = ['pct'] + modelo.FRACTURA_B
EXTRA_NUMBERS = modelo.PROFUNDIDAD_B + ['lon', 'lat', 'start_year', 'stages_per_m', 'sand_per_m', 'water_per_m']


def extend(frame, coordinates):
    result = frame.merge(coordinates, on='idpozo', how='left', validate='one_to_one')
    result['start_year'] = result.inicio.dt.year
    denominator = result.rama.where(result.rama > 0)
    for column, name in [('etapas', 'stages_per_m'), ('arena', 'sand_per_m'), ('agua', 'water_per_m')]:
        result[name] = result[column] / denominator
    return result


def split_mask(frame, split):
    if split == 'every_fifth':
        return pd.Series(np.arange(len(frame)) % 5 == 4, index=frame.index)
    if split == 'from_2023':
        return frame.inicio >= pd.Timestamp('2023-01-01')
    raise ValueError(f'Unknown split: {split}')


def evaluate(frame, numbers, test):
    train = ~test
    x = design(frame, ['grupo', 'area'], numbers, train)
    y = frame.gas.to_numpy()
    medians = frame.loc[train].groupby('area').gas.median()
    predictions = {'area_median': frame.loc[test, 'area'].map(medians).fillna(frame.loc[train, 'gas'].median()).to_numpy()}
    mean_x = x.loc[train].mean().to_numpy()
    mean_y = float(y[train].mean())
    xc = x.loc[train].to_numpy() - mean_x
    coef = np.linalg.solve(xc.T @ xc + np.eye(xc.shape[1]), xc.T @ (y[train] - mean_y))
    predictions['ridge'] = mean_y + (x.loc[test].to_numpy() - mean_x) @ coef
    for seed in SEEDS:
        forest = RandomForestRegressor(n_estimators=500, min_samples_leaf=4, random_state=seed, n_jobs=-1)
        forest.fit(x.loc[train], y[train])
        predictions[f'forest_{seed}'] = forest.predict(x.loc[test])
    if not all(np.isfinite(pred).all() for pred in predictions.values()):
        raise ValueError('Nonfinite predictions')
    result = {'train': int(train.sum()), 'test': int(test.sum()), 'features': list(x.columns),
              'models': {name: metrics(y[test], pred) for name, pred in predictions.items()},
              'test_ids_sha256': hashlib.sha256('\n'.join(frame.loc[test, 'idpozo']).encode()).hexdigest()}
    rows = [{'idpozo': str(row.idpozo), 'actual': float(row.gas),
             **{name: float(pred[i]) for name, pred in predictions.items()}}
            for i, row in enumerate(frame.loc[test].itertuples())]
    return result, rows


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    query = modelo.sql_gas(desde=0, meses=12)
    a, b = modelo.preparar(modelo.sql_local(query), modelo.sql_local(modelo.SQL_A),
                           modelo.sparql_local(modelo.SPARQL_B), objetivo='gas12')
    assert a.idpozo.equals(b.idpozo)
    np.testing.assert_allclose(a.gas, b.gas, rtol=0, atol=0.00050001)
    frame = b.loc[b.rama.notna()].reset_index(drop=True)
    frame = extend(frame, modelo.sql_local(COORDINATES))
    input_bytes = frame.to_csv(index=False).encode()
    (CACHE / 'inputs.csv').write_bytes(input_bytes)
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'status': 'partial_replication',
              'thesis_primary_verified': False, 'thesis_url': 'https://repositorio.utdt.edu/handle/20.500.13098/14415',
              'thesis_access': 'University maintenance redirect; original PDF/code unavailable.',
              'thesis_prior_notes': {'cohort': 642, 'area_median_r2': .47, 'best_ensemble_r2': .75, 'forward_r2': .254},
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'helper_sha256': hashlib.sha256(Path(__file__).with_name('compare_trees.py').read_bytes()).hexdigest(),
              'model_sha256': hashlib.sha256(Path(modelo.__file__).read_bytes()).hexdigest(),
              'input_sha256': hashlib.sha256(input_bytes).hexdigest(), 'sklearn': sklearn.__version__,
              'query_sha256': {name: hashlib.sha256(sql.encode()).hexdigest() for name, sql in
                               {'gas12': query, 'raw_features': modelo.SQL_A, 'semantic_features': modelo.SPARQL_B,
                                'coordinates': COORDINATES}.items()},
              'cohort': {'eligible_before_fracture_filter': len(b), 'with_fracture': len(frame),
                         'earliest_start': str(frame.inicio.min().date()), 'latest_start': str(frame.inicio.max().date()),
                         'coordinate_missing': int(frame.lon.isna().sum())},
              'settings': {'forest_trees': 500, 'forest_min_leaf': 4, 'seeds': SEEDS, 'ridge_alpha': 1.,
                           'test_tuning': False}, 'comparisons': []}
    for feature_set, numbers in [('existing_design', BASE_NUMBERS), ('public_extension', BASE_NUMBERS + EXTRA_NUMBERS)]:
        for split in ('every_fifth', 'from_2023'):
            result, rows = evaluate(frame, numbers, split_mask(frame, split))
            result.update(feature_set=feature_set, split=split)
            report['comparisons'].append(result)
            artifact = CACHE / f'predictions-{feature_set}-{split}.json'
            artifact.write_text(json.dumps(rows, indent=2, allow_nan=False) + '\n')
            result['predictions_sha256'] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            print(feature_set, split, json.dumps(result['models']), flush=True)
    (OUTPUT / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
