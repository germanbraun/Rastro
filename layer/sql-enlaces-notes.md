Además, las tablas de enlaces de Rastro, que ya resuelven los cruces entre fuentes (revisadas: 98-99 % de los enlaces son correctos):

- `linking.trial_drug`: qué fármaco prueba cada ensayo. `nct_id` → `parent_chembl_id` (la molécula padre de ChEMBL: agrupa una molécula y sus sales). Sale del texto de `aact.interventions` e `intervention_other_names`, ya resuelto; no hace falta buscar nombres en el texto.
- `linking.drug`: un fármaco por molécula padre. `chembl_id`, `pref_name` (en mayúsculas) y `approved` (verdadero si alguna de sus sales tiene `max_phase` 4).
- `linking.drug_target`: sobre qué target actúa cada fármaco (`parent_chembl_id` → `target_chembl_id`). Una prodroga actúa sobre los targets de su molécula activa.
- `linking.target_gene`: el gen de cada target (`target_chembl_id` → `gene_symbol`, por ejemplo EGFR o ERBB2).
- `linking.trial_condition`: la condición de cada ensayo como descriptor de MeSH (`nct_id` → `mesh_id`).
- `mesh.ancestor`: la jerarquía de MeSH completa, precalculada. `id` está dentro de `ancestor_id`, e incluye al propio descriptor. Para "ensayos de X" con sus subtipos: `trial_condition.mesh_id = ancestor.id` y `ancestor.ancestor_id` = el descriptor de X.
- `linking.sponsor`: `name` y `industry` (verdadero si `agency_class` es INDUSTRY). El sponsor principal de cada ensayo está en `aact.sponsors` con `lead_or_collaborator = 'lead'`.
- `linking.drug_class`: la clase de cada fármaco según la clasificación ATC (`chembl_id` → `class`): `KinaseInhibitor` (inhibidor de quinasa), `MonoclonalAntibody` (anticuerpo monoclonal), `Chemotherapy` (quimioterapia) o `HormoneTherapy` (terapia hormonal). Una **terapia dirigida** es un inhibidor de quinasa o un anticuerpo monoclonal.

