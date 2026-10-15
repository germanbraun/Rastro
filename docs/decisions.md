# Decisiones

## 2026-10-15 — Área terapéutica: oncología

Mantiene los volúmenes manejables en una laptop, hay abundantes ensayos en AACT y targets en ChEMBL, y los ejemplos son fáciles de contar en una demo comercial.

## 2026-10-15 — Triplestore: GraphDB Free

Rastro se construye de forma independiente, sobre GraphDB Free. Por usar estándares (RDF, R2RML, SPARQL), se puede conectar después a otras plataformas de grafos de conocimiento sin rehacer ontología, mapeos ni datos.

## 2026-10-15 — Registro de fuentes en Postgres y puertos locales

`rastro_meta.source` y `rastro_meta.load_run` registran cada fuente (licencia incluida) y cada carga. Ontop ya expone las fuentes como `:DataSource`: es la base de la marca de procedencia por celda de la Fase 4 y del linaje PROV-O de la Fase 7.

Puertos por defecto 5434 (Postgres) y 7210 (GraphDB) para no chocar con un Postgres local ni con otra GraphDB local. GraphDB va sin inferencia (ruleset `empty`): la jerarquía de MeSH se recorre con property paths.
