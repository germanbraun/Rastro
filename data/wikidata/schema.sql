-- Wikidata: las empresas con LEI de GLEIF que tiene Wikidata, su sede y si cotizan en bolsa.
DROP SCHEMA IF EXISTS wikidata CASCADE;
CREATE SCHEMA wikidata;

INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
    ('wikidata', 'Wikidata', 'https://www.wikidata.org/', 'CC0 1.0', 'wikidata')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE wikidata.company (
    qid         text NOT NULL,      -- por ejemplo Q1340920
    lei         text NOT NULL,      -- P1278
    label       text,               -- nombre en inglés
    exchanges   text[] NOT NULL,    -- bolsas de valores (P414); vacío si no cotiza
    headquarters text,              -- ciudad de la sede (P159)
    PRIMARY KEY (qid, lei)
);
CREATE INDEX ON wikidata.company (lei);
