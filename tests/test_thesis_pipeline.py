"""Guard the thesis replay against neighbor-target and preprocessing leakage."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from thesis_pipeline import NUMERIC, ThesisRegressor, neighbor_values, ratio


def test_neighbors_use_prior_years_and_three_km_radius():
    query = pd.DataFrame({'lat': [-39.], 'lon': [-69.], 'year': [2022]})
    reference = pd.DataFrame({'lat': [-39.] * 5, 'lon': [-69., -69.01, -69., -69., -70.],
                              'year': [2020, 2021, 2022, 2023, 2020]})
    target = np.array([10., 30., 1000., 10000., 100000.])
    np.testing.assert_allclose(neighbor_values(query, reference, target), [20.])
    reference['year'] = 2023
    assert np.isnan(neighbor_values(query, reference, target)).all()


def test_intensity_denominators_are_positive():
    result = ratio(pd.Series([10., 10., 10.]), pd.Series([2., 0., -1.]))
    assert result.iloc[0] == 5.
    assert result.iloc[1:].isna().all()


def test_fit_uses_only_training_targets_and_keeps_log_inverse():
    rng = np.random.default_rng(8)
    frame = pd.DataFrame({col: rng.uniform(1, 20, 35) for col in NUMERIC if col != 'neighbor_q12'})
    frame['lat'], frame['lon'] = -39., -69.
    frame['year'] = [2020] * 15 + [2021] * 15 + [2022] * 5
    for category in ('empresa', 'areayacimiento', 'tipo_terminacion'):
        frame[category] = ['A'] * 30 + ['unseen'] * 5
    frame.loc[34, 'depth'] = np.nan
    target = np.full(30, 50000.)
    reg = ThesisRegressor(RandomForestRegressor(n_estimators=5, random_state=42))
    reg.fit(frame.iloc[:30], target)
    np.testing.assert_allclose(reg.predict(frame.iloc[30:]), 50000., rtol=1e-10)
    assert len(reg.reference_) == 30
    assert not reg.reference_.empresa.eq('unseen').any()
    np.testing.assert_allclose(reg._features(frame.iloc[30:]).neighbor_q12, 50000.)
    # With no earlier-year reference the feature is missing, not filled from query labels.
    earlier = frame.iloc[30:].assign(year=2019)
    assert reg._features(earlier).neighbor_q12.isna().all()


def test_build_input_uses_first_positive_gas_and_longest_trajectory(tmp_path, monkeypatch):
    from thesis_pipeline import build_input
    import json
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data/raw/lab-gas').mkdir(parents=True)
    (tmp_path / 'data/raw/energia').mkdir(parents=True)
    dates = pd.date_range('2024-01-01', periods=13, freq='MS')
    production = pd.DataFrame({'idpozo': ['1'] * 13, 'anio': dates.year, 'mes': dates.month,
                               'prod_gas': [0.] + [100.] * 12, 'empresa': ['old'] + ['A'] * 12,
                               'areayacimiento': ['Area'] * 13, 'cuenca': ['NEUQUINA'] * 13,
                               'tipopozo': ['Gasífero'] * 13, 'sub_tipo_recurso': ['SHALE'] * 13,
                               'formacion': ['vaca muerta'] * 13, 'coordenadax': [-69.] * 13,
                               'coordenaday': [-39.] * 13})
    production.to_csv('production.csv', index=False)
    pd.DataFrame({'idpozo': ['1'], 'arena_bombeada_nacional_tn': [80.],
                  'arena_bombeada_importada_tn': [20.], 'cantidad_fracturas': [20.],
                  'agua_inyectada_m3': [1000.], 'presion_maxima_psi': [10000.],
                  'longitud_rama_horizontal_m': [1500.], 'tipo_terminacion': ['Tapón']}).to_csv(
                      'data/raw/lab-gas/fractura.csv', index=False)
    pd.DataFrame({'idpo': ['1', '1'], 'profundidad_vertical_mt': [2000., 3000.],
                  'largo_rama_horizontal_mt': [1000., 2000.]}).to_csv('data/raw/lab-gas/trayectorias-vm.csv', index=False)
    pd.DataFrame({'idpozo': ['1'], 'geojson': [json.dumps({'type': 'Point', 'coordinates': [-68., -38., 100.]})]}).to_csv(
        'data/raw/energia/pozos.csv', index=False)
    frame, audit = build_input('production.csv')
    assert len(frame) == 1 and audit['complete_12_observations'] == 1
    row = frame.iloc[0]
    assert row.inicio == pd.Timestamp('2024-02-01') and row.empresa == 'A'
    assert row.q12 == 1200.
    assert row.depth == 3000. and row.lateral == 2000.
    assert row.lon == -68. and row.lat == -38.
    assert row.sand_per_m == .05 and row.stages_per_100m == 1.
