-- Fármacos de cada ensayo → familia de ChEMBL (molécula padre).
--
-- Reglas, en orden, todas por nombre normalizado:
--   1. el nombre de la intervención
--   2. sus alias (intervention_other_names)
--   3. cada parte de una combinación ("carboplatin + paclitaxel")
--   4. regímenes conocidos (linking/regimens.csv: FOLFOX, R-CHOP...)
--   5. un nombre de ChEMBL como palabra entera dentro del nombre de la intervención,
--      ganando el nombre más largo
--      ("Pembrolizumab 200 mg", "lenvatinib pembrolizumab", "Nivolumab or pembrolizumab");
--      solo nombres de 5 letras o más y que no sean palabras genéricas
--      (linking/generic_words.csv: "albumin" en "albumin-bound paclitaxel", "chloride"...)
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

-- Nombres de ChEMBL sin ambigüedad. Si un nombre es el nombre preferido de una
-- familia, esa familia gana aunque otra lo tenga como sinónimo (ChEMBL lista, por
-- error, "bicalutamide" entre los sinónimos de talazoparib).
DROP TABLE IF EXISTS linking.drug_name;
CREATE TABLE linking.drug_name AS
WITH names AS (
    SELECT linking.norm(s.synonyms) AS name, m.parent_chembl_id AS family, false AS preferred
    FROM chembl.molecule_synonyms s JOIN chembl.molecule_dictionary m USING (chembl_id)
    UNION
    SELECT linking.norm(pref_name), parent_chembl_id, true
    FROM chembl.molecule_dictionary WHERE pref_name IS NOT NULL
),
per_name AS (
    SELECT name,
           count(DISTINCT family) FILTER (WHERE preferred) AS preferred_families,
           count(DISTINCT family) AS families
    FROM names WHERE length(name) >= 3
    GROUP BY name
)
SELECT DISTINCT n.name, n.family
FROM names n JOIN per_name p USING (name)
WHERE (p.preferred_families = 1 AND n.preferred)
   OR (p.preferred_families = 0 AND p.families = 1);
CREATE INDEX ON linking.drug_name (name);

-- Intervenciones de tipo fármaco o biológico
DROP TABLE IF EXISTS linking.intervention;
CREATE TABLE linking.intervention AS
SELECT id, nct_id, name, linking.norm_aact(name) AS norm
FROM aact.interventions
WHERE intervention_type IN ('DRUG', 'BIOLOGICAL', 'COMBINATION_PRODUCT');
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

-- 5. Nombre de ChEMBL como palabra entera (secuencias de 1 a 4 palabras del nombre
--    de la intervención). Si un nombre está dentro de otro que también coincide, gana
--    el más largo ("trastuzumab emtansine", no "trastuzumab").
INSERT INTO linking.intervention_drug
WITH phrases AS (
    SELECT t.id, t.nct_id, array_to_string(w.words[i:i + n - 1], ' ') AS phrase
    FROM (SELECT id, nct_id, linking.norm(name) AS text FROM linking.intervention) t
    CROSS JOIN LATERAL (SELECT string_to_array(t.text, ' ') AS words) w
    CROSS JOIN LATERAL generate_series(1, 4) AS n
    CROSS JOIN LATERAL generate_series(1, greatest(cardinality(w.words) - n + 1, 0)) AS i
),
matches AS (
    SELECT p.id, p.nct_id, p.phrase, d.family
    FROM phrases p
    JOIN linking.drug_name d ON d.name = p.phrase AND length(d.name) >= 5
    WHERE p.phrase NOT IN (SELECT word FROM linking.generic_word)
)
SELECT m.id, m.nct_id, m.family, m.phrase, 'palabras'
FROM matches m
WHERE NOT EXISTS (
    SELECT 1 FROM matches longer
    WHERE longer.id = m.id AND longer.phrase <> m.phrase
      AND (' ' || longer.phrase || ' ') LIKE ('% ' || m.phrase || ' %')
);

-- Un fármaco por ensayo, con la regla más directa que lo encontró
DROP TABLE IF EXISTS linking.trial_drug;
CREATE TABLE linking.trial_drug AS
SELECT DISTINCT ON (nct_id, family) nct_id, family AS parent_chembl_id, matched, rule
FROM linking.intervention_drug
ORDER BY nct_id, family, array_position(ARRAY['nombre', 'alias', 'combinación', 'régimen', 'palabras'], rule);

CREATE INDEX ON linking.trial_drug (nct_id);
CREATE INDEX ON linking.trial_drug (parent_chembl_id);
