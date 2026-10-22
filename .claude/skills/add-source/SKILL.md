---
name: add-source
description: Add or change a data loader in any domain of the registry (layer/dominios.yaml), including enrichment from an outside source through a shared key. Use it when new data has to be downloaded and loaded into Postgres or the triplestore.
---

# Add a data source

Read `docs/method-contracts.md` for lifecycle states, executable gates, approval reuse and experiment evidence.
For a new domain, run `start-domain` first. Record measured time, interventions and caught errors as work happens.


Step 1 of the method (`docs/method.md`). A loader downloads data, stores it in `data/raw/` and loads it into Postgres (one schema per source) or into the triplestore. Follow the pattern of the existing loaders in `data/`, in Python. The domain's loaders are listed in `method.loaders` of its entry in `layer/dominios.yaml`. Below, `<domain>` is that entry and `<source>` the new source.

## Contract

- **Takes:** the competency questions that need the data (skill `add-question`) and a public source that has it.
- **Returns:** a loader in `data/<source>/`, its service, the data in Postgres (or the triplestore) with each load recorded, and the source in the registry.
- **Does not:** map the data to the dictionary (skill `map-source`) or link it to what Rastro already has (skill `link-entities`).

## Constraints

- **Never load beyond the scope** the questions need: the cut is decided first, and filtered at the origin if the source is large.
- **No secrets in code, URLs or `.env.example`:** credentials only in `.env`, passed as connection parameters.
- **Every load is recorded** in `rastro_meta.load_run` with its file fingerprint (SHA-256) and download day.
- **Never change what is already measured** without running the evaluation again and confirming the result.
- **Downloads never go into the repo:** they go to `data/raw/`, which is not versioned; the repo keeps the scripts.
- **Mark what is uncertain:** an unclear license, key or unit goes into the proposal's open questions, never loaded as "probably right".

## Steps: narrow down, decide, test

1. **Narrow down the source, and write the proposal.** Load only what the domain's competency questions (`method.questions`) ask for. If the source is large, filter at the origin. Look at the source before writing code: its documentation, a sample file, its keys and which things it names that Rastro already has. Write the result as a short source profile, before touching any file:

   | Publisher | URL | License | Format and size | Update frequency | Tables and fields to load (the scope) | Keys | Entities already in Rastro | Risks | How sure | Open question |
   |---|---|---|---|---|---|---|---|---|---|---|

   A person reviews it at a glance; the scope, the license and the open questions are decided here. The profile goes into the decision or the experiment log.
2. **Do not change what the demo already measures.** If the source is only for one consumer (for example, Rastro Lab), it goes in its own schema and its own loader. After loading, run the domain evaluation again (skill `evaluate`, `method.evaluation.run` with `rerun`) and confirm it gives the same result.
3. **Write the loader** in `data/<source>/`:
   - `schema.sql` with the tables, using the original source's names. If the linker needs it even when the source is not loaded, it must not drop anything (`CREATE ... IF NOT EXISTS`) and the loader must empty the tables before loading.
   - `load.py` that registers the source in `rastro_meta.source` (with its license), downloads to `data/raw/<source>/` with cache and retries, and loads with `COPY`.
   - One row in `rastro_meta.load_run` per table, with the source version: use `copiar()` from `data/comun.py` and pass it the downloaded file (`archivo=`), so its SHA-256 fingerprint and download day are recorded.
4. **Add the service** `<source>-loader` in `infra/docker-compose.yml`, with `profiles: ["load"]` and the image `./loaders`, and add it to `method.loaders` in `layer/dominios.yaml`.
5. **Credentials** only through `.env` variables. Add the empty variable to `.env.example`. Pass passwords as connection parameters, never inside a URL, because errors print them.
6. **Dictionary, links and rules:** the terms and the mapping, with the skill `map-source`; if the source names things already in Rastro, the skill `link-entities`; and its possible values, with the skill `quality-rules`. In short, for links: add it to the domain linker (`method.linker.folder`, `links.sql`): its names, each with the source it came from, and a link table with rule and evidence. Map it with `prov:wasDerivedFrom` to the source and add its terms to `term_sources` and `link_sources` in `layer/dominios.yaml`.
7. **Run the load and the linker** (`method.linker.service`), restart the domain's Ontop (`method.ontop.service`) and check with the skill `verify`: counts, a known case, and that nothing falls outside the cut.
8. **Document:** a row in the «Cargar datos» (Load data) table of `README.md` and an entry in `docs/decisions.md` (which cut, why, load numbers).

## A person approves

- **The proposal:** the source profile, its scope, its license and its open questions, before the loader is written.
- A load that touches a schema the evaluation already measures, and any change in its result.

## Enrich with an outside source

If the source belongs to another organization and joins through a shared key (an identifier both sides use), it is an **enrichment**. It can be queried live (a federated query, always up to date) and also stored as one more source, so it can be queried offline and repeated. The stored pattern: a loader that keeps the day's response with its fingerprint, a link through the key with its rule and evidence, and its own class mapped with `prov:wasDerivedFrom` to the source and a load date with the query day.

## Watch out for

- **Large files:** run the loader in the background and filter queries by the records you need before joining files or years.
- **Memory:** import large RDF into the triplestore in parts.
- **Sources updated every day:** store each record's load date if it has one, and map it.
- **Encoding of `+`:** in APIs that use `+` as a space, `requests` encodes it as `%2B`. Use spaces.

Worked examples from the existing domains (loaders, sources, the stored enrichment, sizes): `examples.md`.
