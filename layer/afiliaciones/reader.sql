-- Read-only user for «without Rastro» in research affiliations: it sees the source tables as loaded (crossref, ror),
-- not the tables Rastro builds (schema afiliaciones: identifications, doubtful candidates, possible gaps).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'afiliaciones_reader') THEN
        CREATE ROLE afiliaciones_reader LOGIN PASSWORD 'afiliaciones_reader';
    END IF;
END $$;

ALTER ROLE afiliaciones_reader SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA crossref, ror TO afiliaciones_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA crossref, ror TO afiliaciones_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA afiliaciones FROM afiliaciones_reader;

-- Read-only user for «SQL + links», the fair baseline: the same, plus the tables Rastro builds and the mapping reads.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'afiliaciones_reader_links') THEN
        CREATE ROLE afiliaciones_reader_links LOGIN PASSWORD 'afiliaciones_reader_links';
    END IF;
END $$;

ALTER ROLE afiliaciones_reader_links SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA crossref, ror, afiliaciones TO afiliaciones_reader_links;
GRANT SELECT ON ALL TABLES IN SCHEMA crossref, ror, afiliaciones TO afiliaciones_reader_links;
