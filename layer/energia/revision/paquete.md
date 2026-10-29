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
WITH partes AS (SELECT DISTINCT c.id_concesion, upper(trim(substring(p from '^(.*):'))) AS empresa, replace(regexp_replace(substring(p from ':([^:]*)$'), '[^0-9,.]', '', 'g'), ',', '.') AS pct FROM sig_energia.concesion c CROSS JOIN LATERAL unnest(string_to_array(c.participacion, '<br>')) AS p WHERE p LIKE '%:%'), ypf AS (SELECT id_concesion, sum(pct::numeric) AS pct FROM partes WHERE empresa ~ '^YPF\s*(S\.?\s*A\.?)?$' AND pct ~ '^[0-9]+(\.[0-9]+)?$' GROUP BY id_concesion) SELECT sum(pr.prod_pet * y.pct / 100) AS petroleo_ypf_m3 FROM capitulo4.produccion pr JOIN ypf y ON y.id_concesion = pr.idareapermisoconcesion WHERE pr.anio = 2025
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
WITH ultimo AS (SELECT idpozo, MAX(mes) AS mes FROM capitulo4.produccion WHERE anio = 2025 GROUP BY idpozo) SELECT COUNT(DISTINCT p.idpozo) FROM capitulo4.produccion p JOIN ultimo u ON u.idpozo = p.idpozo AND u.mes = p.mes WHERE p.anio = 2025 AND upper(trim(p.empresa)) ~ '^YPF([ .,]|$)'
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
WITH c AS (SELECT row_number() OVER () AS rid, id_concesion, areapermisoconcesion, anillo::jsonb AS ring FROM sig_energia.concesion WHERE anillo IS NOT NULL AND anillo <> ''), v AS (SELECT c.rid, c.areapermisoconcesion, e.i, (e.p->>0)::float8 AS x, (e.p->>1)::float8 AS y FROM c CROSS JOIN LATERAL jsonb_array_elements(c.ring) WITH ORDINALITY AS e(p, i) WHERE jsonb_typeof(e.p) = 'array'), edges AS (SELECT rid, areapermisoconcesion, x AS x1, y AS y1, COALESCE(lead(x) OVER w, first_value(x) OVER w) AS x2, COALESCE(lead(y) OVER w, first_value(y) OVER w) AS y2 FROM v WINDOW w AS (PARTITION BY rid ORDER BY i ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)), bbox AS (SELECT rid, areapermisoconcesion, min(x) AS minx, max(x) AS maxx, min(y) AS miny, max(y) AS maxy FROM v GROUP BY rid, areapermisoconcesion), pts AS (SELECT gml_id, lon, lat FROM sig_energia.venteo_detectado WHERE fecha >= DATE '2024-01-01' AND lon IS NOT NULL AND lat IS NOT NULL), cand AS (SELECT b.rid, b.areapermisoconcesion, p.gml_id, p.lon, p.lat FROM bbox b JOIN pts p ON p.lon BETWEEN b.minx AND b.maxx AND p.lat BETWEEN b.miny AND b.maxy), inside AS (SELECT cand.rid, cand.areapermisoconcesion, cand.gml_id FROM cand JOIN edges e ON e.rid = cand.rid WHERE ((e.y1 > cand.lat) <> (e.y2 > cand.lat)) AND cand.lon < (e.x2 - e.x1) * (cand.lat - e.y1) / (e.y2 - e.y1) + e.x1 GROUP BY cand.rid, cand.areapermisoconcesion, cand.gml_id HAVING count(*) % 2 = 1) SELECT areapermisoconcesion FROM inside GROUP BY rid, areapermisoconcesion ORDER BY count(DISTINCT gml_id) DESC LIMIT 5
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
SELECT empresa_unificada FROM (SELECT CASE WHEN upper(empresa) LIKE 'PLUSPETROL%' THEN 'PLUSPETROL S.A.' ELSE empresa END AS empresa_unificada, SUM(prod_pet) AS total FROM capitulo4.produccion WHERE anio = 2025 AND (upper(tipo_de_recurso) = 'NO CONVENCIONAL' OR upper(sub_tipo_recurso) IN ('SHALE', 'TIGHT')) GROUP BY 1) t ORDER BY total DESC NULLS LAST LIMIT 5
```

## e05

> ¿Cuántas concesiones tienen al menos un posible venteo detectado por satélite desde el 1 de enero de 2024 dentro de su contorno y tienen el gasoducto de transporte de ENARGAS más cercano a 10 km o más de su contorno?

**Respuesta de Rastro, a confirmar:** 33

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ❌ 36
- SQL + enlaces de Rastro: ✅ 33
- Con Rastro: ✅ 33

**Diferencia ya revisada por el asistente (e05 (gasoductos)):** SQL + enlaces dio 33 en una forma; la referencia daba 29. Rastro no tenía distancia para las concesiones sin ningún gasoducto a menos de ~100 km, y la pregunta las incluye. **Error de Rastro**: se corrigió `linking/energia/link.py` (si no hay gasoducto cerca, se mide contra todos) y se volvieron a ejecutar todas las consultas guardadas. Resultado: Referencia: 33.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Gasoductos de transporte (ENARGAS) (https://www.enargas.gob.ar/): `enargas.gasoducto` (WFS de la Secretaría de Energía, cargada el 2026-10-20)
- Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS) (https://sig.energia.gob.ar/wfsenergia): `sig_energia.concesion` (WFS, cargada el 2026-10-20); `sig_energia.venteo_detectado` (WFS, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
WITH c AS (SELECT id_concesion, anillo::jsonb AS a FROM sig_energia.concesion WHERE anillo IS NOT NULL AND anillo <> ''), cv AS (SELECT c.id_concesion, (t.p->>0)::float8 AS x, (t.p->>1)::float8 AS y, t.i FROM c, jsonb_array_elements(c.a) WITH ORDINALITY AS t(p, i)), bb AS (SELECT id_concesion, MIN(x) AS xmin, MAX(x) AS xmax, MIN(y) AS ymin, MAX(y) AS ymax FROM cv GROUP BY id_concesion), ce AS (SELECT id_concesion, x AS x1, y AS y1, COALESCE(LEAD(x) OVER w, FIRST_VALUE(x) OVER w) AS x2, COALESCE(LEAD(y) OVER w, FIRST_VALUE(y) OVER w) AS y2 FROM cv WINDOW w AS (PARTITION BY id_concesion ORDER BY i ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)), v AS (SELECT gml_id, lon, lat FROM sig_energia.venteo_detectado WHERE fecha >= DATE '2024-01-01' AND lon IS NOT NULL AND lat IS NOT NULL), vb AS (SELECT bb.id_concesion, v.gml_id, v.lon, v.lat FROM bb JOIN v ON v.lon BETWEEN bb.xmin AND bb.xmax AND v.lat BETWEEN bb.ymin AND bb.ymax), dentro AS (SELECT vb.id_concesion, vb.gml_id FROM vb JOIN ce ON ce.id_concesion = vb.id_concesion AND ((ce.y1 > vb.lat) <> (ce.y2 > vb.lat)) AND vb.lon < (ce.x2 - ce.x1) * (vb.lat - ce.y1) / (ce.y2 - ce.y1) + ce.x1 GROUP BY vb.id_concesion, vb.gml_id HAVING COUNT(*) % 2 = 1), cand AS (SELECT DISTINCT id_concesion FROM dentro), gp AS (SELECT g.gml_id, l.j, (t.p->>0)::float8 AS x, (t.p->>1)::float8 AS y, t.i FROM enargas.gasoducto g, jsonb_array_elements(g.lineas::jsonb) WITH ORDINALITY AS l(line, j), jsonb_array_elements(l.line) WITH ORDINALITY AS t(p, i) WHERE g.lineas IS NOT NULL AND g.lineas <> ''), gs AS (SELECT x AS x1, y AS y1, COALESCE(LEAD(x) OVER w, x) AS x2, COALESCE(LEAD(y) OVER w, y) AS y2 FROM gp WINDOW w AS (PARTITION BY gml_id, j ORDER BY i)), cerca AS (SELECT bb.id_concesion, gs.x1, gs.y1, gs.x2, gs.y2 FROM bb JOIN cand ON cand.id_concesion = bb.id_concesion JOIN gs ON GREATEST(gs.x1, gs.x2) >= bb.xmin - 0.2 AND LEAST(gs.x1, gs.x2) <= bb.xmax + 0.2 AND GREATEST(gs.y1, gs.y2) >= bb.ymin - 0.15 AND LEAST(gs.y1, gs.y2) <= bb.ymax + 0.15), d AS (SELECT cv.id_concesion, (cv.x - s.x1) * 111.32 * cos(radians(cv.y)) AS px, (cv.y - s.y1) * 110.574 AS py, (s.x2 - s.x1) * 111.32 * cos(radians(cv.y)) AS dx, (s.y2 - s.y1) * 110.574 AS dy FROM cerca s JOIN cv ON cv.id_concesion = s.id_concesion), dd AS (SELECT id_concesion, px, py, dx, dy, GREATEST(0, LEAST(1, COALESCE((px * dx + py * dy) / NULLIF(dx * dx + dy * dy, 0), 0))) AS t FROM d), cercanas AS (SELECT id_concesion FROM dd GROUP BY id_concesion HAVING MIN(sqrt(power(px - t * dx, 2) + power(py - t * dy, 2))) < 10) SELECT COUNT(*) FROM cand WHERE id_concesion NOT IN (SELECT id_concesion FROM cercanas)
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
WITH v AS MATERIALIZED (SELECT gml_id, lon, lat FROM sig_energia.venteo_detectado WHERE fecha >= DATE '2024-01-01' AND lon IS NOT NULL AND lat IS NOT NULL), cpts AS MATERIALIZED (SELECT c.id_concesion AS pid, p.ord, (p.pt->>0)::float8 AS x, (p.pt->>1)::float8 AS y FROM sig_energia.concesion c CROSS JOIN LATERAL jsonb_array_elements(c.anillo::jsonb) WITH ORDINALITY AS p(pt, ord) WHERE c.anillo IS NOT NULL AND c.anillo <> ''), cbox AS MATERIALIZED (SELECT pid, min(x) AS minx, max(x) AS maxx, min(y) AS miny, max(y) AS maxy FROM cpts GROUP BY pid), cedges AS MATERIALIZED (SELECT pid, x AS x1, y AS y1, COALESCE(lead(x) OVER w, first_value(x) OVER w) AS x2, COALESCE(lead(y) OVER w, first_value(y) OVER w) AS y2 FROM cpts WINDOW w AS (PARTITION BY pid ORDER BY ord)), ccand AS MATERIALIZED (SELECT v.gml_id, v.lon, v.lat, b.pid FROM v JOIN cbox b ON v.lon BETWEEN b.minx AND b.maxx AND v.lat BETWEEN b.miny AND b.maxy), en_conc AS MATERIALIZED (SELECT DISTINCT gml_id, lon, lat FROM (SELECT k.gml_id, k.lon, k.lat, k.pid FROM ccand k JOIN cedges e ON e.pid = k.pid AND ((e.y1 > k.lat) <> (e.y2 > k.lat)) AND k.lon < (e.x2 - e.x1) * (k.lat - e.y1) / (e.y2 - e.y1) + e.x1 GROUP BY k.gml_id, k.lon, k.lat, k.pid HAVING count(*) % 2 = 1) s), apts AS MATERIALIZED (SELECT a.gid || '-' || r.rn AS pid, p.ord, (p.pt->>0)::float8 AS x, (p.pt->>1)::float8 AS y FROM ign.area_protegida a CROSS JOIN LATERAL jsonb_array_elements(a.anillos::jsonb) WITH ORDINALITY AS r(ring, rn) CROSS JOIN LATERAL jsonb_array_elements(r.ring) WITH ORDINALITY AS p(pt, ord) WHERE a.anillos IS NOT NULL AND a.anillos <> ''), abox AS MATERIALIZED (SELECT pid, min(x) AS minx, max(x) AS maxx, min(y) AS miny, max(y) AS maxy FROM apts GROUP BY pid), acand AS MATERIALIZED (SELECT c.gml_id, c.lon, c.lat, b.pid FROM en_conc c JOIN abox b ON c.lon BETWEEN b.minx AND b.maxx AND c.lat BETWEEN b.miny AND b.maxy), aedges AS MATERIALIZED (SELECT pid, x AS x1, y AS y1, COALESCE(lead(x) OVER w, first_value(x) OVER w) AS x2, COALESCE(lead(y) OVER w, first_value(y) OVER w) AS y2 FROM apts WHERE pid IN (SELECT pid FROM acand) WINDOW w AS (PARTITION BY pid ORDER BY ord)), en_area AS (SELECT DISTINCT gml_id FROM (SELECT k.gml_id, k.pid FROM acand k JOIN aedges e ON e.pid = k.pid AND ((e.y1 > k.lat) <> (e.y2 > k.lat)) AND k.lon < (e.x2 - e.x1) * (k.lat - e.y1) / (e.y2 - e.y1) + e.x1 GROUP BY k.gml_id, k.pid HAVING count(*) % 2 = 1) s) SELECT count(*) AS venteos FROM en_area
```

