"""Replay the published thesis pipeline on isolated current public snapshots.

See docs/experiments/gas-thesis/pdf-replay/protocol.md for fixed assumptions.
No database writes, published predictions or app changes.
"""
import argparse
import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, TargetEncoder

RAW = Path('data/raw/gas-thesis')
OUT = Path('docs/experiments/gas-thesis/pdf-replay')
CACHE = Path('data/cache/gas-thesis/pdf-replay')
PROTOCOL = OUT / 'protocol.md'
CATEGORIES = ['empresa', 'areayacimiento', 'tipo_terminacion']
NUMERIC = ['depth', 'lateral', 'year', 'etapas', 'arena', 'agua', 'presion', 'lon', 'lat',
           'sand_per_m', 'water_per_m', 'stages_per_100m', 'sand_per_stage', 'water_per_stage',
           'fracture_energy', 'water_sand_ratio', 'neighbor_q12']
PAPER_WEIGHTS = np.array([.583, .615, .530])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mode(values):
    values = values.dropna().mode()
    return values.iloc[0] if len(values) else np.nan


def ratio(numerator, denominator):
    return numerator / denominator.where(denominator > 0)


def build_input(production, require_months=True):
    """Follow the PDF's source joins without changing the production database."""
    cols = ['idpozo', 'anio', 'mes', 'prod_gas', 'empresa', 'areayacimiento', 'cuenca', 'tipopozo',
            'sub_tipo_recurso', 'formacion', 'coordenadax', 'coordenaday']
    p = pd.read_csv(production, usecols=cols, dtype={'idpozo': str}, low_memory=False)
    p['month'] = pd.to_datetime(dict(year=p.anio, month=p.mes, day=1))
    p = p.loc[p.month <= pd.Timestamp('2026-03-01')].copy()
    audit = {'rows_through_march_2026': len(p), 'all_wells': int(p.idpozo.nunique())}
    for col, val in [('cuenca', 'neuquina'), ('tipopozo', 'gasífero'),
                     ('sub_tipo_recurso', 'shale'), ('formacion', 'vaca muerta')]:
        p = p.loc[p[col].str.strip().str.casefold() == val]
        audit[f'after_{col}'] = int(p.idpozo.nunique())
    monthly = p.groupby(['idpozo', 'month'], as_index=False).prod_gas.sum()
    first = monthly.loc[monthly.prod_gas > 0].groupby('idpozo').month.min().rename('inicio')
    monthly = monthly.join(first, on='idpozo')
    age = ((monthly.month.dt.year - monthly.inicio.dt.year) * 12 + monthly.month.dt.month - monthly.inicio.dt.month)
    first12 = monthly.loc[age.between(0, 11)]
    q12 = first12.groupby('idpozo').agg(q12=('prod_gas', 'sum'), observed_months=('month', 'size')).join(first)
    q12 = q12.loc[q12.inicio < pd.Timestamp('2025-04-01')]
    audit['complete_by_date_only'] = len(q12)
    audit['observed_month_counts'] = {str(k): int(v) for k, v in q12.observed_months.value_counts().items()}
    audit['complete_12_observations'] = int((q12.observed_months == 12).sum())
    audit['require_12_observations'] = require_months
    if require_months:
        q12 = q12.loc[q12.observed_months == 12]
    context = p.merge(first, on='idpozo')
    context = context.loc[context.month == context.inicio].sort_values(['idpozo', 'prod_gas'], ascending=[True, False])
    context = context.drop_duplicates('idpozo').set_index('idpozo')
    frame = q12.join(context[['empresa', 'areayacimiento', 'coordenadax', 'coordenaday']])
    fr = pd.read_csv('data/raw/lab-gas/fractura.csv', dtype={'idpozo': str}, low_memory=False)
    audit['fracture_rows'] = len(fr)
    fr['sand'] = fr.arena_bombeada_nacional_tn.fillna(0) + fr.arena_bombeada_importada_tn.fillna(0)
    def sum_observed(values):
        return values.sum(min_count=1)
    agg = fr.groupby('idpozo').agg(etapas=('cantidad_fracturas', sum_observed), arena=('sand', sum_observed),
                                 agua=('agua_inyectada_m3', sum_observed), presion=('presion_maxima_psi', 'max'),
                                 fracture_lateral=('longitud_rama_horizontal_m', 'max'),
                                 tipo_terminacion=('tipo_terminacion', mode))
    frame = frame.join(agg, how='inner')
    audit['after_fracture_join'] = len(frame)
    tr = pd.read_csv('data/raw/lab-gas/trayectorias-vm.csv', dtype={'idpo': str}, low_memory=False)
    audit['trajectory_rows'] = len(tr)
    tr = tr.sort_values('largo_rama_horizontal_mt', ascending=False, na_position='last').drop_duplicates('idpo')
    tr = tr.set_index('idpo')[['profundidad_vertical_mt', 'largo_rama_horizontal_mt']]
    frame = frame.join(tr)
    frame['depth'] = frame.profundidad_vertical_mt.where(frame.profundidad_vertical_mt > 0)
    frame['lateral'] = frame.largo_rama_horizontal_mt.where(frame.largo_rama_horizontal_mt > 0)
    frame['lateral'] = frame.lateral.fillna(frame.fracture_lateral.where(frame.fracture_lateral > 0))
    registry = pd.read_csv('data/raw/energia/pozos.csv', dtype={'idpozo': str}, low_memory=False)
    # Registry geometry is read exactly as in the existing energy loader.
    def point(value):
        try:
            j = json.loads(value)
            if isinstance(j, dict) and j.get('type') == 'Point':
                return j['coordinates'][:2]
            return [np.nan, np.nan]
        except (TypeError, ValueError, KeyError):
            return [np.nan, np.nan]
    xy = pd.DataFrame(registry.geojson.map(point).tolist(), columns=['registry_lon', 'registry_lat'])
    xy['idpozo'] = registry.idpozo
    xy = xy.drop_duplicates('idpozo').set_index('idpozo')
    frame = frame.join(xy)
    frame['lon'] = frame.registry_lon.fillna(pd.to_numeric(frame.coordenadax, errors='coerce'))
    frame['lat'] = frame.registry_lat.fillna(pd.to_numeric(frame.coordenaday, errors='coerce'))
    frame['year'] = frame.inicio.dt.year
    frame['sand_per_m'] = ratio(frame.arena, frame.lateral)
    frame['water_per_m'] = ratio(frame.agua, frame.lateral)
    frame['stages_per_100m'] = 100 * ratio(frame.etapas, frame.lateral)
    frame['sand_per_stage'] = ratio(frame.arena, frame.etapas)
    frame['water_per_stage'] = ratio(frame.agua, frame.etapas)
    frame['fracture_energy'] = frame.presion * frame.agua
    frame['water_sand_ratio'] = ratio(frame.agua, frame.arena)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=['q12', 'year', 'lateral', 'etapas', 'arena', 'agua'])
    audit['before_target_trim'] = len(frame)
    threshold = float(frame.q12.quantile(.99))
    frame = frame.loc[frame.q12 <= threshold].copy()
    audit['q12_p99_source_units'] = threshold
    audit['after_target_trim'] = len(frame)
    audit['missing_depth_retained_for_knn'] = int(frame.depth.isna().sum())
    counts = frame.areayacimiento.value_counts()
    frame.loc[frame.areayacimiento.isin(counts[counts < 10].index), 'areayacimiento'] = 'OTROS'
    frame = frame.reset_index().rename(columns={'index': 'idpozo'}).sort_values(['inicio', 'idpozo']).reset_index(drop=True)
    frame[CATEGORIES] = frame[CATEGORIES].fillna('DESCONOCIDO').astype(str)
    audit['final'] = len(frame)
    audit['first_start'] = str(frame.inicio.min().date())
    audit['last_start'] = str(frame.inicio.max().date())
    return frame, audit


