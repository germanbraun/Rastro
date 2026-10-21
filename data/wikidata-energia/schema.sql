-- Enriquecimiento con Wikidata, materializado: lo que Wikidata sabe de las empresas de petróleo y gas con LEI,
-- tal como respondió el día de la consulta. Sin DROP: el enlazador de petróleo y gas corre este archivo para crear
-- la tabla vacía si todavía no se cargó; el cargador (load.py) la vacía antes de cargar.
CREATE SCHEMA IF NOT EXISTS wikidata_energia;
CREATE TABLE IF NOT EXISTS wikidata_energia.empresa (
    lei text, wikidata text,             -- el LEI que se buscó y la entidad de Wikidata que lo tiene (P1278)
    sede text, bolsa text, duenio text, sitio text,   -- P159, P414, P749 o P127, P856 (rótulos en español)
    consultado date                      -- el día en que respondió Wikidata
);
