-- Usuario de solo lectura para el enfoque "LLM + SQL crudo": ve las tablas de las
-- fuentes tal como se cargaron, sin los enlaces de Rastro (linking) ni el árbol
-- precalculado de MeSH (mesh.ancestor), y no puede modificar nada.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rastro_reader') THEN
        CREATE ROLE rastro_reader LOGIN PASSWORD 'rastro_reader';
    END IF;
END $$;

ALTER ROLE rastro_reader SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA aact, chembl, openfda, mesh TO rastro_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA aact, chembl, openfda TO rastro_reader;
GRANT SELECT ON mesh.descriptor, mesh.broader TO rastro_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA linking FROM rastro_reader;
REVOKE ALL ON mesh.ancestor FROM rastro_reader;
