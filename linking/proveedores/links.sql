-- Enlaces entre fuentes del dominio de proveedores, cada uno con su evidencia:
-- proveedor o grupo → LEI (GLEIF), proveedor o grupo → lista de control, grupo → Wikidata.

-- Nombre normalizado: mayúsculas, sin puntuación y sin formas societarias
-- («ACME, Inc.», «ACME INC» y «Acme Incorporated» quedan como «ACME»).
CREATE OR REPLACE FUNCTION proveedores.normalize(name text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT trim(regexp_replace(regexp_replace(regexp_replace(regexp_replace(
        replace(replace(upper(coalesce(name, '')), '.', ''), '&', ' AND '),
        '[^A-Z0-9 ]', ' ', 'g'),
        '\m(THE|INC|INCORPORATED|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|LP|LLP|PLC|PLLC|PC|GMBH|AG|SA|NV|BV)\M', ' ', 'g'),
        '\s+', ' ', 'g'), '^\s+|\s+$', '', 'g'))
$$;

-- Nombres a enlazar: proveedores y matrices de USAspending, con su estado y país.
-- (kind = 'group' es una matriz de USAspending, identificada por su UEI.)
DROP TABLE IF EXISTS proveedores.company_name;
CREATE TABLE proveedores.company_name AS
SELECT 'supplier' AS kind, s.uei, s.name, s.state_code AS state, s.country_code AS country
FROM proveedores.supplier s
UNION ALL
SELECT 'group', m.matrix_uei, m.matrix_name, s.state_code, s.country_code
FROM (SELECT DISTINCT ON (matrix_uei) matrix_uei, matrix_name FROM proveedores.supplier_group
      ORDER BY matrix_uei, matrix_name) m
LEFT JOIN proveedores.supplier s ON s.uei = m.matrix_uei;

-- 1. Proveedor o grupo → LEI ------------------------------------------------
-- Candidatos: los que devolvió la búsqueda en GLEIF para ese nombre (data/gleif), cuyo
-- nombre legal o nombre anterior es igual una vez normalizado. La regla dice qué más coincidió.
DROP TABLE IF EXISTS proveedores.lei_candidate;
CREATE TABLE proveedores.lei_candidate AS
SELECT n.kind, n.uei, n.name, r.lei, r.legal_name, o.gleif_name, o.legal, r.entity_status,
       CASE WHEN o.legal AND n.state IS NOT NULL AND n.state IN (split_part(r.region, '-', 2), split_part(r.hq_region, '-', 2))
                 AND 'US' IN (r.country, r.hq_country) THEN 1
            WHEN o.legal AND n.country = 'USA' AND 'US' IN (r.country, r.hq_country) THEN 2
            WHEN NOT o.legal AND n.state IS NOT NULL AND n.state IN (split_part(r.region, '-', 2), split_part(r.hq_region, '-', 2))
                 AND 'US' IN (r.country, r.hq_country) THEN 3
            WHEN o.legal AND n.country <> 'USA' THEN 4
            -- Matriz que no es proveedor: USAspending no da su ubicación
            WHEN o.legal AND n.country IS NULL AND 'US' IN (r.country, r.hq_country) THEN 5
            WHEN o.legal AND n.country IS NULL THEN 6
       END AS priority,
       n.state, r.region, r.hq_region
FROM proveedores.company_name n
JOIN gleif.candidate c ON c.name = n.name
JOIN gleif.lei_record r ON r.lei = c.lei
CROSS JOIN LATERAL (SELECT r.legal_name AS gleif_name, true AS legal
                    UNION ALL SELECT unnest(r.other_names), false) o
WHERE length(proveedores.normalize(n.name)) >= 3
  AND proveedores.normalize(o.gleif_name) = proveedores.normalize(n.name);
DELETE FROM proveedores.lei_candidate WHERE priority IS NULL;
-- Sin ubicación para comparar, solo se aceptan entidades activas
DELETE FROM proveedores.lei_candidate WHERE priority >= 5 AND entity_status <> 'ACTIVE';

-- Se queda el mejor candidato; ante empate, el que está activo. Si siguen empatados varios
-- LEI distintos, el nombre es ambiguo y no se enlaza.
DROP TABLE IF EXISTS proveedores.lei_link;
CREATE TABLE proveedores.lei_link AS
WITH best AS (
    SELECT DISTINCT ON (kind, uei, lei) *
    FROM proveedores.lei_candidate
    ORDER BY kind, uei, lei, priority, legal DESC
), ranked AS (
    SELECT *, rank() OVER (PARTITION BY kind, uei ORDER BY priority, (entity_status = 'ACTIVE') DESC) AS pos
    FROM best
)
SELECT kind, uei, lei,
       proveedores.normalize(name) AS matched_text,  -- «matched» es palabra reservada para Ontop
       'USAspending: ' || rtrim(name, '.') || coalesce(' (' || state || ')', '')
       || '. GLEIF: ' || gleif_name || coalesce(' (' || coalesce(hq_region, region) || ')', '')
       || CASE WHEN entity_status <> 'ACTIVE' THEN ', inactiva' ELSE '' END AS source_text,
       CASE priority WHEN 1 THEN 'nombre legal y estado'
                     WHEN 2 THEN 'nombre legal y país'
                     WHEN 3 THEN 'nombre anterior y estado'
                     WHEN 4 THEN 'nombre legal (proveedor fuera de EE. UU.)'
                     WHEN 5 THEN 'nombre legal, en EE. UU. (sin ubicación en USAspending)'
                     WHEN 6 THEN 'nombre legal (sin ubicación en USAspending)' END AS rule,
       -- Otros candidatos que también coincidían, y por qué perdieron
       (SELECT string_agg(DISTINCT x.legal_name || CASE WHEN x.legal THEN ' (regla más débil)'
                          ELSE ' (solo coincide un nombre anterior: ' || x.gleif_name || ')' END, '; ')
        FROM best x WHERE x.kind = r.kind AND x.uei = r.uei AND x.lei <> r.lei) AS discarded
FROM ranked r
WHERE pos = 1 AND (SELECT count(*) FROM ranked x WHERE x.kind = r.kind AND x.uei = r.uei AND x.pos = 1) = 1;
ALTER TABLE proveedores.lei_link ADD PRIMARY KEY (kind, uei);

-- Matriz final de cada LEI; si GLEIF no registra una, la entidad es su propia matriz final.
DROP TABLE IF EXISTS proveedores.lei_final_parent;
CREATE TABLE proveedores.lei_final_parent AS
SELECT r.lei, coalesce(p.lei, r.lei) AS final_lei
FROM gleif.lei_record r LEFT JOIN gleif.lei_record p ON p.lei = r.ultimate_parent_lei;

-- Grupo consolidado: USAspending reparte un mismo grupo en varias matrices (Leidos figura
-- como LEIDOS HOLDINGS, LEIDOS, INC. y LEIDOS INC). Si la matriz tiene LEI, el grupo es su
-- matriz final en GLEIF, y la evidencia suma los dos pasos.
UPDATE proveedores.supplier_group sg
SET group_id = f.final_lei,
    source_text = sg.source_text || '. La matriz tiene el LEI ' || l.lei || ' (' || l.rule || ')'
        || coalesce('; descartado: ' || l.discarded, '')
        || CASE WHEN f.final_lei = l.lei THEN '. Sin otra matriz por encima en GLEIF'
                ELSE '. Su matriz final en GLEIF es ' || top.legal_name || ' (LEI ' || top.lei || ')' END,
    rule = 'matriz actual en USAspending y matriz final en GLEIF'
FROM proveedores.lei_link l
JOIN proveedores.lei_final_parent f ON f.lei = l.lei
JOIN gleif.lei_record top ON top.lei = f.final_lei
WHERE l.kind = 'group' AND l.uei = sg.matrix_uei;

DROP TABLE IF EXISTS proveedores.group_company;
CREATE TABLE proveedores.group_company AS
SELECT DISTINCT ON (sg.group_id) sg.group_id,
       coalesce(top.legal_name, sg.matrix_name) AS name,
       CASE WHEN top.lei IS NULL THEN sg.matrix_uei END AS uei,
       top.lei
FROM proveedores.supplier_group sg
LEFT JOIN gleif.lei_record top ON top.lei = sg.group_id
ORDER BY sg.group_id, sg.matrix_name;
ALTER TABLE proveedores.group_company ADD PRIMARY KEY (group_id);

-- Países que aparecen en GLEIF y en la Lista Consolidada
DROP TABLE IF EXISTS proveedores.country;
CREATE TABLE proveedores.country AS
SELECT country AS code FROM gleif.lei_record WHERE country IS NOT NULL
UNION SELECT unnest(countries) FROM csl.entry;
ALTER TABLE proveedores.country ADD PRIMARY KEY (code);

-- 2. Proveedor o grupo → lista de control -------------------------------------
-- Nombres y alias de las entradas que son empresas u organizaciones (sin personas,
-- barcos ni aviones; algunas listas no dicen el tipo).
DROP TABLE IF EXISTS proveedores.watchlist_name;
CREATE TABLE proveedores.watchlist_name AS
SELECT id, source, name AS text, 'nombre' AS kind FROM csl.entry
WHERE type IS NULL OR type = 'Entity'
UNION ALL
SELECT id, source, unnest(alt_names), 'alias' FROM csl.entry
WHERE type IS NULL OR type = 'Entity';

DROP TABLE IF EXISTS proveedores.watchlist_alias;
CREATE TABLE proveedores.watchlist_alias AS
SELECT id, source, text AS alias FROM proveedores.watchlist_name WHERE kind = 'alias';

-- Para una matriz, el enlace va a su grupo consolidado (uei = group_id).
DROP TABLE IF EXISTS proveedores.watchlist_link;
CREATE TABLE proveedores.watchlist_link AS
SELECT DISTINCT ON (n.kind, n.uei, w.id, w.source)
       n.kind,
       CASE n.kind WHEN 'group' THEN (SELECT min(sg.group_id) FROM proveedores.supplier_group sg
                                      WHERE sg.matrix_uei = n.uei) ELSE n.uei END AS uei,
       w.id AS entry_id, w.source AS entry_source,
       proveedores.normalize(n.name) AS matched_text,
       'USAspending: ' || rtrim(n.name, '.') || coalesce(' (' || n.country || ')', '')
       || '. Lista: ' || w.text || coalesce(' (' || nullif(array_to_string(e.countries, ', '), '') || ')', '') AS source_text,
       CASE w.kind WHEN 'nombre' THEN 'nombre igual, normalizado' ELSE 'alias igual, normalizado' END
       -- País: USAspending usa códigos de 3 letras y la lista de 2; se compara solo EE. UU.
       || CASE WHEN cardinality(e.countries) = 0 OR n.country IS DISTINCT FROM 'USA' THEN ''
               WHEN 'US' = ANY (e.countries) THEN '; también en EE. UU.'
               ELSE '; la entrada de la lista no está en EE. UU.' END AS rule
FROM proveedores.company_name n
JOIN proveedores.watchlist_name w ON proveedores.normalize(w.text) = proveedores.normalize(n.name)
JOIN csl.entry e ON e.id = w.id AND e.source = w.source
WHERE length(proveedores.normalize(n.name)) >= 4
ORDER BY n.kind, n.uei, w.id, w.source, w.kind DESC;  -- «nombre» antes que «alias»

-- 3. Grupo → Wikidata, por el LEI del grupo -------------------------------------
DROP TABLE IF EXISTS proveedores.group_wikidata;
CREATE TABLE proveedores.group_wikidata AS
SELECT DISTINCT ON (g.group_id) g.group_id, w.qid, cardinality(w.exchanges) > 0 AS listed,
       nullif(array_to_string(w.exchanges, ', '), '') AS exchanges, w.headquarters
FROM proveedores.group_company g JOIN wikidata.company w ON w.lei = g.lei
ORDER BY g.group_id, cardinality(w.exchanges) DESC, w.qid;
ALTER TABLE proveedores.group_wikidata ADD PRIMARY KEY (group_id);

-- 4. Proveedores para revisar: matriz extranjera o coincidencia con una lista ------
-- La matriz final es el LEI del grupo; si el grupo no tiene LEI, la del LEI del proveedor.
DROP TABLE IF EXISTS proveedores.supplier_flag;
CREATE TABLE proveedores.supplier_flag AS
SELECT sg.supplier_uei AS uei, 'ForeignParent' AS flag
FROM proveedores.supplier_group sg
JOIN proveedores.group_company g ON g.group_id = sg.group_id
LEFT JOIN proveedores.lei_link sl ON sl.kind = 'supplier' AND sl.uei = sg.supplier_uei
JOIN proveedores.lei_final_parent f ON f.lei = coalesce(g.lei, sl.lei)
JOIN gleif.lei_record top ON top.lei = f.final_lei
WHERE top.country <> 'US'
UNION
SELECT sg.supplier_uei, 'Watchlist'
FROM proveedores.supplier_group sg
WHERE EXISTS (SELECT 1 FROM proveedores.watchlist_link w
              WHERE (w.kind = 'supplier' AND w.uei = sg.supplier_uei) OR (w.kind = 'group' AND w.uei = sg.group_id));
