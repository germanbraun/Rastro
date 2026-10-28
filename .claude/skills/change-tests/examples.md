# Worked examples from Rastro's domains

## Oil and gas (`energia`): the source changes

Scripts in `layer/energia/cambio/` (`cambio.sh`, `probar.py`). They simulate that the energy secretariat publishes a new version of Capítulo IV.

```bash
layer/energia/cambio/cambio.sh registrar    # the two acts (renamed column, oil in barrels), with and without the fix
```

- Act 1 (`renombrar`): `prod_pet` is renamed to `petroleo`. Act 2 (`valores`): oil is in barrels.
- Each act changes the source, restarts Ontop (`ontop-energia`), measures, fixes **one line** of the mapping and measures again. It always ends with `deshacer`; the guard restores inputs even on failure; if recovery is incomplete, run `python layer/change_guard.py recover` before another test.
- `probar.py` checks that 2025 oil stays around 46.6 million m³ (about 800,000 barrels per day); if the unit changes, Rastro warns.
- The result is saved in `cambio/resultado.json` (steps `antes`, `renombrar`, `renombrar-arreglado`, `valores`, `valores-arreglado`, `despues`), which «Por qué confiar» (Why trust it) and moment 2 of the demo read.
- If you change the mapping line that reads oil (`prod_pet AS petroleo_m3`), update the pattern in `cambio.sh` and the `arreglo` entries in `app/dominios/energia.yaml`.

## Oil and gas (`energia`): one correction, every result

`layer/energia/cambio/correccion.sh` removes the corrected share of Aguada Pichana Este (`linking/energia/participaciones-revisadas.csv`), rebuilds Rastro (`energia-linker`, restart `ontop-energia`), measures and puts it back. About 15 minutes.

```bash
layer/energia/cambio/correccion.sh registrar
git status --short    # when done, the CSV and the saved answers must be as before
```

- The checker's test: `tests/test_energia_correccion.py`.
- It measures the share answer (with Rastro, SQL with links and without Rastro), what goes into the Rastro Lab model and its explanation.
- The result is saved in `cambio/correccion.json`, which moment 4 of the demo reads.
- What was measured: the prediction barely moves (the share is fixed within the concession), so do not say it changes.

## Oil and gas (`energia`): which predictions change

`layer/energia/cambio/impacto.sh` (with `impacto.py`). Rastro says in advance which predictions depend on a source record (question 14, lineage in reverse) and this is checked: the reported fracturing is corrected in the source (record `REGISTRO=4703`, value `CORRECCION=12` in the script), Rastro is rebuilt, a run is published and `python3 lab/gas/modelo.py --comparar` says what changed. They must be exactly the ones Rastro said. Pick a record from a test well (from 2025): a training one changes the model and moves every prediction, and Rastro says so («reentrenar», retrain).

```bash
layer/energia/cambio/impacto.sh registrar    # ~15 minutes; when done, the record and the current run are as before
```

The result is saved in `cambio/impacto.json`, which the Rastro Lab tab shows.

## US suppliers (`proveedores`): the source changes

Guarded: the registry's `change_guard` names the mapping, the saved answers and `usaspending.contract`, and the
column the first act renames (`awarding_agency`). `deshacer` restores the table and the mapping from the guard's
snapshot, never with inverse arithmetic.

Scripts in `layer/proveedores/cambio/` (`cambio.sh`, `probar.py`). They simulate a new USAspending version.

```bash
layer/proveedores/cambio/cambio.sh registrar   # runs the 9 queries, the two acts, and saves resultado.json
```

- Act 1: `awarding_agency` is renamed to `agency_name`. Act 2: amounts are in thousands of dollars.
- The fix is one line of `mappings/proveedores.r2rml.ttl`, then restart `ontop-proveedores` (port 8081).
- No correction or impact test in this domain.

## Research affiliations (`afiliaciones`): one correction, every result

`layer/afiliaciones/cambio/correccion.sh` simulates that ROR adds the official name of the Garrahan hospital as an
alias (a new row in `ror.name`, as its next release would). It measures every saved evaluation query (B, D, C) and
cq1-cq3 before, right after the source change and after rebuilding the links (`afiliaciones-linker`, restart
`ontop-afiliaciones`); then the guard puts everything back. Approved plan:
`docs/experiments/research-affiliations/change-test-proposal.md`.

```bash
layer/afiliaciones/cambio/correccion.sh registrar
```

- Guarded: the files and tables it may change are in `method.change_guard` (`linking/afiliaciones/correcciones.csv`,
  the saved answers, `ror.name` and the `afiliaciones` link tables).
- Result: `cambio/correccion.json` (measurements in `medicion-antes.json`, `medicion-fuente.json`,
  `medicion-despues.json`). The checker's test: `tests/test_afiliaciones_cambio.py`.
- Traceability of 30 answer cells per approach, read-only: `python /layer/afiliaciones/cambio/trazabilidad.py` in the
  `layer-eval` service, written to `cambio/trazabilidad.json`.
- No source-change or impact test in this domain.

## Oncology (`oncologia`)

No change tests (`method.change_tests` is not set in the registry).

## Afterwards (oil and gas)

If a number changed, update it in the script and in the slides «La base cambia» (The source changes) and «Una corrección» (One correction) (skill `decks`), and in `docs/decisions.md`.
