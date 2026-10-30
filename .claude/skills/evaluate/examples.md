# Worked examples from Rastro's domains

Concrete cases for the skill `evaluate`. The generic procedure is in `SKILL.md`; the registry is `layer/dominios.yaml`.

## Which domains are evaluated with `layer/evaluar.py`

Oil and gas (`energia`, folder `layer/energia/`), suppliers (`proveedores`, folder `layer/proveedores/`), research
affiliations (`afiliaciones`, folder `layer/afiliaciones/`) and the predictions set (`energia_lab`, folder
`layer/energia_lab/`). Oncology (`oncologia`) has its evaluation in
`layer/eval`, run with `docker compose run --rm layer-eval`.

## Measure a question (oil and gas)

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia prompt <q> 0 <B|D|C>
docker compose run --rm -T layer-eval python /layer/evaluar.py energia try <q> 0 <B|D|C> < query.sql
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
```

Suppliers, the same with `proveedores` (for example `... evaluar.py proveedores prompt p01 0 C`).

## After changing data, mappings or rules (oil and gas)

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
git diff layer/energia/resultados.md
# Preserve pre-existing edits; review generated diffs without Git checkout/reset.
```

## Independent references (affiliations)

`layer/afiliaciones/eval/referencias.json` replaces the SPARQL references: its `nota` says they come from a blind
review by an AI assistant that did not see Rastro, still to be confirmed by a person. Adjudication in
`layer/afiliaciones/adjudicacion.md`. The domain's `layer-eval` run needs `ontop-afiliaciones` started first (the
service only waits for the oil and gas Ontop). No domain has a `reference-evidence.yaml` yet, so every score is
provisional (`python layer/method.py publication afiliaciones` stays pending).

## One prompt per subagent: the discarded check (oil and gas)

In the consistency check of 22/10/2026, a subagent saw the four forms of a question together, repeated the same query
and the check measured nothing. It was discarded.

## Another question set: `energia_lab` (oil and gas)

`energia_lab` (`layer/energia_lab/`) measures the questions about Rastro Lab's predictions (the gas model for new
Vaca Muerta shale wells), separate from the Layer evaluation. In `layer/dominios.yaml` it inherits from `energia` with
`<<: *energia` and has its own read-only users (`energia_lab_reader`, `energia_lab_reader_links`) and SQL notes
(`layer/energia_lab/sql-notes.md`, `layer/energia_lab/sql-enlaces-notes.md`).

## When it does not have the data (oil and gas)

```bash
docker compose run --rm -T layer-eval python /layer/fuera.py energia prompt C
docker compose run --rm -T layer-eval python /layer/fuera.py energia guardar C < respuesta.json
docker compose run --rm -T layer-eval python /layer/fuera.py energia puntaje
```

Questions in `layer/energia/fuera/preguntas.yaml`. Examples of missing data in this domain: prices, reserves, 2026.

## Failure types seen (oil and gas, from `docs/method.md`)

- Wrong link: a company name joined to the wrong group.
- Wrong mapping: a domain in the dictionary that turned every fracture record into a fracturing.
- Wrong query: Rastro reached the operator through the share instead of the declared name.
- Ambiguous definition: "producing", what each company operates or what it is entitled to.
- Impossible source value: a pressure of 111.515 psi.

## Reference review packet (oil and gas, 2026-10-29)

`review_packet.py energia build` wrote a 536-line packet for the 10 questions and a form with one row each. A
throwaway form (Rastro's answers, e02 changed to 15700) recorded and rescored: B 7, D 10, C 10 of 10 (15700 is within
5 % of 15809). The gate then listed only the run's model, model version and prompts, not saved when oil and gas was
measured. The throwaway files were removed and the results restored; the real form waits for a person.

## Re-measured with saved prompts (oil and gas, 2026-10-29)

30 fresh subagents, each told to read only its prompt file (`prompts/<q>-0-<X>.txt`) and answer with the JSON: B 8,
D 10, C 10 of 10. Three B queries timed out and were given the error back (e08 succeeded on its third attempt). The
consistency forms (n = 1–3) were not re-measured and say so. With `eval/run.yaml` and the prompts, the gate's only
missing piece is the person's review.

## The chat, without an API key (oil and gas, 2026-10-30)

`chat_eval.py energia`: 7 conversations, 13 turns, answered in 4 rounds (7, 6, 6 and 5 calls), each by a fresh
subagent reading only its call file. 11 of 13 right; follow-ups 5 of 6; no unbacked number; no retries; both
no-data questions said what was missing. The two misses asked for a share «en cada concesión» and got the
per-concession breakdown: the question's wording, adjudicated and counted as wrong, not re-measured.