def neighbor_values(query, reference, target):
    """Prior-year neighbors inside 3 km, using only the current fit's reference targets."""
    q = np.radians(query[['lat', 'lon']].to_numpy(dtype=float))
    r = np.radians(reference[['lat', 'lon']].to_numpy(dtype=float))
    dy = q[:, None, 0] - r[None, :, 0]
    dx = q[:, None, 1] - r[None, :, 1]
    a = np.sin(dy / 2) ** 2 + np.cos(q[:, None, 0]) * np.cos(r[None, :, 0]) * np.sin(dx / 2) ** 2
    distance = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    eligible = (distance <= 3) & (reference.year.to_numpy()[None, :] < query.year.to_numpy()[:, None])
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)  # No prior neighbor legitimately yields NaN.
        return np.nanmedian(np.where(eligible, np.asarray(target)[None, :], np.nan), axis=1)


class ThesisRegressor(RegressorMixin, BaseEstimator):
    """Keep neighbor targets, preprocessing and encoding inside each training fold."""
    def __init__(self, estimator):
        self.estimator = estimator

    def fit(self, X, y):
        self.reference_ = X.copy()
        self.target_ = np.asarray(y)
        data = self._features(X)
        self.preprocessor_ = ColumnTransformer([
            ('numeric', Pipeline([('impute', KNNImputer(n_neighbors=5, keep_empty_features=True)),
                                  ('scale', StandardScaler())]), NUMERIC),
            ('categorical', Pipeline([('impute', SimpleImputer(strategy='constant', fill_value='DESCONOCIDO')),
                                      ('encode', TargetEncoder(smooth='auto', target_type='continuous', random_state=42))]), CATEGORIES)])
        log_y = np.log1p(y)
        encoded = self.preprocessor_.fit_transform(data, log_y)
        self.estimator_ = clone(self.estimator).fit(encoded, log_y)
        return self

    def _features(self, X):
        data = X.copy()
        data['neighbor_q12'] = neighbor_values(X, self.reference_, self.target_)
        return data

    def predict(self, X):
        return np.expm1(self.estimator_.predict(self.preprocessor_.transform(self._features(X))))


