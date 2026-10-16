-- Una fila por entidad de Rastro, para que los mapeos lean tablas simples
-- (Ontop no se lleva bien con GROUP BY ni DISTINCT dentro de un mapeo).

-- Fármaco = molécula padre; aprobado si lo está cualquiera de sus sales
DROP TABLE IF EXISTS linking.drug;
CREATE TABLE linking.drug AS
SELECT p.chembl_id, p.pref_name, bool_or(m.max_phase >= 4) AS approved
FROM chembl.molecule_dictionary p
JOIN chembl.molecule_dictionary m ON m.parent_chembl_id = p.chembl_id
WHERE p.chembl_id = p.parent_chembl_id
GROUP BY p.chembl_id, p.pref_name;
ALTER TABLE linking.drug ADD PRIMARY KEY (chembl_id);

-- Fármaco → target, a nivel de molécula padre. Una prodroga actúa sobre los targets de
-- su molécula activa: el acetato de abiraterona, sobre los de la abiraterona.
DROP TABLE IF EXISTS linking.drug_target;
CREATE TABLE linking.drug_target AS
SELECT DISTINCT parent_chembl_id, target_chembl_id
FROM chembl.drug_mechanism WHERE target_chembl_id IS NOT NULL
UNION
SELECT DISTINCT m.parent_chembl_id, dm.target_chembl_id
FROM chembl.molecule_dictionary m
JOIN chembl.molecule_dictionary a ON a.chembl_id = m.active_chembl_id
JOIN chembl.drug_mechanism dm ON dm.parent_chembl_id = a.parent_chembl_id
WHERE m.active_chembl_id <> m.chembl_id AND dm.target_chembl_id IS NOT NULL;

-- Genes de cada target (un complejo o una fusión tiene varios)
DROP TABLE IF EXISTS linking.target_gene;
CREATE TABLE linking.target_gene AS
SELECT DISTINCT target_chembl_id, gene_symbol
FROM chembl.target_components WHERE gene_symbol IS NOT NULL;

-- Sponsor principal = una organización por nombre; industria si alguna vez figura así
DROP TABLE IF EXISTS linking.sponsor;
CREATE TABLE linking.sponsor AS
SELECT name, bool_or(agency_class = 'INDUSTRY') AS industry
FROM aact.sponsors WHERE lead_or_collaborator = 'lead'
GROUP BY name;
ALTER TABLE linking.sponsor ADD PRIMARY KEY (name);
