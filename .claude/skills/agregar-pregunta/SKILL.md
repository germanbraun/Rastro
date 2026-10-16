---
name: agregar-pregunta
description: Sumar o cambiar una pregunta de competencia de Rastro con su query SPARQL, y extender la ontología solo si hace falta. Usalo al tocar ontology/competency-questions.md, ontology/rastro.ttl u ontology/queries/.
---

# Agregar una pregunta de competencia

Las preguntas mandan: la ontología solo tiene lo que alguna pregunta necesita.

## Pasos

1. **La pregunta en palabras de negocio**, como la diría un cliente. Tiene que cruzar al menos dos fuentes; si una sola tabla la responde, no muestra el valor de Rastro.
2. **Sumala a la tabla** de `ontology/competency-questions.md`, con número, fuentes y para qué producto es (Demo, Layer o Lab).
3. **Escribí la query** en `ontology/queries/cq<N>.rq`:
   - Primera línea: `# <N>. <la pregunta>`.
   - Prefijos `:` (Rastro), `meshv:` y `rdfs:`.
   - Para "una enfermedad y sus subtipos": `?x rdfs:label "..."@en . ?c meshv:broaderDescriptor* ?x`.
   - Valores de ClinicalTrials.gov tal cual (`"TERMINATED"`, `"PHASE3"`).
   - Si tiene parámetro, usá `VALUES` con un comentario.
4. **Si falta un término**, agregalo a `ontology/rastro.ttl` con `rdfs:label` en español y un comentario corto. Preferí un atributo simple a una clase nueva.
5. **Validá:** `docker compose run --rm ontology-check` tiene que dar OK para todas las queries.
6. Si la pregunta es de Rastro Lab, usá solo datos anteriores al inicio del ensayo.
