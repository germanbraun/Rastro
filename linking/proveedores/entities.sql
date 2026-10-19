-- Una fila por entidad del dominio de proveedores, para que los mapeos lean tablas
-- simples (Ontop no se lleva bien con GROUP BY ni DISTINCT dentro de un mapeo).
CREATE SCHEMA IF NOT EXISTS proveedores;

-- Agencias que contratan
DROP TABLE IF EXISTS proveedores.agency;
CREATE TABLE proveedores.agency AS
SELECT DISTINCT awarding_agency AS name FROM usaspending.contract WHERE awarding_agency IS NOT NULL;
ALTER TABLE proveedores.agency ADD PRIMARY KEY (name);

-- Proveedor → grupo, con la evidencia. El grupo es la matriz actual del proveedor en
-- USAspending (links.sql lo consolida después con la matriz final de GLEIF). La evidencia
-- incluye las otras matrices que USAspending registró para el proveedor: por ejemplo, la
-- SAIC de hoy figura también con LEIDOS HOLDINGS, la matriz de la vieja SAIC.
DROP TABLE IF EXISTS proveedores.supplier_group;
CREATE TABLE proveedores.supplier_group AS
SELECT r.uei AS supplier_uei, r.parent_uei AS group_id, r.parent_uei AS matrix_uei, r.parent_name AS matrix_name,
       r.parent_name || ' (UEI ' || r.parent_uei || ')' AS matched,
       'Matriz actual en USAspending: ' || r.parent_name || ' (UEI ' || r.parent_uei || ')'
       || coalesce('. Otras matrices registradas: ' || (
            SELECT string_agg(p.parent_name || coalesce(' (UEI ' || p.parent_uei || ')', ''), '; '
                              ORDER BY p.parent_name)
            FROM usaspending.recipient_parent p
            WHERE p.recipient_id = r.recipient_id
              AND p.parent_uei IS DISTINCT FROM r.parent_uei
              AND p.parent_uei IS DISTINCT FROM r.uei), '') AS source_text,
       'matriz actual del proveedor en USAspending' AS rule
FROM usaspending.recipient r
WHERE r.uei IS NOT NULL AND r.parent_uei IS NOT NULL;
ALTER TABLE proveedores.supplier_group ADD PRIMARY KEY (supplier_uei);

-- Grupo: uno por group_id. Si figura con varios nombres, se usa el más frecuente.
DROP TABLE IF EXISTS proveedores.group_company;
CREATE TABLE proveedores.group_company AS
SELECT DISTINCT ON (group_id) group_id, matrix_name AS name, matrix_uei AS uei, NULL::text AS lei
FROM (SELECT group_id, matrix_name, matrix_uei, count(*) AS n FROM proveedores.supplier_group GROUP BY 1, 2, 3) x
ORDER BY group_id, n DESC, matrix_name;
ALTER TABLE proveedores.group_company ADD PRIMARY KEY (group_id);

-- Proveedor = una empresa por UEI
DROP TABLE IF EXISTS proveedores.supplier;
CREATE TABLE proveedores.supplier AS
SELECT DISTINCT ON (uei) uei, name, state_code, country_code
FROM usaspending.recipient WHERE uei IS NOT NULL ORDER BY uei, recipient_id;
ALTER TABLE proveedores.supplier ADD PRIMARY KEY (uei);

-- Sectores: NAICS 2022 más los códigos de versiones anteriores que usan algunos contratos
-- (por ejemplo 541712, que en 2022 se dividió). Un código viejo cuelga de su prefijo más
-- largo que exista en 2022: 541712 queda dentro de 54171 y de 54.
DROP TABLE IF EXISTS proveedores.sector;
CREATE TABLE proveedores.sector AS
SELECT code, title, parent_code, false AS old_code FROM naics.sector
UNION ALL
SELECT c.naics_code, max(c.naics_description),
       (SELECT s.code FROM naics.sector s
        WHERE c.naics_code LIKE s.code || '%' OR (s.code LIKE '%-%' AND left(c.naics_code, 2)::int
              BETWEEN split_part(s.code, '-', 1)::int AND split_part(s.code, '-', 2)::int)
        ORDER BY s.level DESC LIMIT 1),
       true
FROM usaspending.contract c
WHERE c.naics_code IS NOT NULL AND NOT EXISTS (SELECT 1 FROM naics.sector s WHERE s.code = c.naics_code)
GROUP BY c.naics_code;
ALTER TABLE proveedores.sector ADD PRIMARY KEY (code);

-- Cada sector con todos sus ancestros, incluido él mismo (como naics.ancestor)
DROP TABLE IF EXISTS proveedores.sector_ancestor;
CREATE TABLE proveedores.sector_ancestor AS
WITH RECURSIVE up(code, ancestor_code) AS (
    SELECT code, code FROM proveedores.sector
    UNION
    SELECT up.code, s.parent_code FROM up JOIN proveedores.sector s ON s.code = up.ancestor_code
    WHERE s.parent_code IS NOT NULL
)
SELECT code, ancestor_code FROM up;
ALTER TABLE proveedores.sector_ancestor ADD PRIMARY KEY (code, ancestor_code);