## e07

> ¿Qué empresas que declaran producción en 2025 tienen un LEI activo en GLEIF cuyo nombre legal es el de la empresa?

**Respuesta de Rastro, a confirmar:** CAPEX S.A.; COMPAÑIA GENERAL DE COMBUSTIBLES; PAMPA ENERGIA S.A.; PAN AMERICAN ENERGY SL; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL; ROCH S.A.; SHELL ARGENTINA S.A.; TECPETROL S.A.; VISTA ENERGY ARGENTINA SAU; YPF S.A.

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ CAPEX S.A.; COMPAÑÍA GENERAL DE COMBUSTIBLES S.A.; PAMPA ENERGIA S.A.; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL S.A.; ROCH S.A.; SHELL ARGENTINA S.A.; TECPETROL S.A.; VISTA ENERGY ARGENTINA SAU; YPF S.A.
- SQL + enlaces de Rastro: ✅ CAPEX S.A.; COMPAÑIA GENERAL DE COMBUSTIBLES; PAMPA ENERGIA S.A.; PAN AMERICAN ENERGY SL; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL; ROCH S.A.; SHELL ARGENTINA S.A.; TECPETROL S.A.; VISTA ENERGY ARGENTINA SAU; YPF S.A.
- Con Rastro: ✅ CAPEX S.A.; COMPAÑIA GENERAL DE COMBUSTIBLES; PAMPA ENERGIA S.A.; PAN AMERICAN ENERGY SL; PECOM SERVICIOS ENERGIA SAU; PETROQUIMICA COMODORO RIVADAVIA S.A.; PLUSPETROL; ROCH S.A.; SHELL ARGENTINA S.A.; TECPETROL S.A.; VISTA ENERGY ARGENTINA SAU; YPF S.A.

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Capítulo IV: producción y padrón de pozos (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo): `capitulo4.produccion` (producción 2025, cargada el 2026-10-20)
- GLEIF (LEI) (https://www.gleif.org/): `gleif_energia.candidato` (API de GLEIF, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
WITH emp AS (SELECT DISTINCT empresa, regexp_replace(regexp_replace(upper(translate(empresa, 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')), '[^A-Z0-9]', '', 'g'), '(SOCIEDADANONIMA|SAU|SA|SRL|INC|LTD|LLC|SUCURSALARGENTINA)+$', '') AS n FROM capitulo4.produccion WHERE anio = 2025 AND empresa IS NOT NULL), gl AS (SELECT DISTINCT nombre_legal, regexp_replace(regexp_replace(upper(translate(nombre_legal, 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')), '[^A-Z0-9]', '', 'g'), '(SOCIEDADANONIMA|SAU|SA|SRL|INC|LTD|LLC|SUCURSALARGENTINA)+$', '') AS n FROM gleif_energia.candidato WHERE upper(estado) = 'ACTIVE' AND lei IS NOT NULL) SELECT DISTINCT emp.empresa FROM emp JOIN gl ON emp.n = gl.n AND emp.n <> '' ORDER BY emp.empresa
```

## e08

> ¿Cuántas concesiones hay que revisar por venteos, si se revisa una concesión que tiene posibles venteos detectados por satélite desde el 1 de enero de 2024 dentro de su contorno y además cumple al menos una de dos reglas, (a) el gasoducto de transporte de ENARGAS más cercano está a 10 km o más de su contorno, o (b) tiene al menos 20 de esos posibles venteos y no presentó ninguna planilla de venteo de gas (Res. 143/98) desde el 1 de enero de 2022 según el listado de estudios ambientales?

**Respuesta de Rastro, a confirmar:** 45

**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):

- Sin Rastro (SQL): ✅ 47
- SQL + enlaces de Rastro: ✅ 45
- Con Rastro: ✅ 45

**Fuentes** (las tablas que lee la consulta sin Rastro):

- Estudios ambientales de petróleo y gas (Secretaría de Energía) (http://datos.energia.gob.ar/dataset/actividad-ambiental-petroleo-y-gas): `ambiental.estudio` (listado de estudios ambientales, cargada el 2026-10-20)
- Gasoductos de transporte (ENARGAS) (https://www.enargas.gob.ar/): `enargas.gasoducto` (WFS de la Secretaría de Energía, cargada el 2026-10-20)
- Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS) (https://sig.energia.gob.ar/wfsenergia): `sig_energia.concesion` (WFS, cargada el 2026-10-20); `sig_energia.venteo_detectado` (WFS, cargada el 2026-10-20)

**Consulta de partida sobre las fuentes tal como vienen**:

```sql
WITH c AS MATERIALIZED (SELECT id_concesion, areapermisoconcesion AS nombre, anillo::jsonb AS a FROM sig_energia.concesion WHERE anillo IS NOT NULL AND anillo <> ''), cv AS MATERIALIZED (SELECT c.id_concesion, t.ord, (t.p->>0)::float8 AS x, (t.p->>1)::float8 AS y FROM c, jsonb_array_elements(c.a) WITH ORDINALITY AS t(p, ord) WHERE jsonb_typeof(t.p) = 'array' AND jsonb_typeof(t.p->0) = 'number'), cl AS (SELECT id_concesion, max(ord) AS mx FROM cv GROUP BY 1), ce AS MATERIALIZED (SELECT a.id_concesion, a.x AS x1, a.y AS y1, b.x AS x2, b.y AS y2 FROM cv a JOIN cv b ON b.id_concesion = a.id_concesion AND b.ord = a.ord + 1 UNION ALL SELECT a.id_concesion, a.x, a.y, b.x, b.y FROM cl JOIN cv a ON a.id_concesion = cl.id_concesion AND a.ord = cl.mx JOIN cv b ON b.id_concesion = cl.id_concesion AND b.ord = 1), ceb AS MATERIALIZED (SELECT ce.id_concesion, ce.x1, ce.y1, ce.x2, ce.y2, b FROM ce, generate_series(floor(least(ce.y1, ce.y2) / 0.05)::int, floor(greatest(ce.y1, ce.y2) / 0.05)::int) AS b WHERE ce.y1 <> ce.y2), bb AS MATERIALIZED (SELECT id_concesion, min(x) AS minx, max(x) AS maxx, min(y) AS miny, max(y) AS maxy FROM cv GROUP BY 1), det AS MATERIALIZED (SELECT gml_id, lon, lat FROM sig_energia.venteo_detectado WHERE fecha >= DATE '2024-01-01' AND lon IS NOT NULL AND lat IS NOT NULL), dentro AS (SELECT e.id_concesion, d.gml_id FROM det d JOIN bb ON d.lon BETWEEN bb.minx AND bb.maxx AND d.lat BETWEEN bb.miny AND bb.maxy JOIN ceb e ON e.id_concesion = bb.id_concesion AND e.b = floor(d.lat / 0.05)::int WHERE ((e.y1 > d.lat) <> (e.y2 > d.lat)) AND d.lon < (e.x2 - e.x1) * (d.lat - e.y1) / (e.y2 - e.y1) + e.x1 GROUP BY 1, 2 HAVING count(*) % 2 = 1), nv AS MATERIALIZED (SELECT id_concesion, count(DISTINCT gml_id) AS n FROM dentro GROUP BY 1), bbn AS MATERIALIZED (SELECT bb.* FROM bb JOIN nv USING (id_concesion)), cp AS MATERIALIZED (SELECT e.id_concesion, e.x1 + (e.x2 - e.x1) * i::float8 / k.n AS x, e.y1 + (e.y2 - e.y1) * i::float8 / k.n AS y FROM ce e JOIN nv USING (id_concesion) CROSS JOIN LATERAL (SELECT greatest(1, ceil(sqrt(power(e.x2 - e.x1, 2) + power(e.y2 - e.y1, 2)) / 0.02))::int AS n) k CROSS JOIN LATERAL generate_series(0, k.n) AS i), gv AS MATERIALIZED (SELECT g.gml_id, l.li, q.pi, (q.p->>0)::float8 AS x, (q.p->>1)::float8 AS y FROM enargas.gasoducto g, jsonb_array_elements(g.lineas::jsonb) WITH ORDINALITY AS l(line, li), jsonb_array_elements(l.line) WITH ORDINALITY AS q(p, pi) WHERE g.lineas IS NOT NULL AND g.lineas <> '' AND jsonb_typeof(l.line) = 'array' AND jsonb_typeof(q.p) = 'array'), ge AS MATERIALIZED (SELECT a.x AS x1, a.y AS y1, b.x AS x2, b.y AS y2 FROM gv a JOIN gv b ON b.gml_id = a.gml_id AND b.li = a.li AND b.pi = a.pi + 1), gp0 AS (SELECT s.x1 + (s.x2 - s.x1) * i::float8 / k.n AS x, s.y1 + (s.y2 - s.y1) * i::float8 / k.n AS y FROM ge s CROSS JOIN LATERAL (SELECT greatest(1, ceil(sqrt(power(s.x2 - s.x1, 2) + power(s.y2 - s.y1, 2)) / 0.02))::int AS n) k CROSS JOIN LATERAL generate_series(0, k.n) AS i UNION ALL SELECT x, y FROM gv), gp AS MATERIALIZED (SELECT row_number() OVER () AS gid, x, y, floor(x / 0.1)::int AS gx, floor(y / 0.1)::int AS gy FROM gp0), off AS (SELECT dx, dy FROM generate_series(-2, 2) AS dx, generate_series(-1, 1) AS dy), cerca AS (SELECT DISTINCT cp.id_concesion FROM cp CROSS JOIN off JOIN gp ON gp.gx = floor(cp.x / 0.1)::int + off.dx AND gp.gy = floor(cp.y / 0.1)::int + off.dy WHERE sqrt(power((gp.x - cp.x) * 111.32 * cos(radians(cp.y)), 2) + power((gp.y - cp.y) * 111.32, 2)) < 10), adentro AS (SELECT DISTINCT id_concesion FROM (SELECT e.id_concesion, g.gid FROM gp g JOIN bbn ON g.x BETWEEN bbn.minx AND bbn.maxx AND g.y BETWEEN bbn.miny AND bbn.maxy JOIN ceb e ON e.id_concesion = bbn.id_concesion AND e.b = floor(g.y / 0.05)::int WHERE ((e.y1 > g.y) <> (e.y2 > g.y)) AND g.x < (e.x2 - e.x1) * (g.y - e.y1) / (e.y2 - e.y1) + e.x1 GROUP BY 1, 2 HAVING count(*) % 2 = 1) z), pl AS (SELECT DISTINCT regexp_replace(translate(lower(concesion), 'áéíóúüñ', 'aeiouun'), '[^a-z0-9]', '', 'g') AS k FROM ambiental.estudio WHERE tipo_estudio = 'Inf. de presentación de planillas Aventamiento de Gas(Res143/98)' AND fecha_estudio >= DATE '2022-01-01' AND concesion IS NOT NULL), cn AS (SELECT DISTINCT id_concesion, regexp_replace(translate(lower(nombre), 'áéíóúüñ', 'aeiouun'), '[^a-z0-9]', '', 'g') AS k FROM c) SELECT count(DISTINCT nv.id_concesion) FROM nv WHERE (nv.id_concesion NOT IN (SELECT id_concesion FROM cerca) AND nv.id_concesion NOT IN (SELECT id_concesion FROM adentro)) OR (nv.n >= 20 AND NOT EXISTS (SELECT 1 FROM cn JOIN pl ON pl.k = cn.k WHERE cn.id_concesion = nv.id_concesion))
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
WITH base AS (SELECT anio, mes, idareapermisoconcesion AS conc, empresa, prod_pet, prod_gas FROM capitulo4.produccion_historica WHERE anio BETWEEN 2023 AND 2024 UNION ALL SELECT anio, mes, idareapermisoconcesion, empresa, prod_pet, prod_gas FROM capitulo4.produccion WHERE anio = 2025), norm AS (SELECT anio, mes, conc, CASE WHEN upper(empresa) LIKE '%PLUSPETROL%' THEN 'PLUSPETROL' WHEN upper(empresa) LIKE '%GENERAL DE COMBUSTIBLES%' OR upper(trim(empresa)) LIKE 'CGC%' THEN 'CGC' WHEN upper(empresa) LIKE '%GEOPARK%' THEN 'GEOPARK' ELSE upper(trim(empresa)) END AS emp, COALESCE(prod_pet,0) + COALESCE(prod_gas,0) AS vol FROM base WHERE conc IS NOT NULL AND empresa IS NOT NULL), por_emp AS (SELECT conc, anio*12 + mes AS idx, emp, SUM(vol) AS vol FROM norm GROUP BY conc, anio*12 + mes, emp), ranked AS (SELECT conc, idx, emp, ROW_NUMBER() OVER (PARTITION BY conc, idx ORDER BY vol DESC, emp) AS rn FROM por_emp), op AS (SELECT conc, idx, emp FROM ranked WHERE rn = 1), islas AS (SELECT conc, emp, idx, idx - ROW_NUMBER() OVER (PARTITION BY conc, emp ORDER BY idx) AS grp FROM op), rachas AS (SELECT conc, emp, MIN(idx) AS inicio, COUNT(*) AS largo FROM islas GROUP BY conc, emp, grp HAVING COUNT(*) >= 3), seq AS (SELECT conc, emp, LAG(emp) OVER (PARTITION BY conc ORDER BY inicio) AS prev FROM rachas) SELECT COUNT(*) AS cambios FROM seq WHERE prev IS NOT NULL AND prev <> emp
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
SELECT empresa_unificada FROM (SELECT CASE WHEN upper(trim(empresa)) LIKE 'PLUSPETROL%' THEN 'PLUSPETROL S.A.' ELSE trim(empresa) END AS empresa_unificada, SUM(prod_gas) AS gas FROM capitulo4.produccion WHERE anio = 2025 AND upper(trim(sub_tipo_recurso)) = 'SHALE' GROUP BY 1) t ORDER BY gas DESC NULLS LAST LIMIT 5
```
