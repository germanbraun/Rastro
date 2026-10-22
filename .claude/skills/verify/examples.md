# Worked examples from Rastro's domains

These are domain paths and historical evidence. Use the executable contracts in `SKILL.md` and
`docs/method-contracts.md`; historical scores are not immutable expected values.

## Oil and gas (`energia`)

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

Historical evaluation: B 7/10, D 10/10, C 10/10. Re-measure and investigate changes rather than enforcing those
numbers. The query gate covers every current competency query, including any explicitly expected empty answer.
Historical Lab consistency output says A's and B's gas match in every well; execute the model to verify it today.

Quality runner: `docker compose run --rm calidad`, with results in `layer/energia/calidad.json`. Review detected
source defects and their downstream impact separately from runner/test failures.

In the app, exercise the Demo and Lab tabs. Restart imported modules when changed; health alone is insufficient.

## Suppliers, oncology and Lab question sets

Registry entries supply the Ontop service/port and evaluation harness. Suppliers use `proveedores` with the current
harness; oncology uses the legacy runner and `--rerun`. Oncology's service is `ontop`, not `ontop-proveedores`.
Start required services only as needed and restore their previous running state afterwards.

`energia_lab` shares energy's ontology/service, but its evaluation folder is `layer/energia_lab` and its command must
end in `evaluar.py energia_lab`. It must not inherit energy's question-set target.
