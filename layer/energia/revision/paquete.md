# Revisión independiente de las referencias: petróleo y gas en Argentina

Las respuestas de referencia de las 10 preguntas de la evaluación salieron de Rastro y las escribió un asistente de IA. Hasta que una persona las confirme con las fuentes, todo número de precisión es provisional. Este paquete es para esa persona.

## Qué se pide

1. Para cada pregunta, obtener la respuesta **con las fuentes, sin usar Rastro**: ni la app, ni sus consultas SPARQL, ni sus tablas de enlaces. Sirven las tablas de las fuentes tal como se cargaron (acceso de solo lectura) o los archivos originales de cada organismo, en la versión indicada.
2. La consulta SQL de cada pregunta es la que escribió el evaluador sin Rastro: un punto de partida, no la respuesta. Revísela, corríjala o use otra forma.
3. Anotar en `formulario.csv` (una fila por pregunta): `respuesta_revisada` (un número sin separador de miles y con punto decimal, o una lista separada por «;»), `fuentes_y_version`, `como_lo_verifique` (una o dos frases; si su respuesta difiere de la de Rastro, por qué), `revisor`, `fecha` (AAAA-MM-DD) y `estado` = `revisada`.
4. Si una pregunta admite más de una lectura, anote la suya en `como_lo_verifique`; no la cambie.

Para saber qué cambia: una respuesta cuenta como correcta si está a menos de 5 % de la referencia (números) o si sus nombres coinciden en un 80 % o más (listas).

El revisor no puede ser quien aprobó las preguntas como requisito de negocio. Tiempo estimado: una o dos horas con acceso a las tablas.

## e01

> ¿Cuántos metros cúbicos de petróleo producidos en 2025 le corresponden a YPF según su participación, es decir, sumando en cada concesión la producción de petróleo multiplicada por el porcentaje de YPF en esa concesión?

**Respuesta de Rastro, a confirmar:** 12570093.35

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ 12581212.57
- SQL + enlaces de Rastro: ✅ 12570093.35
- Con Rastro: ✅ 12570093.35

