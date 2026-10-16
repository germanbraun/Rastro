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
