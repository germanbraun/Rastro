# Rastro

Two commercial MVPs on semantic technologies, with public data:

- **Rastro Layer** — business questions over integrated sources, with the provenance of every value.
- **Rastro Lab** — a machine-learning model whose predictions are explained with that same evidence. Today: the gas of
  new Vaca Muerta shale gas wells.

The demo case is **oil and gas in Argentina**. Three more domains show that the same Rastro works for other data:
US federal suppliers, oncology clinical trials and research affiliations. In the app they appear when «Ver detalles
técnicos» is turned on.

## The approach

**An agent builds and maintains the semantic layer, every decision keeps its evidence, and a person approves what is
a business decision.** The agent does the work, executable checks decide whether it is right, and a person decides
what it means. Three principles:

1. **Questions first.** What to map, and how to measure whether it works, comes from the business questions.
2. **Correctness is decided by checks that run,** not by a model's opinion: it loads, it answers, it passes the quality
   rules, and it gets the questions right against independent references.
3. **What a value means is decided by a person.** «Operates», «owns» and «has a share in» are not interchangeable. The
   agent proposes, with evidence and alternatives, and does not decide silently.

The method is a sequence of steps. Each one has a skill that does it (`.claude/skills/`), a check that decides, and a
person's approval only where there is a business decision:

| Step | Skill | What decides | A person approves |
|---|---|---|---|
| Inspect candidate sources | `inspect-sources` | Versions, keys, join evidence, read-only | Which domain and sources |
| Start a domain | `start-domain` | Registry entry, its Ontop starts, experiment log | The scope |
| Business questions | `add-question` | Each question has definitions, a query and an executable check | What each word means |
| Connect the sources | `add-source` | Counts, file fingerprints, repeatable load | What goes in |
| Dictionary and mappings | `map-source` | Every term exists; counts equal the tables | The terms, as they will be written |
| Links with evidence | `link-entities` | Every link has its source, rule and evidence | Doubtful corrections |
| Quality rules | `quality-rules` | SHACL after every load, with a good and a broken example per rule | Thresholds and what to do with findings |
| Measure | `evaluate` | Three approaches with independent evaluators; independent references | The plan and each adjudication |
| Show | `show-in-app` | Both views load; every number comes from its file | The business wording and the demo |
| Explain how («Paso a paso») | `walkthrough` | One real case through each part of Rastro, read live; every number matches a query | The case and the purpose of each step |
| Maintain | `change-tests` | A source changes or a value is corrected: the smallest fix reaches every answer, then everything is restored | The plan and what is claimed |
| Verify and close | `verify`, `close-phase` | Registry, lifecycle and query checks pass | The phase |

What this means in practice:

- **Every link is evidence.** A link is a `prov:Entity` with its source (`prov:wasDerivedFrom`), its rule and its
  evidence text. Corrections live in a reviewed CSV, with their reason. Those reviewed by an AI assistant say that a
  person still has to confirm them.
- **Three approaches, always.** Without Rastro (B: SQL over the sources as they come), SQL with Rastro's links (D: the
  fair baseline) and with Rastro (C: SPARQL). Each evaluator is a fresh assistant that sees only its prompt. Where
  approaches differ, the answer is adjudicated with each source's data.
- **Generic machinery, one registry.** A domain is an entry in `layer/dominios.yaml` (its Ontop, ontology, notes,
  readers and a `method:` block) plus its files. The skills, the quality runner, the evaluation harness, the change
  guard and the app read their paths from it. The aim is that a new domain needs data and decisions, not new code.
  The research-affiliations experiment tests that aim, and records every change to generic code it needed.
- **Requirements have a lifecycle.** A question goes proposed → approved → implemented → validated
  (`layer/lifecycle.py`). Approvals bind the exact text approved, and changing an approved artifact invalidates what
  depends on it.
- **A second reviewer.** Each stage of a new domain is reviewed by an independent assistant, and the discussion and
  decisions are kept in the repo (`docs/experiments/`).

The full method, with its contracts and gates: [docs/method.md](docs/method.md) and
[docs/method-contracts.md](docs/method-contracts.md). The plan by phases: [docs/plan.md](docs/plan.md). Decisions,
with their numbers: [docs/decisions.md](docs/decisions.md). How sources are integrated:
[docs/integracion.md](docs/integracion.md). What each source contains: [docs/fuentes.md](docs/fuentes.md).