**Diferencia ya revisada por el asistente (e01 (Rastro)):** Rastro dio 0 en las 4 formas. El LLM unió la participación con la concesión por `energia:concession` en lugar de `energia:inConcession`. Las dos propiedades se parecen y la ontología no dice cuál va con cada clase. **Debilidad del diccionario**, no de los datos. Se dejó una sola propiedad (`energia:inConcession`) y se volvió a medir: 4 de 4 correctas. Resultado: Medido de nuevo: correcta.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Capítulo IV: producción y padrón de pozos (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo): `capitulo4.produccion` (producción 2025, cargada el 2026-10-20)
- Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS) (https://sig.energia.gob.ar/wfsenergia): `sig_energia.concesion` (WFS, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
with fila as (
  select c.id_concesion, c.ctid as r,
         sum(replace(substring(part from ':\s*([0-9]+(?:[.,][0-9]+)?)\s*%'), ',', '.')::numeric) as pct
  from sig_energia.concesion c,
       regexp_split_to_table(c.participacion, '<br>') as part
  where upper(trim(part)) ~ '^YPF[^A-Z]' and part ~ ':\s*[0-9]'
  group by c.id_concesion, c.ctid
),
ypf as (select id_concesion, max(pct) as pct from fila group by id_concesion),
prod as (
  select idareapermisoconcesion as id, sum(prod_pet) as pet
  from capitulo4.produccion where anio = 2025 group by idareapermisoconcesion
)
select round(sum(prod.pet * ypf.pct / 100), 2)
from prod join ypf on ypf.id_concesion = prod.id
```

## e02

> ¿Cuántos pozos con producción declarada en 2025 opera hoy YPF, si la operadora de un pozo es la empresa que declara su producción en el último mes en que el pozo aparece en 2025?

**Respuesta de Rastro, a confirmar:** 15809

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ 15809
- SQL + enlaces de Rastro: ✅ 15809
- Con Rastro: ✅ 15809

**Diferencia ya revisada por el asistente (e02, forma 2):** SQL sin Rastro dio 6.263. Leyó «pozos con producción» como «con producción mayor que cero». La pregunta dice «con producción declarada»: es una lectura distinta, no un error de datos. Resultado: Cuenta como respuesta distinta.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Capítulo IV: producción y padrón de pozos (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo): `capitulo4.produccion` (producción 2025, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
WITH ultimo AS (
  SELECT idpozo, max(mes) AS mes FROM capitulo4.produccion WHERE anio = 2025 GROUP BY idpozo
)
SELECT count(DISTINCT p.idpozo)
FROM capitulo4.produccion p
JOIN ultimo u ON u.idpozo = p.idpozo AND u.mes = p.mes
WHERE p.anio = 2025 AND upper(p.empresa) LIKE 'YPF%'
```

## e03

> ¿Cuáles son las 5 concesiones con más posibles venteos detectados por satélite desde el 1 de enero de 2024, contando los puntos que caen dentro del contorno de cada concesión?

**Respuesta de Rastro, a confirmar:** LOMA CAMPANA; LOMA LA LATA - SIERRA BARROSA; BAJO DEL CHOIQUE - LA INVERNADA; LA CALERA; LA ANGOSTURA SUR I

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ LOMA CAMPANA; LOMA LA LATA - SIERRA BARROSA; BAJO DEL CHOIQUE - LA INVERNADA; LA CALERA; LA ANGOSTURA SUR I
- SQL + enlaces de Rastro: ✅ LOMA CAMPANA; LOMA LA LATA - SIERRA BARROSA; BAJO DEL CHOIQUE - LA INVERNADA; LA CALERA; LA ANGOSTURA SUR I
- Con Rastro: ✅ LOMA CAMPANA; LOMA LA LATA - SIERRA BARROSA; BAJO DEL CHOIQUE - LA INVERNADA; LA CALERA; LA ANGOSTURA SUR I

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS) (https://sig.energia.gob.ar/wfsenergia): `sig_energia.concesion` (WFS, cargada el 2026-10-20); `sig_energia.venteo_detectado` (WFS, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
with pts as (
  select c.id_concesion, c.areapermisoconcesion, (p.value->>0)::float8 as x, (p.value->>1)::float8 as y, p.ord
  from sig_energia.concesion c,
       jsonb_array_elements(c.anillo::jsonb) with ordinality as p(value, ord)
  where c.anillo is not null and jsonb_typeof(p.value->0) = 'number'
),
edges as (
  select id_concesion, areapermisoconcesion, x as x1, y as y1,
         coalesce(lead(x) over w, first_value(x) over w) as x2,
         coalesce(lead(y) over w, first_value(y) over w) as y2
  from pts
  window w as (partition by id_concesion order by ord)
),
bbox as (
  select id_concesion, min(x1) minx, max(x1) maxx, min(y1) miny, max(y1) maxy
  from edges group by id_concesion
),
cand as (
  select b.id_concesion, v.gml_id, v.lon, v.lat
  from bbox b join sig_energia.venteo_detectado v
    on v.lon between b.minx and b.maxx and v.lat between b.miny and b.maxy
  where v.fecha >= date '2024-01-01'
),
inside as (
  select c.id_concesion, c.gml_id
  from cand c join edges e on e.id_concesion = c.id_concesion
  where (e.y1 > c.lat) <> (e.y2 > c.lat)
    and c.lon < (e.x2 - e.x1) * (c.lat - e.y1) / (e.y2 - e.y1) + e.x1
  group by c.id_concesion, c.gml_id
  having count(*) % 2 = 1
)
select max(e.areapermisoconcesion) as concesion
from inside i join (select distinct id_concesion, areapermisoconcesion from edges) e on e.id_concesion = i.id_concesion
group by i.id_concesion
order by count(distinct i.gml_id) desc
limit 5
```

## e04

> ¿Cuáles son las 5 empresas que declararon más petróleo no convencional (shale o tight) en 2025, contando como una sola empresa a Pluspetrol S.A. y Pluspetrol Cuenca Neuquina S.R.L.?

**Respuesta de Rastro, a confirmar:** YPF S.A.; VISTA ENERGY ARGENTINA SAU; PLUSPETROL; PAN AMERICAN ENERGY SL; SHELL ARGENTINA S.A.

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ YPF S.A.; VISTA ENERGY ARGENTINA SAU; PLUSPETROL S.A.; PAN AMERICAN ENERGY SL; SHELL ARGENTINA S.A.
- SQL + enlaces de Rastro: ✅ YPF S.A.; VISTA ENERGY ARGENTINA SAU; PLUSPETROL; PAN AMERICAN ENERGY SL; SHELL ARGENTINA S.A.
- Con Rastro: ✅ YPF S.A.; VISTA ENERGY ARGENTINA SAU; PLUSPETROL; PAN AMERICAN ENERGY SL; SHELL ARGENTINA S.A.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Capítulo IV: producción y padrón de pozos (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo): `capitulo4.produccion` (producción 2025, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
SELECT empresa FROM (
  SELECT CASE WHEN upper(empresa) LIKE 'PLUSPETROL%' THEN 'PLUSPETROL S.A.' ELSE empresa END AS empresa,
         sum(prod_pet) AS pet
  FROM capitulo4.produccion
  WHERE anio = 2025 AND upper(sub_tipo_recurso) IN ('SHALE','TIGHT')
  GROUP BY 1
) t
ORDER BY pet DESC NULLS LAST
LIMIT 5
```

## e05

> ¿Cuántas concesiones tienen al menos un posible venteo detectado por satélite desde el 1 de enero de 2024 dentro de su contorno y tienen el gasoducto de transporte de ENARGAS más cercano a 10 km o más de su contorno?

**Respuesta de Rastro, a confirmar:** 33

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ❌ —
- SQL + enlaces de Rastro: ✅ 33
- Con Rastro: ✅ 33

**Diferencia ya revisada por el asistente (e05 (gasoductos)):** SQL + enlaces dio 33 en una forma; la referencia daba 29. Rastro no tenía distancia para las concesiones sin ningún gasoducto a menos de ~100 km, y la pregunta las incluye. **Error de Rastro**: se corrigió `linking/energia/link.py` (si no hay gasoducto cerca, se mide contra todos) y se volvieron a ejecutar todas las consultas guardadas. Resultado: Referencia: 33.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Gasoductos de transporte (ENARGAS) (https://www.enargas.gob.ar/): `enargas.gasoducto` (WFS de la Secretaría de Energía, cargada el 2026-10-20)
- Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS) (https://sig.energia.gob.ar/wfsenergia): `sig_energia.concesion` (WFS, cargada el 2026-10-20); `sig_energia.venteo_detectado` (WFS, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen** (no llegó a una respuesta: se agotó el tiempo o falló):

```sql
WITH c AS MATERIALIZED (
  SELECT id_concesion,
         CASE WHEN jsonb_typeof(anillo::jsonb->0->0)='array' THEN anillo::jsonb->0 ELSE anillo::jsonb END AS ring
  FROM sig_energia.concesion WHERE anillo IS NOT NULL AND anillo <> ''
),
cv AS MATERIALIZED (
  SELECT id_concesion, ord, (p->>0)::float8 AS x, (p->>1)::float8 AS y
  FROM c, jsonb_array_elements(ring) WITH ORDINALITY t(p, ord)
),
bb AS MATERIALIZED (
  SELECT id_concesion, min(x) minx, max(x) maxx, min(y) miny, max(y) maxy FROM cv GROUP BY id_concesion
),
vd AS MATERIALIZED (
  SELECT DISTINCT round(lon::numeric,3)::float8 lon, round(lat::numeric,3)::float8 lat
  FROM sig_energia.venteo_detectado WHERE fecha >= DATE '2024-01-01'
),
vb AS MATERIALIZED (
  SELECT bb.id_concesion, vd.lon, vd.lat
  FROM vd JOIN bb ON vd.lon BETWEEN bb.minx AND bb.maxx AND vd.lat BETWEEN bb.miny AND bb.maxy
),
conc AS MATERIALIZED (SELECT DISTINCT id_concesion FROM vb),
ce AS MATERIALIZED (
  SELECT a.id_concesion, a.x x1, a.y y1, b.x x2, b.y y2
  FROM cv a JOIN cv b ON a.id_concesion=b.id_concesion AND b.ord=a.ord+1
  WHERE a.id_concesion IN (SELECT id_concesion FROM conc)
),
gl AS MATERIALIZED (
  SELECT g.gml_id, l.lord, l.line
  FROM enargas.gasoducto g,
       jsonb_array_elements(CASE WHEN jsonb_typeof(g.lineas::jsonb->0->0)='array' THEN g.lineas::jsonb ELSE jsonb_build_array(g.lineas::jsonb) END) WITH ORDINALITY l(line, lord)
  WHERE g.lineas IS NOT NULL AND g.lineas <> ''
),
gv AS MATERIALIZED (
  SELECT gml_id, lord, ord, (p->>0)::float8 x, (p->>1)::float8 y
  FROM gl, jsonb_array_elements(line) WITH ORDINALITY t(p, ord)
),
ge AS MATERIALIZED (
  SELECT a.x x1, a.y y1, b.x x2, b.y y2
  FROM gv a JOIN gv b ON a.gml_id=b.gml_id AND a.lord=b.lord AND b.ord=a.ord+1
),
cand AS MATERIALIZED (
  SELECT bb.id_concesion, ge.x1, ge.y1, ge.x2, ge.y2
  FROM bb JOIN conc ON conc.id_concesion=bb.id_concesion
  JOIN ge ON greatest(ge.x1,ge.x2) >= bb.minx-0.15 AND least(ge.x1,ge.x2) <= bb.maxx+0.15
         AND greatest(ge.y1,ge.y2) >= bb.miny-0.12 AND least(ge.y1,ge.y2) <= bb.maxy+0.12
),
dd AS (
  SELECT ce.id_concesion, p.px, p.py, ce.x1, ce.y1, ce.x2, ce.y2
  FROM cand k CROSS JOIN LATERAL (VALUES (k.x1,k.y1),(k.x2,k.y2)) p(px,py)
  JOIN ce ON ce.id_concesion=k.id_concesion
  WHERE p.px BETWEEN least(ce.x1,ce.x2)-0.15 AND greatest(ce.x1,ce.x2)+0.15
    AND p.py BETWEEN least(ce.y1,ce.y2)-0.12 AND greatest(ce.y1,ce.y2)+0.12
  UNION ALL
  SELECT k.id_concesion, cv.x, cv.y, k.x1, k.y1, k.x2, k.y2
  FROM cand k JOIN cv ON cv.id_concesion=k.id_concesion
  WHERE cv.x BETWEEN least(k.x1,k.x2)-0.15 AND greatest(k.x1,k.x2)+0.15
    AND cv.y BETWEEN least(k.y1,k.y2)-0.12 AND greatest(k.y1,k.y2)+0.12
),
dk AS (
  SELECT id_concesion,
    (px-x1)*111.32*cos(radians(py)) ax, (py-y1)*110.574 ay,
    (x2-x1)*111.32*cos(radians(py)) bx, (y2-y1)*110.574 by_
  FROM dd
),
cerca AS MATERIALIZED (
  SELECT DISTINCT id_concesion FROM (
    SELECT id_concesion, ax, ay, bx, by_,
      CASE WHEN bx*bx+by_*by_ = 0 THEN 0
           ELSE greatest(0, least(1, (ax*bx+ay*by_)/(bx*bx+by_*by_))) END t
    FROM dk
  ) s
  WHERE sqrt(power(ax - bx*t, 2) + power(ay - by_*t, 2)) < 10
),
lejos AS MATERIALIZED (
  SELECT id_concesion FROM conc WHERE id_concesion NOT IN (SELECT id_concesion FROM cerca)
),
dentro AS (
  SELECT DISTINCT id_concesion FROM (
    SELECT vb.id_concesion, vb.lon, vb.lat
    FROM vb JOIN lejos l ON l.id_concesion=vb.id_concesion
    JOIN ce ON ce.id_concesion=vb.id_concesion
    WHERE (ce.y1 > vb.lat) <> (ce.y2 > vb.lat)
      AND vb.lon < (ce.x2-ce.x1)*(vb.lat-ce.y1)/(ce.y2-ce.y1)+ce.x1
    GROUP BY vb.id_concesion, vb.lon, vb.lat
    HAVING count(*) % 2 = 1
  ) s
)
SELECT count(*) FROM dentro
```

## e06

> ¿Cuántos posibles venteos detectados por satélite desde el 1 de enero de 2024, dentro del contorno de alguna concesión, caen dentro de un área protegida del Instituto Geográfico Nacional?

**Respuesta de Rastro, a confirmar:** 60

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ❌ 43
- SQL + enlaces de Rastro: ✅ 60
- Con Rastro: ✅ 60

**Diferencia ya revisada por el asistente (e06 (áreas protegidas)):** SQL sin Rastro dio 41–43; Rastro, 60. Se volvió a contar con los contornos originales del IGN, huecos incluidos: 60. El SQL trata las partes de un área protegida con varios polígonos como un solo contorno y el test de paridad se invierte. Resultado: Referencia: 60.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Instituto Geográfico Nacional (IGN) (https://www.ign.gob.ar/): `ign.area_protegida` (WFS del IGN, cargada el 2026-10-20)
- Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS) (https://sig.energia.gob.ar/wfsenergia): `sig_energia.concesion` (WFS, cargada el 2026-10-20); `sig_energia.venteo_detectado` (WFS, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
with v as materialized (
  select gml_id, lon as x, lat as y from sig_energia.venteo_detectado
  where fecha >= date '2024-01-01' and lon is not null and lat is not null
),
cpts as materialized (
  select c.id_concesion as pid, (p->>0)::float8 as lon, (p->>1)::float8 as lat, n
  from sig_energia.concesion c, jsonb_array_elements(c.anillo::jsonb) with ordinality t(p, n)
  where c.anillo is not null and jsonb_typeof(c.anillo::jsonb) = 'array'
),
cedges as materialized (
  select pid, x1, y1, x2, y2, least(y1, y2) as ylo, greatest(y1, y2) as yhi from (
    select pid, lon as x1, lat as y1,
           coalesce(lead(lon) over w, first_value(lon) over w) as x2,
           coalesce(lead(lat) over w, first_value(lat) over w) as y2
    from cpts window w as (partition by pid order by n)) s
  where y1 <> y2
),
cbox as materialized (select pid, min(x1) mnx, max(x1) mxx, min(y1) mny, max(y1) mxy from cedges group by pid),
vc as materialized (
  select v.gml_id, v.x, v.y, b.pid from v join cbox b
  on v.x between b.mnx and b.mxx and v.y between b.mny and b.mxy
),
en_conc as materialized (
  select distinct s.gml_id, s.x, s.y from (
    select vc.gml_id, vc.x, vc.y, vc.pid
    from vc join cedges e on e.pid = vc.pid
     and vc.y > e.ylo and vc.y <= e.yhi
     and vc.x < (e.x2 - e.x1) * (vc.y - e.y1) / (e.y2 - e.y1) + e.x1
    group by vc.gml_id, vc.x, vc.y, vc.pid
    having count(*) % 2 = 1) s
),
apts as materialized (
  select a.gid as pid, r.rn, (p->>0)::float8 as lon, (p->>1)::float8 as lat, n
  from ign.area_protegida a,
       jsonb_array_elements(a.anillos::jsonb) with ordinality r(ring, rn),
       jsonb_array_elements(r.ring) with ordinality t(p, n)
  where a.anillos is not null
),
aedges as materialized (
  select pid, x1, y1, x2, y2, least(y1, y2) as ylo, greatest(y1, y2) as yhi from (
    select pid, lon as x1, lat as y1,
           coalesce(lead(lon) over w, first_value(lon) over w) as x2,
           coalesce(lead(lat) over w, first_value(lat) over w) as y2
    from apts window w as (partition by pid, rn order by n)) s
  where y1 <> y2
),
abox as materialized (select pid, min(x1) mnx, max(x1) mxx, min(y1) mny, max(y1) mxy from aedges group by pid),
ca as materialized (
  select c.gml_id, c.x, c.y, b.pid from en_conc c join abox b
  on c.x between b.mnx and b.mxx and c.y between b.mny and b.mxy
)
select count(distinct gml_id) from (
  select ca.gml_id, ca.pid
  from ca join aedges e on e.pid = ca.pid
   and ca.y > e.ylo and ca.y <= e.yhi
   and ca.x < (e.x2 - e.x1) * (ca.y - e.y1) / (e.y2 - e.y1) + e.x1
  group by ca.gml_id, ca.pid
  having count(*) % 2 = 1) s
```

## e07

> ¿Qué empresas que declaran producción en 2025 tienen un LEI activo en GLEIF cuyo nombre legal es el de la empresa?

**Respuesta de Rastro, a confirmar:** CAPEX S.A.; COMPAÑIA GENERAL DE COMBUSTIBLES; PAMPA ENERGIA S.A.; PAN AMERICAN ENERGY SL; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL; ROCH S.A.; SHELL ARGENTINA S.A.; TECPETROL S.A.; VISTA ENERGY ARGENTINA SAU; YPF S.A.

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ CAPEX S.A.; COMPAÑÍA GENERAL DE COMBUSTIBLES S.A.; PAMPA ENERGIA S.A.; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL S.A.; ROCH S.A.; SHELL ARGENTINA S.A.; VISTA ENERGY ARGENTINA SAU
- SQL + enlaces de Rastro: ✅ CAPEX S.A.; COMPAÑIA GENERAL DE COMBUSTIBLES; PAMPA ENERGIA S.A.; PAN AMERICAN ENERGY SL; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL; ROCH S.A.; SHELL ARGENTINA S.A.; TECPETROL S.A.; VISTA ENERGY ARGENTINA SAU; YPF S.A.
- Con Rastro: ✅ CAPEX S.A.; COMPAÑIA GENERAL DE COMBUSTIBLES; PAMPA ENERGIA S.A.; PAN AMERICAN ENERGY SL; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL; ROCH S.A.; SHELL ARGENTINA S.A.; TECPETROL S.A.; VISTA ENERGY ARGENTINA SAU; YPF S.A.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Capítulo IV: producción y padrón de pozos (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo): `capitulo4.produccion` (producción 2025, cargada el 2026-10-20)
- GLEIF (LEI) (https://www.gleif.org/): `gleif_energia.candidato` (API de GLEIF, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
WITH emp AS (
  SELECT empresa FROM capitulo4.produccion WHERE anio = 2025 AND empresa IS NOT NULL GROUP BY empresa
), e AS (
  SELECT empresa,
    regexp_replace(trim(regexp_replace(upper(translate(empresa,'áéíóúÁÉÍÓÚñÑüÜ','aeiouAEIOUnNuU')),'[^A-Z0-9]+',' ','g')),
      '( S ?A ?U| S ?A| S ?R ?L| S ?E| INC| LLC| LTD| LIMITED| SUCURSAL ARGENTINA| ARGENTINA SUCURSAL)+$','') AS n
  FROM emp
), g AS (
  SELECT DISTINCT
    regexp_replace(trim(regexp_replace(upper(translate(nombre_legal,'áéíóúÁÉÍÓÚñÑüÜ','aeiouAEIOUnNuU')),'[^A-Z0-9]+',' ','g')),
      '( S ?A ?U| S ?A| S ?R ?L| S ?E| INC| LLC| LTD| LIMITED| SUCURSAL ARGENTINA| ARGENTINA SUCURSAL)+$','') AS n
  FROM gleif_energia.candidato
  WHERE upper(estado) = 'ACTIVE' AND lei IS NOT NULL
)
SELECT DISTINCT e.empresa FROM e JOIN g ON e.n = g.n ORDER BY 1
```

## e08

> ¿Cuántas concesiones hay que revisar por venteos, si se revisa una concesión que tiene posibles venteos detectados por satélite desde el 1 de enero de 2024 dentro de su contorno y además cumple al menos una de dos reglas, (a) el gasoducto de transporte de ENARGAS más cercano está a 10 km o más de su contorno, o (b) tiene al menos 20 de esos posibles venteos y no presentó ninguna planilla de venteo de gas (Res. 143/98) desde el 1 de enero de 2022 según el listado de estudios ambientales?

**Respuesta de Rastro, a confirmar:** 45

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ❌ —
- SQL + enlaces de Rastro: ✅ 45
- Con Rastro: ✅ 45

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Estudios ambientales de petróleo y gas (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/actividad-ambiental-petroleo-y-gas): `ambiental.estudio` (listado de estudios ambientales, cargada el 2026-10-20)
- Gasoductos de transporte (ENARGAS) (https://www.enargas.gob.ar/): `enargas.gasoducto` (WFS de la Secretaría de Energía, cargada el 2026-10-20)
- Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS) (https://sig.energia.gob.ar/wfsenergia): `sig_energia.concesion` (WFS, cargada el 2026-10-20); `sig_energia.venteo_detectado` (WFS, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen** (no llegó a una respuesta: se agotó el tiempo o falló):

```sql
WITH c AS MATERIALIZED (
  SELECT id_concesion, areapermisoconcesion, anillo::jsonb a FROM sig_energia.concesion WHERE anillo IS NOT NULL AND anillo <> ''
), v AS MATERIALIZED (
  SELECT c.id_concesion, (p->>0)::float x, (p->>1)::float y, i FROM c, jsonb_array_elements(c.a) WITH ORDINALITY t(p,i)
), n AS MATERIALIZED (SELECT id_concesion, count(*) n FROM v GROUP BY 1),
e AS MATERIALIZED (
  SELECT v1.id_concesion, v1.x x1, v1.y y1, v2.x x2, v2.y y2
  FROM v v1 JOIN n USING (id_concesion)
  JOIN v v2 ON v2.id_concesion = v1.id_concesion AND v2.i = (v1.i % n.n) + 1
  WHERE v1.y <> v2.y
), bb AS MATERIALIZED (
  SELECT id_concesion, min(x) minx, max(x) maxx, min(y) miny, max(y) maxy FROM v GROUP BY 1
), dpts AS MATERIALIZED (
  SELECT lon, lat, count(*) k FROM sig_energia.venteo_detectado
  WHERE fecha >= DATE '2024-01-01' AND lon IS NOT NULL AND lat IS NOT NULL GROUP BY 1, 2
), pts AS MATERIALIZED (
  SELECT d.lon, d.lat, d.k, bb.id_concesion
  FROM dpts d JOIN bb ON d.lon BETWEEN bb.minx AND bb.maxx AND d.lat BETWEEN bb.miny AND bb.maxy
), det AS MATERIALIZED (
  SELECT p.id_concesion, p.lon, p.lat, p.k
  FROM pts p JOIN e ON e.id_concesion = p.id_concesion AND ((e.y1 > p.lat) <> (e.y2 > p.lat))
  WHERE p.lon < (e.x2 - e.x1) * (p.lat - e.y1) / (e.y2 - e.y1) + e.x1
  GROUP BY 1, 2, 3, 4 HAVING count(*) % 2 = 1
), dc AS MATERIALIZED (SELECT id_concesion, sum(k) nv FROM det GROUP BY 1),
gp AS MATERIALIZED (
  SELECT DISTINCT (p->>0)::float x, (p->>1)::float y,
         floor((p->>0)::float * 10)::int cx, floor((p->>1)::float * 10)::int cy
  FROM enargas.gasoducto g, jsonb_array_elements(g.lineas::jsonb) l(line), jsonb_array_elements(line) t(p)
), vc AS MATERIALIZED (
  SELECT v.id_concesion, v.x, v.y, floor(v.x * 10)::int cx, floor(v.y * 10)::int cy
  FROM v JOIN dc USING (id_concesion)
), near AS MATERIALIZED (
  SELECT DISTINCT vc.id_concesion
  FROM vc CROSS JOIN generate_series(-2, 2) ox CROSS JOIN generate_series(-1, 1) oy
  JOIN gp ON gp.cx = vc.cx + ox AND gp.cy = vc.cy + oy
  WHERE sqrt(((gp.x - vc.x) * 111.32 * cos(radians(vc.y)))^2 + ((gp.y - vc.y) * 110.574)^2) < 10
), planilla AS (
  SELECT DISTINCT regexp_replace(lower(translate(concesion, 'ÁÉÍÓÚÜáéíóúüÑñ', 'AEIOUUaeiouuNn')), '[^a-z0-9]', '', 'g') nom
  FROM ambiental.estudio
  WHERE tipo_estudio = 'Inf. de presentación de planillas Aventamiento de Gas(Res143/98)'
    AND fecha_estudio >= DATE '2022-01-01' AND concesion IS NOT NULL
)
SELECT count(*) FROM dc
JOIN c USING (id_concesion)
WHERE dc.id_concesion NOT IN (SELECT id_concesion FROM near)
   OR (dc.nv >= 20 AND regexp_replace(lower(translate(c.areapermisoconcesion, 'ÁÉÍÓÚÜáéíóúüÑñ', 'AEIOUUaeiouuNn')), '[^a-z0-9]', '', 'g') NOT IN (SELECT nom FROM planilla))
```

## e09

> ¿Cuántos cambios de operadora hubo en las concesiones entre 2023 y 2025, si cada mes la operadora de una concesión es la empresa que declara la mayor parte de su producción (petróleo en m³ más gas en miles de m³), solo cuentan las rachas de al menos 3 meses seguidos con la misma operadora, y hay un cambio cada vez que la racha siguiente es de otra empresa? Contar como una sola empresa a Pluspetrol S.A. y Pluspetrol Cuenca Neuquina S.R.L., a CGC Energía SAU y Compañía General de Combustibles S.A., y a GeoPark Argentina Ltd. (Sucursal Argentina) y GeoPark Argentina S.A.

**Respuesta de Rastro, a confirmar:** 64

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ 64
- SQL + enlaces de Rastro: ✅ 64
- Con Rastro: ✅ 64

**Diferencia ya revisada por el asistente (e09 (cambios de operadora)):** SQL sin Rastro dio 64; Rastro y SQL + enlaces, 55 (la referencia). Los 9 cambios de más están en áreas donde cada mes declara una sola empresa, aunque declare cero: Centenario, Don Ruiz, Laguna de los Capones, Llancanelo R, La Paloma - Cerro Alquitrán, Los Toldos II Oeste, Octans-Pegaso, Palermo Aike y Poseidón (en Vega Grande, el mismo cambio, un mes antes). Varios son cesiones conocidas: YPF → Bentia en Don Ruiz, YPF → PCR en Llancanelo R, ExxonMobil → Pluspetrol en Los Toldos II Oeste. Rastro descartaba los meses sin producción («no dicen quién opera») y la pregunta no lo pide. **Error de Rastro**: se corrigió `linking/energia/links.sql` (un mes sin producción cuenta si lo declara una sola empresa; no hay ningún mes sin producción con dos), se rehicieron las dos tablas y se volvieron a ejecutar las consultas guardadas, sin pedir respuestas nuevas: Rastro y SQL + enlaces dan 64. Resultado: Referencia: 64.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Capítulo IV: producción y padrón de pozos (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo): `capitulo4.produccion` (producción 2025, cargada el 2026-10-20); `capitulo4.produccion_historica` (producción 2024, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
with p as (
  select anio, mes, idareapermisoconcesion as c, empresa, prod_pet, prod_gas from capitulo4.produccion_historica where anio between 2023 and 2024
  union all
  select anio, mes, idareapermisoconcesion, empresa, prod_pet, prod_gas from capitulo4.produccion where anio = 2025
), n as (
  select c, anio*12+mes as m,
    case when empresa ilike 'pluspetrol%' then 'PLUSPETROL'
         when empresa ilike 'cgc%' or empresa ilike '%general de combustibles%' then 'CGC'
         when empresa ilike 'geopark%' then 'GEOPARK'
         else empresa end as e,
    coalesce(prod_pet,0)+coalesce(prod_gas,0) as v
  from p where c is not null
), t as (
  select c, m, e, sum(v) as v from n group by c, m, e
), op as (
  select distinct on (c, m) c, m, e from t order by c, m, v desc, e
), g as (
  select c, m, e, m - row_number() over (partition by c, e order by m) as grp from op
), r as (
  select c, e, min(m) as ini, count(*) as largo from g group by c, e, grp
), r3 as (
  select c, e, ini, lag(e) over (partition by c order by ini) as prev from r where largo >= 3
)
select count(*) from r3 where prev is not null and prev <> e
```

## e10

> ¿Cuáles son las 5 empresas que declararon más gas de shale en 2025 (producción cuyo subtipo de recurso es shale, gas en miles de m³), contando como una sola empresa a Pluspetrol S.A. y Pluspetrol Cuenca Neuquina S.R.L.?

**Respuesta de Rastro, a confirmar:** YPF S.A.; TECPETROL S.A.; PLUSPETROL; TOTAL AUSTRAL S.A.; PAMPA ENERGIA S.A.

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ YPF S.A.; TECPETROL S.A.; PLUSPETROL S.A.; TOTAL AUSTRAL S.A.; PAMPA ENERGIA S.A.
- SQL + enlaces de Rastro: ✅ YPF S.A.; TECPETROL S.A.; PLUSPETROL; TOTAL AUSTRAL S.A.; PAMPA ENERGIA S.A.
- Con Rastro: ✅ YPF S.A.; TECPETROL S.A.; PLUSPETROL; TOTAL AUSTRAL S.A.; PAMPA ENERGIA S.A.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Capítulo IV: producción y padrón de pozos (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo): `capitulo4.produccion` (producción 2025, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
SELECT empresa FROM (SELECT CASE WHEN upper(empresa) LIKE 'PLUSPETROL%' THEN 'PLUSPETROL S.A.' ELSE empresa END AS empresa, sum(prod_gas) AS gas FROM capitulo4.produccion WHERE anio = 2025 AND upper(trim(sub_tipo_recurso)) = 'SHALE' GROUP BY 1) t ORDER BY gas DESC NULLS LAST LIMIT 5
```