def model_specs():
    from xgboost import XGBRegressor
    from lightgbm import LGBMRegressor
    return {
        'rf': RandomForestRegressor(n_estimators=500, max_depth=8, min_samples_leaf=4, max_features=.7,
                                    random_state=42, n_jobs=2),
        'xgb': XGBRegressor(n_estimators=400, max_depth=3, learning_rate=.02, subsample=.8,
                           colsample_bytree=.8, reg_lambda=2, reg_alpha=.1, random_state=42, n_jobs=2),
        'lgbm': LGBMRegressor(n_estimators=600, max_depth=3, learning_rate=.04, subsample=.9,
                             subsample_freq=1, min_child_samples=10, num_leaves=31, random_state=42,
                             n_jobs=2, verbosity=-1),
    }


def scores(y, pred):
    if not np.isfinite(pred).all():
        raise ValueError('Nonfinite predictions')
    return {'r2': float(r2_score(y, pred)), 'mae_source_thousand_m3': float(mean_absolute_error(y, pred)),
            'rmse_source_thousand_m3': float(np.sqrt(mean_squared_error(y, pred))),
            'mae_million_m3': float(mean_absolute_error(y, pred) / 1000)}


def run(frame):
    import sklearn
    import xgboost
    import lightgbm
    specs = model_specs()
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'status': 'pdf_guided_partial_replay', 'thesis_primary_verified': True,
              'thesis_sha256': sha(RAW / 'thesis.pdf'), 'script_sha256': sha(__file__),
              'protocol_sha256': sha(PROTOCOL),
              'versions': {'sklearn': sklearn.__version__, 'xgboost': xgboost.__version__, 'lightgbm': lightgbm.__version__},
              'parameters': {name: {k: str(v) if isinstance(v, float) and not np.isfinite(v) else v
                                    for k, v in spec.get_params().items()} for name, spec in specs.items()},
              'paper_table4_r2': {'area_median': .4712, 'rf': .7269, 'xgb': .7466, 'lgbm': .7424, 'ensemble': .7539},
              'paper_forward_ensemble_r2': .254, 'splits': []}
    masks = {'every_fifth': np.arange(len(frame)) % 5 == 4,
             'last_20_percent': np.arange(len(frame)) >= int(len(frame) * .8),
             'from_2023': (frame.inicio >= pd.Timestamp('2023-01-01')).to_numpy()}
    for split, test in masks.items():
        train = ~test
        X = frame.drop(columns='q12')
        y = frame.q12
        medians = frame.loc[train].groupby('areayacimiento').q12.median()
        predictions = {'area_median': frame.loc[test, 'areayacimiento'].map(medians).fillna(y[train].median()).to_numpy()}
        cv = {}
        for name, spec in specs.items():
            estimator = ThesisRegressor(spec)
            cv[name] = cross_val_score(estimator, X.loc[train], y[train], cv=TimeSeriesSplit(n_splits=5),
                                       scoring='r2', error_score='raise').tolist()
            fitted = estimator.fit(X.loc[train], y[train])
            predictions[name] = fitted.predict(X.loc[test])
            print(split, name, 'CV', cv[name], 'test', scores(y[test], predictions[name]), flush=True)
        means = np.array([np.mean(cv[name]) for name in specs])
        weights = np.maximum(means, 0)
        weights = weights / weights.sum() if weights.sum() > 0 else np.ones(3) / 3
        stack = np.stack([predictions[name] for name in specs])
        predictions['ensemble_local_cv'] = np.expm1(np.average(np.log1p(stack), axis=0, weights=weights))
        predictions['ensemble_paper_weights'] = np.expm1(np.average(np.log1p(stack), axis=0, weights=PAPER_WEIGHTS))
        predictions['ensemble_original_scale_sensitivity'] = np.average(stack, axis=0, weights=weights)
        result = {'split': split, 'train': int(train.sum()), 'test': int(test.sum()), 'cv_fold_r2': cv,
                  'local_weights': dict(zip(specs, weights.tolist())), 'raw_cv_means': means.tolist(),
                  'weight_clipping_needed': bool((means < 0).any()),
                  'metrics': {name: scores(y[test], pred) for name, pred in predictions.items()}}
        artifact = CACHE / f'predictions-{split}.csv'
        rows = frame.loc[test, ['idpozo', 'inicio', 'q12']].copy()
        for name, pred in predictions.items():
            rows[name] = pred
        rows.to_csv(artifact, index=False)
        result['predictions_sha256'] = sha(artifact)
        report['splits'].append(result)
        print(split, 'RESULT', json.dumps(result), flush=True)
    return report


