-- Condición de cada ensayo → descriptor de MeSH.
-- AACT trae el término MeSH como texto (browse_conditions, tipo mesh-list); se
-- enlaza con el descriptor que tiene exactamente esa etiqueta.
DROP TABLE IF EXISTS linking.trial_condition;
CREATE TABLE linking.trial_condition AS
SELECT DISTINCT b.nct_id, d.id AS mesh_id
FROM aact.browse_conditions b
JOIN mesh.descriptor d ON lower(d.label) = b.downcase_mesh_term
WHERE b.mesh_type = 'mesh-list';

CREATE INDEX ON linking.trial_condition (nct_id);
CREATE INDEX ON linking.trial_condition (mesh_id);
