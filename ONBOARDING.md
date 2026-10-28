# Onboarding

Day-to-day commands to run Rastro on a laptop. Everything runs from the repository root with Docker Compose
(`compose.yaml` includes `infra/docker-compose.yml`). The why behind each part is in `README.md`; the plan in
`docs/plan.md`; a map of the code, in `docs/code-structure.md`.

## What runs where

| Service | Address | What it is |
|---|---|---|
| `app` | http://localhost:8501 | The demo (opens on oil and gas) |
| `postgres` | localhost:5434 | The sources, the links and the load log |
| `ontop-energia` | http://localhost:8082/sparql | Oil and gas, the demo domain |
| `ontop-proveedores` | http://localhost:8081/sparql | US federal suppliers |
| `ontop` | http://localhost:8080/sparql | Oncology |
| `ontop-afiliaciones` | http://localhost:8083/sparql | Research affiliations (profile `afiliaciones`, off by default) |
| `graphdb` | http://localhost:7210 | MeSH for oncology |

## First time on a new machine

1. Install Docker Desktop and give it at least 8 GB of memory (MeSH needs about 3 GB more while it loads).
2. Copy the settings and fill in only what you need:
   ```bash
   cp .env.example .env
   ```
   For questions in plain words, set `RASTRO_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`. Keys go only in `.env`,
   never in `.env.example` or a commit. A password with `$` goes in single quotes.
3. Build and start:
   ```bash
   docker compose up -d --build
   ```
4. Load the demo data (about 350 MB, resumable), then the links:
   ```bash
   docker compose run --rm energia-loader
   docker compose run --rm energia-linker
   docker compose restart ontop-energia
   ```
   Rastro Lab and the other domains need more loaders: see «Load data» in `README.md`.
5. Open http://localhost:8501.

## Start, stop, restart

```bash
docker compose up -d                                   # start everything (also after Docker restarts)
docker compose --profile afiliaciones up -d            # also the research-affiliations Ontop
docker compose ps                                      # what is up and healthy
docker compose stop                                    # stop, keeping the data
docker compose restart app                             # after editing app/, layer/ or lab/ code
docker compose restart ontop-energia                   # after changing mappings, ontology or links (oil and gas)
docker compose up -d --build app                       # after changing requirements or a Dockerfile
docker compose down                                    # remove the containers; the data volumes stay
```

Only GraphDB restarts by itself. When Docker Desktop restarts, the rest stays stopped: run `docker compose up -d`.

## Is it working?

```bash
docker compose ps
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8501/
docker compose exec postgres psql -U rastro -c "select * from rastro_meta.source_counts"
docker compose run --rm ontology-check                 # ontologies and competency queries, all domains
```

The full check, with the query gate, quality rules and evaluation, is the `verify` skill.

## When something is wrong

```bash
docker compose logs --tail 50 app                      # or ontop-energia, postgres…
docker compose logs -f ontop-energia                   # follow live
```

- **An Ontop does not start:** almost always a mistake in its mapping (`mappings/<domain>.r2rml.ttl`) or a term the
  ontology lacks. Its log names it.
- **The app shows an old error after a code change:** `docker compose restart app` (Streamlit keeps imported modules).
- **GraphDB restarts by itself:** Docker is short on memory; stop other containers or raise the limit.
- **Port already in use:** change it in `.env` (`APP_PORT`, `PG_PORT`, `ONTOP_ENERGIA_PORT`…).

## Trace a number, from the source to the screen

The fastest way to learn the code, and to debug a number that looks wrong, is to follow one value down the chain:

```
download (data/) → raw table (Postgres, one schema per source) → linker (linking/<domain>/, SQL + reviewed CSVs)
  → linked table (schema energia) → mapping (mappings/<domain>.r2rml.ttl) → Ontop (SPARQL → SQL) → app (app/)
```

Example: the first demo question, «¿Cuánto petróleo le corresponde a cada empresa?», for YPF in Loma Campana.

