# Thesis-style Q12 replication attempt

The user requested a tree-based reproduction on 2026-10-24, before deciding whether to add it to Lab. **Historical run status: partial replication; the original thesis and code had not yet been retrieved.**

**Update:** the user subsequently supplied the PDF. The primary-source review and a new pipeline replay are recorded separately in [pdf-replay](pdf-replay/protocol.md); the simplified results below are retained as earlier evidence. The official handle redirects to university maintenance, and public repository metadata endpoints are unavailable. A local/alternate copy has been requested from the user.

## Protocol fixed before this run

Use the existing 12-month target and eligibility rules (`--como-trabajo-publicado`): complete calendar months 1–12, shale-gas Vaca Muerta wells with fracture data, aligned raw and semantic targets. Use the two splits already implemented from prior thesis-reading notes: every fifth well after sorting by start date/id, and starts from 2023 as a forward test. This split specification is **not newly verified against the PDF**.

Compare the training concession median, ridge (alpha 1), and Random Forest (500 trees, minimum leaf size 4; seeds 42, 7 and 123). No search or selection to approach the thesis's reported score. Retain every seed result.

Two feature sets:

- **Existing design:** operator, concession, share and five fracture variables; the same inputs as the existing thesis-style console branch.
- **Public extension:** additionally vertical depth, registry latitude/longitude, start year, and stages/sand/water per lateral metre. These are plausible additional public predictors, **not a claim to reproduce the thesis feature engineering**. Coordinate records are joined from the already loaded public well registry with one unambiguous coordinate pair per well. Missing values use training means; invalid nonpositive denominators are missing. No neighbor-production or interpolated-geology features are invented.

The thesis numbers currently recorded in the repository are R² 0.47 for the area baseline, 0.75 for its best tree ensemble and 0.254 for a forward evaluation. Until the PDF is available, these remain prior-note values, not newly verified primary evidence. A similar score on a different cohort does not establish reproduction.

## Acceptance

To claim reproduction, first verify the PDF/code and match the population, observation period, target, preprocessing, feature definitions, split membership, model/hyperparameters and metrics; record unavoidable deviations. For app integration, also evaluate the chosen tree model on the current months-2–7 task with a proper chronological development/test protocol and a faithful explanation. Similarity to 0.75 alone does not approve integration.

## Reproduce

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"  # macOS, if needed
.venv/bin/python lab/gas/reproduce_thesis.py
```

The script only reads local sources and writes experiment results. The prepared input and per-well predictions are retained under ignored `data/cache/gas-thesis/`, with their fingerprints in `results.json`. It leaves the live model, source tables and published predictions unchanged. The extension mixes Rastro features with a raw-registry coordinate join for research; it is not an A/B comparison of semantic technology.

This is retrospective. Input load dates and mature training outcomes at the split date are not fully enforced; production before 2018 is absent locally; source snapshots may differ from those used by the thesis. Mixed-date testing is not future-well validation. These splits have been inspected in earlier Rastro work; they are not untouched final holdouts for deciding a production model.

## Measured results (2026-10-24, Argentina time)

The current local data yield **501** fracture-equipped wells (out of 512 with complete Q12), starting February 2018 through January 2025. Every fifth testing uses 401 training / 100 test wells; the forward split uses 327 / 174. All 501 have one unambiguous registry coordinate pair. The previous notes describe 642 wells in the thesis, so the cohort is not matched.

R², with forest ranges over all three predeclared seeds:

| Model / feature set | Every fifth | Starts from 2023 |
|---|---:|---:|
| Concession median | 0.448 | 0.261 |
| Ridge, existing design | 0.585 | −0.391 |
| Forest, existing design | 0.496–0.500 | 0.300–0.301 |
| Ridge, public extension | 0.621 | −0.358 |
| Forest, public extension | **0.671–0.675** | **0.355–0.361** |
| Thesis area baseline, prior notes only | 0.47 | Not recorded |
| Thesis best ensemble, prior notes only | 0.75 | 0.254 |

The extended forest's MAE is 18.47–18.63 million m³ in the interleaved test and 23.17–23.25 in the forward test, against 22.58 and 24.06 for the concession median. This is promising for Q12 on these local data. It does **not** establish equality with the thesis, superiority to its model, or suitability for the months-2–7 app. The score difference to 0.75 is approximately 0.075–0.079 R²; without matched wells and uncertainty for both studies, it should not be called equivalent.

The untouched existing `--como-trabajo-publicado` command was also rerun: rounded forest R² 0.49 / 0.30, ridge B 0.59 / −0.40, and area median 0.45 / 0.26. Its forest uses training **medians** for imputation, whereas this comparison uses training **means** consistently across models. Its console ridge also includes vertical depth, unlike the new existing-design feature set. This explains why that check is recorded separately rather than called an exact rerun of the new runner.

## What remains to reproduce the thesis

| Item | Current evidence / mismatch |
|---|---|
| Original PDF and code | Not retrieved; official repository is in maintenance. See `source-access.json`. |
| Population and historical data | 501 local wells, from 2018; 642 in prior thesis notes. Earlier production is not loaded. |
| Target definition | Current calendar months 1–12 include the initial partial month. Thesis details need PDF verification. |
| Features and cleaning | Added public predictors are an explicitly separate extension. Exact thesis definitions, exclusions, neighbor features and geology are unverified or unavailable. |
| Split membership | Existing every-fifth/date-cutoff approximation; original IDs and within-date ordering are unavailable. |
| Algorithms and hyperparameters | Fixed Random Forest, not the thesis's unverified best ensemble. |
| Deployment evidence | No model or run published. The main Lab keeps its current ridge model and target. |

**Decision:** retain this as a partial replication experiment. It supports investigating an optional Q12 tree model, not claiming a reproduced 0.75 or changing the current app. Obtain the thesis PDF/code before closing the replication gap.

## Verification

77 tests passed, 5 opt-in PostgreSQL change-guard tests skipped. Ruff and whitespace checks passed. Tests cover explicit split membership, coordinate-join cardinality, invalid intensity denominators and independence from held-out targets. Script, prepared-input and every per-well prediction fingerprint were checked against the saved receipt.
