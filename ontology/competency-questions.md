# Preguntas de competencia

> **Borrador para revisar** (2026-10-16). La ontología crece solo lo necesario para responder estas preguntas. Cada una tiene su SPARQL en [`queries/`](queries/).

Criterios para elegirlas:

- **Cruzan fuentes.** Cada pregunta necesita al menos dos de AACT, ChEMBL, openFDA y MeSH. Las que se responden con una sola tabla no muestran el valor de la capa.
- **Las haría alguien de negocio.** Desarrollo clínico, inteligencia competitiva, farmacovigilancia o portfolio, no un ingeniero de datos.
- **Responden con lo que ya cargamos.** Nada que dependa de `facilities`, `outcomes` o datos que no están en el recorte.
- **Alimentan los dos productos.** Las marcadas *Lab* son la base de features de la Fase 6.

| ID | Pregunta | Fuentes | Producto |
|---|---|---|---|
| CQ01 | ¿Qué fármacos con target HER2 (ERBB2) están en ensayos de fase 3 para cáncer de mama, y quién los patrocina? | AACT, ChEMBL | Layer |
| CQ02 | Para un target dado (por ejemplo EGFR), ¿cuántos ensayos hay por fase y por estado? | AACT, ChEMBL | Layer |
| CQ03 | ¿Qué sponsors de la industria tienen más ensayos terminados o retirados en cáncer de pulmón, y qué motivos declaran? | AACT, MeSH | Layer |
| CQ04 | ¿Qué condiciones, agrupadas por la jerarquía de MeSH, concentran más ensayos con inhibidores de PD-1 o PD-L1? | AACT, ChEMBL, MeSH | Layer, Lab |
| CQ05 | ¿Cuáles son los eventos adversos más reportados para los fármacos que se están probando en ensayos de leucemia? | AACT, ChEMBL, openFDA, MeSH | Layer |
| CQ06 | ¿Qué fármacos comparten al menos un target con imatinib y en cuántos ensayos aparece cada uno? | AACT, ChEMBL | Layer |
| CQ07 | ¿Qué fármacos ya aprobados (fase máxima 4) se están probando en ensayos para tipos de cáncer en los que ChEMBL no les registra ninguna indicación? | AACT, ChEMBL, MeSH | Layer |
| CQ08 | ¿Qué targets tienen fármacos en ensayos activos pero ningún fármaco aprobado? | AACT, ChEMBL | Layer |
| CQ09 | Para un ensayo dado, ¿cuántos reportes de eventos adversos (totales, serios y con muerte) acumulaban sus fármacos antes del año de inicio del ensayo? | AACT, ChEMBL, openFDA | Lab |
| CQ10 | Para un sponsor, ¿qué proporción de sus ensayos de fase 2 cerrados terminaron antes de tiempo, por gran área de MeSH? | AACT, MeSH | Lab |
| CQ11 | ¿Qué ensayos de cáncer colorrectal combinan dos o más fármacos con mecanismos de acción distintos? | AACT, ChEMBL, MeSH | Layer, Lab |
| CQ12 | ¿Cuántos targets distintos tiene cada fármaco de un ensayo, y cuántos de esos targets ya tenían un fármaco aprobado al inicio del ensayo? | AACT, ChEMBL | Lab |
| CQ13 | ¿De qué fuente y de qué carga viene cada dato de una respuesta? | Las cuatro + `rastro_meta` | Layer |

## Notas por pregunta

**CQ01** es la pregunta de la demo: corta, con un target conocido y una respuesta que un comercial puede verificar a ojo (trastuzumab, pertuzumab, T-DXd, tucatinib…). Necesita el enlace intervención de AACT → fármaco de ChEMBL, que es el corazón de la Fase 2.

**CQ02** es la versión agregada de CQ01. Sirve para el modo comparación contra SQL directo: el SQL sobre los esquemas crudos necesita saber que el target está en `target_components.gene_symbol`, que el fármaco se enlaza por sinónimos y que el estado está en `overall_status`.

**CQ03** usa la jerarquía de MeSH: "cáncer de pulmón" debe incluir *Carcinoma, Non-Small-Cell Lung* y *Small Cell Lung Carcinoma*, que en AACT son términos distintos. `why_stopped` es texto libre y se muestra tal cual.

**CQ04** generaliza condiciones por MeSH (por ejemplo, agrupar al nivel de *Lung Neoplasms*). Es el mismo cálculo que una feature semántica de la Fase 6.

**CQ05** cruza las cuatro fuentes. La respuesta debe aclarar que FAERS son reportes espontáneos, sin denominador y con duplicados, y que el fármaco puede no ser el sospechoso del reporte.

**CQ06** recorre fármaco → target → fármaco. Es la típica pregunta de grafo que en SQL exige un self-join poco obvio.

**CQ07** es reposicionamiento: compara las indicaciones de ChEMBL con las condiciones de los ensayos usando la jerarquía de MeSH, para no contar como nueva una indicación que solo es más específica.

**CQ08** detecta espacios en blanco competitivos. La fase máxima viene de ChEMBL y el estado activo de AACT.

**CQ09** es la feature de eventos adversos de Rastro Lab, con la regla de no usar datos posteriores al inicio del ensayo. La granularidad es el año, porque openFDA se agrega por año de recepción.

**CQ10** es la base del historial del sponsor como feature. "Cerrados" son los estados COMPLETED, TERMINATED y WITHDRAWN.

**CQ11** usa el mecanismo de acción de ChEMBL para decidir que dos fármacos son distintos de verdad, y no dos sales de la misma molécula.

**CQ12** combina la cantidad de targets con la novedad del target. "Aprobado al inicio" usa el `first_approval` de ChEMBL contra el año de inicio del ensayo.

**CQ13** no es de negocio, pero es la promesa de Rastro: cada celda de una respuesta debe poder decir de qué fuente y de qué carga viene. Se responde con `rastro:DataSource` y el registro de cargas.

## Supuestos que dependen de la Fase 2

- **Intervención → fármaco.** AACT nombra las intervenciones en texto libre (`interventions.name`, `intervention_other_names`) y como términos MeSH (`browse_interventions`). Las queries asumen el enlace `rastro:mentionsDrug`, que se construye en la Fase 2 por identificadores y sinónimos.
- **Condición → descriptor MeSH.** `browse_conditions` trae el término MeSH como texto, sin el identificador. El enlace a la IRI del descriptor se resuelve por etiqueta exacta, con el conector Lucene como apoyo.
- **Federación.** Las queries se escriben como si todo estuviera en un solo grafo. En la práctica, AACT, ChEMBL y openFDA vienen de Ontop y MeSH de GraphDB. Decidir en la Fase 2 entre `SERVICE` o materializar la parte de MeSH que se usa (el árbol C04 y las etiquetas).
