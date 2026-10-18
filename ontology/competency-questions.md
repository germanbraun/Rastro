# Preguntas de competencia

Las preguntas que Rastro tiene que poder responder. La ontología tiene solo lo necesario para estas diez, y cada una tiene su SPARQL en [`queries/`](queries/).

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
| 9 | ¿Cuántos ensayos de fase 3 de cáncer de mama prueban alguna terapia dirigida? | AACT, ChEMBL, MeSH | Layer |
| 10 | ¿Por qué Rastro dice que un ensayo prueba un fármaco? | AACT, ChEMBL | Layer |

## Notas

- **La 1 es la pregunta de la demo:** corta, con una respuesta que cualquiera reconoce (trastuzumab, pertuzumab…).
- **"Cáncer de mama", "cáncer de pulmón" y "leucemia" incluyen sus subtipos.** Eso lo resuelve la jerarquía de MeSH con `:within`: "cáncer de pulmón" incluye "carcinoma de pulmón de células no pequeñas" sin listarlo a mano.
- **Los targets son los directos de ChEMBL.** Por eso la 6 lista MTOR: ChEMBL registra los rapálogos aprobados (everolimus, temsirolimus) sobre FKBP1A, la proteína a la que se unen.
- **Los eventos adversos (4 y 7) son conteos de reportes espontáneos de FAERS**, no frecuencias clínicas. La interfaz lo tiene que decir.
- **La 7 y la 8 son las features de Rastro Lab:** usan solo datos anteriores al inicio de cada ensayo.
- **"Detenido" es TERMINATED o WITHDRAWN** en ClinicalTrials.gov.
- **La 9 usa una clase deducida.** «Terapia dirigida» no tiene mapeo: la ontología dice que los inhibidores de quinasa y los anticuerpos monoclonales lo son, y Ontop lo aplica.
- **La 10 es la procedencia de un enlace.** Cada `:DrugLink` guarda el texto del sponsor, lo que coincidió, la regla y de qué fuentes deriva (PROV-O).
- **Cada dato de una respuesta lleva su fuente.** No es una pregunta aparte: toda entidad apunta a la fuente de la que viene (`rastro:fromSource`).

## Cómo se responden

Todas corren contra Ontop (http://localhost:8080/sparql) y tardan alrededor de un segundo. Los resultados de la Fase 2 están en [docs/results.md](../docs/results.md).

- **Ensayo → fármaco** (`:testsDrug`) y **ensayo → condición** (`:condition`) salen de `linking/`.
- **MeSH** está copiado en Postgres, así que no hace falta federar con GraphDB.
