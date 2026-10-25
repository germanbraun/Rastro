# Alternative tree model in Lab

The user clarified on 2026-10-24 that the goal is to use algorithms from the thesis and put the best candidate in the app as an alternative, not reproduce the thesis's exact results. This supersedes the earlier replication prerequisite.

Protocol before measurement: use the existing live Lab cohort, target (gas months 2–7, million m³), raw/semantic variables and chronological split. Compare Random Forest, XGBoost and LightGBM using the thesis's fixed Table 3 settings and seed 42. Numeric missing values use training means; categorical vocabulary is fitted on training rows. All models train on log1p of gas in source thousand-m³ numeric units, then invert to million m³. Select the tree by mean annual MAE in 2023 and 2024; evaluate 2025 separately. Add the selected tree even if ridge remains better in 2025, and label the comparison experimental. These years have been examined in prior work, so they are not independent external validation.

Keep the original ridge model and walkthrough as the default. The alternative shows a saved, fingerprinted evaluation on the same selected well and its input provenance. It never reuses ridge's additive explanation. A visualization shows a real path through the first tree, explicitly described as one component of a multi-tree model. Store measured output in an ignored app-readable artifact, and disable it if current inputs or model code no longer match. Published ridge runs are unchanged; the experimental artifact is not a new current RDF run.

No new source, target, mapping or model parameter search is required. The sources retain the current Lab's retrospective/late-arrival limitations. The optional libraries run only during experiment generation; the Streamlit app reads results and checks their identity.


## Follow-up selection scope

Before measuring additional configurations, expand the candidates to both direct gas and log1p targets for each fixed algorithm. The user wants the algorithms rather than exact thesis reproduction; imposing its target transform on months 2–7 is unnecessary. Select among all six configurations using the same predeclared 2023–2024 MAE rule; never use 2025 to select. Preserve the earlier three-log-configuration output in the local cache. This is a small predefined comparison, not a test-score search.


## Final selection and app behavior

Selected **Random Forest with direct gas**. Mean annual selection MAE (2023–2024): 15.802 million m³. All six configurations and every annual validation fold are in `results.json`. This replaces the intermediate log-only XGBoost choice; the initial log-only artifact is retained locally.

| Configuration | Selection MAE, 2023–2024 | MAE, 2025 | R², 2025 |
|---|---:|---:|---:|
| Random Forest, log | 16.366 | 18.636 | 0.204 |
| XGBoost, log | 16.349 | 18.453 | 0.211 |
| LightGBM, log | 18.498 | 19.663 | 0.139 |
| Random Forest, direct | 15.802 | 16.274 | 0.430 |
| XGBoost, direct | 16.116 | 16.122 | 0.396 |
| LightGBM, direct | 17.774 | 16.881 | 0.397 |

The unchanged ridge gives 2025 MAE 16.672 and R² 0.457. The selected forest slightly improves MAE but has lower R². Direct XGBoost has a lower 2025 MAE than the forest, but selection is deliberately not redone using that test result. The observed improvement is exploratory, not a proven generalization advantage.

In **Rastro Lab → Modelo para explorar**, select the alternative. It shares the chosen 2025 well with the ridge view, shows all test results and the actual observed gas, and opens the source inputs and their provenance. Missing or changed snapshots/code disable the saved alternative until it is regenerated. It is distinct from the ridge run published in RDF.

The tree visualization follows the actual selected well through the first tree. For the direct forest it shows that tree’s estimate and the complete forest’s average separately. It does not attribute the entire prediction to one tree or claim causality. [Example SVG for well 165404](well-165404.svg). The app also downloads this diagram and updates it when the well changes. Algorithm descriptions and the selection/visualization explanation are in the domain FAQ.

## Generate or refresh

```bash
# With development dependencies, the optional requirements-thesis.txt libraries,
# local Postgres and Ontop energia available:
python lab/gas/alternative.py
```

The output is `data/cache/gas-alternative/model.json`, already mounted read-only in the app. No tree libraries are needed in the Streamlit runtime. Retain the file locally for laptop restarts; a clean checkout needs the generation command. The artifact fingerprints the complete shared input cohort and the model/preprocessing code. Technical settings come from `thesis_pipeline.model_specs`; scalar imputation/category vocabulary come from `compare_trees.design`. No source, mapping or published ridge result was changed.

## Publication status

The existing `layer/method.py publication energia` gate still reports pending independent reference evidence. Accordingly, the interface labels this as experimental, keeps the original default and displays the test limitations. No independent-validation or reproduced-thesis claim is published.

## Verification

85 tests passed, 5 opt-in PostgreSQL change-guard tests skipped; targeted alternative tests also passed after final responsive-layout changes. Tests cover selection independence from 2025 targets, full-cohort/code freshness, actual RF leaf traversal and rendering the real domain labels. Native XGBoost first-tree predictions were checked against the exported paths as well. All configured domain example queries and both default views passed the live checker; the selected alternative rendered in business and technical views for two wells. Fresh desktop/mobile browser sessions exercised the model selector, tree diagram, SVG download and new algorithm FAQ entries without browser errors. Visual inspection caught and corrected fixed-width mobile clipping. Ruff and whitespace checks passed.
