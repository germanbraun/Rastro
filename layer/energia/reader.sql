-- Usuario de solo lectura para «sin Rastro» en el dominio de petróleo y gas: ve las tablas
-- de las fuentes tal como se cargaron, sin las tablas que arma Rastro (esquema energia).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'energia_reader') THEN
        CREATE ROLE energia_reader LOGIN PASSWORD 'energia_reader';
    END IF;
END $$;

ALTER ROLE energia_reader SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA capitulo4, sig_energia, ambiental, enargas, ign, gleif_energia TO energia_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA capitulo4, sig_energia, ambiental, enargas, ign, gleif_energia TO energia_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA energia FROM energia_reader;

-- Usuario de solo lectura para «SQL + enlaces», la línea de base justa: lo mismo, más las
-- tablas que arma Rastro y que leen los mapeos (esquema energia).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'energia_reader_links') THEN
        CREATE ROLE energia_reader_links LOGIN PASSWORD 'energia_reader_links';
    END IF;
END $$;

ALTER ROLE energia_reader_links SET statement_timeout = '60s';
GRANT USAGE ON SCHEMA capitulo4, sig_energia, ambiental, enargas, ign, gleif_energia, energia TO energia_reader_links;
GRANT SELECT ON ALL TABLES IN SCHEMA capitulo4, sig_energia, ambiental, enargas, ign, gleif_energia TO energia_reader_links;
GRANT SELECT ON energia.empresa, energia.empresa_nombre, energia.empresa_lei, energia.produccion_pozo,
                energia.concesion, energia.participacion, energia.operador_pozo, energia.venteo,
                energia.concesion_gasoducto, energia.venteo_entorno, energia.estudio,
                energia.concesion_revisar, energia.operador_area_mes, energia.cambio_operadora
             TO energia_reader_links;