## The domains

### Oil and gas in Argentina (`energia`, the demo)

Production by well, the well registry, concessions and their partners, ventings, pipelines, towns and protected areas,
from the Secretaría de Energía, ENARGAS and IGN, linked with the companies' LEI (GLEIF) and enriched with Wikidata.
Rastro answers who operates and who owns each concession, how much each company is entitled to by its share, and where
wells are. Every value says where it comes from. **Rastro Lab** predicts the gas of new Vaca Muerta shale wells with the
same model trained twice, on the raw tables and on Rastro, and explains each prediction with the records it used.

- **Measured:** B 7 of 10, D 10 of 10, C 10 of 10 questions.
- **Also running:** quality rules in SHACL, a test for what Rastro says when it lacks the data, and change tests
  (a source renames a column or changes a unit; one correction reaches every result; which predictions change when the
  source corrects a record).
- **Ontop** on :8082. Script: [docs/demo-guion-energia.md](docs/demo-guion-energia.md).

### US federal suppliers (`proveedores`)

Federal contracts over US$10 million from fiscal year 2025 (USAspending), sectors (NAICS), the global company
identifier (GLEIF), the government's screening lists (trade.gov) and Wikidata. Rastro builds corporate groups once,
with the evidence of each company's membership. For example, Leidos is split across 13 parents in the contracts data,
and the 2013 SAIC rename is resolved explicitly.

- **Measured:** B 4 of 9, D 8 of 9, C 8 of 9.
- **Also:** a question over texts, where an exact query picks the contracts and an assistant summarizes only those,
  citing each one.
- **Ontop** on :8081.

### Oncology (`oncologia`)

Clinical trials (AACT), drugs and targets (ChEMBL), adverse events (openFDA) and the MeSH 2026 vocabulary, with trials
linked to drugs and conditions. The first domain. It compares an LLM alone, direct SQL and Rastro on 20 questions, and
has its own evaluation (`layer/eval/`). **Ontop** on :8080; MeSH lives in GraphDB.

### Research affiliations in Argentina (`afiliaciones`, transfer experiment)

Which Argentine research organizations (ROR, the global registry) the authors of 100 scientific publications from
2025 name in their affiliation texts (Crossref), and which organizations the registry might be missing. It is a test
of the method itself: a new domain built only with the skills, with the method frozen and every change to generic code
recorded. Claude implemented it and another assistant reviewed every stage.

- **Built so far:**
  - three validated questions;
  - 539 identifications, each with its rule and evidence;
  - seven quality rules (one registry warning, 91 AI decisions awaiting a person);
  - the app's two views;
  - 33 evaluation answers, collected but not scored;
  - an alias correction: with Rastro and with SQL plus links every saved answer behaved as declared, with no edits,
    while the raw-SQL answers did not change;
  - 30 of 30 sampled answer cells traceable to their records and rule with Rastro, for the evidence kept in this
    setup.
- **Still missing:** accuracy against a blind human reference, and closing the experiment.
- **Where to read more:** [docs/experiments/afiliaciones.yaml](docs/experiments/afiliaciones.yaml) (the log) and
  [process notes](docs/experiments/research-affiliations/process-notes.md) (what the skills got right, missed or
  should flag).
- **Ontop** on :8083, with `--profile afiliaciones`.

## Structure

| Folder | Contents |
|---|---|
| `infra/` | docker-compose: Postgres, one Ontop per domain, triplestore (`compose.yaml`, at the root, includes it) |
| `data/` | download and load scripts (the data is not versioned) |
| `ontology/` | per domain: competency questions, ontology, one query per question, quality rules (SHACL) |
| `mappings/` | R2RML mappings, one per domain, read by that domain's Ontop |
| `linking/` | links between each domain's sources, with their rule, evidence and reviewed corrections |
| `layer/` | the domain registry (`dominios.yaml`), lifecycle and method commands, natural-language questions (`answer.py`), the evaluation (`evaluar.py`) and each domain's evaluation, change tests and notes |
| `lab/` | Rastro Lab: the Vaca Muerta gas model (`lab/gas/`) |
| `app/` | the demo (Streamlit, in Spanish); each domain is a YAML file in `app/dominios/` |
| `.claude/skills/` | the method's skills, generic for any domain |
| `docs/` | method, plan, decisions, experiments, decks (`slides/`), demo scripts and human review |
| `tests/` | tests (pytest) |

