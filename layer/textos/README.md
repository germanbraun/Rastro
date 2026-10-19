# Preguntas sobre textos

El grafo elige los registros con una consulta exacta y un asistente de IA resume solo sus textos, citando cada registro. Es GraphRAG anclado en la capa semántica: los números y la selección son exactos y auditables; el resumen es del LLM, y se puede comprobar contra los textos.

| Archivo | Qué es |
|---|---|
| `detenidos-pulmon.rq` | La consulta que elige los ensayos: fase 3, detenidos, cáncer de pulmón y sus subtipos, inhibidores de quinasa, con motivo escrito (26) |
| `detenidos-pulmon.json` | El resumen: 7 motivos, cada uno con sus ensayos. Lo hizo un asistente de IA (Claude) leyendo los 26 textos, el 19 oct 2026 |

Además, el motivo de los 12.611 ensayos detenidos con texto pasó a ser un dato del grafo (`:stopReason`), clasificado con reglas legibles (`linking/stop_reasons.sql`) y con su evidencia en PROV-O (`:StopReasonLink`). La pregunta de competencia 11 los cuenta con una consulta exacta. Precisión en una muestra revisada: 92 % (`linking/review-stop-reasons-2026-10-19.md`).

La app lo muestra en «Una pregunta sobre textos» (dominio de oncología): el resumen de la IA y, debajo, el conteo exacto. Los textos se leen en vivo; si cambian los datos, el resumen hay que volver a generarlo.
