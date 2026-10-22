# Rastro

Two MVPs on semantic technologies, with public data. The demo case is **oil and gas in Argentina**. The other two cases, US federal suppliers and oncology clinical trials (AACT, ChEMBL, openFDA, MeSH), show that the same approach works for other data: in the app they appear when «Ver detalles técnicos» is turned on.

- **Rastro Layer** — a virtual semantic layer over heterogeneous sources, and natural-language questions with the provenance of every value.
- **Rastro Lab** — a model whose predictions are explained with that same evidence. Today: the gas of new Vaca Muerta shale gas wells.

The method (steps, skills, checks and human approvals) is in [docs/method.md](docs/method.md). The full plan, by phases and with checkpoints, is in [docs/plan.md](docs/plan.md). How the sources are integrated (schema and data heterogeneity), in [docs/integracion.md](docs/integracion.md). What each source contains, for readers outside the domain, in [docs/fuentes.md](docs/fuentes.md).

## Structure

| Folder | Contents |
|---|---|
| `infra/` | docker-compose: Postgres, Ontop, triplestore (`compose.yaml`, at the root, includes it) |
| `data/` | download and load scripts (the data is not versioned) |
| `ontology/` | competency questions, ontology and one query per question; quality rules (SHACL) |
| `mappings/` | R2RML mappings, one per domain (`rastro`, `proveedores`, `energia`), read by each domain's Ontop |
| `linking/` | links between each domain's sources (for example, trials with MeSH and ChEMBL), with their review |
| `layer/` | Rastro Layer: natural-language questions (`answer.py`) and their evaluation (`evaluar.py`, `eval/`) |
| `lab/` | Rastro Lab: the Vaca Muerta gas model (`lab/gas/`) |
| `app/` | the demo (Streamlit, in Spanish) |
| `docs/` | method, plan, decisions, results, decks (`slides/`), demo scripts and human review |
| `tests/` | tests (pytest) |

Each domain uses its own SPARQL prefix: `energia:`, `proveedores:` and `oncologia:` (for example, `energia:Well`).

## The demo

The app, decks and demo scripts are in Spanish, for Argentine audiences.

| Domain | Script | Deck |
|---|---|---|
| Oil and gas in Argentina | [docs/demo-guion-energia.md](docs/demo-guion-energia.md) | `docs/slides/energia.html` |
| US federal suppliers | [docs/demo-guion.md](docs/demo-guion.md) | `docs/slides/proveedores.html` |
| Oncology | [docs/demo-guion-oncologia.md](docs/demo-guion-oncologia.md) | `docs/slides/oncologia.html` |

For a technical audience: [docs/demo-guion-tecnico.md](docs/demo-guion-tecnico.md). What a person still has to confirm: [docs/verificacion-humana.md](docs/verificacion-humana.md). An evaluation with questions we did not write: [docs/preguntas-a-ciegas.md](docs/preguntas-a-ciegas.md), and the invitation to send: [docs/invitacion-prueba-a-ciegas.md](docs/invitacion-prueba-a-ciegas.md).

## Start the environment

From the repo folder:

```bash
docker compose up -d
```

| Service | Local URL | What it is |
|---|---|---|
| **Rastro Layer demo** | **http://localhost:8501** | Opens on oil and gas; with «Ver detalles técnicos» the **Caso de uso** selector shows suppliers and oncology |
| Postgres | `localhost:5434` (user and password `rastro`) | Relational sources, one schema per source, and `rastro_meta` with the source and load registry |
| Ontop, one per domain | oncology http://localhost:8080, suppliers :8081, oil and gas :8082 (`/sparql`) | Virtual SPARQL endpoint over Postgres, with its domain's ontology and mappings; reloads when they are edited |
| GraphDB Free | http://localhost:7210 | Triplestore with the `rastro` repository: MeSH 2026 in the graph `<http://id.nlm.nih.gov/mesh/2026>` and the Lucene connector `mesh` |

Ports are changed by copying `.env.example` to `.env`. By default they avoid 5432 and 7200, to coexist with a local Postgres and GraphDB.

Count per source (Phase 0 checkpoint):

```bash
docker compose exec postgres psql -U rastro -c "select * from rastro_meta.source_counts"
```

Every script in `data/` records its loads in `rastro_meta.load_run`, which feeds that view.

## Evaluate Rastro Layer

