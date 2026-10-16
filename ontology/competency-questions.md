# Preguntas de competencia

Las preguntas que Rastro tiene que poder responder. La ontología tiene solo lo necesario para estas ocho, y cada una tiene su SPARQL en [`queries/`](queries/).

Todas cruzan al menos dos fuentes: es lo que una base sola no puede contestar.

| # | Pregunta | Fuentes | Para |
|---|---|---|---|
| 1 | ¿Qué fármacos anti-HER2 están en ensayos de fase 3 de cáncer de mama, y quién los patrocina? | AACT, ChEMBL, MeSH | Demo |
| 2 | ¿Cuántos ensayos hay por fase para fármacos que actúan sobre EGFR? | AACT, ChEMBL | Layer |
| 3 | ¿Qué empresas tienen más ensayos detenidos en cáncer de pulmón, y por qué? | AACT, MeSH | Layer |
| 4 | ¿Cuáles son los eventos adversos más reportados de los fármacos que se prueban en leucemia? | AACT, ChEMBL, openFDA, MeSH | Layer |
| 5 | ¿Qué otros fármacos actúan sobre los mismos targets que imatinib? | ChEMBL, AACT | Layer |
| 6 | ¿Qué targets tienen fármacos en ensayos activos pero ningún fármaco aprobado? | AACT, ChEMBL | Layer |
| 7 | ¿Cuántos reportes de eventos adversos tenían los fármacos de un ensayo antes de que empezara? | AACT, ChEMBL, openFDA | Lab |
| 8 | ¿Qué porcentaje de los ensayos de fase 2 de un sponsor se detuvo antes de tiempo? | AACT | Lab |

## Notas

- **La 1 es la pregunta de la demo:** corta, con una respuesta que cualquiera reconoce (trastuzumab, pertuzumab…).
- **"Cáncer de mama", "cáncer de pulmón" y "leucemia" incluyen sus subtipos.** Eso lo resuelve la jerarquía de MeSH: "cáncer de pulmón" incluye "carcinoma de pulmón de células no pequeñas" sin listarlo a mano.
- **Los eventos adversos (4 y 7) son conteos de reportes espontáneos de FAERS**, no frecuencias clínicas. La interfaz lo tiene que decir.
- **La 7 y la 8 son las features de Rastro Lab:** usan solo datos anteriores al inicio de cada ensayo.
- **"Detenido" es TERMINATED o WITHDRAWN** en ClinicalTrials.gov.
- **Cada dato de una respuesta lleva su fuente.** No es una pregunta aparte: toda entidad apunta a la fuente de la que viene (`rastro:fromSource`).

## Supuestos para la Fase 2

- **Ensayo → fármaco.** AACT nombra las intervenciones en texto libre. El enlace `rastro:testsDrug` se construye en la Fase 2: por nombre exacto o alias ya enlaza el 69 % de las intervenciones de tipo fármaco.
- **Ensayo → condición.** AACT da el término MeSH como texto; se enlaza con el descriptor de MeSH por su etiqueta.
- **Un solo grafo.** Las queries se escriben como si todo estuviera junto. Cómo se juntan Ontop (Postgres) y GraphDB (MeSH) se decide en la Fase 2.
