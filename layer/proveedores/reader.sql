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
