-- Un esquema por fuente; los scripts de data/ cargan cada uno.
CREATE SCHEMA IF NOT EXISTS aact;
CREATE SCHEMA IF NOT EXISTS chembl;
CREATE SCHEMA IF NOT EXISTS openfda;

-- Registro de fuentes y de cargas: base de la trazabilidad de cada dato.
CREATE SCHEMA IF NOT EXISTS rastro_meta;

CREATE TABLE rastro_meta.source (
    id          text PRIMARY KEY,
    name        text NOT NULL,
    homepage    text NOT NULL,
    license     text NOT NULL,
    db_schema   text            -- NULL si la fuente vive en el triplestore
);

INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
    ('aact',    'AACT (ClinicalTrials.gov)',  'https://aact.ctti-clinicaltrials.org/', 'Dominio público (ClinicalTrials.gov)', 'aact'),
    ('chembl',  'ChEMBL',                     'https://www.ebi.ac.uk/chembl/',        'CC BY-SA 3.0',                          'chembl'),
    ('openfda', 'openFDA Drug Adverse Events', 'https://open.fda.gov/apis/drug/event/', 'CC0 1.0',                              'openfda'),
    ('mesh',    'MeSH (NLM)',                 'https://id.nlm.nih.gov/mesh/',         'Términos y condiciones de NLM',         NULL),
    -- Segundo dominio: proveedores del Estado (los esquemas los crea cada cargador)
    ('usaspending', 'USAspending (contratos federales)', 'https://www.usaspending.gov/', 'Dominio público', 'usaspending'),
    ('naics',   'NAICS 2022 (Census)',        'https://www.census.gov/naics/',        'Dominio público',                       'naics'),
    ('csl',     'Lista Consolidada de Control (trade.gov)', 'https://www.trade.gov/consolidated-screening-list', 'Dominio público', 'csl'),
    ('gleif',   'GLEIF (LEI)',                'https://www.gleif.org/',               'CC0 1.0',                               'gleif'),
    ('wikidata', 'Wikidata',                  'https://www.wikidata.org/',            'CC0 1.0',                               'wikidata'),
    -- Tercer dominio: petróleo y gas en Argentina (también los inserta data/energia/load.py)
    ('capitulo4', 'Producción por pozo, Capítulo IV (Secretaría de Energía)', 'http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo', 'CC-BY 4.0', 'capitulo4'),
    ('sig_energia', 'Mapas de la Secretaría de Energía (WFS)', 'https://sig.energia.gob.ar/wfsenergia', 'Datos públicos (Secretaría de Energía)', 'sig_energia');

CREATE TABLE rastro_meta.load_run (
    id          bigserial PRIMARY KEY,
    source_id   text NOT NULL REFERENCES rastro_meta.source(id),
    version     text,           -- release o fecha del snapshot descargado
    loaded_at   timestamptz NOT NULL DEFAULT now(),
    table_name  text NOT NULL,
    row_count   bigint NOT NULL
);

-- Checkpoint de la Fase 0: conteo por fuente según la última carga de cada tabla.
CREATE VIEW rastro_meta.source_counts AS
SELECT s.id AS source_id,
       count(DISTINCT l.table_name) AS tables_loaded,
       coalesce(sum(l.row_count), 0) AS row_count,
       max(l.loaded_at) AS last_loaded_at
FROM rastro_meta.source s
LEFT JOIN LATERAL (
    SELECT DISTINCT ON (table_name) table_name, row_count, loaded_at
    FROM rastro_meta.load_run
    WHERE source_id = s.id
    ORDER BY table_name, loaded_at DESC
) l ON true
GROUP BY s.id
ORDER BY s.id;
