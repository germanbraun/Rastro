---
name: verificar
description: Comprobar que Rastro levanta y responde en los tres dominios (servicios, conteo por fuente, ontologías, queries, Rastro Lab y la app). Usalo después de un cambio y antes de cerrar una fase o commitear.
---

# Verificar Rastro

Corré todo y contá qué pasó, con los números. Si algo falla, decilo tal cual.

## Petróleo y gas (la demo): siempre

```bash
docker compose ps                                      # postgres, ontop-energia y app arriba; ontop-energia healthy
docker compose exec -T postgres psql -U rastro -c "select * from rastro_meta.source_counts"
docker compose run --rm ontology-check                 # OK en todas las queries de los tres dominios
for q in ontology/energia/queries/cq*.rq; do echo "$q $(curl -s -H 'Accept: text/csv' --data-urlencode "query@$q" http://localhost:8082/sparql | wc -l) filas"; done
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje   # sin Rastro 7/10, SQL + enlaces 10/10, con Rastro 10/10
git diff --stat layer/energia                          # solo debería cambiar la fecha: si es así, git checkout layer/energia/resultados.*
python3 lab/gas/modelo.py | head -8                    # el gas de A y B coincide; error de A y B; datos dudosos
```

Qué esperar:

- Ontop de energía `healthy`. Si no levanta, `docker compose logs ontop-energia`: casi siempre un término del mapeo que no está en la ontología o una columna que cambió.
- Las 10 consultas de competencia con filas, en pocos segundos cada una.
- La evaluación con los mismos puntajes de `layer/energia/resultados.md`. Si cambian, no es un detalle: buscá qué dato o regla cambió.
- Rastro Lab: «El gas de A (SQL) y el de B (Rastro) coinciden en todos los pozos: True».

## La app

Abrí http://localhost:8501 y recorré la pestaña **Demo** (los cuatro momentos) y **Rastro Lab**. Si cambiaste un módulo que importa la app (`app/dominio.py`, `app/lab.py`, `lab/gas/modelo.py`), reiniciala: `docker compose restart app`. La primera carga después de cambiar datos tarda (se recalculan y se guardan en disco).

## Proveedores y oncología: cuando los tocaste

Están apagados para ahorrar memoria (`ontop-proveedores`, `graphdb`). Levantalos, verificá y volvé a apagarlos:

```bash
docker compose start ontop-proveedores graphdb
curl -s -H 'Accept: text/csv' --data-urlencode 'query@ontology/proveedores/queries/cq1.rq' http://localhost:8081/sparql | head -3
curl -s -H 'Accept: text/csv' --data-urlencode 'query@ontology/queries/cq1.rq' http://localhost:8080/sparql | head -3
docker compose stop ontop-proveedores graphdb
```

Si GraphDB se reinicia solo, casi siempre es memoria de Docker: revisá qué otros contenedores corren.
