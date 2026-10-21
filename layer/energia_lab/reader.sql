-- Usuarios de solo lectura para medir las preguntas sobre las predicciones de Rastro Lab.
-- «Sin Rastro»: las fuentes tal como se cargaron (también las que usa solo Lab) y las tablas que deja el modelo
-- (lab_gas), como las tendría cualquier proceso de aprendizaje automático. Sin las tablas de Rastro (energia).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'energia_lab_reader') THEN
        CREATE ROLE energia_lab_reader LOGIN PASSWORD 'energia_lab_reader';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'energia_lab_reader_links') THEN
        CREATE ROLE energia_lab_reader_links LOGIN PASSWORD 'energia_lab_reader_links';
    END IF;
END $$;

ALTER ROLE energia_lab_reader SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA capitulo4, capitulo4_anterior, sig_energia, fractura, trayectoria, lab_gas TO energia_lab_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA capitulo4, capitulo4_anterior, sig_energia, fractura, trayectoria, lab_gas TO energia_lab_reader;

-- «SQL + enlaces»: lo mismo, más las tablas que arma Rastro (esquema energia)
ALTER ROLE energia_lab_reader_links SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA capitulo4, capitulo4_anterior, sig_energia, fractura, trayectoria, lab_gas, energia TO energia_lab_reader_links;
GRANT SELECT ON ALL TABLES IN SCHEMA capitulo4, capitulo4_anterior, sig_energia, fractura, trayectoria, lab_gas, energia
    TO energia_lab_reader_links;
