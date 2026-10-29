# Rastro

Two commercial MVPs on semantic technologies, with public data:

- **Rastro Layer:** business questions over integrated sources, with the provenance of every value.
- **Rastro Lab:** a machine-learning model whose predictions are explained with that same evidence. Today, the gas of new Vaca Muerta shale wells.

The demo case is **oil and gas in Argentina** (`energia`). US federal suppliers (`proveedores`) and oncology (`oncologia`) show that the same Rastro works for other data: the app shows them only with «Ver detalles técnicos». The plan is in `docs/plan.md`; the method in `docs/method.md`; the decisions in `docs/decisions.md`.

## Main rule: simple

It is a commercial MVP: someone in sales has to understand it and be able to tell it in three minutes.

- Do the minimum that works for the demo or for a number in the demo. If a piece is not needed, don't build it.
- Simple names in business words: "Pozo", "Concesión", "operadora". No internal acronyms.
- Before adding a class, a table, a service or a dependency, ask whether it can be avoided.
- Every step ends in something you can see working.

## Conventions

- **Language:** code, comments, technical docs, skills and commits in English. What users see stays in Spanish: the app (`app/**/*.yaml`), the decks, the demo scripts and the ontology labels (`rdfs:label "…"@es`). Ontology names are in English (`energia:Well`). Existing Spanish comments and docs are translated when they are touched; the history in `docs/decisions.md` stays as written, new entries in English.
- **R2RML mappings**, one file per domain (`mappings/rastro.r2rml.ttl` for oncology, `proveedores.r2rml.ttl`, `energia.r2rml.ttl`). Each Ontop reads a single mapping file.
- **Minimal ontology** (`ontology/<domain>/`): only what its competency questions need. One property per relation (for example, `energia:inConcession` is the only one that links something to its concession). A property used by two classes has no `rdfs:domain`.
- **Everything is queried through Ontop**: oncology on :8080, suppliers on :8081, oil and gas on :8082. Each domain has its prefix (`oncologia:`, `proveedores:`, `energia:`); never the empty prefix. Ontop does not support `*` or `+` paths: anything that needs a closure is precomputed in Postgres.
- **Enrichment** adds what an outside source knows (today, Wikidata) through a shared key (the LEI), keeping where it came from. Done live (a federated query, always up to date) or saved in Rastro (`energia:Enrichment`, with its date and file fingerprint, so it can be queried offline and repeated; today question 15 uses it, the model does not). It is not "data augmentation" in the machine-learning sense (synthetic examples).
- **Every link is evidence:** a `prov:Entity` with `prov:wasDerivedFrom` (the source) and its rule and evidence as text. Corrections go in a reviewed CSV (`linking/<domain>/`), with their reason or document; those reviewed by an AI assistant say a person still has to confirm them.
- **Data outside the repo:** downloads go to `data/raw/`, which is not versioned. The repo keeps scripts. Every load is recorded in `rastro_meta.load_run`. One exception: the Rastro Lab notebook's input snapshot (`lab/notebooks/datos/`, under 1 MB, saved by `lab/gas/snapshot.py`), so it runs in Colab.
- **Secrets only in `.env`**, never in `.env.example` or in commits. Before committing, check that `.env.example` has no keys.
- **App texts** in YAML (`app/dominios/*.yaml`, `app/ayuda.yaml`, `app/faq*.yaml`), not in code. Measured numbers are read from their JSON (`layer/<domain>/resultados.json`, `layer/energia/cambio/*.json`), never typed by hand.
- **Register (in the app, in Spanish):** formal and jargon-free in the business view («diccionario de negocio», «evidencia»); the technical part goes behind «Ver detalles técnicos». In visible texts, «Rastro deduce / traduce / genera», not the tool names; tools are named only where they are explained.
- **No names of commercial knowledge-graph products or companies** in the repo (interface, docs, code, commits). To talk about interoperability, say "other knowledge-graph platforms or tools".
- **The method** is in `docs/method.md`: every step with its skill, the check that decides and where a person approves.
- **Decisions** in `docs/decisions.md`: one short entry per decision, with the why and the numbers.
- **Commits:** stage only the files you changed (no `git add -A`): other sessions may have work in progress in the same folder.

## Measurement rules

