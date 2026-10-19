# Evaluación del dominio de proveedores

El mismo método que oncología (`layer/eval`, `layer/consistencia`, `layer/cambio`), con las 9 preguntas del dominio y dos formas de responder: **sin Rastro** (el LLM escribe SQL sobre las tablas de las fuentes tal como se cargaron) y **con Rastro** (escribe SPARQL sobre el segundo Ontop).

## Resultado (19 oct 2026, con las correcciones de los enlaces)

| | Sin Rastro (SQL) | Con Rastro |
|---|---|---|
| Correctas (de 9) | 4 | **8** |
| Misma respuesta en las 4 formas (de 5 preguntas) | 3 | **4** |
| Si una columna cambia de nombre | 3 consultas rotas, a buscar y reescribir | todo falla junto, se arregla con **1 línea** |
| Si los montos pasan a miles de dólares | 3 respuestas distintas, sin aviso | 3 distintas, **con aviso**; se arregla con **1 línea** |

- **Lo que muestra:** sin Rastro fallan las preguntas que unen USAspending con GLEIF (p04, p07, p09), porque cada consulta inventa el enlace sin verificarlo; en una de las formas, el SQL le sumó a Leidos los contratos de SAIC. Con Rastro, el enlace está hecho una vez y con reglas.
- **Lo que no:** Rastro también falló una (p05: el diccionario no decía que algunas listas dejan vacío el tipo de entrada) y su respuesta de p01 cambió en una de las 4 formas. La primera revisión encontró que la referencia se quedaba corta en p01 y p04 (filiales de Leidos y matrices extranjeras que el enlace no encontraba); se corrigió con búsquedas más en GLEIF, dos LEI revisados y una tabla corta de correcciones, y las consultas guardadas se volvieron a ejecutar sobre los datos nuevos, sin pedirle nada nuevo al LLM. Todo está en [adjudicacion.md](adjudicacion.md).

Detalle por pregunta: [resultados.md](resultados.md). La app lee `resultados.json` y `cambio/resultado.json`.

## Cómo se hizo

- Las respuestas las escribieron subagentes de Claude Code (Claude Opus 5.5), cada uno con una sola forma de las preguntas y un solo enfoque, viendo solo el prompt y el resultado de sus consultas. Hasta 3 intentos por pregunta, como en oncología. Uno de los subagentes, una vez, comparó dos prompts con `diff` en su carpeta temporal; no vio otra cosa que los prompts.
- Las referencias son SPARQL sobre Rastro (`eval/questions.yaml`) y las escribió un asistente de IA. Como pueden favorecer a Rastro, las diferencias se revisaron con los datos (`adjudicacion.md`). Falta que una persona las confirme.
- Correcto: números a menos del 5 % de la referencia; listas con al menos 80 % de coincidencia (F1), comparando las empresas por nombre normalizado.
- Sin Rastro ve `usaspending`, `naics.sector`, `csl`, `gleif` y `wikidata` (usuario `proveedores_reader`, `reader.sql`), sin el esquema `proveedores` que arma Rastro ni `naics.ancestor`.

## Repetir

```bash
docker compose run --rm -T layer-eval python /layer/proveedores/evaluar.py prompt p01 0 C   # el prompt (0 = la pregunta; 1-3 = otras formas)
docker compose run --rm -T layer-eval python /layer/proveedores/evaluar.py try p01 0 C      # una consulta por stdin
docker compose run --rm -T layer-eval python /layer/proveedores/evaluar.py puntaje          # puntúa y escribe resultados.json y .md
layer/proveedores/cambio/cambio.sh registrar                                                # la prueba de cambio (deja todo como estaba)
```
