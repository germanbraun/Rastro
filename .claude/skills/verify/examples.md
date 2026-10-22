# Worked examples from Rastro's domains

## Oil and gas (`energia`, the demo): always

```bash
docker compose ps                                      # postgres, ontop-energia and app up; ontop-energia healthy
docker compose exec -T postgres psql -U rastro -c "select * from rastro_meta.source_counts"
docker compose run --rm ontology-check                 # OK on every query of the three domains
for q in ontology/energia/queries/cq*.rq; do echo "$q $(curl -s -H 'Accept: text/csv' --data-urlencode "query@$q" http://localhost:8082/sparql | wc -l) filas"; done
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje   # without Rastro 7/10, SQL + links 10/10, with Rastro 10/10
git diff --stat layer/energia                          # only the date should change: if so, git checkout layer/energia/resultados.*
python3 lab/gas/modelo.py | head -8                    # A and B gas match; A and B error; doubtful data
```

The oil and gas quality rules (SHACL): `docker compose run --rm calidad` (about 3 minutes). All of them in «se cumple» (holds); if one does not, the detail is in `layer/energia/calidad.json` and in the app («Bajo el capó», Under the hood).

What to expect:

- `ontop-energia` `healthy`. If it does not start, `docker compose logs ontop-energia`.
- The 10 competency queries with rows, in a few seconds each.
- The evaluation with the same scores as `layer/energia/resultados.md`.
- Rastro Lab: «El gas de A (SQL) y el de B (Rastro) coinciden en todos los pozos: True» (A's and B's gas match in every well).

The app: open http://localhost:8501 and walk through the **Demo** tab (the four moments) and **Rastro Lab**. If you changed `app/dominio.py`, `app/lab.py` or `lab/gas/modelo.py`, restart it: `docker compose restart app`.

## US suppliers (`proveedores`) and oncology (`oncologia`): when you touched them

They are stopped to save memory (`ontop-proveedores`, `graphdb`). Start them, verify and stop them again:

```bash
docker compose start ontop-proveedores graphdb
curl -s -H 'Accept: text/csv' --data-urlencode 'query@ontology/proveedores/queries/cq1.rq' http://localhost:8081/sparql | head -3
curl -s -H 'Accept: text/csv' --data-urlencode 'query@ontology/queries/cq1.rq' http://localhost:8080/sparql | head -3
docker compose stop ontop-proveedores graphdb
```

If GraphDB restarts on its own, it is almost always Docker memory: check which other containers are running.
