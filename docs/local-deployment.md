# Local deployment on this laptop

Deployed on 2026-10-23 from `main`. Open the app at <http://localhost:8501>.

## Running scope

- PostgreSQL on port 5434, with persisted data in the `rastro_pgdata` Docker volume.
- Oil and gas semantic endpoint on port 8082, with its public source data and links loaded.
- Rastro Lab: historical production, fracturing and trajectories loaded; a local model run published.
- Research affiliations endpoint on port 8083, loaded from the approved Crossref sample and ROR v2.15 snapshots.
- Streamlit app on port 8501, including both mapping/linking and Lab walkthroughs.

Suppliers and oncology have not been loaded on this laptop. GraphDB federation and the saved Wikidata
materialization have not been configured here. The existing saved enrichment example remains available in the app.
Free-form AI questions require an API key or a configured local model; saved example questions work without either.
None of these deployment checks supplies the experiment's pending independent human reference.

## Start and stop

Docker Desktop must be running. Its CLI is installed inside the application bundle and is not currently on the
shell's default path. From the repository root:

```sh
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
open -a Docker
# Once Docker Desktop is ready:
docker compose up -d postgres ontop-energia ontop-afiliaciones app
```

To stop the local app and its endpoints without deleting the database:

```sh
docker compose stop app ontop-energia ontop-afiliaciones postgres
```

The ignored `.env` holds local defaults and enables the `afiliaciones` profile. Downloads are cached under
`data/raw/energia/` and `data/raw/lab-gas/`; restarting does not reload or redownload them. Do not delete the
PostgreSQL volume to restart the app.

## Deployment evidence

Both domains' configured example queries and business/technical views were exercised against the actual services
with `app/check_domain.py`. Oil and gas ontology/query checks and all seven quality-rule example pairs passed.
The published local model contains 559 finite predictions. These are execution checks, not new accuracy claims.

Local receipts are ignored artifacts in `data/cache/`: `local-deployment-source-counts.json`,
`local-deployment-model.json`, and the live quality receipt `local-deployment-quality.json`.
The affiliations loader wrote its current load receipt to `data/cache/local-afiliaciones/sources.yaml`,
keeping the frozen shared experiment manifest unchanged. Source fingerprints were checked before loading.

The live quality run completed with 19 violations, no warnings and no informational findings, matching the existing
energy receipt's totals. These source-quality findings remain visible in the app; deployment did not repair or
remove them. The check's status is `defects_detected`, not a defect-free validation.
