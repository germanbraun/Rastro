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
curl -s -H 'Accept: text/csv' --data-urlencode 'query=PREFIX : <https://w3id.org/rastro/ontology#> SELECT (COUNT(*) AS ?n) WHERE { ?s a :DataSource }' http://localhost:8080/sparql
curl -s http://localhost:7210/repositories/rastro/size
```

Qué esperar:

- Los servicios `postgres`, `ontop` y `graphdb` arriba, con Ontop `healthy`.
- El conteo por fuente con filas en las cuatro fuentes cargadas.
- `ontology-check` en OK para todas las queries.
- Ontop devuelve 4 fuentes. Si Ontop no levanta, mirá `docker compose logs ontop`: casi siempre es un error en `mappings/rastro.r2rml.ttl` o un término del mapeo que no está en la ontología.
- GraphDB con unos 15,4 M de triples (MeSH 2026).

Desde la Fase 2, corré además las queries de `ontology/queries/` contra Ontop y revisá que las respuestas tengan sentido.

Si GraphDB se reinicia solo, casi siempre es memoria de Docker: revisá qué otros contenedores corren.
