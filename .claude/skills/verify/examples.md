# Worked examples from Rastro's domains

These are domain paths and historical evidence. Use the executable contracts in `SKILL.md` and
`docs/method-contracts.md`; historical scores are not immutable expected values.

## Oil and gas (`energia`)

The default path, with the services up:

```bash
python layer/experiment.py energia --expectations layer/energia/query-checks.yaml --measure
```

The same checks one by one, to read a failure:

```bash
python layer/method.py registry energia
docker compose exec -T postgres psql -U rastro -c "select * from rastro_meta.source_counts"
docker compose run --rm ontology-check python /ontology/check.py /ontology/energia
# Requires reviewed query expectations; missing evidence remains pending:
python layer/method.py verify energia --expectations layer/energia/query-checks.yaml
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
git diff layer/energia/resultados.md   # preserve pre-existing edits; no Git reset/checkout
python3 lab/gas/modelo.py             # inspect the complete output and exit status
python layer/method.py publication energia
```

The gate covers new claims; numbers already published stay as they are, labelled provisional until the gate passes.

Historical evaluation: B 7/10, D 10/10, C 10/10. Re-measure and investigate changes rather than enforcing those
numbers. The query gate covers every current competency query, including any explicitly expected empty answer.
Historical Lab consistency output says A's and B's gas match in every well; execute the model to verify it today.

Quality runner: `docker compose run --rm calidad`, with results in `layer/energia/calidad.json`. Review detected
source defects and their downstream impact separately from runner/test failures.

In the app, exercise the Demo and Lab tabs. Restart imported modules when changed; health alone is insufficient.

## Research affiliations (`afiliaciones`)

```bash
docker compose up -d postgres ontop-afiliaciones
python layer/experiment.py afiliaciones --expectations layer/afiliaciones/query-checks.yaml --measure
```

Its query checks (`layer/afiliaciones/query-checks.yaml`) are all `evidence: invariant`: technically validated, not
yet against independent references. It is the only domain with `method.lifecycle` (`layer/afiliaciones/lifecycle.json`)
and `method.source_manifest` (`layer/afiliaciones/sources.yaml`); check a question's state with
`python layer/lifecycle.py status afiliaciones <qid>`. Its quality result is `review_findings` (AI decisions waiting for
a person), not defects. The publication gate stays pending until a person confirms the references.

## Suppliers, oncology and Lab question sets

Registry entries supply the Ontop service/port and evaluation harness. Suppliers use `proveedores` with the current
harness; oncology uses the legacy runner: `docker compose run --rm layer-eval python /layer/eval/run.py --rerun`
(scoring is part of that runner). Oncology's service is `ontop`, not `ontop-proveedores`, and its ontology check is
`docker compose run --rm ontology-check python /ontology/check.py /ontology`. Its app is `app_mode: legacy`, so
`layer/experiment.py` skips the app check: exercise its screen by hand. Neither domain has a `query-checks.yaml` yet,
so the query gate is pending for both.
Start required services only as needed and restore their previous running state afterwards.

`energia_lab` shares energy's ontology/service, but its evaluation folder is `layer/energia_lab` and its command must
end in `evaluar.py energia_lab`. It must not inherit energy's question-set target.
