# Integración en Rastro: qué heterogeneidad hay y cómo se resuelve

Rastro es un **Virtual Knowledge Graph (VKG)**: una ontología con el vocabulario del dominio, mapeos R2RML que la conectan con las fuentes y un grafo virtual que Ontop traduce a SQL. La clasificación de heterogeneidad sigue el tutorial *Designing Virtual Knowledge Graphs with Ontop and Ontopic Studio* (Calvanese, Cogrel y Lanti, Ontobras 2022).

## Los cuatro tipos de heterogeneidad

| Tipo | Qué es | En Rastro | Lo resuelve |
|---|---|---|---|
| **De modelo de datos** | Las fuentes usan modelos distintos | AACT y ChEMBL son tablas, openFDA es JSON, MeSH es RDF | Los cargadores (`data/`) |
| **De sistema** | Se accede a cada fuente de forma distinta | AACT en un Postgres en la nube, ChEMBL y openFDA por API, MeSH como archivo | Un cargador por fuente |
| **De esquema** | El mismo concepto se nombra, organiza o detalla distinto | Ver la lista de abajo | **Ontología y mapeos** (`ontology/`, `mappings/`) |
| **De datos** | La misma entidad se escribe distinto en los valores | «Pembrolizumab 200 mg», «MK-3475» y «Keytruda» son un mismo fármaco | **Entity linking** (`linking/`) |

## Heterogeneidad de esquema en este MVP

Los casos concretos que aparecen en las cuatro fuentes y cómo los resuelve cada mapeo de `mappings/rastro.r2rml.ttl`.

### 1. El mismo identificador, con nombres distintos

| Concepto | Columnas que lo forman | En Rastro |
|---|---|---|
| Fármaco | `chembl.molecule_dictionary.chembl_id`, `openfda.reports_by_year.query_id`, `openfda.reactions.query_id`, `linking.trial_drug.parent_chembl_id` | Un solo `:Drug`, con IRI `drug/{id}` |
| Ensayo | `nct_id` en `aact.studies`, `aact.sponsors` y las tablas de enlaces | Un solo `:Trial`, con IRI `trial/{nct_id}` |
| Target | `chembl.target_dictionary.chembl_id`, `chembl.drug_mechanism.target_chembl_id` | Un solo `:Target` |
| Condición | `mesh.descriptor.id` en Postgres y el mismo descriptor en GraphDB | La IRI de MeSH (`http://id.nlm.nih.gov/mesh/2026/{id}`) |

### 2. El mismo atributo, con nombres distintos

| Atributo | Columnas |
|---|---|
| `:name` | `pref_name` (fármacos y targets de ChEMBL), `name` (sponsors de AACT y fuentes) |
| `:reports` | `reports` en dos tablas de openFDA: por año y por reacción |

### 3. La misma relación, organizada distinto

| Relación | En las fuentes | En Rastro |
|---|---|---|
| Fármaco actúa sobre un gen | Tres tablas de ChEMBL: `drug_mechanism` → `target_dictionary` → `target_components.gene_symbol` | `?fármaco :hasTarget/:gene "EGFR"` |
| Ensayo tiene un sponsor | Una tabla aparte con filas principal y colaborador (`lead_or_collaborator`) | `:sponsor`, solo el principal |
| Una condición y sus subtipos | AACT repite los ancestros en `browse_conditions` (`mesh-ancestor`); MeSH los tiene como jerarquía (`broaderDescriptor`) | `:within`, precalculado en `mesh.ancestor` |

### 4. Distinto nivel de detalle

| Caso | Diferencia | En Rastro |
|---|---|---|
| Molécula y sus sales | ChEMBL registra imatinib y mesilato de imatinib por separado | Un solo fármaco: la molécula padre (`linking/entities.sql`) |
| Prodroga | El acetato de abiraterona es otra entrada, con otros mecanismos | Actúa sobre los targets de su molécula activa |
| Eventos adversos | openFDA tiene reportes individuales | Conteos por año y por reacción (`:YearlyReports`, `:ReportedReaction`) |

### 5. Valores codificados de forma distinta

| Atributo | En la fuente | En Rastro |
|---|---|---|
| Aprobado | `max_phase = 4` en cualquiera de las sales | `:approved true` |
| Industria | `agency_class = 'INDUSTRY'` | `:industry true` |
| Fase y estado | Texto de ClinicalTrials.gov (`PHASE1/PHASE2`, `TERMINATED`) | Igual, documentado en la ontología |

### 6. Distinta cobertura

Las fuentes no cubren lo mismo, y conviene decirlo en la demo:

- AACT: todos los ensayos de oncología (106.483).
- ChEMBL: solo las familias de fármacos con alguna indicación oncológica (3.739).
- openFDA: solo los fármacos con UNII, y casi solo los aprobados tienen reportes.
- MeSH: completo.

Por eso un fármaco puede estar en un ensayo y no tener eventos adversos: no es un error, es la cobertura de la fuente.

## Si Ontop y los mapeos resuelven los cruces, ¿para qué la tabla de enlaces?

Porque **los mapeos resuelven la heterogeneidad de esquema, no la de datos**.

Un mapeo dice qué columna existente es qué concepto. Ontop une dos tablas cuando comparten un **valor igual**: `aact.studies.nct_id` y `aact.sponsors.nct_id` tienen el mismo «NCT02252172», y el `query_id` de openFDA tiene el mismo «CHEMBL941» que el `chembl_id` de ChEMBL. Ahí la unión es automática.

Entre AACT y ChEMBL **no hay un valor en común**. AACT tiene el texto «Pembrolizumab 200 mg» y ChEMBL tiene `CHEMBL3137343`. Ningún `=` de SQL los une, y ningún mapeo puede inventar esa igualdad. Hace falta algo que **produzca** la clave: el entity linking.

```
AACT: «Pembrolizumab 200 mg» ──(entity linking, una vez)──► linking.trial_drug: NCT… → CHEMBL3137343
                                                                   │
                                          mapeo: trial/{nct_id} :testsDrug drug/{parent_chembl_id}
                                                                   │
                                          Ontop: unión por igualdad, automática
```

**¿Se podría poner el entity linking dentro del mapeo?** Técnicamente sí: un mapeo R2RML puede tener cualquier consulta SQL. Pero Ontop la ejecutaría **en cada pregunta**, comparando texto contra 130.000 intervenciones. Eso es justamente lo que hizo lento y frágil al SQL directo en la evaluación. Y el resultado dejaría de ser una foto fija revisada (98-99 % de precisión en una muestra). Por eso Rastro lo calcula una vez y el mapeo lee el resultado: es un **VKG pragmático**.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Vocabulario (conceptos y relaciones) | `ontology/rastro.ttl` |
| Mapeos de columnas a conceptos | `mappings/rastro.r2rml.ttl` |
| Entity linking y entidades | `linking/` (`drugs.sql`, `conditions.sql`, `entities.sql`) |
| Revisión de los enlaces | `linking/review-2026-10-16.md` |
| Cargadores de cada fuente | `data/` |
