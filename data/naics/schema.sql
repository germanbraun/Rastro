-- Sectores NAICS 2022 (Census): de 2 a 6 dígitos.
DROP SCHEMA IF EXISTS naics CASCADE;
CREATE SCHEMA naics;

INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
    ('naics', 'NAICS 2022 (Census)', 'https://www.census.gov/naics/', 'Dominio público', 'naics')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE naics.sector (
    code        text PRIMARY KEY,   -- 2 a 6 dígitos; los sectores agrupados son rangos: 31-33, 44-45, 48-49
    title       text NOT NULL,
    level       int NOT NULL,       -- cantidad de dígitos: 2 a 6
    parent_code text REFERENCES naics.sector
);
CREATE INDEX ON naics.sector (parent_code);

-- Cada sector con todos sus ancestros, incluido él mismo (como mesh.ancestor):
-- "dentro de 54 Servicios profesionales" es una sola fila por subsector.
CREATE TABLE naics.ancestor (
    code          text NOT NULL REFERENCES naics.sector,
    ancestor_code text NOT NULL REFERENCES naics.sector,
    PRIMARY KEY (code, ancestor_code)
);
CREATE INDEX ON naics.ancestor (ancestor_code);
