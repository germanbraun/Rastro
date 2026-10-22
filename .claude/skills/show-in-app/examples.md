# Worked examples from Rastro's domains

## Which domains are in the app, and how

- **Oil and gas in Argentina** (`app/dominios/energia.yaml`) is the first in `app/dominios.yaml`, so the app opens on it.
  It uses every module: questions over texts, check a claim, Wikidata enrichment (live and saved), the map, quality
  rules, "when the data is missing" and the Rastro Lab tab.
- **US federal suppliers** (`app/dominios/proveedores.yaml`) uses the business and technical views, questions over texts
  (`layer/proveedores/textos/leidos.json`, with a comparison against a word search) and the change test.
- **Oncology** still has its own screen in `app/app.py` (older than the template in `app/dominio.py`); its question over
  texts is `layer/textos/detenidos-pulmon.json`. Moving it to the template is pending.
- Suppliers and oncology appear only with «Ver detalles técnicos» (the demo is oil and gas).

## A business-view question (oil and gas, e01)

«¿Cuánto petróleo de 2025 le corresponde a cada empresa, según su participación?» (how much 2025 oil belongs to each
company, by its share): `query: /ontology/energia/queries/cq1.rq`; «¿Por qué este número?» lists, concession by
concession, the share and the partners' text from the concessions map, with its source; `antes_despues` shows YPF with
21.4 million m³ when summing by who reports the production, and 12.6 by its share. Those two numbers are typed in the
YAML and come from `layer/energia/sin-rastro.sql` and question 1: they are checked by hand after each re-measurement.

## Trust cards (oil and gas)

`tarjetas` uses placeholders: «{c_correct} de {n_questions}» (correct answers with Rastro), «{b_correct}» (without),
«{c_consistent} de {n_consistency}», «{b_broken}» (queries to rewrite when a source changes), «{pct_evidencia}» and
«{n_enlaces}» from `layer/energia/evidencia.json`. On 22/10/2026 a commit carried an invalid consistency number into the
deck and the script by hand; the cards were right because they read the JSON.

## Technical view (oil and gas)

- Console: `/ontology/energia/queries`, port 8082 (the domain registry).
- Example records (`technical.instances` in the domain YAML): the concession Loma Campana, the company YPF, Chevron's share in Loma Campana (a link
  with evidence), the operator link of well 107709, a well's production in December 2025, a venting seen by satellite and
  the link that places it in its concession.
- Pieces (`technical.pieces` in the domain YAML): the partners of each concession separated from the map's text, the company names joined across
  sources, the operator of each well, each venting in its concession, with their R2RML blocks.
- Quality rules: «Bajo el capó → Reglas de calidad (SHACL)», each rule with a real record in Turtle and a broken
  example.

## Questions over texts (oil and gas)

`layer/energia/textos/venteos.rq` selects the five concessions with the most possible ventings seen by satellite since
2024 and the environmental studies filed for them since 2022 (joined by concession name): 72 studies. An assistant read
only those texts and grouped them into themes, each citing its studies by number; saved 19/10/2026
(`venteos.json`). The app shows the five steps: the question, the graph chooses, the AI reads only that, the summary
with citations, check.

## The map (oil and gas)

`map_data` in `app/dominio.py` queries `energia:Concession`, `energia:DetectedVenting`, `energia:Pipeline` and
`energia:ConcessionToReview` with `geo:asWKT`: its domain-specific queries and display settings now live in `technical.map` in the domain YAML.
