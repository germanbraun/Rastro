# Worked examples from Rastro's domains

The domain-specific content of the `map-source` skill. The skill itself is generic; these are the real cases behind it.

## Where each piece lives today

| Domain | Ontology | Mapping | Notes for the assistant | Ontop |
|---|---|---|---|---|
| Oil and gas (`energia`) | `ontology/energia/energia.ttl` | `mappings/energia.r2rml.ttl` | `layer/energia/sparql-notes.md` | :8082, `ontop-energia` |
| Suppliers (`proveedores`) | `ontology/proveedores/proveedores.ttl` | `mappings/proveedores.r2rml.ttl` | `layer/proveedores/sparql-notes.md` | :8081, `ontop-proveedores` |
| Oncology (`oncologia`) | `ontology/rastro.ttl` | `mappings/rastro.r2rml.ttl` | `layer/sparql-notes.md` | :8080, `ontop` |
| Research affiliations (`afiliaciones`) | `ontology/afiliaciones/afiliaciones.ttl` | `mappings/afiliaciones.r2rml.ttl` | `layer/afiliaciones/sparql-notes.md` | :8083, `ontop-afiliaciones` |

This table is a snapshot: the registry is the source of truth. Oncology does not follow the `ontology/<domain>/` layout: always read the paths from `layer/dominios.yaml`.

## Naming and modelling (oil and gas)

- A term name with its unit: `energia:lateralLengthM`.
- One single property per relationship: `energia:inConcession` is the only one that links something to its concession.
- A definition that can be read two ways: a company's production, operated or by working interest. Not chosen by the
  agent: it is a business decision.
- Source values kept as they are, without translating them: `"vaca muerta"`, `"SHALE"`.
- Link properties in the mapping: `prov:wasDerivedFrom`, `prov:wasGeneratedBy`, `energia:rule` and
  `energia:sourceText`. (Suppliers uses `proveedores:linkRule` and `proveedores:sourceText`; oncology,
  `oncologia:linkRule` and `oncologia:interventionText`; research affiliations, `afiliaciones:rule`,
  `afiliaciones:sourceText` and `afiliaciones:linkStatus`, with one `prov:wasDerivedFrom` per source the link joins.)

## Checks, as run for oil and gas

```bash
docker compose restart ontop-energia
docker compose logs ontop-energia
curl -s -H 'Accept: text/csv' --data-urlencode "query@ontology/energia/queries/cq<N>.rq" http://localhost:8082/sparql
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
```

Count check: `SELECT (COUNT(DISTINCT ?x) AS ?n) WHERE { ?x a energia:<Clase> }` against `SELECT count(*)` on the table.

## Business definitions a person approved (oil and gas)

What «operadora» (operator), «pozo nuevo» (new well) or «no convencional» (unconventional) means.

## Watch out for: what happened

- **`rdfs:domain` on a shared property (oil and gas):** `energia:fracStages` had domain `energia:Fracturing` and every
  fracturing record also uses it, so Rastro counted 9,732 fracturings instead of 4,733. A quality rule found it.
- **One note missing from the dictionary (oil and gas):** the notes did not describe `energia:CompanyName` and the
  assistant reached the operator by another path (22 instead of 24). It was fixed with one line, at the same level as
  the SQL notes.
- **Two similar words for the same thing (oil and gas):** «concesión» (concession) in two forms; the assistant used the
  wrong one. Only one was kept.
- **Ontop does not support `*` or `+` paths (oncology):** the condition hierarchy is precomputed in Postgres and mapped
  as `oncologia:within`.
