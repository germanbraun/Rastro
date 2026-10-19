-- Las tablas del dominio de petróleo y gas que leen los mapeos, y los enlaces entre fuentes,
-- cada uno con su evidencia. Lo corre link.py, después de cargar correcciones.csv y de
-- ubicar cada venteo en su concesión (venteo_ubicado).
-- (link.py crea el esquema energia con correccion y venteo_ubicado, y corre desde acá)
CREATE SCHEMA energia;

-- Mayúsculas, sin acentos, sin puntuación y sin forma societaria: «Vista Energy Argentina S.A.U.» → «VISTA ENERGY ARGENTINA»
CREATE FUNCTION energia.normalizar(t text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT trim(regexp_replace(regexp_replace(
           translate(upper(coalesce(t, '')), 'ÁÉÍÓÚÜÑ.,()', 'AEIOUUN    '),
           '\m(S ?A ?U|S ?A ?A ?I|S ?R ?L|S ?A|S ?L|SAU|SUCURSAL ARGENTINA|INC|LLC|LTD)\M', '', 'g'),
         '\s+', ' ', 'g'))
$$;

-- Empresas: todos los nombres de las tres tablas que nombran empresas, unidos por nombre normalizado
CREATE TABLE energia.empresa_nombre AS
WITH nombres AS (
  SELECT DISTINCT 'capitulo4' AS fuente, trim(empresa) AS nombre FROM capitulo4.produccion
  UNION SELECT DISTINCT 'capitulo4', trim(empresa) FROM capitulo4.pozo WHERE empresa IS NOT NULL
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

-- Concesiones del mapa
CREATE TABLE energia.concesion AS
SELECT c.id_concesion, c.areapermisoconcesion AS nombre, en.empresa_id AS operadora_mapa,
       c.empresa_informante AS informante, c.estadodearea AS estado
FROM sig_energia.concesion c
LEFT JOIN energia.empresa_nombre en ON en.fuente = 'sig_energia' AND en.nombre = trim(c.empresa_operadora);

-- Participaciones: el texto del mapa, separado en socios y porcentajes
CREATE TABLE energia.participacion AS
SELECT c.id_concesion, en.empresa_id, replace(m[2], ',', '.')::numeric AS porcentaje,
       trim(m[1]) || ': ' || m[2] || ' %' AS texto
FROM sig_energia.concesion c,
     regexp_matches(c.participacion, '<br>\s*([^:<]+?)\s*:\s*([0-9.,]+)\s*%', 'g') m
JOIN energia.empresa_nombre en ON en.fuente = 'sig_energia' AND en.nombre = trim(m[1]);

-- Quién opera hoy cada pozo: la empresa que declara su producción del último mes (diciembre de 2025).
-- La evidencia guarda lo que dice el padrón de pozos cuando no coincide.
CREATE TABLE energia.operador_pozo AS
WITH ultimo AS (
  SELECT DISTINCT ON (idpozo) idpozo, trim(empresa) AS empresa, mes
  FROM capitulo4.produccion ORDER BY idpozo, mes DESC, prod_pet DESC NULLS LAST
)
SELECT u.idpozo, en.empresa_id,
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
       'El punto (' || round(v.lon::numeric, 4) || ', ' || round(v.lat::numeric, 4)
       || ') cae dentro del contorno de la concesión ' || c.areapermisoconcesion || ' en el mapa.' AS evidencia
FROM energia.venteo_ubicado v
JOIN sig_energia.concesion c USING (id_concesion);