1. **The question in the app** is `e01` in `app/dominios/energia.yaml`; it runs `ontology/energia/queries/cq1.rq`
   (`query:`), and «¿Por qué este número?» runs the `porque.query` next to it.
2. **Ask Rastro for one concession** (paste into http://localhost:8082/sparql or run with curl):
   ```bash
   curl -s --fail-with-body -H 'Accept: text/csv' --data-urlencode 'query=PREFIX energia: <https://w3id.org/rastro/energia#>
   SELECT ?percent ?text (SUM(?oil) AS ?production) WHERE {
     ?c energia:name "LOMA CAMPANA" .
     ?s a energia:Stake ; energia:inConcession ?c ; energia:partner/energia:name "YPF S.A." ;
        energia:percent ?percent ; energia:sourceText ?text .
     ?p a energia:WellProduction ; energia:inConcession ?c ; energia:oil ?oil .
   } GROUP BY ?percent ?text' http://localhost:8082/sparql
   ```
   It answers 50 %, the text «YPF S.A.: 50 %» and the concession's oil; YPF's share is the oil × 50 %.
3. **See the SQL Rastro generates** for the same query: send it to `/ontop/reformulate` instead of `/sparql`
   (`curl -s -G --data-urlencode 'query=…' http://localhost:8082/ontop/reformulate`). It joins `energia.participacion`
   and `capitulo4.produccion`: those are the two tables to look at.
4. **The mapping** says where each term comes from: in `mappings/energia.r2rml.ttl`, `<#Stake>` reads
   `energia.participacion` and `<#WellProduction>` reads the raw `capitulo4.produccion`.
5. **The linker** built `energia.participacion` (`linking/energia/links.sql`, «Participaciones»): it splits the
   concessions map's partner text with a regular expression and joins each name to a company. A name that does not
   match goes through `linking/energia/correcciones.csv`: Loma Campana's other partner, «COMPAÑIA DE HIDROCARBURO NO
   CONVENCIONAL S.R.L.», becomes CHEVRON there, with its reason.
6. **The raw data**, without Rastro:
   ```bash
   docker compose exec postgres psql -U rastro -c "select participacion from sig_energia.concesion where id_concesion = 'LCAM'"
   docker compose exec postgres psql -U rastro -c "select round(sum(prod_pet)) from capitulo4.produccion where idareapermisoconcesion = 'LCAM'"
   ```
   If these two agree with step 2, Rastro carried the number faithfully; if not, the difference is in the linker or
   the mapping, and the step where it changes tells you which.

The screen code is the package `app/dominio/`, one module per part of the screen: `screen.py` (the tabs),
`answers.py` («Preguntar»), `hood.py` («Bajo el capó»), `trust_view.py` («Por qué confiar»), `faq.py` and `common.py`
(cached queries, tables). Modules call each other as `common.run(...)`, so a call says where the function lives; a
test replaces a function there (`patch.object(dominio.common, "run", ...)`). Oncology keeps its older screen in its extension,
`app/extensions/oncologia/screen.py`.

Where a wrong number usually comes from: a name the linker did not join (look for the company in
`energia.empresa_nombre`), a source column that changed (the mapping), or a stale app (`docker compose restart app`).

## Measure and test

```bash
docker compose run --rm calidad                                            # quality rules, oil and gas (~3 min)
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
python3 -m pip install -r requirements-dev.txt                             # once, for tests and Lab
python3 -m ruff check . && python3 -m pytest -q                            # lint and unit tests (GitHub runs both on every push)
python3 lab/gas/modelo.py                                                  # Rastro Lab from the console
python3 docs/slides/build.py                                               # the HTML decks
```

## Start from zero (deletes all loaded data)

```bash
docker compose down -v
```

This removes the Postgres and GraphDB volumes: every source has to be loaded again (hours for some). Downloads in
`data/raw/` stay, and the loaders that cache there (oil and gas among them) reuse them.

## Before committing

- Stage only your files (`git add <files>`, never `git add -A`): other sessions may be working in the same folder.
- Check that `.env.example` has no keys.
- Code, comments and docs in English; what users see in Spanish (see `CLAUDE.md`).