- **The references come from Rastro**, so Rastro's advantage can be circular. Before publishing a number, adjudicate with each source's data the questions where the approaches differ (`layer/<domain>/adjudicacion.md`), and run the blind tests (`docs/preguntas-a-ciegas.md`, `docs/lab-explicaciones-a-ciegas.md`).
- **Three approaches, always:** without Rastro (B, SQL over the sources as they come), SQL with Rastro's links (D, the fair baseline) and with Rastro (C).
- **One prompt per evaluator:** each evaluator is a fresh assistant that sees only its prompt; never several wordings of the same question together.
- **A fix after measuring** is re-measured only where it applies, and said so. When a rule or a value changes, all saved queries are re-run (`rerun`).
- **Rastro Lab compares the same model** with variables from the raw tables (A) and from Rastro (B). Accuracy only shows nothing is lost; what is measured is the explanation.
- **Rastro Lab does not use the future:** the operator and the well type are those of the month the well started; the fracturing, what was reported up to that month. Anything that arrived later is flagged.
- **What only Lab loads does not change Layer:** it goes in its own schema, and that is confirmed by re-running the evaluation.

## Commands

```bash
docker compose up -d                                   # app :8501, Postgres :5434, Ontop :8080/:8081/:8082, GraphDB :7210
docker compose run --rm energia-loader                 # loaders: <source>-loader (see README)
docker compose run --rm lab-gas-loader                 # Capítulo IV 2018–2022, fracturing and trajectories, only for Lab
docker compose run --rm wikidata-energia-loader        # Wikidata enrichment, saved (after the linker, then the linker again)
docker compose run --rm energia-linker                 # oil and gas links (proveedores-linker; linker for oncology)
docker compose restart ontop-energia                   # after changing mappings, ontology or links
docker compose run --rm ontology-check                 # ontologies and competency queries, all three domains
docker compose run --rm calidad                        # quality rules (SHACL) over the oil and gas data (~3 min)
docker compose run --rm -T layer-eval python /layer/fuera.py energia prompt|guardar|puntaje   # does it say when it lacks the data?
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun|puntaje   # evaluation (energia_lab: questions about the predictions)
layer/energia/cambio/cambio.sh registrar               # change test (always ends with «deshacer»)
layer/energia/cambio/correccion.sh registrar           # one correction, every result (~15 min)
layer/energia/cambio/impacto.sh registrar              # which predictions change if the source corrects a record (~15 min)
python3 lab/gas/modelo.py [<well>|--12-meses|--como-trabajo-publicado|--publicar|--comparar]   # Rastro Lab from the console
python layer/method.py new-domain <domain> --title "…"  # a new domain's scaffold (skill start-domain)
python3 docs/slides/build.py                           # builds the HTML decks
```

The scripts in `lab/` and `layer/energia/cambio/correccion.py` run on the machine, not in Docker: they need Python with `requirements-dev.txt` and the oil and gas Ontop on localhost:8082.

## Repo skills

**Method skills** — generic for any domain; each domain's paths and commands come from its `method:` block in `layer/dominios.yaml`, and real cases from each skill's `examples.md`:

- `inspect-sources`: inspect candidate sources read-only, with versions, keys, join evidence and proposed questions
- `start-domain`: initialize a domain, its approved scope and experiment log
- `add-question`: approve a business requirement, then implement and validate its query
- `add-source`: add or change a data loader
- `map-source`: a source's dictionary and mapping, with their checks
- `link-entities`: link entities across sources, with rule, evidence and reviewed corrections
- `quality-rules`: SHACL rules over the integrated data, and the predictions that inherit what fails
- `evaluate`: measure the questions with the three approaches, score and adjudicate
- `show-in-app`: show a domain in the app, business and technical view, and optional modules such as questions over texts
- `walkthrough`: a «Paso a paso» on real data, read live: one case through each part of Rastro, saying what each step shows, with its slides
- `change-tests`: the change test and the correction test, and where they show
- `verify`: check that everything starts and answers
- `close-phase`: mark the plan, document and commit

**Project and domain skills:**

- `rastro-lab`: train, measure and explain the oil and gas model with and without Rastro
- `decks`: build and publish Rastro's decks and keep the demo script consistent
