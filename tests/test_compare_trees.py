"""Check leakage boundaries and paired evaluation of the alternative gas models."""
import numpy as np
import pandas as pd

from compare_trees import available_inputs, compare_fold, design
import modelo


def test_training_only_means_and_category_vocabulary():
    frame = pd.DataFrame({'operator': ['A', 'A', 'future'], 'value': [2., 4., np.nan]})
    x = design(frame, ['operator'], ['value'], pd.Series([True, True, False]))
    assert list(x.columns) == ['operator=A', 'value']
    assert x.iloc[2].to_dict() == {'operator=A': 0., 'value': 3.}


def test_late_and_unknown_arrivals_hide_all_fracture_inputs():
    frame = pd.DataFrame({'inicio': pd.to_datetime(['2025-02-01'] * 3),
                          'rama': [100., 200., 300.], 'etapas': [10., 20., 30.], 'other': [1, 2, 3]})
    loaded = pd.Series(pd.to_datetime(['2025-02-28', '2025-03-01', None]))
    masked, count = available_inputs(frame, loaded, ['rama', 'etapas'])
    assert count == 2
    assert masked.loc[1:, ['rama', 'etapas']].isna().all().all()
    assert masked.loc[0, 'rama'] == 100.
    assert masked.other.equals(frame.other)
    assert frame.rama.notna().all()  # The source frame stays intact.


def test_models_do_not_use_test_targets_or_subsequent_years():
    rng = np.random.default_rng(42)
    n = 45
    frame = pd.DataFrame({'idpozo': [str(i) for i in range(n)],
                          'inicio': pd.to_datetime(['2024-01-01'] * 40 + ['2025-01-01'] * 4 + ['2026-01-01']),
                          'grupo': ['A'] * n, 'area': ['X'] * n, 'gas': rng.uniform(20, 100, n)})
    for name in modelo.VARIABLES['B']['numeros']:
        frame[name] = rng.uniform(1, 100, n)
    result, rows, tree, _ = compare_fold(frame, 'B', 2025)
    changed = frame.copy()
    changed.loc[40:, 'gas'] += 1000
    second, other_rows, _, _ = compare_fold(changed, 'B', 2025)
    assert result['train'] == 40 and result['test'] == 4
    assert tree.get_depth() <= 2
    for row, other in zip(rows, other_rows):
        for key in result['models']:
            np.testing.assert_allclose(row[key], other[key], rtol=0, atol=1e-10)
    assert result['models']['ridge']['mae'] != second['models']['ridge']['mae']
