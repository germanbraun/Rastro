---
name: add-source
description: Add or change a data loader in any domain of the registry (layer/dominios.yaml), including enrichment from an outside source through a shared key. Use it when new data has to be downloaded and loaded into Postgres or the triplestore.
---

# Add a data source

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

Step 1 of the method (`docs/method.md`). If access, reuse terms, coverage or joins are still uncertain, run
`inspect-sources` first and reuse its profile and snapshot; it does not approve loading.

A loader downloads data into `data/raw/` and loads it into Postgres (one schema per source) or into the triplestore,
following the existing Python loaders in `data/`. The domain's loaders are in `method.loaders` of its registry entry.
Below, `<domain>` is that entry and `<source>` the new source.

## Contract

- **Takes:** the approved competency questions that need the data (skill `add-question`) and a public source that has it.
- **Returns:** a loader in `data/<source>/`, its service, the data loaded with each load recorded, and the source in the registry.
- **Does not:** map the data (`map-source`), link it (`link-entities`) or write its quality rules (`quality-rules`).

## Constraints

- **Never load beyond the scope** the questions need: decide the cut first, filter at the origin if the source is large.
- **No secrets in code, URLs or `.env.example`:** credentials only in `.env`, passed as connection parameters.
- **Every load is recorded** in `rastro_meta.load_run` with its file fingerprint (SHA-256) and download day.
- **Downloads never go into the repo:** `data/raw/` is not versioned; the repo keeps the scripts.
- **Mark what is uncertain:** an unclear license, key or unit is an open question, never loaded as "probably right".

## Steps: narrow down, decide, test

1. **Proposal.** Look at the source before writing code: documentation, a sample file, keys, and what it names that
   Rastro already has. Write a short profile, before touching any file:

   | Publisher | URL | License | Format and size | Update frequency | Tables and fields to load (the scope) | Keys | Entities already in Rastro | Risks | How sure | Open question |
   |---|---|---|---|---|---|---|---|---|---|---|

   A person approves the scope, the license and the open questions. The profile goes into the decision or the experiment log.
2. **Do not change what is already measured.** Data only one consumer needs (for example, a model) goes in its own
   schema and loader. After loading, re-run the domain evaluation (`method.evaluation.run` with `rerun`) and confirm
   the same result.
3. **Write the loader** in `data/<source>/`:
   - `schema.sql` with the source's own names. If the linker needs the tables even when the source is not loaded,
     use `CREATE ... IF NOT EXISTS` and empty the tables before loading.
   - `load.py`: registers the source in `rastro_meta.source` (with its license), downloads to `data/raw/<source>/`
     with cache and retries, and loads with `copiar()` from `data/comun.py`, passing the downloaded file (`archivo=`)
     so the fingerprint and download day are recorded in `rastro_meta.load_run`.
   - If the domain declares `method.source_manifest`, the loader rewrites it after every successful load (versions,
     fingerprints, row counts): that is what makes earlier validations stale.
4. **Service** `<source>-loader` in `infra/docker-compose.yml`, with `profiles: ["load"]` and `build: ./loaders`; add it
   to `method.loaders`.
5. **Credentials** only through `.env` variables; add the empty variable to `.env.example`. Never put a password in a
   URL: errors print it.
6. **Then:** follow `map-source` (dictionary and mapping), `link-entities` if it names things already in Rastro, and
   `quality-rules` for its possible values.
7. **Load and check:** run the loader and the linker (`method.linker.service`), restart the domain's Ontop
   (`method.ontop.service`) and follow `verify`: counts, a known case, nothing outside the cut.
8. **Document:** a row in the "Load data" table of `README.md` and an entry in `docs/decisions.md` (cut, why, load numbers).
   If the domain describes its sources in the app (`fuentes_detalle` in its YAML, in both languages), add the new
   source there: what it is, what Rastro uses it for and what is worth knowing (skill `show-in-app`).

## A person approves

- **The proposal:** the profile, its scope, its license and its open questions, before the loader is written.
- A load that touches a schema the evaluation already measures, and any change in its result.

## Enrich with an outside source

If the source belongs to another organization and joins through a shared key, it is an **enrichment**. It can be
queried live (a federated query) and also stored as one more source: a loader that keeps the day's response with its
fingerprint, a link through the key with its rule and evidence, and its own class mapped with `prov:wasDerivedFrom` and
the query day.

## Watch out for

- **Large files:** run the loader in the background; filter by the records you need before joining files or years.
- **Memory:** import large RDF into the triplestore in parts.
- **Sources updated every day:** store each record's load date if it has one, and map it.
- **Encoding of `+`:** in APIs that use `+` as a space, `requests` encodes it as `%2B`. Use spaces.

Worked examples from the existing domains: `examples.md`.
