# Onboarding

Day-to-day commands to run Rastro on a laptop. Everything runs from the repository root with Docker Compose
(`compose.yaml` includes `infra/docker-compose.yml`). The why behind each part is in `README.md`; the plan in
`docs/plan.md`.

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

## Measure and test

```bash
docker compose run --rm calidad                                            # quality rules, oil and gas (~3 min)
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
python3 -m pip install -r requirements-dev.txt                             # once, for tests and Lab
python3 -m ruff check . && python3 -m pytest -q                            # lint and unit tests, on the machine
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
