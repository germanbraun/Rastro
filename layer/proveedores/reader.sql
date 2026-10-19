-- Usuario de solo lectura para «sin Rastro» en el dominio de proveedores: ve las tablas
-- de las fuentes tal como se cargaron, sin las tablas que arma Rastro (esquema
-- proveedores: grupos consolidados, enlaces, sectores con ancestros) ni naics.ancestor.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'proveedores_reader') THEN
        CREATE ROLE proveedores_reader LOGIN PASSWORD 'proveedores_reader';
    END IF;
END $$;

ALTER ROLE proveedores_reader SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA usaspending, naics, csl, gleif, wikidata TO proveedores_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA usaspending, csl, gleif, wikidata TO proveedores_reader;
GRANT SELECT ON naics.sector TO proveedores_reader;
REVOKE ALL ON naics.ancestor FROM proveedores_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA proveedores FROM proveedores_reader;

-- Usuario de solo lectura para «SQL + enlaces», la línea de base justa: lo mismo, más las
-- tablas que arma Rastro y que leen los mapeos (esquema proveedores).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'proveedores_reader_links') THEN
        CREATE ROLE proveedores_reader_links LOGIN PASSWORD 'proveedores_reader_links';
    END IF;
END $$;

ALTER ROLE proveedores_reader_links SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA usaspending, naics, csl, gleif, wikidata, proveedores TO proveedores_reader_links;
GRANT SELECT ON ALL TABLES IN SCHEMA usaspending, csl, gleif, wikidata TO proveedores_reader_links;
GRANT SELECT ON naics.sector TO proveedores_reader_links;
GRANT SELECT ON proveedores.supplier, proveedores.supplier_group, proveedores.group_company, proveedores.sector,
                proveedores.sector_ancestor, proveedores.agency, proveedores.lei_link, proveedores.lei_final_parent,
                proveedores.watchlist_link, proveedores.group_wikidata, proveedores.supplier_flag
             TO proveedores_reader_links;
