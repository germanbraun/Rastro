-- Tercer dominio: petróleo y gas en Argentina. Dos fuentes de la Secretaría de Energía,
-- cada una en su esquema, con los nombres de columna originales.

-- Capítulo IV: declaraciones juradas mensuales de producción y padrón de pozos (datos.energia.gob.ar)
DROP SCHEMA IF EXISTS capitulo4 CASCADE;
CREATE SCHEMA capitulo4;

CREATE TABLE capitulo4.produccion (      -- una fila por pozo y mes de 2025
    anio int, mes int, idpozo text, idempresa text, empresa text,
    prod_pet numeric,                    -- petróleo, m³
    prod_gas numeric,                    -- gas, miles de m³
    formacion text, idareapermisoconcesion text, areapermisoconcesion text, areayacimiento text,
    cuenca text, provincia text, tipo_de_recurso text, sub_tipo_recurso text, tipoestado text
);

CREATE TABLE capitulo4.pozo (            -- padrón de pozos, con su ubicación
    idpozo text, sigla text, empresa text, cod_area text, area text, yacimiento text, formacion text,
    cuenca text, provincia text, tipo_recurso text, sub_tipo_recurso text, tipoestado text,
    lon double precision, lat double precision
);

-- Servicio de mapas (WFS) de la Secretaría de Energía (sig.energia.gob.ar)
DROP SCHEMA IF EXISTS sig_energia CASCADE;
CREATE SCHEMA sig_energia;

CREATE TABLE sig_energia.concesion (     -- concesiones de explotación (RES. 319/93)
    id_concesion text, areapermisoconcesion text, empresa_informante text, empresa_operadora text,
    participacion text,                  -- texto con los socios y sus porcentajes, tal como viene
    estadodearea text, observaciones text,
    anillo text                          -- el contorno, como JSON [[lon, lat], ...]
);

CREATE TABLE sig_energia.venteo_declarado (   -- puntos de venteo y quema declarados (RES. 319/93)
    gml_id text, nombre text, tipo text, procedencia text, nombre_procedencia text,
    empresa_informante text, empresa_operadora_area text,
    lon double precision, lat double precision
);

CREATE TABLE sig_energia.venteo_detectado (   -- posibles venteos: anomalías térmicas vistas por satélite
    gml_id text, fecha date, provincia text, satelite text,
    lon double precision, lat double precision
);
