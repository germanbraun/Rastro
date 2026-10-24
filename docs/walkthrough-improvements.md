# Connected Lab walkthrough

Approved scope: the user's 2026-10-24 request to implement the suggested improvements.
Purpose: follow one selected real test well from source fields to model inputs, prediction and inspectable evidence.

| Step | What changes | Evidence |
|---|---|---|
| Select | One well selector controls the Lab walkthrough and the prediction comparison | Existing aligned test cohort |
| Inputs | Original baseline values, ontology properties, integrated values, effective inputs and status | Existing SQL_A/SPARQL_B result and parameterized raw-source queries |
| Train | Show the selected row and explain chronological splitting and retrospective availability | Existing model preparation; late arrivals remain visible |
| Explain | Explore a concept, its variables and coefficients, then the actual source rows | Existing model contributions and linked source URIs |
| Audit | Compare published code version, full input snapshot, selected output/contributions and source IDs | Read-only lab_gas tables, current fitted model, SPARQL provenance |
| Slides | Follow the same real well and visual sequence, with dated snapshot notes | Existing 165404 example; no new accuracy claim |

The model algorithm, source/link rules and experiment measurements remain unchanged. The renderer gains optional
selected-well/input/evidence hooks. Published runs are not overwritten to make status comparisons pass.

## Implemented behavior

- The Lab tab's single selector drives the walkthrough, source rows, contribution explorer and prediction comparison.
  The separate timed Demo keeps its own fixed example.
- The input table shows the SQL baseline calculation, ontology property, integrated value before imputation and
  effective model value. Source queries remain inspectable and parameterized. Observation today is not independent
  confirmation; reviewed-link notices, missing values and late arrivals are separate states.
- A group selector opens its variables and coefficients. A variable selector opens raw source rows and current
  semantic entity/source URI, original report ID, rule, evidence and dates. Unselected candidate source rows are
  explicitly distinguished from the linker's selected/aggregated values.
- Published-run checks compare code version, the entire saved input table (including training wells), and the selected
  well's prediction, grouped contributions and source identifiers. Persisted rounding is respected and missingness
  is preserved. Audit queries are pinned to the same captured run ID as its status message. Missing or differing runs
  are never relabeled as matching. Current source text is not claimed to be an immutable historical snapshot.
- The existing Lab reader role supplies raw-source and published-result inspection. The linker initializes that
  existing role for fresh deployments; Layer's baseline reader permissions are unchanged. No new service or dependency
  is added. The model-data cache now includes the model code fingerprint.
- Lab slides 19–22 follow well 165404, source report 4799, 53 stages and the unchanged 54.14767395030741 M m³ prediction.
  The event date and the later publication date are explicit. No historical no-leakage claim is made.

The existing published run was deliberately retained: inputs, numeric results and source IDs match for 165404,
while its code version differs. The app correctly reports that difference. The model algorithm and its existing
explanation generator were not changed, and frozen evaluation/blind-reference artifacts were not regenerated.

## Validation — 2026-10-24

- Full pytest suite: **71 passed, 5 skipped** (the opt-in change-guard PostgreSQL integration tests were not enabled).
  Ruff passed. Regression cases cover complete-input drift despite equal selected predictions, code/contribution/URI
  drift, persisted precision, missing values and runs, pinned run identity, and rendering inside the actual outer
  expander. The source panel uses a container because this Streamlit version disallows nested expanders.
- Against the local database/endpoints, all four steps rendered for wells **165404** and **166133** in both views;
  every contribution group and its source queries were exercised, including missing inputs. The standard domain
  runner also passed all configured energy questions and both app views.
- Real Chrome interactions passed: choosing Lab, opening the walkthrough, exploring fracture stages and switching
  wells. No browser page errors. At a fresh 390 px mobile viewport, the document width was also 390 px.
- Chrome measured the four slides' content bottoms at **696, 696, 696 and 782 px**, all before 920 px and the footer.
  The source-to-input slide and the desktop contribution panel were visually inspected.
- The fresh-deployment linker container sees the existing Lab reader SQL. That reader can SELECT fracturing but
  cannot UPDATE it; the Layer baseline reader still lacks access to that schema. No evaluated reader definitions changed.

Operational logs/screenshots are temporary `/tmp/rastro-connected-*` review artifacts on this laptop. The local app
was restarted to load the implementation. These checks establish functioning UI and numerical consistency, not
independently reviewed prediction accuracy or historical information availability.
