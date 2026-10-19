-- Lista Consolidada de Control (trade.gov): las listas de control del gobierno
-- de EE. UU. en un solo archivo (OFAC, Comercio, Estado).
DROP SCHEMA IF EXISTS csl CASCADE;
CREATE SCHEMA csl;

INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
    ('csl', 'Lista Consolidada de Control (trade.gov)',
     'https://www.trade.gov/consolidated-screening-list', 'Dominio público', 'csl')
ON CONFLICT (id) DO NOTHING;

-- Una entrada de una lista. La misma persona o empresa puede estar en varias listas.
CREATE TABLE csl.entry (
    id              text NOT NULL,      -- _id del archivo; se repite entre listas (SDN y SSI)
    source          text NOT NULL,      -- la lista: "Entity List (EL) - Bureau of Industry and Security"
    type            text,               -- Entity, Individual, Vessel, Aircraft (vacío en algunas listas)
    name            text NOT NULL,
    alt_names       text[] NOT NULL,    -- alias, separados por ";" en el archivo
    countries       text[] NOT NULL,    -- códigos ISO de 2 letras, tomados de las direcciones
    programs        text,
    addresses       text,
    ids             text,               -- identificadores declarados (registro, ISIN, etc.)
    start_date      date,
    source_list_url text,
    PRIMARY KEY (id, source)
);
CREATE INDEX ON csl.entry (name);
