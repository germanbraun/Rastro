# Decisiones

## 2026-10-15 — Área terapéutica: oncología

Mantiene los volúmenes manejables en una laptop, hay abundantes ensayos en AACT y targets en ChEMBL, y los ejemplos son fáciles de contar en una demo comercial.

## 2026-10-15 — Triplestore: GraphDB Free

Rastro se construye de forma independiente, sobre GraphDB Free. Por usar estándares (RDF, R2RML, SPARQL), se puede conectar después a otras plataformas de grafos de conocimiento sin rehacer ontología, mapeos ni datos.

## 2026-10-15 — Registro de fuentes en Postgres y puertos locales

`rastro_meta.source` y `rastro_meta.load_run` registran cada fuente (licencia incluida) y cada carga. Ontop ya expone las fuentes como `:DataSource`: es la base de la marca de procedencia por celda de la Fase 4 y del linaje PROV-O de la Fase 7.

Puertos por defecto 5434 (Postgres) y 7210 (GraphDB) para no chocar con un Postgres local ni con otra GraphDB local. GraphDB va sin inferencia (ruleset `empty`): la jerarquía de MeSH se recorre con property paths.

## 2026-10-16 — Recorte de AACT a oncología

Se cargan los estudios con algún término de condición bajo *Neoplasms* (MeSH C04) en `browse_conditions`, que ya incluye los ancestros de cada término. El criterio sale de la jerarquía y no de buscar texto, así que es reproducible y explicable.

Se extrae de la base de AACT en la nube (cuenta gratuita) y no del snapshot completo de varios GB. El snapshot sigue como alternativa (`AACT_DUMP`).

Carga del 2026-10-16: 106.483 estudios (83.680 intervencionales), 13 tablas, 4,0 M filas, 1,2 GB. Sin `facilities` ni `outcomes` por volumen; se suman si una pregunta de competencia las necesita.

Para Rastro Lab hay 23.898 ensayos intervencionales con fármaco completados, contra 7.019 terminados y 2.201 retirados: alcanza para la variable objetivo de la Fase 5.

## 2026-10-16 — Subconjunto de ChEMBL desde la API, por familia de moléculas

Se cargan las familias de moléculas (padre y sales) con alguna indicación bajo *Neoplasms* (MeSH C04, 703 descriptores consultados al SPARQL de NLM), con todas sus indicaciones, mecanismos, targets y componentes. Es el mismo criterio que el recorte de AACT.

- **API y no dump:** el dump de ChEMBL 37 pesa 2 GB comprimido y mucho más restaurado, para quedarnos con 270 mil filas. La API da la versión exacta (`ChEMBL_37`), que queda en `rastro_meta.load_run`.
- **Por familia:** ChEMBL registra indicaciones y mecanismos tanto sobre la molécula padre como sobre sus sales (el mecanismo de imatinib está en el mesilato). La resolución de entidades de la Fase 2 trabaja a nivel padre (`parent_chembl_id`).
- **Tablas con nombres de ChEMBL:** se respetan nombres de tablas y columnas del esquema original, pero las claves son los ChEMBL ID porque la API no expone `molregno`.
- **Llaves de enlace ya disponibles:** UNII por UniChem (2.063 familias, para openFDA) y los NCT de las referencias de indicaciones (3.000 familias enlazadas con 32.039 estudios de AACT), además de sinónimos e InChIKey.

Carga del 2026-10-16: 3.739 familias, 4.455 moléculas, 833 targets, 9 tablas.

## 2026-10-16 — openFDA agregado por fármaco, desde la API

Por cada familia de ChEMBL con UNII (2.064) se consulta `drug/event` por sus UNII y se guardan: reportes por año de recepción (totales, serios y con muerte) y las 100 reacciones más reportadas. Nada de reportes individuales: FAERS se usa solo agregado, como dice el plan.

- **Por año:** permite las features de Rastro Lab con datos estrictamente anteriores al inicio de cada ensayo.
- **Cualquier rol:** openFDA no permite exigir que el UNII y el rol de sospechoso estén en el mismo fármaco del reporte, así que se cuentan también los concomitantes. Se aclara en la interfaz.
- **Caché reanudable:** un JSON por fármaco en `data/raw/openfda/`. Sin API key (1000 requests por día) la descarga se completa en varias corridas.
- **Detalle de la API:** en `search`, los espacios hacen de OR/AND. `requests` codifica `+` como `%2B`, que openFDA toma literal y devuelve cero resultados.

Carga del 2026-10-16: 2.064 fármacos consultados, 673 con reportes (625 de los 778 aprobados), 13.558 filas año-fármaco y 65.268 reacciones. Los fármacos en ensayo casi nunca tienen reportes, como es de esperar en FAERS.

## 2026-10-16 — MeSH 2026 en GraphDB, importado por trozos, con conector Lucene

MeSH 2026 completo (15,4 M triples) en el grafo `<http://id.nlm.nih.gov/mesh/2026>` del repositorio `rastro`.

- **Por trozos de 500 mil triples:** importarlo en una sola transacción hacía que el OOM killer de la VM de Docker matara a GraphDB cuando otras pilas (otros triplestores y plataformas) compartían la memoria. Si GraphDB igual se cae, se reinicia solo (`restart: unless-stopped`) y el cargador reintenta el trozo.
- **Carpeta de importación explícita:** GraphDB busca por defecto en `${user.home}/graphdb-import`; se fija `/import`, montada sobre `data/raw/mesh/`.
- **Descarga sin descomprimir:** NLM responde con `Content-Encoding: x-gzip` y `requests` lo descomprime solo; se guardan los bytes crudos.
- **Conector Lucene `mesh`:** indexa descriptores y SCR de enfermedades por etiqueta, sinónimos (concepto → término) y número de árbol (sin analizar, para filtrar por rama, por ejemplo `C04*`). Sirve para normalizar condiciones de texto libre (Fase 6) y resolver nombres en NL→SPARQL (Fase 3).
