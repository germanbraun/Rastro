-- Fármacos de cada ensayo → familia de ChEMBL (molécula padre).
--
-- Reglas, en orden, todas por nombre normalizado:
--   1. el nombre de la intervención
--   2. sus alias (intervention_other_names)
--   3. cada parte de una combinación ("carboplatin + paclitaxel")
--   4. regímenes conocidos (linking/regimens.csv: FOLFOX, R-CHOP...)
-- Normalizar = minúsculas, sin lo que va entre [] o (), y sin puntuación.
-- En AACT además se saca la vía o la forma al final ("Daratumumab IV", "... tablets").
-- Se descartan nombres ambiguos (que apuntan a más de una familia) y los de
-- menos de 3 letras.

CREATE OR REPLACE FUNCTION linking.norm(name text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT trim(regexp_replace(
               regexp_replace(lower(name), '\[[^]]*\]|\([^)]*\)', ' ', 'g'),
               '[^a-z0-9]+', ' ', 'g'))
$$;

CREATE OR REPLACE FUNCTION linking.norm_aact(name text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT trim(regexp_replace(linking.norm(name),
        '( (iv|sc|po|oral|intravenous|subcutaneous|injection|infusion|tablets?|capsules?))+$', ''))
$$;

-- Nombres de ChEMBL sin ambigüedad
DROP TABLE IF EXISTS linking.drug_name;
CREATE TABLE linking.drug_name AS
WITH names AS (
    SELECT linking.norm(s.synonyms) AS name, m.parent_chembl_id AS family
    FROM chembl.molecule_synonyms s JOIN chembl.molecule_dictionary m USING (chembl_id)
    UNION
    SELECT linking.norm(pref_name), parent_chembl_id
    FROM chembl.molecule_dictionary WHERE pref_name IS NOT NULL
)
SELECT name, min(family) AS family
FROM names
WHERE length(name) >= 3
GROUP BY name
HAVING count(DISTINCT family) = 1;
CREATE INDEX ON linking.drug_name (name);

-- Intervenciones de tipo fármaco o biológico
DROP TABLE IF EXISTS linking.intervention;
CREATE TABLE linking.intervention AS
SELECT id, nct_id, name, linking.norm_aact(name) AS norm
FROM aact.interventions
WHERE intervention_type IN ('DRUG', 'BIOLOGICAL');
CREATE INDEX ON linking.intervention (norm);

-- Todos los enlaces por intervención (sirve para medir y para revisar a mano)
DROP TABLE IF EXISTS linking.intervention_drug;
CREATE TABLE linking.intervention_drug AS
-- 1. nombre
SELECT i.id, i.nct_id, d.family, i.name AS matched, 'nombre' AS rule
FROM linking.intervention i JOIN linking.drug_name d ON d.name = i.norm
UNION ALL
-- 2. alias
SELECT i.id, i.nct_id, d.family, o.name, 'alias'
FROM linking.intervention i
JOIN aact.intervention_other_names o ON o.intervention_id = i.id
JOIN linking.drug_name d ON d.name = linking.norm_aact(o.name)
UNION ALL
-- 3. partes de una combinación
SELECT i.id, i.nct_id, d.family, part, 'combinación'
FROM linking.intervention i
CROSS JOIN LATERAL regexp_split_to_table(
    regexp_replace(lower(i.name), '\[[^]]*\]|\([^)]*\)', ' ', 'g'), '\s*(\+|/|,| and | plus | with )\s*') AS part
JOIN linking.drug_name d ON d.name = linking.norm_aact(part)
WHERE i.name ~* '\+|/|,| and | plus | with '
UNION ALL
-- 4. regímenes conocidos
SELECT i.id, i.nct_id, d.family, i.name, 'régimen'
FROM linking.intervention i
JOIN linking.regimen r ON i.norm = r.regimen OR i.norm LIKE r.regimen || ' %'
JOIN linking.drug_name d ON d.name = r.drug;
CREATE INDEX ON linking.intervention_drug (id);

-- Un fármaco por ensayo, con la regla más directa que lo encontró
DROP TABLE IF EXISTS linking.trial_drug;
CREATE TABLE linking.trial_drug AS
SELECT DISTINCT ON (nct_id, family) nct_id, family AS parent_chembl_id, matched, rule
FROM linking.intervention_drug
ORDER BY nct_id, family, array_position(ARRAY['nombre', 'alias', 'combinación', 'régimen'], rule);

CREATE INDEX ON linking.trial_drug (nct_id);
CREATE INDEX ON linking.trial_drug (parent_chembl_id);
