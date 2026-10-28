# Code structure

A map of the code for developers: what each folder and main file does, how a value flows through them, and where
to change what. How to run it is in `ONBOARDING.md`; the why behind each part, in `README.md` and
`docs/decisions.md`.

## How a value flows

```
data/<source>/load.py         download to data/raw/, load one Postgres schema per source, log the load
        │
linking/<domain>/             SQL + reviewed CSVs: one table per business concept, each link with rule and evidence
        │
mappings/<domain>.r2rml.ttl   says which table and column fills each term of the ontology
ontology/<domain>/            the terms (the business dictionary), one SPARQL query per question, quality rules
        │
Ontop (one per domain)        answers SPARQL by translating it to SQL over Postgres: nothing is copied
        │
layer/answer.py               runs SPARQL or SQL, and asks the LLM (questions in plain words)
        │
app/                          Streamlit: the business view and, with «Ver detalles técnicos», the technical one
```

Rastro Lab (`lab/gas/`) reads the same Ontop for its variables. Measurement (`layer/evaluar.py`, the change tests)
runs the saved queries again and writes JSON that the app and the slides read.

Every domain repeats the same pattern; its paths and commands are registered in `layer/dominios.yaml`.

## Folders and main files

### `app/` — the demo (Streamlit)

| File | What it does |
|---|---|
| `app.py` | Entry point: language and view switches, the domain selector, and oncology's own (older) screen |
| `dominio/` | Every other domain's screen, drawn from its YAML. One module per part of the screen: |
| `dominio/screen.py` | `render`: the tabs, in the business or the technical view |
| `dominio/answers.py` | «Preguntar»: an answer with its sources and evidence, «¿Por qué este número?», the demo, claims, outside data, questions over texts |
| `dominio/hood.py` | «Bajo el capó»: dictionary, mappings, instances as RDF, quality rules, the SPARQL console, the map |
| `dominio/trust_view.py` | «Por qué confiar»: the measured evaluation, the change and correction tests, the «sin dato» test |
| `dominio/faq.py` | «Preguntas frecuentes» and the glossary |
| `dominio/common.py` | What they share: configuration, cached queries (`run`), tables (`tabla`), short texts |
| `lab.py` | The «Rastro Lab» tab: the gas model with and without Rastro, and each well's explanation |
| `layer_story.py`, `lab_walkthrough.py`, `lab_alternative.py` | The «Paso a paso» walkthroughs and the alternative model view |
| `contraste.py` | The numbers of the «Sin Rastro / Con Rastro» cards, read live; also writes the slides' numbers |
| `idioma.py` | Spanish by default, English on request: `t(key)` reads `textos/*.yaml`, `localized()` overlays `*.en.yaml` |
| `enlaces.py` | The one mark for a link's review status (rule, AI-reviewed, person-confirmed) |
| `grafo.py` | Draws an instance of the graph as SVG |
| `check_domain.py` | Renders a domain in both views and runs every example query (the app check) |
| `text_snapshot.py` | Captures every visible text, to compare languages |
| `dominios/<domain>.yaml` (+ `.en.yaml`) | Everything specific to a domain's screen: questions, columns, evidence, cards |
| `textos/*.yaml`, `ayuda*.yaml`, `faq*.yaml` | Interface texts in Spanish and English; no visible text lives in code |

### `layer/` — answering and measuring

| File | What it does |
|---|---|
| `dominios.yaml` | The registry: each domain's Ontop, ontology, mapping, queries, app file and method commands |
| `answer.py` | Runs SPARQL (`run_sparql_table`) and SQL (`run_sql`), gets the SQL Rastro generates (`ontop_sql`), and the three ways an LLM answers a question |
| `evaluar.py` | A domain's evaluation: B (SQL over the sources), D (SQL with Rastro's links) and C (with Rastro); `rerun`, `puntaje` |
| `fuera.py` | Does the assistant say when it lacks the data? |
| `evidencia.py` | How many links keep their source, rule and evidence |
| `method.py`, `lifecycle.py`, `experiment.py`, `experiment_log.py` | The method's executable gates, question lifecycle, gate runner and experiment log |
| `change_guard.py` | Saves and restores the exact inputs of a change test |
| `<domain>/` | Per domain: evaluation questions and saved answers (`eval/`), `resultados.json`, adjudication, change tests (`cambio/`) |

### `lab/gas/` — Rastro Lab

| File | What it does |
|---|---|
| `modelo.py` | The gas model with variables from the raw tables (A) and from Rastro (B); training, explanation, publishing a run (`--publicar`). Its version is the hash of this file |
| `a_ciegas.py` | Builds the blind test of the explanations |
| `alternative.py`, `compare_trees.py`, `thesis_pipeline.py`, `reproduce_thesis.py` | Read-only comparisons with other models and the published thesis |

### Data, links, dictionary

| Folder | What it does |
|---|---|
| `data/<source>/load.py` | One loader per source; `data/comun.py` has the shared download with cache. Downloads go to `data/raw/` (not versioned) |
| `linking/<domain>/` | `link.py` runs `links.sql` and loads the reviewed CSVs (`correcciones.csv` and similar), each row with its reason |
| `mappings/<domain>.r2rml.ttl` | One R2RML file per domain (`rastro.r2rml.ttl` is oncology) |
| `ontology/<domain>/` | The ontology (`.ttl`), `competency-questions.md`, one query per question in `queries/`, quality rules in `calidad/` |
| `ontology/check.py`, `ontology/calidad.py` | Checks the ontology and queries; runs the quality rules (SHACL) |

### The rest

| Folder | What it does |
|---|---|
| `infra/` | `docker-compose.yml` (included by `compose.yaml` at the root), the Ontop and loader images, Postgres init |
| `tests/` | pytest; runs without Docker. GitHub runs it with ruff on every push (`.github/workflows/calidad.yml`) |
| `docs/` | Method, plan, decisions, experiments, demo scripts; `docs/slides/` builds the decks (`build.py`, `estilo.py`) |
| `.claude/skills/` | The method as skills, generic for any domain; real cases in each `examples.md` |

## Where to change what

| To change… | Edit | Then |
|---|---|---|
| A text the user sees | `app/textos/*.yaml` or `app/dominios/<domain>.yaml`, in Spanish and English | `docker compose restart app` |
| How a part of the screen works | the module in `app/dominio/` | `docker compose restart app`; `check_domain.py <domain>` |
| A business question | `ontology/<domain>/competency-questions.md` and `queries/` (skill `add-question`) | `ontology-check` |
| Where a term's data comes from | `mappings/<domain>.r2rml.ttl` (skill `map-source`) | `docker compose restart ontop-<domain>` |
| How two sources are joined | `linking/<domain>/` (skill `link-entities`) | run the linker, restart that Ontop |
| A new source | `data/<source>/` and a service in `infra/docker-compose.yml` (skill `add-source`) | run the loader |
| The gas model | `lab/gas/modelo.py`; its sentences in `app/textos/modelo.yaml` | `python3 lab/gas/modelo.py --publicar`, restart the app |

## Names

Code, comments and docs are in English; what users see is in Spanish (with English overlays). Some older files and
functions keep Spanish names: `dominio` (domain), `calidad` (quality), `evaluar` (evaluate), `cambio` (change),
`correccion` (correction), `enlaces` (links), `idioma` (language), `textos` (texts), `contraste` (contrast),
`a_ciegas` (blind), `modelo` (model), `puntaje` (score), `revisados` (checked).
