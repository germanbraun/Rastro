Base PostgreSQL con cuatro fuentes públicas, cargadas tal como vienen:

- `aact.*`: ClinicalTrials.gov (base AACT), estudios de oncología. Un estudio es un ensayo (`nct_id`).
  - `studies`: fase (`phase`: PHASE1, PHASE2, PHASE3, PHASE4, PHASE1/PHASE2, PHASE2/PHASE3, EARLY_PHASE1, NA) y estado (`overall_status`: RECRUITING, COMPLETED, TERMINATED, WITHDRAWN, ACTIVE_NOT_RECRUITING, NOT_YET_RECRUITING, ENROLLING_BY_INVITATION, SUSPENDED, UNKNOWN).
  - `browse_conditions`: condiciones del ensayo como términos MeSH; `mesh_type` es `mesh-list` (el término) o `mesh-ancestor` (sus ancestros en MeSH). `downcase_mesh_term` está en minúsculas.
  - `interventions` e `intervention_other_names`: lo que prueba el ensayo, en texto libre como lo escribió el sponsor.
  - `sponsors`: `lead_or_collaborator` (`lead` es el principal) y `agency_class` (INDUSTRY, NIH, OTHER...).
- `chembl.*`: ChEMBL 37, fármacos con indicaciones en oncología. `molecule_dictionary.pref_name` está en mayúsculas; `parent_chembl_id` agrupa una molécula con sus sales; `max_phase` 4 es aprobado. Los targets de cada fármaco están en `drug_mechanism` → `target_dictionary` → `target_components` (`gene_symbol`).
- `openfda.*`: eventos adversos de FAERS, agregados por fármaco. `query_id` es el `parent_chembl_id` de ChEMBL del fármaco consultado. `reports_by_year` tiene reportes por año de recepción (totales, serios y con muerte); `reactions`, las 100 reacciones más reportadas.
- `mesh.descriptor` y `mesh.broader`: descriptores de MeSH (etiqueta en inglés) y su jerarquía directa.
