# Resultados

> **Pendiente:** las preguntas de evaluación, sus respuestas de referencia, la adjudicación y la revisión de enlaces las hizo un asistente de IA (Claude Code). Los números salen de ejecutar queries sobre los datos y de un puntaje automático, pero falta que una persona confirme las referencias: [verificacion-humana.md](verificacion-humana.md).

Los números propios de Rastro, para el one-pager de la Fase 8. Cada uno dice cómo se midió.

## Fase 2 — Conectar las fuentes (16 oct 2026)

| Qué | Resultado | Cómo se midió |
|---|---|---|
| Intervenciones de tipo fármaco o biológico enlazadas con ChEMBL | **74,4 %** (96.983 de 130.331) | `docker compose run --rm linker` |
| Enlaces de fármacos correctos | **99 de 100**, y 30 de 30 en la regla agregada después | Revisión uno por uno de una muestra al azar, hecha por un asistente de IA (falta revisión humana): [linking/review-2026-10-16.md](../linking/review-2026-10-16.md) |
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

**Interpretación:** la ventaja de Rastro no es cuántas acierta, sino cuánto se puede confiar en cada respuesta. El SQL directo tuvo que inventar cómo reconocer un fármaco en 16 de las 20 preguntas, y lo hizo de 4 formas distintas. Sus errores parecen razonables (488 en vez de 438). Sus queries tardan 20 s en total contra 2 s de Rastro, y 3 necesitaron reintento. Rastro, además, dice de dónde sale cada dato. Detalle en `layer/eval/adjudication.md`.

Cómo se midió: `layer/eval/` (preguntas, respuestas guardadas y puntaje) y `layer/eval/adjudication.md` (las diferencias revisadas con ensayos reales). La adjudicación también encontró y corrigió errores de Rastro: la cobertura de enlaces de fármacos pasó de 74 % a 81 %, con 98-99 % de precisión.

### Otros números que salieron de esta fase

| Qué | Resultado |
|---|---|
| Fármacos aprobados con reportes de eventos adversos en openFDA | **774 de 778** (antes 625: buscar solo por UNII perdía fármacos enteros) |
| Intervenciones de tipo fármaco enlazadas con ChEMBL | **80,8 %** (antes 74,4 %) |

## Fase 4 — Interfaz de Rastro Layer (16 oct 2026)

Demo en http://localhost:8501:

- **Preguntar:** las 20 preguntas de ejemplo funcionan sin LLM (queries guardadas, ejecutadas en vivo). Muestra la fuente de cada columna y dónde vive cada fuente (🐘 Postgres, 🕸️ GraphDB). "¿Cómo lo supe?" tiene tres pasos: la consulta que escribió el LLM, el SQL que Ontop generó y ejecutó, y las fuentes con su licencia.
- **Con y sin Rastro:** el puntaje y qué significa, y cada pregunta con las tres respuestas lado a lado. Para cada respuesta incorrecta explica por qué falló; para cada query del SQL directo, cómo reconoció los fármacos; y para Rastro, el SQL que generó Ontop, para compararlo con el escrito a mano.

## Consistencia y cambio (17 oct 2026)

| Qué | SQL directo | Rastro | Cómo se midió |
|---|---|---|---|
| La misma pregunta escrita de 4 formas da la misma respuesta | 1 de 10 preguntas | **10 de 10** | [layer/consistencia/](../layer/consistencia/README.md) |
| Correctas en esas 40 versiones | 32 de 40 | **40 de 40** | Mismo criterio que la evaluación |
| Una columna cambia de nombre | 5 consultas fallan | **1 línea del mapeo** | [demo-cambio.md](demo-cambio.md) |
| Un valor cambia de formato | 5 respuestas pasan a 0 sin aviso | el control de vocabulario avisa; **1 línea** | [demo-cambio.md](demo-cambio.md) |
| Largo promedio de la consulta del LLM | 726 caracteres | **368** (el SQL de Ontop: 633) | Las 20 consultas guardadas |

## La línea de base justa: SQL con las tablas de enlaces (17 oct 2026)

Para separar lo que aporta la integración de lo que aporta la capa semántica, el mismo LLM respondió con SQL sobre las fuentes **más las tablas de enlaces de Rastro**, documentadas (`layer/sql-enlaces-notes.md`).

| Qué | SQL directo | SQL + enlaces | Rastro |
|---|---|---|---|
| Correctas, de 20 | 18 | **20** | **20** |
| Misma respuesta, preguntando de 4 formas | 1 de 10 | **10 de 10** | **10 de 10** |
| Preguntas de 3 o 4 cruces (layer/composicion/) | — | **5 de 5** | **5 de 5** |
| Largo promedio de la consulta del LLM | 726 | 348 | 368 |
| Tiempo de las 20 consultas | 28 s | 1,9 s | 2,6 s |
| Una columna de la fuente cambia de nombre | 5 rotas | 5 rotas | **1 línea del mapeo** |
| Un valor cambia de formato | 5 en 0, sin aviso | 4 en 0 y 1 error, sin aviso | **avisa; 1 línea** |
| De dónde sale cada dato | no | no | **por columna** |
| Une datos de Wikidata en la misma consulta (layer/externo/) | no | no | **sí** |

**Interpretación:** la precisión, la consistencia, el largo de la consulta y la velocidad vienen de **integrar una vez**. Con esas tablas, el SQL es tan bueno como Rastro. La capa semántica aporta que esa integración se mantiene en un solo lugar (los mapeos), trae la procedencia de cada dato y se conecta con datos de otras organizaciones con estándares abiertos. Una capa de vistas SQL resolvería parte de lo primero, no lo último.

