# Prueba de consistencia

¿El mismo LLM da la misma respuesta si la pregunta se escribe de otra forma? Diez de las 20 preguntas de la evaluación, cada una en su versión original y en 3 paráfrasis con el mismo significado (`parafrasis.yaml`), respondidas con SQL directo, con SQL sobre las tablas de enlaces de Rastro y con Rastro.

## Resultado (17 oct 2026)

| | SQL directo | SQL + enlaces | Rastro |
|---|---|---|---|
| Correctas (10 preguntas × 4 versiones) | 32 de 40 | **40 de 40** | **40 de 40** |
| Misma respuesta en las 4 versiones | 1 de 10 preguntas | **10 de 10** | **10 de 10** |
| Consultas que necesitaron reintento (de las 30 nuevas) | 3, por tiempo límite | 0 | 1, por un error de formato al pasar la consulta |

**Lo que significa:** la consistencia viene de integrar una vez. Con las mismas tablas de enlaces, el SQL es tan consistente como Rastro.

Respuestas por versión (original / paráfrasis 1 / 2 / 3; en las listas, cantidad de nombres):

```
     SQL directo                                     Rastro
q01  4/4 correctas · 13 / 13 / 10 / 13               4/4 correctas · 13 / 13 / 13 / 13
q02  0/4 correctas · 488 / 488 / 409 / 488           4/4 correctas · 438 / 438 / 438 / 438
q03  4/4 correctas · 3 / 3 / 3 / 3                   4/4 correctas · 3 / 3 / 3 / 3
q09  4/4 correctas · 973 / 973 / 961 / 973           4/4 correctas · 961 / 961 / 961 / 961
q10  4/4 correctas · 270 / 270 / 257 / 270           4/4 correctas · 269 / 269 / 269 / 269
q12  4/4 correctas · 301 / 301 / 295 / 301           4/4 correctas · 293 / 293 / 293 / 293
q13  4/4 correctas · 675 / 675 / 650 / 675           4/4 correctas · 658 / 658 / 658 / 658
q16  0/4 correctas · 545 / 550 / 532 / 547           4/4 correctas · 604 / 604 / 604 / 604
q18  4/4 correctas · 22 / 22 / 21 / 22               4/4 correctas · 22 / 22 / 22 / 22
q19  4/4 correctas · 304 / 297 / 295 / 297           4/4 correctas · 309 / 309 / 309 / 309
```

El SQL directo inventa en cada consulta cómo reconocer un fármaco en el texto del ensayo, y cada forma da otro número. Rastro y el SQL con enlaces usan siempre el mismo enlace. (La tabla de arriba muestra SQL directo y Rastro; `puntaje` muestra las tres columnas.)

## Cómo se hizo

- Las respuestas originales son las de la evaluación (`layer/eval/results.json`). Las 60 nuevas las generaron subagentes de Claude Code (Claude Opus 5.5) con el mismo prompt que la evaluación, leyendo solo el prompt y los resultados de sus consultas.
- Cada subagente respondió una paráfrasis de las 10 preguntas, así que nunca vio dos versiones de la misma pregunta. Sí pudo reusar su forma de reconocer fármacos entre preguntas distintas, lo que favorece la consistencia del SQL directo, no la de Rastro.
- El puntaje usa el mismo criterio de la evaluación (5 % para números, 80 % para listas) y la misma referencia de la pregunta original.
- Como en la evaluación, las paráfrasis y las referencias las escribió un asistente de IA; falta la revisión humana (`docs/verificacion-humana.md`).

## Repetir

```bash
docker compose run --rm -T layer-eval python /layer/consistencia/manual.py prompt q01 1 C   # el prompt
docker compose run --rm -T layer-eval python /layer/consistencia/manual.py try q01 1 C      # una consulta por stdin
docker compose run --rm -T layer-eval python /layer/consistencia/manual.py puntaje          # el resultado
```
