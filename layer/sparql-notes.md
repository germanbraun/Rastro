Endpoint SPARQL de Rastro (Ontop) sobre cuatro fuentes públicas integradas: ensayos de oncología de ClinicalTrials.gov, fármacos y targets de ChEMBL 37, eventos adversos de FAERS (openFDA) y MeSH.

- Prefijos: `PREFIX oncologia: <https://w3id.org/rastro/oncologia#>` y `PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>`.
- Fase (`oncologia:phase`) y estado (`oncologia:status`) tienen los valores de ClinicalTrials.gov: PHASE1, PHASE2, PHASE3, PHASE4, PHASE1/PHASE2, PHASE2/PHASE3, EARLY_PHASE1, NA; RECRUITING, COMPLETED, TERMINATED, WITHDRAWN, ACTIVE_NOT_RECRUITING, NOT_YET_RECRUITING, ENROLLING_BY_INVITATION, SUSPENDED, UNKNOWN.
- Los nombres de fármacos (`oncologia:name`) están en mayúsculas, como en ChEMBL. Un fármaco agrupa una molécula y sus sales.
- Las condiciones son descriptores de MeSH con `rdfs:label` en inglés (`"Breast Neoplasms"@en`).
- El endpoint no soporta caminos de largo arbitrario (`*`, `+`).
