# PDF-guided replay protocol

Approved scope: continue the user's requested thesis reproduction after receiving the PDF on 2026-10-24. This protocol is recorded before running the replay. Earlier simplified experiment artifacts remain unchanged.

Primary source: user-provided `MiM_Fernandez Gazzaniga_2026.pdf`, 84 PDF pages, SHA-256 `2e1e9cd9e1375c4ca763acba96493440c460fea1e46dff6d6fa24affd8de336b`. Cover says 2026 but its suggested citation says 2025. Page references below are PDF page numbers (printed page = PDF page minus one).

## Verified specifications

- PDF pp. 52–53: nonconventional production from 2006 through March 2026; Neuquina / gas well / shale / Vaca Muerta filters; first **positive gas** calendar month; Q12 sums months 0–11; starts before April 2025. Reported counts 814 eligible, 700 complete Q12, 642 after the fracture join.
- pp. 53–55: sum fracture stages, sand and water; maximum pressure; dominant completion type. Select longest trajectory; TVD for depth and trajectory lateral in preference to reported fracture lateral. Base categories are company, area/reservoir, completion type and fluid window; numeric features include year, coordinates, fracture totals, three lateral intensities, four interactions, and median Q12 of prior-year wells within 3 km.
- pp. 55–57: exclude target above overall p99; pool area categories with fewer than 10 wells; unknown categories as `DESCONOCIDO`; KNNImputer(5), StandardScaler, TargetEncoder(smooth='auto'). Every fifth chronological well is held out; 5-fold TimeSeriesSplit on the remainder.
- pp. 59–60, Table 3: RF 500 trees, max_depth 8, min_samples_leaf 4, max_features .7. XGB 400 trees, depth 3, learning rate .02, subsample .8, colsample .8, reg_lambda 2, reg_alpha .1. LGBM 600 trees, depth 3, learning rate .04, subsample .9, min_child_samples 10, num_leaves 31. Log1p target and expm1 inverse.
- pp. 58–59: ensemble weights proportional to training temporal CV R². Also report a fixed-weight replay using the published CV values .583/.615/.530; do not choose between them using test scores.
- pp. 61–62, Table 4: baseline R² .4712, RF .7269, XGB .7466, LGBM .7424, ensemble .7539. p. 65: forward ensemble .254. Table 6 on p. 64 has slightly different XGB/ensemble values; use Table 4 consistently, record that discrepancy.

## Predeclared interpretation and unavoidable deviations

1. Use the current publisher snapshots, filtered through March 2026, in isolated CSV processing. Do not mutate Rastro's database, mappings, published runs or app. Source versions differ from those of the thesis.
2. Require all 12 monthly observations and record losses; the PDF only explicitly describes the cutoff completeness criterion. Aggregate multiple source rows for a well/month before summing.
3. Use first-positive-gas-month company and area metadata. The PDF does not specify which monthly row supplies static context. Order by exact start month then well ID; original within-year ordering/test IDs are unavailable.
4. Retain missing TVD for KNN, following p. 54's explicit 24-well imputation; p. 56 instead says critical missing depth is removed. Record this unresolved contradiction. Use the literal KNN → scaler order described on pp. 56–57; the text later says scaling is needed for KNN, which would require the reverse order.
5. Omit `ventana_fluido`: the PDF provides thresholds but not the coefficients of its calibrated lon/lat-to-Ro formula. Do not fabricate geology. Do not add share/pct, which is absent from the thesis's specified predictors.
6. Build neighbors inside each fit from training wells only, restricted to earlier start years and radius 3 km. This avoids held-out targets entering training features; the PDF does not provide implementation code to establish its exact construction. This is not full target-maturity simulation.
7. Use the reported best hyperparameters directly, seed 42. Original RandomizedSearchCV search spaces and package versions are missing, so do not invent a 20-trial search or tune to .7539. Record all estimator defaults. Set LGBM subsample_freq=1 so the reported .9 subsample takes effect; the PDF does not state this parameter.
8. Main replay uses the numeric gas units in the public production column (thousand m³). PDF p. 25 identifies that source unit, while its result tables label the summed values m³. Keep both the source-unit metrics and converted million-m³ metrics; do not silently treat them as the same physical unit. Log1p is unit dependent.
9. In addition to every-fifth testing, report the last 20% of chronological wells (the PDF's forward design) **and** starts from 2023. They need not coincide on the refreshed cohort. No test-score-driven selection. Training CV weights require nonnegative weights; if a local mean CV R² is negative, clip it to zero and record the adjustment; use equal weights only if all are nonpositive.
10. Target trimming uses overall p99 to replay the described retrospective procedure. This uses test-target distribution information and is not a prospective validation. Pooling rare areas also follows the PDF's full-cohort preprocessing. Results cannot be described as independent external validation or exact reproduction without original code, IDs and snapshots.

11. Combine ensemble predictions in log space and then invert, following the stated global log-target training. The PDF does not specify whether inversion occurs before or after voting; also record original-scale arithmetic voting as an explicit sensitivity.

No promotion to the app solely because a score resembles .7539. The active months-2–7 use case needs its own validation and a faithful tree explanation.


## Follow-up specified after the initial join audit

The strict run found 701 wells passing the date cutoff but only 669 with 12 monthly rows. To isolate this discrepancy from the PDF, repeat the same fixed models and preprocessing with **cutoff-only completeness**, as literally specified in section 5.3.2. Store it under `date-only/`; never select or merge results by score. Keep the strict 12-observation replay as the main coverage check. Missing monthly rows in the cutoff-only sample remain a limitation, not evidence of observed zero gas. No other settings or predictors change.
