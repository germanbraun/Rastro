---
name: verificar
description: Comprobar que Rastro levanta y responde (servicios, conteo por fuente, ontología, queries y mapeos). Usalo después de un cambio y antes de cerrar una fase o commitear.
---

# Verificar Rastro

Corré todo y contá qué pasó, con los números. Si algo falla, decilo tal cual.

```bash
docker compose up -d
docker compose ps
docker compose exec -T postgres psql -U rastro -c "select * from rastro_meta.source_counts"
docker compose run --rm ontology-check
curl -s -H 'Accept: text/csv' --data-urlencode 'query=PREFIX oncologia: <https://w3id.org/rastro/oncologia#> SELECT (COUNT(*) AS ?n) WHERE { ?s a oncologia:DataSource }' http://localhost:8080/sparql
curl -s http://localhost:7210/repositories/rastro/size
curl -s http://localhost:8501/_stcore/health
docker compose run --rm layer-eval
```

Qué esperar:

- Los servicios `postgres`, `ontop` y `graphdb` arriba, con Ontop `healthy`.
- El conteo por fuente con filas en las cuatro fuentes cargadas.
- `ontology-check` en OK para todas las queries.
- Ontop devuelve 4 fuentes (y, desde la Fase 2, unos 106 mil ensayos y 3.700 fármacos). Si Ontop no levanta, mirá `docker compose logs ontop`: casi siempre es un error en `mappings/rastro.r2rml.ttl` o un término del mapeo que no está en la ontología.
- GraphDB con unos 15,4 M de triples (MeSH 2026).
- La demo responde `ok` en http://localhost:8501. Abrila y probá una pregunta de ejemplo: tiene que mostrar la tabla, las fuentes y "¿Cómo lo supe?".
- `layer-eval` muestra el puntaje de las tres formas de responder. Si cambiaste datos o enlaces, corré antes `--rerun`.

Y las preguntas de competencia contra Ontop (cada una tarda alrededor de un segundo):

```bash
for f in ontology/queries/cq*.rq; do echo "== $(head -1 $f)"; curl -s -m 300 -H 'Accept: text/csv' --data-urlencode "query@$f" http://localhost:8080/sparql | head -5; done
```

Las ocho tienen que devolver filas. Referencias: la 1 tiene que mostrar trastuzumab y pertuzumab; la 7, daratumumab con 0 reportes previos.

Si GraphDB se reinicia solo, casi siempre es memoria de Docker: revisá qué otros contenedores corren.
