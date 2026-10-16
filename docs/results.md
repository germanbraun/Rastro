# Resultados

Los números propios de Rastro, para el one-pager de la Fase 8. Cada uno dice cómo se midió.

## Fase 2 — Conectar las fuentes (16 oct 2026)

| Qué | Resultado | Cómo se midió |
|---|---|---|
| Intervenciones de tipo fármaco o biológico enlazadas con ChEMBL | **74,4 %** (96.983 de 130.331) | `docker compose run --rm linker` |
| Enlaces de fármacos correctos | **99 de 100**, y 30 de 30 en la regla agregada después | Revisión a mano de una muestra al azar: [linking/review-2026-10-16.md](../linking/review-2026-10-16.md) |
| Ensayos con al menos un fármaco de ChEMBL | 46.863 de 106.483 | Incluye solo intervenciones de tipo fármaco o biológico |
| Ensayos con su condición en MeSH | **99,8 %** | Término MeSH de AACT igual a la etiqueta del descriptor |
| Preguntas de competencia que responden | **8 de 8**, en alrededor de un segundo cada una | Contra Ontop, sobre los datos reales |

Respuesta a la pregunta de la demo (fármacos anti-HER2 en fase 3 de cáncer de mama): trastuzumab (128 ensayos), pertuzumab (46), lapatinib (29), trastuzumab emtansina (16), trastuzumab deruxtecán (13), pirotinib (11), neratinib, tucatinib y otros.

## Fase 3 — Preguntas en lenguaje natural (16 oct 2026)

El mismo LLM (Claude Opus 5.5) respondió 20 preguntas de negocio de tres formas:

| | Correctas | Cómo |
|---|---|---|
| LLM solo | **5 de 20** | Sin datos: acierta listas de fármacos conocidos, ningún conteo |
| LLM + SQL crudo | **18 de 20** | Queries largas y frágiles (3 necesitaron un segundo intento) |
| LLM + Rastro | **20 de 20** | Todas las queries funcionaron al primer intento; cada dato con su fuente |

Para la pregunta de la demo, la query del SQL directo tiene 1.543 caracteres y la de Rastro, 435.

Cómo se midió: `layer/eval/` (preguntas, respuestas guardadas y puntaje) y `layer/eval/adjudication.md` (las diferencias revisadas con ensayos reales). La adjudicación también encontró y corrigió errores de Rastro: la cobertura de enlaces de fármacos pasó de 74 % a 81 %, con 98-99 % de precisión.

### Otros números que salieron de esta fase

| Qué | Resultado |
|---|---|
| Fármacos aprobados con reportes de eventos adversos en openFDA | **774 de 778** (antes 625: buscar solo por UNII perdía fármacos enteros) |
| Intervenciones de tipo fármaco enlazadas con ChEMBL | **80,8 %** (antes 74,4 %) |

## Fase 4 — Interfaz de Rastro Layer (16 oct 2026)

Demo en http://localhost:8501: las 20 preguntas de ejemplo funcionan sin LLM (queries guardadas, ejecutadas en vivo), con la fuente de cada columna y un "¿cómo lo supe?" con la query. La pestaña "Con y sin Rastro" muestra el puntaje y las tres respuestas de cada pregunta lado a lado.

