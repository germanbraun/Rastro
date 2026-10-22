---
name: agregar-pregunta
description: Sumar o cambiar una pregunta de competencia de Rastro con su query SPARQL, en cualquiera de los tres dominios, y extender la ontología solo si hace falta. Usalo al tocar ontology/**/competency-questions.md, las ontologías u ontology/**/queries/.
---

# Agregar una pregunta de competencia

Las preguntas mandan: la ontología solo tiene lo que alguna pregunta necesita.

| Dominio | Ontología | Preguntas y queries | Mapeo | Ontop |
|---|---|---|---|---|
| Petróleo y gas | `ontology/energia/energia.ttl` | `ontology/energia/` | `mappings/energia.r2rml.ttl` | :8082 |
| Proveedores | `ontology/proveedores/proveedores.ttl` | `ontology/proveedores/` | `mappings/proveedores.r2rml.ttl` | :8081 |
| Oncología | `ontology/rastro.ttl` | `ontology/` | `mappings/rastro.r2rml.ttl` | :8080 |

## Pasos

1. **La pregunta en palabras de negocio**, como la diría un cliente. Tiene que cruzar al menos dos fuentes; si una sola tabla la responde, no muestra el valor de Rastro. Si depende de una definición («operadora», «no convencional»), escribila en la pregunta.
2. **Sumala a la tabla** de `competency-questions.md` del dominio, con número, fuentes y para qué es (demo, Layer o Lab).
3. **Escribí la query** en `queries/cq<N>.rq` del dominio:
   - Primera línea: `# <N>. <la pregunta>`.
   - El prefijo del dominio (`energia:`, `proveedores:`, `oncologia:`), nunca el prefijo vacío.
   - Sin caminos `*` o `+`: Ontop no los soporta. Lo que necesite clausura se precalcula en Postgres.
   - Valores de la fuente tal cual (`"vaca muerta"`, `"SHALE"`, `"TERMINATED"`).
4. **Si falta un término**, agregalo a la ontología con `rdfs:label` en español y un comentario corto. Preferí un atributo a una clase nueva; una propiedad que usan dos clases va sin `rdfs:domain` (si no, Ontop deduce clases equivocadas). Sumalo a `term_sources` (y a `link_sources` si es un enlace) del dominio en `layer/dominios.yaml`, y a las notas que lee el asistente (`layer/<dominio>/sparql-notes.md`).
5. **Si necesita un dato nuevo,** agregá su mapeo (con `rr:datatype` si la columna sale de un `GROUP BY` o `DISTINCT`) y reiniciá el Ontop del dominio.
6. **Validá:** `docker compose run --rm ontology-check` en OK, y la query contra Ontop con una respuesta que tenga sentido para alguien del negocio:
   `curl -s -H 'Accept: text/csv' --data-urlencode "query@ontology/energia/queries/cq<N>.rq" http://localhost:8082/sparql`
7. **Si va a la app,** sumala a `preguntas` de `app/dominios/<dominio>.yaml` (pregunta simple, formulación técnica y, si se puede, «¿Por qué este número?»). Si va a la evaluación, seguí la skill `evaluar`.
8. **Si es de Rastro Lab,** solo datos anteriores al inicio del pozo (ver la skill `rastro-lab`).