Oil and gas and suppliers compare three ways of answering: **B**, without Rastro (SQL over the raw tables); **D**, SQL with Rastro's link tables; and **C**, with Rastro (SPARQL). In oil and gas: B 7 of 10, D 10 of 10 and C 10 of 10.

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje   # or proveedores; also prompt, try and rerun
```

The results go to `layer/<domain>/resultados.md`; the detail of each command, in the docstring of `layer/evaluar.py`.

Oncology compares how many of 20 questions an LLM alone, direct SQL and Rastro answer correctly:

```bash
docker compose run --rm layer-eval
```

The results are in `layer/eval/results.md`. Answers already generated are saved in `layer/eval/results.json`, so this works without an API key. Generating new answers needs `ANTHROPIC_API_KEY` in `.env` (Claude API, pay per use: a full run with Claude Opus 5.5 costs a few dollars). `RASTRO_MODEL` picks another model, for example a cheaper one for a live demo.

To check the ontologies and queries of the three domains, and the oil and gas quality rules:

```bash
docker compose run --rm ontology-check
docker compose run --rm calidad      # SHACL over the integrated data, ~3 minutes
```

## Rastro Lab

A linear model (ridge regression) predicts the gas of months 2 to 7 of a new Vaca Muerta shale gas well, with the raw tables and with Rastro, and explains each prediction with the exact contribution of each variable. Both predict equally well; with Rastro, each variable says where it comes from and which ones were corrected or arrived late. In the app, the **Rastro Lab** tab. Details in [docs/lab-gas-vaca-muerta.md](docs/lab-gas-vaca-muerta.md).

It runs on the machine, not in Docker: it needs `python3 -m pip install -r requirements-dev.txt`, the oil and gas Ontop on `localhost:8082` and the `lab-gas-loader` data (below).

```bash
python3 lab/gas/modelo.py              # or a well, --12-meses, --como-trabajo-publicado
python3 lab/gas/modelo.py --publicar   # saves the run, its input and its predictions in Rastro, to query them
python3 lab/gas/modelo.py --comparar   # what changed between the last two runs, well by well
layer/energia/cambio/impacto.sh registrar   # Rastro says which predictions change if the source corrects a record, and it is checked
python3 lab/gas/a_ciegas.py            # builds the blind test: docs/lab-explicaciones-a-ciegas.md
```

## Code quality

```bash
python3 -m ruff check .
python3 -m pytest -q
```

They also run on GitHub with every change (`.github/workflows/calidad.yml`).

## Load data

The loaders run on demand and need credentials in `.env` (copied from `.env.example`).

| Source | Command | Requirement |
|---|---|---|
| AACT (oncology) | `docker compose run --rm aact-loader` | A free AACT account (`AACT_USER`, `AACT_PASSWORD`) or a snapshot in `data/raw/` (`AACT_DUMP`) |
| ChEMBL (oncology) | `docker compose run --rm chembl-loader` | None: uses the public ChEMBL API, NLM's MeSH and UniChem |
| openFDA (adverse events) | `docker compose run --rm openfda-loader` | ChEMBL loaded first. A free API key is recommended (`OPENFDA_API_KEY`): without it, 1000 requests per day and the download continues on the next run |
| MeSH 2026 (GraphDB) | `docker compose run --rm mesh-loader` | About 3 GB of free Docker memory during the import. Also creates the Lucene connector `mesh` and copies descriptors and hierarchy to Postgres |
| USAspending (suppliers) | `docker compose run --rm usaspending-loader` | None: public API. Fiscal-year 2025 contracts over US$10 million and each supplier's profile with its parents; the first time takes about an hour and it can resume |
| NAICS 2022 (suppliers) | `docker compose run --rm naics-loader` | None: public Census spreadsheet. Sectors from 2 to 6 digits with their ancestors |
| Consolidated Screening List (suppliers) | `docker compose run --rm csl-loader` | None: public CSV from trade.gov |
| GLEIF (suppliers) | `docker compose run --rm gleif-loader` | USAspending loaded first. LEI candidates for parents and for the 1000 suppliers with the most revenue; 60 queries per minute, resumable |
| Wikidata (suppliers) | `docker compose run --rm wikidata-loader` | GLEIF loaded first. Companies with those LEIs in Wikidata, their headquarters and whether they are listed |
| Oil and gas (Secretaría de Energía) | `docker compose run --rm energia-loader`, then `docker compose run --rm energia-linker` | None: 2025 production by well and the well registry (datos.energia.gob.ar), concessions, ventings and ENARGAS pipelines from the WFS, IGN towns and protected areas, and the companies' LEI in GLEIF; about 350 MB, resumable |
| Rastro Lab, Vaca Muerta gas | `docker compose run --rm lab-gas-loader`, then `docker compose run --rm energia-linker` | None: Capítulo IV from 2018 to 2022, well fracturing data (Adjunto IV) and Vaca Muerta well trajectories, from datos.energia.gob.ar; about 1.5 GB. It does not change what Rastro Layer uses |
| Wikidata enrichment (oil and gas) | `docker compose run --rm wikidata-energia-loader`, then `docker compose run --rm energia-linker` | Rastro's LEIs (the linker first). Saves what Wikidata knows about the companies (headquarters, stock exchange, owner, website), with the query date; live, it is queried without loading anything |
| Oncology links | `docker compose run --rm linker` | The sources above already loaded. Links trials with MeSH and with ChEMBL in a few seconds |
| Supplier tables and links | `docker compose run --rm proveedores-linker` | USAspending and NAICS loaded (plus GLEIF, the Consolidated Screening List and Wikidata for the links). Builds suppliers, groups and sectors, and the links with their evidence |
| Research affiliations (Crossref + ROR, transfer experiment) | `docker compose run --rm afiliaciones-loader` | The approved snapshots in `data/raw/research-affiliations/` (`fetch.py` and `draw.py` in `docs/experiments/research-affiliations/`); the loader checks their fingerprints and never downloads. 100 works with 1,456 affiliations; ROR v2.15 complete |

Downloads stay in `data/raw/`, which is not versioned: openFDA keeps one JSON per drug there and does not request it again.

If a password contains `$`, put it in single quotes in `.env`: Docker Compose interprets `$` in unquoted values.
