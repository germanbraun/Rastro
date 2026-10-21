-- Las tablas del dominio de petróleo y gas que leen los mapeos, y los enlaces entre fuentes,
-- cada uno con su evidencia. Lo corre link.py, después de cargar correcciones.csv y de
-- ubicar cada venteo en su concesión (venteo_ubicado).
-- (link.py crea el esquema energia con correccion y venteo_ubicado, y corre desde acá)
CREATE SCHEMA energia;

-- Mayúsculas, sin acentos, sin puntuación y sin forma societaria: «Vista Energy Argentina S.A.U.» → «VISTA ENERGY ARGENTINA»
CREATE FUNCTION energia.normalizar(t text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT trim(regexp_replace(regexp_replace(
           translate(upper(coalesce(t, '')), 'ÁÉÍÓÚÜÑ.,()', 'AEIOUUN    '),
           '\m(SOCIEDAD ANONIMA|ARGENTINE BRANCH|S ?A ?U|S ?A ?A ?I|S ?R ?L|S ?A|S ?L|SAU|SUCURSAL ARGENTINA|INC|LLC|LTD)\M', '', 'g'),
         '\s+', ' ', 'g'))
$$;

-- Empresas: todos los nombres de las tablas que nombran empresas, unidos por nombre normalizado
CREATE TABLE energia.empresa_nombre AS
WITH nombres AS (
  SELECT DISTINCT 'capitulo4' AS fuente, trim(empresa) AS nombre FROM capitulo4.produccion
  UNION SELECT DISTINCT 'capitulo4', trim(empresa) FROM capitulo4.produccion_historica
  UNION SELECT DISTINCT 'capitulo4', trim(empresa) FROM capitulo4.pozo WHERE empresa IS NOT NULL
  UNION SELECT DISTINCT 'capitulo4', trim(empresa) FROM capitulo4_anterior.produccion   -- 2018 a 2022, para Rastro Lab
  UNION SELECT DISTINCT 'fractura', trim(empresa_informante) FROM fractura.fractura WHERE empresa_informante IS NOT NULL
  UNION SELECT DISTINCT 'sig_energia', trim(empresa_operadora) FROM sig_energia.concesion WHERE empresa_operadora IS NOT NULL
  UNION SELECT DISTINCT 'sig_energia', trim(m[1]) FROM sig_energia.concesion,
        regexp_matches(participacion, '<br>\s*([^:<]+?)\s*:\s*[0-9.,]+\s*%', 'g') m
)
SELECT n.fuente, n.nombre,
       CASE WHEN c.nombre IS NOT NULL THEN energia.normalizar(c.grupo) ELSE energia.normalizar(n.nombre) END AS empresa_id,
       CASE WHEN c.nombre IS NOT NULL THEN 'corrección revisada' ELSE 'mismo nombre normalizado' END AS regla,
       coalesce(c.motivo, 'Coincide el nombre sin acentos, puntuación ni forma societaria: «'
                || energia.normalizar(n.nombre) || '».') AS evidencia
FROM nombres n
LEFT JOIN energia.correccion c ON energia.normalizar(c.nombre) = energia.normalizar(n.nombre)
WHERE n.nombre <> '';

CREATE TABLE energia.empresa AS
SELECT empresa_id, coalesce(max(c.grupo), mode() WITHIN GROUP (ORDER BY n.nombre)) AS nombre
FROM energia.empresa_nombre n
LEFT JOIN energia.correccion c ON energia.normalizar(c.grupo) = n.empresa_id
GROUP BY empresa_id;

-- Producción 2025 por pozo y formación, con la empresa que la declara (las declaraciones juradas
-- son mensuales; un pozo puede producir de varias formaciones)
CREATE TABLE energia.produccion_pozo AS
SELECT md5(concat_ws('|', p.idpozo, p.idareapermisoconcesion, en.empresa_id, p.formacion, p.sub_tipo_recurso)) AS id,
       p.idpozo, p.idareapermisoconcesion AS id_concesion, en.empresa_id, p.formacion,
       p.tipo_de_recurso AS tipo_recurso, nullif(p.sub_tipo_recurso, '') AS sub_tipo_recurso,
       max(p.cuenca) AS cuenca, max(p.provincia) AS provincia,
       sum(p.prod_pet) AS petroleo_m3, sum(p.prod_gas) AS gas_mm3
FROM capitulo4.produccion p
JOIN energia.empresa_nombre en ON en.fuente = 'capitulo4' AND en.nombre = trim(p.empresa)
GROUP BY p.idpozo, p.idareapermisoconcesion, en.empresa_id, p.formacion, p.tipo_de_recurso, p.sub_tipo_recurso;

-- Concesiones del mapa (algunas tienen dos polígonos en el mapa: una fila por concesión)
CREATE TABLE energia.concesion AS
SELECT DISTINCT ON (c.id_concesion) c.id_concesion, c.areapermisoconcesion AS nombre, en.empresa_id AS operadora_mapa,
       c.empresa_informante AS informante, c.estadodearea AS estado,
       -- el contorno en WKT (el estándar de OGC que leen GeoSPARQL y cualquier herramienta de mapas)
       (SELECT 'POLYGON((' || string_agg(p->>0 || ' ' || (p->>1), ', ' ORDER BY n) || '))'
          FROM jsonb_array_elements(c.anillo::jsonb) WITH ORDINALITY AS a(p, n)) AS wkt
FROM sig_energia.concesion c
LEFT JOIN energia.empresa_nombre en ON en.fuente = 'sig_energia' AND en.nombre = trim(c.empresa_operadora)
ORDER BY c.id_concesion;

-- Participaciones: el texto del mapa, separado en socios y porcentajes
-- Si una concesión tiene participaciones revisadas (participaciones-revisadas.csv, cada una con su
-- documento), esas reemplazan a las del mapa en esa concesión.
CREATE TABLE energia.participacion AS
WITH mapa AS (
  SELECT DISTINCT c.id_concesion, en.empresa_id, replace(m[2], ',', '.')::numeric AS porcentaje,
         trim(m[1]) || ': ' || m[2] || ' %' AS texto, 'texto de socios del mapa' AS regla
  FROM sig_energia.concesion c,
       regexp_matches(c.participacion, '<br>\s*([^:<]+?)\s*:\s*([0-9.,]+)\s*%', 'g') m
  JOIN energia.empresa_nombre en ON en.fuente = 'sig_energia' AND en.nombre = trim(m[1])
), revisada AS (
  SELECT DISTINCT c.id_concesion,
         (SELECT en.empresa_id FROM energia.empresa_nombre en
           WHERE energia.normalizar(en.nombre) = energia.normalizar(r.empresa) LIMIT 1) AS empresa_id,
         r.porcentaje,
         'Corrección revisada: ' || r.empresa || ': ' || r.porcentaje || ' %. ' || r.motivo || ' Documento: ' || r.documento AS texto,
         'corrección revisada con documento' AS regla
  FROM energia.participacion_revisada r
  JOIN sig_energia.concesion c ON energia.normalizar(c.areapermisoconcesion) = energia.normalizar(r.concesion)
)
SELECT * FROM mapa WHERE id_concesion NOT IN (SELECT id_concesion FROM revisada)
UNION ALL
SELECT * FROM revisada;

-- Quién opera hoy cada pozo: la empresa que declara su producción del último mes (diciembre de 2025).
-- La evidencia guarda lo que dice el padrón de pozos cuando no coincide.
CREATE TABLE energia.operador_pozo AS
WITH ultimo AS (
  SELECT DISTINCT ON (idpozo) idpozo, trim(empresa) AS empresa, mes, nullif(trim(tipopozo), '') AS tipo_pozo
  FROM capitulo4.produccion ORDER BY idpozo, mes DESC, prod_pet DESC NULLS LAST
)
SELECT u.idpozo, en.empresa_id, u.tipo_pozo,   -- el tipo de pozo de su última declaración: Petrolífero, Gasífero…
       CASE WHEN pn.empresa_id IS NULL OR pn.empresa_id = en.empresa_id THEN 'coinciden las fuentes'
            ELSE 'rige la declaración jurada' END AS regla,
       'Declara la producción de ' || to_char(make_date(2025, u.mes, 1), 'MM/YYYY') || ': ' || rtrim(u.empresa, '.')
       || CASE WHEN pn.empresa_id IS NULL OR pn.empresa_id = en.empresa_id THEN '.'
               ELSE '. El padrón de pozos dice: ' || rtrim(trim(p.empresa), '.') || '.' END AS evidencia,
       p.empresa AS empresa_padron
FROM ultimo u
JOIN energia.empresa_nombre en ON en.fuente = 'capitulo4' AND en.nombre = u.empresa
LEFT JOIN capitulo4.pozo p ON p.idpozo = u.idpozo
LEFT JOIN energia.empresa_nombre pn ON pn.fuente = 'capitulo4' AND pn.nombre = trim(p.empresa);

-- Venteos: los detectados por satélite desde 2024 y los declarados, cada uno en su concesión
CREATE TABLE energia.venteo AS
SELECT v.gml_id AS id, v.tipo, v.fecha, v.satelite, v.nombre, v.id_concesion,
       'POINT(' || v.lon || ' ' || v.lat || ')' AS wkt,
       'El punto (' || round(v.lon::numeric, 4) || ', ' || round(v.lat::numeric, 4)
       || ') cae dentro del contorno de la concesión ' || c.nombre || ' en el mapa.' AS evidencia
FROM energia.venteo_ubicado v
JOIN energia.concesion c USING (id_concesion);   -- una fila por concesión (algunas tienen dos polígonos)

-- Gasoductos de transporte (ENARGAS), con su trazado en WKT
CREATE TABLE energia.gasoducto AS
SELECT g.gml_id AS id, trim(coalesce(g.nombregaso, g.nombretram)) AS nombre, trim(g.licenciata) AS licenciataria,
       'MULTILINESTRING(' || (SELECT string_agg('(' || (SELECT string_agg(p->>0 || ' ' || (p->>1), ', ' ORDER BY n)
                                                        FROM jsonb_array_elements(l) WITH ORDINALITY AS b(p, n)) || ')', ', ')
                              FROM jsonb_array_elements(g.lineas::jsonb) AS a(l)) || ')' AS wkt
FROM enargas.gasoducto g;

-- LEI de GLEIF: se acepta el candidato cuyo nombre legal, normalizado, es igual al de la empresa.
-- La evidencia guarda los candidatos descartados (por ejemplo, consorcios que nombran a varias empresas)
CREATE TABLE energia.empresa_lei AS
SELECT e.empresa_id, c.lei, c.nombre_legal,
       'mismo nombre legal normalizado' AS regla,
       'GLEIF, buscando «' || c.nombre_buscado || '» en Argentina: ' || c.nombre_legal || ' (' || c.lei || ').'
       || coalesce(' Descartado: ' || (SELECT string_agg(d.nombre_legal, '; ') FROM gleif_energia.candidato d
                                       WHERE d.nombre_buscado = c.nombre_buscado AND d.lei <> c.lei), '') AS evidencia
FROM gleif_energia.candidato c
JOIN energia.empresa e ON e.empresa_id = energia.normalizar(c.nombre_legal)
WHERE c.estado = 'ACTIVE';

-- Gasoducto de transporte más cercano a cada concesión y venteos con su entorno (IGN): las
-- calcula link.py (concesion_gasoducto_calc y venteo_entorno_calc); acá se les pone la evidencia
CREATE TABLE energia.concesion_gasoducto AS
SELECT DISTINCT ON (g.id_concesion) g.id_concesion, g.gasoducto, g.licenciataria, round(g.distancia_km::numeric, 1) AS distancia_km,
       CASE WHEN g.distancia_km = 0 THEN 'El gasoducto de transporte «' || g.gasoducto || '» (' || g.licenciataria
                 || ') cruza el contorno de la concesión ' || c.areapermisoconcesion || '.'
            ELSE 'El gasoducto de transporte más cercano es «' || g.gasoducto || '» (' || g.licenciataria || '), a '
                 || round(g.distancia_km::numeric, 1) || ' km del contorno de la concesión ' || c.areapermisoconcesion || '.'
       END AS evidencia
FROM energia.concesion_gasoducto_calc g JOIN sig_energia.concesion c USING (id_concesion)
ORDER BY g.id_concesion, g.distancia_km;   -- con dos polígonos, el más cercano

CREATE TABLE energia.venteo_entorno AS
SELECT v.id, v.localidad, v.provincia, round(v.distancia_km::numeric, 1) AS distancia_km, v.area_protegida,
       'La localidad más cercana es ' || v.localidad || ' (' || v.provincia || '), a ' || round(v.distancia_km::numeric, 1)
       || ' km.' || coalesce(' El punto está dentro del área protegida «' || v.area_protegida || '».', '') AS evidencia
FROM energia.venteo_entorno_calc v;

-- Estudios ambientales: el listado nombra la concesión como texto. Se une con la concesión del
-- mapa por nombre normalizado; los que no coinciden quedan sin concesión (no se adivina).
CREATE TABLE energia.estudio AS
SELECT md5(concat_ws('|', e.id_estudio, e.nombre_objeto, e.observaciones)) AS id, e.id_estudio, e.fecha_estudio, e.tipo_estudio, e.nombre_objeto, e.observaciones, en.empresa_id,
       c.id_concesion,
       CASE WHEN c.id_concesion IS NOT NULL
            THEN 'El estudio nombra la concesión «' || e.concesion || '», igual al nombre del mapa: ' || c.nombre || '.'
       END AS evidencia
FROM ambiental.estudio e
LEFT JOIN energia.concesion c ON energia.normalizar(c.nombre) = energia.normalizar(e.concesion)
LEFT JOIN (SELECT DISTINCT nombre, empresa_id FROM energia.empresa_nombre) en ON en.nombre = trim(e.empresa)
WHERE e.id_estudio IS NOT NULL;   -- un estudio puede tener varios objetos: una fila por objeto

-- Concesiones para revisar: las dos reglas de negocio, cada una con su motivo. El diccionario dice que
-- las dos son «concesión para revisar»; esa clase no tiene mapeo, Ontop la deduce
CREATE TABLE energia.concesion_revisar AS
SELECT c.id_concesion, 'sin gasoducto cerca' AS motivo,
       count(*) || ' posibles venteos desde 2024 y el gasoducto de transporte más cercano a ' || g.distancia_km || ' km.' AS evidencia
FROM energia.concesion c
JOIN energia.venteo v ON v.id_concesion = c.id_concesion AND v.tipo = 'detectado'
JOIN energia.concesion_gasoducto g ON g.id_concesion = c.id_concesion AND g.distancia_km >= 10
GROUP BY c.id_concesion, g.distancia_km
UNION ALL
SELECT c.id_concesion, 'sin planillas de venteo',
       count(*) || ' posibles venteos desde 2024 y ninguna planilla de venteo de gas (Res. 143/98) presentada desde 2022.'
FROM energia.concesion c
JOIN energia.venteo v ON v.id_concesion = c.id_concesion AND v.tipo = 'detectado'
WHERE NOT EXISTS (SELECT 1 FROM energia.estudio e WHERE e.id_concesion = c.id_concesion
                  AND e.tipo_estudio ILIKE '%aventamiento%' AND e.fecha_estudio >= DATE '2022-01-01')
GROUP BY c.id_concesion
HAVING count(*) >= 20;   -- al menos 20 detecciones: un caso aislado no alcanza para revisar

-- Quién operó cada concesión mes a mes, de 2023 a 2025: la empresa que declara la mayor parte de su
-- producción. Se suman petróleo (m³) y gas (miles de m³), que en energía equivalen más o menos. Un mes
-- sin producción también cuenta si lo declara una sola empresa: un área parada sigue teniendo operadora.
CREATE TABLE energia.operador_area_mes AS
WITH todo AS (
  SELECT anio, mes, idareapermisoconcesion, empresa, prod_pet, prod_gas FROM capitulo4.produccion
  UNION ALL
  SELECT anio, mes, idareapermisoconcesion, empresa, prod_pet, prod_gas FROM capitulo4.produccion_historica
), por_empresa AS (
  SELECT t.idareapermisoconcesion AS id_concesion, make_date(t.anio, t.mes, 1) AS mes, en.empresa_id,
         coalesce(sum(t.prod_pet), 0) AS petroleo_m3, coalesce(sum(t.prod_gas), 0) AS gas_mm3
  FROM todo t
  JOIN energia.empresa_nombre en ON en.fuente = 'capitulo4' AND en.nombre = trim(t.empresa)
  GROUP BY 1, 2, 3
), con_total AS (
  SELECT *, sum(petroleo_m3) OVER w AS area_petroleo_m3, sum(gas_mm3) OVER w AS area_gas_mm3,
         sum(petroleo_m3 + gas_mm3) OVER w AS area_total, count(*) OVER w AS empresas
  FROM por_empresa WINDOW w AS (PARTITION BY id_concesion, mes)
)
SELECT DISTINCT ON (id_concesion, mes) id_concesion, mes, empresa_id,
       area_petroleo_m3 AS petroleo_m3, area_gas_mm3 AS gas_mm3,   -- lo que produjo toda la concesión ese mes
       CASE WHEN area_total > 0 THEN round(100 * (petroleo_m3 + gas_mm3) / area_total) ELSE 100 END AS porcentaje
FROM con_total
WHERE area_total > 0 OR empresas = 1   -- sin producción y con varias empresas, el mes no dice quién opera
ORDER BY id_concesion, mes, petroleo_m3 + gas_mm3 DESC, empresa_id;

-- Cambios de operadora: otra empresa pasa a declarar la mayor parte de la producción de una concesión
-- y la sigue declarando al menos 3 meses seguidos (un mes suelto no es un cambio). Antes y después,
-- lo que producía la concesión por mes, en promedio, con cada operadora.
CREATE TABLE energia.cambio_operadora AS
WITH marcado AS (
  SELECT *, row_number() OVER (PARTITION BY id_concesion ORDER BY mes)
            - row_number() OVER (PARTITION BY id_concesion, empresa_id ORDER BY mes) AS tramo
  FROM energia.operador_area_mes
), tramos AS (   -- meses seguidos con la misma operadora
  SELECT id_concesion, empresa_id, min(mes) AS desde, max(mes) AS hasta, count(*) AS meses,
         avg(petroleo_m3) AS petroleo_m3, avg(gas_mm3) AS gas_mm3, round(avg(porcentaje)) AS porcentaje
  FROM marcado GROUP BY id_concesion, empresa_id, tramo
  HAVING count(*) >= 3
), seguidos AS (
  SELECT t.*, lag(empresa_id) OVER x AS antes_id, lag(hasta) OVER x AS antes_hasta,
         lag(petroleo_m3) OVER x AS antes_petroleo_m3, lag(gas_mm3) OVER x AS antes_gas_mm3,
         lag(porcentaje) OVER x AS antes_porcentaje
  FROM tramos t WINDOW x AS (PARTITION BY id_concesion ORDER BY desde)
)
SELECT s.id_concesion, s.desde AS mes, s.antes_id AS anterior_id, s.empresa_id AS nueva_id,
       round(s.antes_petroleo_m3) AS petroleo_antes_m3, round(s.petroleo_m3) AS petroleo_despues_m3,
       round(s.antes_gas_mm3) AS gas_antes_mm3, round(s.gas_mm3) AS gas_despues_mm3,
       'Hasta ' || to_char(s.antes_hasta, 'MM/YYYY') || ', ' || a.nombre || ' declaraba la mayor parte de la producción de '
       || coalesce(c.nombre, (SELECT max(trim(areapermisoconcesion)) FROM capitulo4.produccion_historica h
                                WHERE h.idareapermisoconcesion = s.id_concesion), s.id_concesion) || ' (' || s.antes_porcentaje || ' %); desde ' || to_char(s.desde, 'MM/YYYY')
       || ', ' || n.nombre || ' (' || s.porcentaje || ' %, ' || s.meses || ' meses seguidos).' AS evidencia
FROM seguidos s
JOIN energia.empresa a ON a.empresa_id = s.antes_id
JOIN energia.empresa n ON n.empresa_id = s.empresa_id
LEFT JOIN energia.concesion c USING (id_concesion)
WHERE s.antes_id <> s.empresa_id;

-- Las claves de las tablas de enlaces: con ellas, Rastro sabe que hay una fila por clave y no
-- necesita quitar repetidos en cada consulta (la participación pasa de 18 a 8 segundos)
-- Cómo arrancó cada pozo nuevo: el primer mes con petróleo o gas, quién lo declaró ese mes y con qué tipo
-- de pozo. Para un modelo que predice un pozo nuevo, la operadora de hoy sería usar el futuro. Va desde 2018
-- si se cargaron los años anteriores del Capítulo IV (data/lab-gas/), si no desde 2023. Se descartan los
-- pozos que ya estaban en el primer mes de los datos (pozos viejos que se reactivan).
CREATE TABLE energia.inicio_pozo AS
WITH todo AS (
  SELECT anio, mes, idpozo, empresa, prod_pet, prod_gas, tipopozo, idareapermisoconcesion, formacion, sub_tipo_recurso
  FROM capitulo4.produccion
  UNION ALL
  SELECT anio, mes, idpozo, empresa, prod_pet, prod_gas, tipopozo, idareapermisoconcesion, formacion, sub_tipo_recurso
  FROM capitulo4.produccion_historica
  UNION ALL
  SELECT anio, mes, idpozo, empresa, prod_pet, prod_gas, tipopozo, idareapermisoconcesion, formacion, sub_tipo_recurso
  FROM capitulo4_anterior.produccion
), desde AS (SELECT min(make_date(anio, mes, 1)) AS mes FROM todo
), primero AS (
  SELECT idpozo, min(make_date(anio, mes, 1)) AS primera_fila,
         min(make_date(anio, mes, 1)) FILTER (WHERE prod_pet > 0 OR prod_gas > 0) AS inicio
  FROM todo GROUP BY idpozo
), fila AS (   -- la fila del primer mes que más produjo (un pozo puede declarar varias formaciones)
  SELECT DISTINCT ON (t.idpozo) t.idpozo, p.inicio, trim(t.empresa) AS empresa, nullif(trim(t.tipopozo), '') AS tipo_pozo,
         t.idareapermisoconcesion AS id_concesion, t.formacion, t.sub_tipo_recurso
  FROM todo t JOIN primero p ON p.idpozo = t.idpozo AND make_date(t.anio, t.mes, 1) = p.inicio
  WHERE p.inicio > (SELECT mes FROM desde) AND p.primera_fila > (SELECT mes FROM desde)
  ORDER BY t.idpozo, coalesce(t.prod_gas, 0) + coalesce(t.prod_pet, 0) DESC
), gas AS (   -- el gas del pozo (todas sus formaciones) por mes desde que arrancó: 0 es el primer mes
  SELECT f.idpozo, (12 * (t.anio - extract(year FROM f.inicio)) + t.mes - extract(month FROM f.inicio))::int AS n,
         sum(coalesce(t.prod_gas, 0)) / 1000.0 AS gas   -- millones de m³
  FROM fila f JOIN todo t ON t.idpozo = f.idpozo AND make_date(t.anio, t.mes, 1) >= f.inicio
  GROUP BY 1, 2
), acumulado AS (   -- solo si están todos los meses: los que faltan no se cuentan como cero
  SELECT idpozo,
         CASE WHEN count(*) FILTER (WHERE n BETWEEN 1 AND 6) = 6 THEN sum(gas) FILTER (WHERE n BETWEEN 1 AND 6) END AS gas_2_7,
         CASE WHEN count(*) FILTER (WHERE n BETWEEN 0 AND 11) = 12 THEN sum(gas) FILTER (WHERE n BETWEEN 0 AND 11) END AS gas_12
  FROM gas GROUP BY 1
)
SELECT f.idpozo, f.inicio AS mes, en.empresa_id, f.empresa AS nombre_declarado, f.tipo_pozo, f.id_concesion,
       f.formacion, f.sub_tipo_recurso, round(g.gas_2_7, 3) AS gas_2_7, round(g.gas_12, 3) AS gas_12,
       'Primer mes con producción: ' || to_char(f.inicio, 'MM/YYYY') || '. Lo declara ' || rtrim(f.empresa, '.')
       || coalesce(' como pozo ' || lower(f.tipo_pozo), '') || ', en ' || f.id_concesion || '.' AS evidencia
FROM fila f
JOIN energia.empresa_nombre en ON en.fuente = 'capitulo4' AND en.nombre = f.empresa
LEFT JOIN acumulado g ON g.idpozo = f.idpozo;

-- La fractura de cada pozo (Adjunto IV): las fracturas informadas hasta el mes en que arrancó (las de después
-- no se sabían al arrancar), sumadas. La empresa que informa se une a las demás por su nombre, con su regla.
CREATE TABLE energia.fractura_pozo AS
WITH f AS (
  SELECT x.*, en.empresa_id, en.regla AS regla_nombre
  FROM fractura.fractura x
  LEFT JOIN energia.inicio_pozo i ON i.idpozo = x.idpozo
  LEFT JOIN energia.empresa_nombre en ON en.fuente = 'fractura' AND en.nombre = trim(x.empresa_informante)
  WHERE x.fecha_inicio_fractura < coalesce(i.mes + interval '1 month', DATE '2100-01-01')
)
SELECT idpozo, count(*) AS fracturas,
       max(longitud_rama_horizontal_m) AS rama_m, sum(cantidad_fracturas) AS etapas,
       sum(coalesce(arena_bombeada_nacional_tn, 0) + coalesce(arena_bombeada_importada_tn, 0)) AS arena_tn,
       sum(agua_inyectada_m3) AS agua_m3, max(presion_maxima_psi) AS presion_psi,
       min(fecha_inicio_fractura) AS fecha, max(empresa_id) AS empresa_id, max(trim(empresa_informante)) AS nombre_informado,
       max(regla_nombre) AS regla_nombre,
       max(fecha_data)::date AS cargada,   -- cuándo se cargó en el portal: puede ser meses después de que arrancó el pozo
       'Fractura informada por ' || rtrim(max(trim(empresa_informante)), '.') || ' desde ' || to_char(min(fecha_inicio_fractura), 'DD/MM/YYYY')
       || ': rama horizontal de ' || round(max(longitud_rama_horizontal_m)) || ' m, ' || sum(cantidad_fracturas) || ' etapas, '
       || round(sum(coalesce(arena_bombeada_nacional_tn, 0) + coalesce(arena_bombeada_importada_tn, 0))) || ' t de arena, '
       || round(sum(agua_inyectada_m3)) || ' m³ de agua, presión máxima ' || round(max(presion_maxima_psi)) || ' psi'
       || CASE WHEN count(*) > 1 THEN ' (' || count(*) || ' fracturas informadas)' ELSE '' END
       || '. Cargada en el portal el ' || to_char(max(fecha_data), 'DD/MM/YYYY') || '.' AS evidencia
FROM f GROUP BY idpozo;

-- Los registros de origen, uno por uno, para que cada predicción de Rastro Lab llegue hasta ellos.
-- Cada fractura informada (Adjunto IV), con su identificador; «usada» si entra en la fractura del pozo (informada
-- hasta el mes en que arrancó).
CREATE TABLE energia.fractura_registro AS
SELECT x.id_base_fractura_adjiv AS id, x.idpozo, x.fecha_inicio_fractura AS fecha, x.cantidad_fracturas AS etapas,
       x.longitud_rama_horizontal_m AS rama_m, x.fecha_data::date AS cargada, trim(x.empresa_informante) AS informante,
       (i.mes IS NULL OR x.fecha_inicio_fractura < i.mes + interval '1 month') AS usada
FROM fractura.fractura x
LEFT JOIN energia.inicio_pozo i ON i.idpozo = x.idpozo;

-- Cada mes de gas de un pozo nuevo que suma su gas de los meses 2 a 7, de las declaraciones juradas
CREATE TABLE energia.gas_mes AS
WITH todo AS (
  SELECT anio, mes, idpozo, prod_gas FROM capitulo4.produccion
  UNION ALL SELECT anio, mes, idpozo, prod_gas FROM capitulo4.produccion_historica
  UNION ALL SELECT anio, mes, idpozo, prod_gas FROM capitulo4_anterior.produccion
)
SELECT i.idpozo, make_date(t.anio, t.mes, 1) AS mes, to_char(make_date(t.anio, t.mes, 1), 'YYYY-MM') AS mes_texto,
       round(sum(coalesce(t.prod_gas, 0)) / 1000.0, 3) AS gas
FROM energia.inicio_pozo i
JOIN todo t ON t.idpozo = i.idpozo
           AND make_date(t.anio, t.mes, 1) >= i.mes + interval '1 month'
           AND make_date(t.anio, t.mes, 1) < i.mes + interval '7 months'
WHERE i.gas_2_7 IS NOT NULL
GROUP BY 1, 2, 3;

ALTER TABLE energia.participacion ADD PRIMARY KEY (id_concesion, empresa_id);
ALTER TABLE energia.empresa ADD PRIMARY KEY (empresa_id);
ALTER TABLE energia.empresa_nombre ADD PRIMARY KEY (fuente, nombre);
ALTER TABLE energia.concesion ADD PRIMARY KEY (id_concesion);
ALTER TABLE energia.inicio_pozo ADD PRIMARY KEY (idpozo);
ALTER TABLE energia.fractura_pozo ADD PRIMARY KEY (idpozo);
ALTER TABLE energia.fractura_registro ADD PRIMARY KEY (id);
ALTER TABLE energia.gas_mes ADD PRIMARY KEY (idpozo, mes);
