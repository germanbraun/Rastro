# Worked examples from Rastro's domains

Concrete cases for the skill `add-source`. The generic procedure is in `SKILL.md`; the registry is `layer/dominios.yaml`.

## Sources already loaded

- Oil and gas (`energia`): Capítulo IV (production well by well), Secretaría de Energía maps, fracturing, well
  trajectories, and the Wikidata enrichment.
- Suppliers (`proveedores`): USAspending, NAICS, the government control lists (CSL), GLEIF, Wikidata.
- Oncology (`oncologia`): AACT, ChEMBL, openFDA, MeSH.
- Research affiliations (`afiliaciones`): Crossref (100 works) and the ROR data dump.

## Loaders to copy

- `data/energia/` (oil and gas): several sources of one domain in one loader.
- `data/lab-gas/` (oil and gas): the sources only Rastro Lab uses (earlier years, fracturing and well trajectories).
  Well trajectories are the most complete example of a source added end to end: loader, link with its rule, mapping,
  dictionary, model and explanation.

## A loader that writes the source manifest (research affiliations)

`data/afiliaciones/load.py` loads approved snapshots from `data/raw/research-affiliations/` (it checks their
fingerprints and never downloads) and, after a successful load, rewrites `layer/afiliaciones/sources.yaml`
(`method.source_manifest`): each source's version, file fingerprints and row counts per table. A change there makes
the domain's implemented and validated questions stale (`layer/lifecycle.py`).

## A source only for Rastro Lab (oil and gas)

`capitulo4_anterior` and `fractura` live in their own schemas and are loaded by their own loader in `data/lab-gas/`
(`docker compose run --rm lab-gas-loader`). After loading, the Layer evaluation is run again to confirm nothing changed:

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
```

## Links in the linker (oil and gas)

A new source that names companies adds its names to `empresa_nombre` with their `fuente` in
`linking/energia/links.sql`, and a link table with rule and evidence. Then `docker compose run --rm energia-linker` and
`docker compose restart ontop-energia`.

## The stored enrichment (oil and gas, Wikidata through the LEI)

- Live: a federated query, `layer/energia/externo/wikidata.rq`.
- Stored: `data/wikidata-energia/` keeps the day's response with its fingerprint; the link through the LEI with its rule
  and evidence is `energia.enriquecimiento`; its own class `energia:Enrichment` is mapped with `prov:wasDerivedFrom` to the
  source and `energia:loadedOn` with the query day. Today question 15 uses it, not the model.
- Order: `energia-linker`, then `wikidata-energia-loader`, then `energia-linker` again.

## Watch out for, in practice

- **Large files:** Capítulo IV is about 300 MB per year; filter by the wells you need before joining years.
- **Memory:** `data/mesh/load.py` (oncology) imports MeSH into GraphDB in parts.
- **Sources updated every day:** fracturing (oil and gas) has `fecha_data`, mapped to `energia:loadedOn`.
