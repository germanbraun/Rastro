-- Datos que solo usa Rastro Lab (gas de Vaca Muerta), cada fuente en su esquema, con los nombres de columna
-- originales. Sin DROP: el enlazador de petróleo y gas corre este archivo para crear las tablas vacías si
-- todavía no se cargaron; el cargador (load.py) las vacía antes de cargar.

-- Capítulo IV, años anteriores (2018 a 2022): las mismas columnas que capitulo4.produccion. En su propio
-- esquema para no cambiar lo que usa Rastro Layer (2023 a 2025).
CREATE SCHEMA IF NOT EXISTS capitulo4_anterior;
CREATE TABLE IF NOT EXISTS capitulo4_anterior.produccion (
    anio int, mes int, idpozo text, idempresa text, empresa text,
    prod_pet numeric,                    -- petróleo, m³
    prod_gas numeric,                    -- gas, miles de m³
    formacion text, idareapermisoconcesion text, areapermisoconcesion text, areayacimiento text,
    cuenca text, provincia text, tipo_de_recurso text, sub_tipo_recurso text, tipoestado text,
    tipopozo text
);

-- Datos de fractura de pozos (Adjunto IV, datos.energia.gob.ar): una fila por fractura informada.
-- Se actualiza todos los días y el portal lo marca «preliminar, sujeto a revisión».
CREATE SCHEMA IF NOT EXISTS fractura;
CREATE TABLE IF NOT EXISTS fractura.fractura (
    id_base_fractura_adjiv text, idpozo text, sigla text, cuenca text, areapermisoconcesion text, yacimiento text,
    formacion_productiva text, tipo_reservorio text, subtipo_reservorio text,
    longitud_rama_horizontal_m numeric,  -- largo de la rama horizontal
    cantidad_fracturas numeric,          -- etapas de fractura
    tipo_terminacion text,
    arena_bombeada_nacional_tn numeric, arena_bombeada_importada_tn numeric,
    agua_inyectada_m3 numeric, co2_inyectado_m3 numeric,
    presion_maxima_psi numeric, potencia_equipos_fractura_hp numeric,
    fecha_inicio_fractura date, fecha_fin_fractura date, fecha_data timestamp,
    empresa_informante text
);