Each domain uses its own SPARQL prefix (`energia:`, `proveedores:`, `oncologia:`, `afiliaciones:`), for example
`energia:Well`.

The main files, how a value flows through them and where to change what: `docs/code-structure.md`. Running and
debugging: `ONBOARDING.md`.

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
| **Rastro Layer demo** | **http://localhost:8501** | Opens on oil and gas; with «Ver detalles técnicos» the **Caso de uso** selector shows the other domains |
| Postgres | `localhost:5434` (user and password `rastro`) | Relational sources, one schema per source, and `rastro_meta` with the source and load registry |
| Ontop, one per domain | oncology http://localhost:8080, suppliers :8081, oil and gas :8082, research affiliations :8083 (`/sparql`; the last one with `docker compose --profile afiliaciones up -d`) | Virtual SPARQL endpoint over Postgres, with its domain's ontology and mappings; reloads when they are edited |
| GraphDB Free | http://localhost:7210 | Triplestore with the `rastro` repository: MeSH 2026 in the graph `<http://id.nlm.nih.gov/mesh/2026>` and the Lucene connector `mesh` |

The app opens in Spanish; the sidebar's «Idioma» switch, or `http://localhost:8501/?lang=en`, shows it in English.

Ports are changed by copying `.env.example` to `.env`. By default they avoid 5432 and 7200, to coexist with a local Postgres and GraphDB.

Count per source (Phase 0 checkpoint):

```bash
docker compose exec postgres psql -U rastro -c "select * from rastro_meta.source_counts"
```

Every script in `data/` records its loads in `rastro_meta.load_run`, which feeds that view.

## Evaluate Rastro Layer

Oil and gas, suppliers and research affiliations compare three ways of answering: **B**, without Rastro (SQL over the raw tables); **D**, SQL with Rastro's link tables; and **C**, with Rastro (SPARQL). In oil and gas: B 7 of 10, D 10 of 10 and C 10 of 10; in suppliers: B 4 of 9, D 8 of 9 and C 8 of 9. Research affiliations has its answers collected and waits for a blind reference before scoring.

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje   # or another domain; also prompt, try and rerun
```

The results go to `layer/<domain>/resultados.md`; the detail of each command, in the docstring of `layer/evaluar.py`.

Oncology compares how many of 20 questions an LLM alone, direct SQL and Rastro answer correctly:

```bash
docker compose run --rm layer-eval
```

The results are in `layer/eval/results.md`. Answers already generated are saved in `layer/eval/results.json`, so this works without an API key. Generating new answers needs `ANTHROPIC_API_KEY` in `.env` (Claude API, pay per use: a full run with Claude Opus 5.5 costs a few dollars). `RASTRO_MODEL` picks another model, for example a cheaper one for a live demo.

To check the ontologies and queries of every domain, and the quality rules:

```bash
docker compose run --rm ontology-check
docker compose run --rm calidad      # SHACL over the oil and gas data, ~3 minutes
docker compose run --rm --no-deps calidad python /ontology/calidad.py afiliaciones   # another domain
```

## Rastro Lab

A linear model (ridge regression) predicts the gas of months 2 to 7 of a new Vaca Muerta shale gas well, with the raw tables and with Rastro, and explains each prediction with the exact contribution of each variable. Both predict equally well; with Rastro, each variable says where it comes from and which ones were corrected or arrived late. In the app, the **Rastro Lab** tab. Details in [docs/lab-gas-vaca-muerta.md](docs/lab-gas-vaca-muerta.md).

**Without installing anything:** [`lab/notebooks/rastro-lab.ipynb`](lab/notebooks/rastro-lab.ipynb)
([open in Colab](https://colab.research.google.com/github/germanbraun/Rastro/blob/main/lab/notebooks/rastro-lab.ipynb))
trains the same model from a saved copy of its inputs (`lab/notebooks/datos/`) and shows how Rastro explains a
prediction: the facts behind each factor with their rule, evidence and source, the predictions to review, and what a
correction changes. It checks that its numbers are the published run's.

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
