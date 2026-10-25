# PDF-guided replay: results and interpretation

The user supplied the original 84-page thesis PDF after the first approximate experiments. Its methodology and Table 4 have now been checked directly. The earlier document-access blocker is resolved. Original code, frozen dataset and geology-calibration coefficients remain unavailable.

**Result:** the replay reaches approximately **0.68–0.69 R²** in the every-fifth holdout, compared with **0.7539** for the published ensemble. Trees improve on the area baseline on these refreshed data, but exact reproduction is not established. Keep the app model unchanged pending a separate integration/validation decision.

## Comparable table, with population differences explicit

R². Strict coverage has 609 wells (488 train / 121 test); the PDF-cutoff-only sensitivity has 616 (493 / 123). The thesis has 642 (514 / 128). These are different held-out wells, not a paired comparison.

| Model | Thesis Table 4 | Strict 12 observations | Date-cutoff-only sensitivity |
|---|---:|---:|---:|
| Area median | 0.4712 | 0.4910 | 0.3409 |
| Random Forest | 0.7269 | 0.6858 | 0.6789 |
| XGBoost | 0.7466 | 0.6838 | 0.6682 |
| LightGBM | 0.7424 | 0.6886 | 0.6806 |
| Ensemble, local CV weights | 0.7539 | 0.6908 | 0.6799 |
| Ensemble, published weights | 0.7539 | 0.6934 | 0.6916 |

The two ensemble rows are predeclared alternatives, not candidates selected by test score. The primary replay derives weights from its own training-only temporal CV; the fixed published weights show sensitivity to the original weighting recipe. The original-scale voting sensitivity is retained in the JSON as well.

## Forward evaluation

| Cohort / split | Train / test | Area median R² | Local-CV ensemble R² | Published-weight ensemble R² |
|---|---:|---:|---:|---:|
| Strict coverage, last_20_percent | 487 / 122 | 0.1435 | 0.3699 | 0.3487 |
| Strict coverage, from_2023 | 422 / 187 | 0.2160 | 0.3315 | 0.2987 |
| Date cutoff only, last_20_percent | 492 / 124 | 0.0617 | 0.3728 | 0.3784 |
| Date cutoff only, from_2023 | 429 / 187 | 0.1567 | 0.2845 | 0.2793 |

The thesis reports forward ensemble R² 0.254. Its last 20% and from-2023 descriptions refer to the same original cohort; they differ on the refreshed data, so both are shown. None of these values demonstrates prospective accuracy: target trimming uses the full-cohort p99 as described by the PDF, and the replay does not reconstruct complete historical data availability or target maturity.

## What was reproduced

Random Forest, XGBoost and LightGBM with Table 3 hyperparameters; log1p target / expm1 inverse; KNN(5), scaling and automatic target encoding inside fits; five chronological CV folds; fracture totals, trajectory-priority effective geometry, lateral intensities, physical interactions, coordinates, year and prior-year neighbors within 3 km; area baseline, interleaved and forward evaluation. See [protocol.md](protocol.md) for the exact interpretation and assumptions.

## Why this is still partial

- Current source snapshots differ. The full production source is now inspected through March 2026, including pre-2018 history; raw data are isolated from the running app.
- Selection differs: 831 current wells pass the four production filters versus 814 in the PDF; 701 pass the date cutoff versus 700. Strict monthly coverage retains 669 before joins; fracture joins, critical-feature availability and p99 trimming yield the final 609 / 616. No rule was changed to force 642. Full counts are in each input receipt.
- The PDF does not give the coefficients for its fluid-window approximation. That feature is omitted, not invented. Exact original row IDs, within-year ordering, category choices, search spaces and library versions are unavailable.
- The text is ambiguous about missing TVD removal versus KNN imputation, KNN/scaling order, and inversion before/after ensemble voting. Each choice and sensitivity is explicit.
- Neighbors are computed from training targets only inside every CV fold. The PDF gives the prior-year rule but no executable implementation; its exact handling of held-out neighbors is unknown.
- The source gas column is thousand m³, whereas the thesis tables label their numerical totals m³. Metrics retain source units plus explicit million-m³ MAE. Log1p depends on the numerical unit.
- Local CV scores differ from the paper. Negative local model weights are clipped to zero as predeclared; the published-weight row shows the result without relying on that adaptation.

## Interpretation and next step

A similar-order score supports continued research, not a claim of identical predictions or a replicated 0.7539. The scores alone do not prove equivalence, even where they overlap the thesis bootstrap interval, because cohorts and processing differ. Obtain original code/data or resolve the remaining methodological choices to pursue exact reproduction. An optional Q12 module would also need a faithful explanation and preserved source provenance. Replacing the current months-2–7 model requires evaluating that target separately.

## Reproduce and audit

```bash
.venv/bin/python -m pip install -r lab/gas/requirements-thesis.txt
# macOS requires an OpenMP runtime for the optional boosting libraries.
.venv/bin/python lab/gas/thesis_pipeline.py
.venv/bin/python lab/gas/thesis_pipeline.py --date-only-completeness
# Replay exact prepared snapshots without fetching sources:
.venv/bin/python lab/gas/thesis_pipeline.py --prepared
.venv/bin/python lab/gas/thesis_pipeline.py --prepared --date-only-completeness
```

Dependencies were installed only under `/tmp` for this run; a temporary OpenMP runtime avoided a system-wide install. See `environment.json` for actual versions. Prepared CSVs round-trip byte-for-byte with the runner’s explicit float parser. Per-well predictions, input and source hashes, code/protocol fingerprints and every CV fold are retained in the receipts. Raw inputs and predictions stay in ignored data folders; preserve those files locally for audit. No source tables, mappings, model publication or app predictions were changed.

## Verification

81 tests passed; 5 opt-in PostgreSQL change-guard tests skipped. Ruff and whitespace checks passed. New tests verify first-positive-gas timing, trajectory precedence, registry-coordinate precedence, valid intensity denominators, prior-year/3-km neighbor eligibility, log inversion and training-only reference targets. Both final result files match the saved script/protocol/input/prediction fingerprints, and both prepared CSVs round-trip exactly with the replay parser. The downloaded production file is 148,923,474 bytes, matching publisher metadata.
