-- GLEIF: candidatos a LEI para los nombres de proveedores y matrices de USAspending.
-- La búsqueda por nombre es aproximada: acá solo se guardan los candidatos, sin
-- decidir cuál es el correcto. El enlace con su evidencia es la Fase P2.
DROP SCHEMA IF EXISTS gleif CASCADE;
CREATE SCHEMA gleif;

INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
    ('gleif', 'GLEIF (LEI)', 'https://www.gleif.org/', 'CC0 1.0', 'gleif')
ON CONFLICT (id) DO NOTHING;

-- Qué nombre se buscó y por qué (matriz o proveedor de los que más facturan)
CREATE TABLE gleif.name_query (
    name        text PRIMARY KEY,   -- tal como está en USAspending
    kind        text NOT NULL,      -- matriz | proveedor
    total_hits  int NOT NULL,       -- resultados de GLEIF; se guardan los primeros 5
    fetched_at  timestamptz NOT NULL
);

-- Candidatos en el orden de relevancia de GLEIF (rank 1 = el más parecido según GLEIF).
-- Los rank 6 a 10 son de una segunda búsqueda con el nombre normalizado, si ninguno coincidía,
-- y los 11 a 20, de una tercera por nombre legal, solo para los grupos grandes.
CREATE TABLE gleif.candidate (
    name    text NOT NULL REFERENCES gleif.name_query,
    rank    int NOT NULL,
    lei     text NOT NULL,
    PRIMARY KEY (name, rank)
);
CREATE INDEX ON gleif.candidate (lei);

-- Registro LEI de cada candidato y de su matriz final
CREATE TABLE gleif.lei_record (
    lei                 text PRIMARY KEY,
    legal_name          text NOT NULL,
    other_names         text[] NOT NULL,   -- nombres anteriores y otros nombres
    country             text,              -- país del domicilio legal (ISO de 2 letras)
    region              text,              -- estado o provincia del domicilio legal: US-VA
    hq_country          text,
    hq_region           text,              -- estado o provincia de la sede
    jurisdiction        text,
    entity_status       text,              -- ACTIVE | INACTIVE
    registration_status text,              -- ISSUED, LAPSED, RETIRED...
    ultimate_parent_lei text               -- matriz final, si GLEIF la tiene
);

-- LEI revisados: nombres que las búsquedas no encuentran, con el LEI pedido directo a GLEIF
-- (lei-revisados.csv) y por qué
CREATE TABLE gleif.lei_reviewed (
    name    text PRIMARY KEY,   -- tal como está en USAspending
    lei     text NOT NULL REFERENCES gleif.lei_record,
    reason  text NOT NULL
);