def main():
    global OUT, CACHE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', action='store_true', help='Replay the saved prepared input, verifying its receipt.')
    parser.add_argument('--date-only-completeness', action='store_true',
                        help='Use the PDF cutoff-only completeness criterion; keep gaps explicit.')
    args = parser.parse_args()
    if args.date_only_completeness:
        OUT = OUT / 'date-only'
        CACHE = CACHE / 'date-only'
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    if args.prepared:
        receipt = json.loads((OUT / 'input-receipt.json').read_text())
        if sha(CACHE / 'inputs.csv') != receipt['prepared_sha256']:
            raise ValueError('Saved prepared input fingerprint differs')
        frame = pd.read_csv(CACHE / 'inputs.csv', dtype={'idpozo': str}, parse_dates=['inicio'], float_precision='round_trip')
    else:
        frame, audit = build_input(RAW / 'nonconventional.csv', require_months=not args.date_only_completeness)
        frame.to_csv(CACHE / 'inputs.csv', index=False)
        receipt = {'created_utc': datetime.now(timezone.utc).isoformat(), 'audit': audit,
                   'prepared_sha256': sha(CACHE / 'inputs.csv'), 'sources': {str(p): sha(p) for p in
                    [RAW / 'nonconventional.csv', RAW / 'thesis.pdf', Path('data/raw/lab-gas/fractura.csv'),
                     Path('data/raw/lab-gas/trayectorias-vm.csv'), Path('data/raw/energia/pozos.csv')]}}
        (OUT / 'input-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('INPUT', receipt['audit'], flush=True)
    report = run(frame)
    report['require_12_observations'] = not args.date_only_completeness
    report['input_receipt_sha256'] = sha(OUT / 'input-receipt.json')
    (OUT / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
