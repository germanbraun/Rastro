-- The customer setup's database users (run by setup.sh, with the passwords of .env).
--
-- rastro_readonly: Ontop and the app read every table, present and future, and write nothing (pg_read_all_data).
-- The domains' SQL readers (layer/dominios.yaml, «readers») keep their own grants and get the password of .env
-- instead of their own name.

SET client_min_messages = warning;   -- running it again is expected: no notices

SELECT format('CREATE ROLE rastro_readonly LOGIN PASSWORD %L', :'readonly_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rastro_readonly') \gexec

ALTER ROLE rastro_readonly PASSWORD :'readonly_password';
ALTER ROLE rastro_readonly SET statement_timeout = '120s';
GRANT pg_read_all_data TO rastro_readonly;

SELECT format('ALTER ROLE %I PASSWORD %L', rolname, :'reader_password')
FROM pg_roles WHERE rolname = ANY (string_to_array(:'readers', ',')) \gexec
