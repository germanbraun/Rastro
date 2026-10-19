-- Los números «sin Rastro» de la demo de petróleo y gas: lo que da un SQL directo sobre las
-- tablas de cada fuente, tal como vienen. Se corren con:
--   docker compose exec -T postgres psql -U rastro -f - < layer/energia/sin-rastro.sql

-- 1. Integración: petróleo de 2025 por empresa, sumando por quien declara la producción
SELECT empresa, round(sum(prod_pet) / 1e6, 2) AS millones_m3
FROM capitulo4.produccion WHERE empresa ILIKE '%YPF%' OR empresa ILIKE '%PETRONAS%' GROUP BY 1;

-- 2. Trazabilidad: ¿cuántos pozos con producción en 2025 opera YPF? Según el padrón y según las declaraciones
SELECT count(*) FILTER (WHERE p.empresa ILIKE 'YPF%') AS segun_padron,
       count(*) FILTER (WHERE u.empresa ILIKE 'YPF%') AS segun_declaraciones
FROM (SELECT DISTINCT ON (idpozo) idpozo, empresa FROM capitulo4.produccion ORDER BY idpozo, mes DESC) u
LEFT JOIN capitulo4.pozo p USING (idpozo);

-- 3. Cruce con mapas: posibles venteos detectados por satélite desde 2024, por provincia (la capa no dice más)
SELECT provincia, count(*) FROM sig_energia.venteo_detectado WHERE fecha >= '2024-01-01' GROUP BY 1 ORDER BY 2 DESC;
