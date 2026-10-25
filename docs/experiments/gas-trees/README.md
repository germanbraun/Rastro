# Gas models: ridge, forest and a small visual tree

Approved by the user on 2026-10-24 as an experiment before any app integration. The user also requested a visual tree. This is a comparison of predictors, not a measurement of Rastro's semantic explanation advantage or a reproduction of the thesis.

## Protocol

- Target: gas in months 2–7, in millions of m³, using the existing eligible cohort and features, including vertical depth.
- Paths: A (raw SQL) and B (Rastro). Within each path, every model gets identical rows, features, targets and training/test membership. Target values agree across paths within the existing semantic output precision (0.0005 million m³); their original precision is retained.
- Annual chronological tests: 2023 (337 training / 88 test), 2024 (425 / 85), 2025 (510 / 49). Each test contains only that year's starts; training contains earlier starts. Later test years never enter an earlier fold.
- Baseline: training concession median, falling back to the overall training median for unseen concessions.
- Ridge: the unchanged deployed calculation, alpha 1.0. Forest: 500 trees, minimum leaf size 4, seeds 42, 7 and 123. Visual tree: maximum depth 2, minimum leaf size 10, seed 42. These settings were fixed before inspecting the results, with no test-set tuning.
- Numeric imputation uses training means only. Tree/forest category vocabulary is fitted on training rows; unseen categories have all-zero indicators. Existing ridge retains its original encoding (test-only category columns are zero throughout training and have zero coefficients).
- Two availability conditions: the current retrospective inputs, and a conservative sensitivity hiding **all five** fracture inputs if the aggregate's latest load month is after the start month, or its load date is unknown. The same mask is applied to A and B, to training and test wells. It may discard some timely reports in mixed-date aggregates.
- Report MAE and R². A paired well bootstrap (10,000 draws, seed 42) describes the uncertainty in ridge MAE minus forest-42 MAE. Positive favors the forest. It does not account for dependence between wells in a concession.

## Results and decision

Path B, retrospective inputs; MAE in millions of m³ (lower is better). Forest ranges cover the three fixed seeds.

| Test year | Concession median | Ridge | Forest | Small tree |
|---|---:|---:|---:|---:|
| 2023 | 17.15 | 17.85 | 17.08–17.37 | 18.22 |
| 2024 | 14.74 | 15.32 | 15.00–15.03 | 16.25 |
| 2025 | 17.80 | **16.67** | 16.92–16.98 | 21.17 |

In 2025, R² is 0.457 for ridge, 0.388–0.403 for the forest, 0.124 for the small tree and 0.424 for the concession median. The small earlier-year MAE improvements do not establish consistent superiority: the forest also trails the simple concession median in 2024. Ridge's 2023 R² is negative despite a moderate MAE, reflecting sensitivity to large errors.

With late/unknown fracture inputs hidden, path B MAE is:

| Test year | Ridge | Forest | Small tree |
|---|---:|---:|---:|
| 2023 | 17.57 | 15.62–15.64 | 19.74 |
| 2024 | **14.42** | 16.71–16.75 | 18.40 |
| 2025 | **16.40** | 17.76–17.99 | 19.66 |

For 2025 retrospective B, ridge MAE minus forest-42 MAE is −0.31, with a paired bootstrap interval of [−2.50, 1.92]. With the fracture mask it is −1.44, interval [−5.05, 2.03]. Both intervals include zero. Path A also shows no consistent forest improvement; full metrics for both paths and every seed are in [results.json](results.json).

**Decision:** retain ridge in the app and deck. The tested forest does not show a consistent advantage. Retain the small tree as an experimental teaching artifact; its visual simplicity costs accuracy here. This does not rule out other tree settings or additional features, but those would need a separate development/validation protocol.

## Visual example

[Open the visual tree](small-tree.svg). Highlighted nodes show well 165404's exact path through the **independent small tree**, trained on the 510 pre-2025 wells. It is not a picture of the forest and does not explain the ridge prediction of 54.15. Each node shows its training sample count and mean gas; a leaf's mean is this tree's prediction. Binary operator columns use 0 for false and 1 for true. Branches describe statistical rules, not physical causes. Inputs come from the same retrospective Rastro table used by the comparison.

## Limits

This remains retrospective: hiding late fracture inputs is not a complete historical simulation. Other sources do not all have historical load timestamps; training targets for wells starting shortly before a cutoff can include production after that cutoff. Outcome maturity, right censoring, concession dependence and the small 2025 cohort limit conclusions. No claim of prospective performance or independent validation follows. The thesis used a different target/design and more features; its 0.75 R² is not a directly comparable target for this experiment.

## Reproduce and evidence

With the existing local sources, Postgres, Ontop energia, and development dependencies:

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"  # macOS Docker Desktop if needed
.venv/bin/python lab/gas/compare_trees.py
.venv/bin/python -m pytest -q tests/test_compare_trees.py
```

The script reads sources and writes experiment artifacts only. It does not alter sources, links, mappings, published model runs, or app predictions. `results.json` records UTC time, code/query/input fingerprints, settings, versions and all fold metrics. Prepared inputs and per-well predictions are stored locally under ignored `data/cache/gas-trees/`; they are not immutable source snapshots and must be retained locally if needed to audit this run. Re-running against changed sources can produce different results; compare fingerprints first. The SVG is generated from the actual fitted depth-2 tree, not drawn from an illustrative set of thresholds.

## Verification

74 tests passed; 5 opt-in PostgreSQL change-guard tests skipped. Ruff and whitespace checks passed. The new tests check training-only imputation/category vocabulary, the late/unknown arrival mask, and prediction invariance when held-out targets change. Browser inspection confirmed the exact three-node highlighted path and that all SVG labels fit.
