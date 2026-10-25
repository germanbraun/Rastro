"""Guard target exclusion, well alignment and thesis-style split membership."""
import numpy as np
import pandas as pd
import pytest

from reproduce_thesis import BASE_NUMBERS, evaluate, extend, split_mask


def test_extension_preserves_alignment_and_undefined_intensities():
    frame = pd.DataFrame({'idpozo': ['b', 'a', 'c'], 'inicio': pd.to_datetime(['2020-01-01'] * 3),
                          'rama': [100., 0., -5.], 'etapas': [10., 2., 1.],
                          'arena': [1000., 1., 1.], 'agua': [2000., 2., 2.]})
    coordinates = pd.DataFrame({'idpozo': ['a', 'b'], 'lon': [-70., -69.], 'lat': [-39., -38.]})
    result = extend(frame, coordinates)
    assert result.idpozo.tolist() == ['b', 'a', 'c']
    assert result.loc[0, 'lon'] == -69.
    assert result.loc[0, 'stages_per_m'] == .1
    assert result.loc[1:, ['stages_per_m', 'sand_per_m', 'water_per_m']].isna().all().all()
    with pytest.raises(pd.errors.MergeError):
        extend(frame, pd.concat([coordinates, coordinates]))


def test_splits_are_explicit_and_different():
    frame = pd.DataFrame({'inicio': pd.to_datetime(['2022-01-01'] * 5 + ['2023-01-01'] * 5)})
    assert split_mask(frame, 'every_fifth').tolist() == [False] * 4 + [True] + [False] * 4 + [True]
    assert split_mask(frame, 'from_2023').tolist() == [False] * 5 + [True] * 5
    with pytest.raises(ValueError):
        split_mask(frame, 'random')


def test_all_models_ignore_held_out_targets():
    rng = np.random.default_rng(44)
    frame = pd.DataFrame({'idpozo': [str(i) for i in range(40)], 'grupo': ['A'] * 40,
                          'area': ['X'] * 40, 'gas': rng.uniform(20, 150, 40),
                          'inicio': pd.to_datetime(['2020-01-01'] * 40)})
    for name in BASE_NUMBERS:
        frame[name] = rng.uniform(1, 100, 40)
    test = split_mask(frame, 'every_fifth')
    result, rows = evaluate(frame, BASE_NUMBERS, test)
    changed = frame.copy()
    changed.loc[test, 'gas'] += 1000
    other, other_rows = evaluate(changed, BASE_NUMBERS, test)
    assert result['test_ids_sha256'] == other['test_ids_sha256']
    assert result['train'] == 32 and result['test'] == 8
    for row, other_row in zip(rows, other_rows):
        for model in result['models']:
            np.testing.assert_allclose(row[model], other_row[model], rtol=0, atol=1e-10)
