-- Eventos adversos de openFDA (FAERS), agregados por fármaco. Nunca como verdad
-- clínica: son reportes espontáneos, con duplicados y sin denominador.
DROP SCHEMA IF EXISTS openfda CASCADE;
CREATE SCHEMA openfda;

-- Qué se consultó: una familia de ChEMBL buscada por sus UNII en patient.drug.openfda.unii
CREATE TABLE openfda.drug_query (
    query_id        text PRIMARY KEY,   -- parent_chembl_id de la familia consultada
    uniis           text[] NOT NULL,
    total_reports   int NOT NULL,       -- 0 si openFDA no tiene reportes
    fetched_at      timestamptz NOT NULL,
    data_updated    date                -- meta.last_updated de openFDA
);

-- Reportes por año de recepción: permite usar solo datos previos al inicio de un ensayo
CREATE TABLE openfda.reports_by_year (
    query_id    text NOT NULL REFERENCES openfda.drug_query,
    year        int NOT NULL,
    reports     int NOT NULL,
    serious     int NOT NULL,
    deaths      int NOT NULL,
    PRIMARY KEY (query_id, year)
);

-- Reacciones (MedDRA PT) más reportadas por fármaco, todo el período (las 100 principales)
CREATE TABLE openfda.reactions (
    query_id    text NOT NULL REFERENCES openfda.drug_query,
    reaction    text NOT NULL,
    reports     int NOT NULL,
    PRIMARY KEY (query_id, reaction)
);
