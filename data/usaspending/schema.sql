-- USAspending: contratos federales del año fiscal 2025 de más de US$10 millones,
-- sus proveedores y las matrices de cada proveedor.
DROP SCHEMA IF EXISTS usaspending CASCADE;
CREATE SCHEMA usaspending;

INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
    ('usaspending', 'USAspending (contratos federales)', 'https://www.usaspending.gov/', 'Dominio público', 'usaspending')
ON CONFLICT (id) DO NOTHING;

-- Un contrato (award). amount es el monto total del contrato en toda su vida
-- ("Award Amount"), no solo lo obligado en 2025.
CREATE TABLE usaspending.contract (
    generated_internal_id text PRIMARY KEY,  -- id único de USAspending: CONT_AWD_...
    award_id              text NOT NULL,     -- número del contrato (PIID), puede repetirse entre agencias
    contract_award_type   text,              -- DEFINITIVE CONTRACT, DELIVERY ORDER, PURCHASE ORDER, BPA CALL
    recipient_id          text,              -- proveedor en USAspending: <hash>-C
    recipient_name        text,
    recipient_uei         text,
    awarding_agency       text,
    awarding_sub_agency   text,
    naics_code            text,              -- puede ser de una versión anterior a NAICS 2022
    naics_description     text,
    amount                numeric NOT NULL,
    start_date            date,
    end_date              date,
    description           text
);
CREATE INDEX ON usaspending.contract (recipient_id);
CREATE INDEX ON usaspending.contract (naics_code);

-- Perfil de cada proveedor distinto de los contratos (GET /recipient/{id}/).
CREATE TABLE usaspending.recipient (
    recipient_id    text PRIMARY KEY,
    name            text,
    alternate_names text[] NOT NULL,
    uei             text,
    duns            text,
    recipient_level text,               -- C: hijo, P: matriz, R: sin matriz
    parent_id       text,               -- matriz actual
    parent_name     text,
    parent_uei      text,
    parent_duns     text,
    city            text,
    state_code      text,
    country_code    text,
    business_types  text[] NOT NULL
);
CREATE INDEX ON usaspending.recipient (parent_uei);

-- Todas las matrices que tuvo un proveedor, según USAspending (la lista "parents"):
-- por ejemplo SCIENCE APPLICATIONS INTERNATIONAL CORPORATION con SAIC y con LEIDOS HOLDINGS.
CREATE TABLE usaspending.recipient_parent (
    recipient_id text NOT NULL REFERENCES usaspending.recipient,
    parent_id    text NOT NULL,
    parent_name  text,
    parent_uei   text,
    parent_duns  text,
    PRIMARY KEY (recipient_id, parent_id)
);
CREATE INDEX ON usaspending.recipient_parent (parent_uei);
