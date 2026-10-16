-- Copia de MeSH en Postgres: solo descriptores y jerarquía. Así Ontop responde
-- todas las preguntas solo, sin federar con GraphDB.
DROP SCHEMA IF EXISTS mesh CASCADE;
CREATE SCHEMA mesh;

CREATE TABLE mesh.descriptor (
    id      text PRIMARY KEY,   -- por ejemplo D001943
    label   text NOT NULL       -- en inglés, como lo usa AACT: Breast Neoplasms
);

CREATE TABLE mesh.broader (
    id          text NOT NULL REFERENCES mesh.descriptor,
    broader_id  text NOT NULL REFERENCES mesh.descriptor,
    PRIMARY KEY (id, broader_id)
);

CREATE INDEX ON mesh.descriptor (label);
CREATE INDEX ON mesh.broader (broader_id);

-- Cada descriptor con todos sus ancestros, incluido él mismo. Ontop no soporta
-- caminos de largo arbitrario (broaderDescriptor*), así que se precalculan:
-- "está dentro de Breast Neoplasms" es una sola fila por subtipo. (No se llama
-- within porque WITHIN es palabra reservada de SQL y Ontop no la acepta.)
CREATE TABLE mesh.ancestor (
    id          text NOT NULL REFERENCES mesh.descriptor,
    ancestor_id text NOT NULL REFERENCES mesh.descriptor,
    PRIMARY KEY (id, ancestor_id)
);
CREATE INDEX ON mesh.ancestor (ancestor_id);
