---
name: change-tests
description: Run and record the tests that show what happens when a source changes (a renamed column, a new unit), when a value is corrected once (the correction reaches every result) and which predictions depend on a source record. Use it when you touch layer/*/cambio/, the mappings those tests change or the reviewed corrections, in any domain.
---

# Change tests

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

They are the central argument of the method (step 8, Maintain, in `docs/method.md`): with the semantic layer, the hard part is fixed or corrected in one place.

## Constraints

- **A change test always ends with everything as it was,** even when it fails halfway: the guard restores it (below);
  `deshacer` is only for the manual demo steps.
- **Never leave altered** the source, the reviewed corrections CSVs or the saved answers: their bytes and database values match the captured starting state, including pre-existing edits.
- **Never edit the model or the mapping while an impact test runs:** the comparison of runs would mix two changes.
- **Report only what was measured:** every number comes from the saved JSON.

## Where they live

Read the domain's entry in `layer/dominios.yaml`:

- `method.change_tests`: the folder with the scripts (for example `layer/<domain>/cambio/`).
- `method.change_guard`: the files and tables each test may change, which the guard restores, and the column a
  `cambio` test renames (`renamed: {table, column, to}`), which the guard checks before and renames back.
- `method.mapping`, `method.ontop.service`, `method.linker.service`, `method.linker.corrections`, `method.evaluation`: what the scripts change, restart and measure.

If the domain has no `change_tests`, create the folder following the existing pattern (see examples.md) and add the path to the registry.

## Guarded execution

Stop other writers and use an isolated development database. In a domain with `method.change_guard`, the
`registrar` scripts automatically enter `layer/change_guard.py`, which snapshots actual files and affected tables, restores on success/failure/signals,
checks exact table and file equality, and retains recovery data on failure. Do not bypass it. Use
`python layer/change_guard.py recover` after interruption. Standalone mutating demo subcommands are refused outside
a guarded run. Restoration removes test-created model runs and restores the original current-run flags; retain
result JSONs as evidence. A script without the guard is legacy: do not run it until it has one (see `examples.md`).

## First: the plan

Before running any test or touching any file, write the plan as a short table, one row per change:

| What is broken or corrected | Questions or predictions expected to change | By how much | Evidence | How sure | How it is undone | Open question |
|---|---|---|---|---|---|---|

The evidence is why the change is expected (the mapping line, the correction row, the `prov:used` records). A person
reviews it; the table goes into the decision or the experiment log, and the result is compared with it.

## 1. The source changes (`cambio.sh` + `probar.py`)

Simulate a new version of a source and measure all the saved evaluation queries, without the semantic layer (SQL over the raw sources) and with it.

Each "act" does the same thing:

1. **Measure before**: run every saved query (`probar.py`), both paths.
2. **Break the source on purpose**: rename a column the mapping reads, or change the unit of a value (for example, multiply by a conversion factor).
3. **Restart the domain's Ontop** and measure again. Expect: Ontop may not start (renamed column) or answers silently change (new unit); the SQL path breaks in every query that touches the column.
4. **Fix in one place**: change one line of the mapping, restart, measure again. Count how many SQL queries would need the same fix.
5. **Always undo:** the guard restores the database and the mapping (`cambio.sh deshacer` does it in the manual
   steps). If restoration fails, keep the recovery directory and run `python layer/change_guard.py recover`; verify the original bytes and values, not merely Git cleanliness.

Usual subcommands: `probar`, `renombrar`, `valores`, `arreglar <act>`, `deshacer`, `registrar` (runs all acts and saves `resultado.json`, which the app reads).

Add a sanity check in `probar.py` on a known total (for example the yearly volume) so a unit change is caught even when queries "still answer".

Save each numeric answer next to its status (`values` in `resultado.json`), so the app and the slides can tell a scenario with one real number (a `valor` in the domain's `cambios`: the question, its wording, scale and unit) instead of counts. Run the evaluator with `--no-deps` while the layer is broken on purpose: a service that waits for a healthy layer would never start. A step with a question that SQL over the sources cannot answer (`—`) is not a broken step.

## 2. One correction, every result (`correccion.sh`)

Change one value once - remove a reviewed correction (a row of a file in `method.linker.corrections`), or add the row a
source's next release would add - rebuild the layer (linker + Ontop restart), measure, and let the guard put it back.

- Measure the affected answer with the three paths (without the layer, SQL with links, with the layer) and anything downstream that uses it (a model's inputs and explanations, if the domain has one).
- Save the result in `correccion.json`, with the business answer the correction moves most (the one the demo shows) and the document's value, saved while the corrections file still has it (the check runs after the row is removed).
- When done, the changed file or table and the saved answers must be as before (byte-for-byte comparison to the starting snapshot, including untracked files).
- What is claimed must match what was measured: if a downstream result barely moves, do not say it changes.
- **Declare exact expectations before measuring and check them with code** (`correccion.py verificar`, run by
  `correccion.sh`): which paths change and which do not, the named records, unchanged coverage. A missing or failed
  measurement fails; it is never read as «no change». The checker has a test with broken copies of the result
  (each domain's test is in `examples.md`). Report «behaved as expected».

## 3. Which predictions change (`impacto.sh`)

Only for domains with predictions saved with the records they used (`prov:used`). The layer says in advance which predictions depend on a source record (lineage in reverse); the test checks it:

1. Ask which predictions use the record.
2. Simulate that the source corrects it, rebuild the layer, publish a new run, compare runs.
3. The predictions that changed must be exactly the ones announced.
4. Restore the record and the current run.

Pick a record used only by test predictions: a record used in training changes the model and moves every prediction, and the layer should say so ("retrain").

Save the result in `impacto.json`.

## Afterwards

If a number changed, update it everywhere it is shown (app texts, demo script, slides: skill `decks`) and add an entry to `docs/decisions.md`. A fix after measuring is measured again only in what it affects, and said so.

## A person approves

- **The plan:** what will be broken or corrected, what is expected to change and how it is undone, before running.
- What is claimed from the result, before it is shown in the app, the script or the slides.

## Lessons

- Always end in undo; a test that leaves the source broken corrupts every later measurement.
- Fix in the mapping, not in the data: the point is that one line fixes every question.
- A unit change is the dangerous one: queries keep answering with wrong numbers. Keep a plausibility check on a known total.
- Tests that rebuild the layer are slow (the linker runs twice); run them only when the mapping, the corrections or the links changed.
- Report only what was measured; the saved JSON is the source of every number shown.

See examples.md for the commands, scripts and numbers from Rastro's domains.
