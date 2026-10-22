# Worked examples from Rastro's domains

Concrete cases for the skill `add-question`. The generic procedure is in `SKILL.md`; the registry is `layer/dominios.yaml`.

## Where each domain keeps its pieces

| Domain | Ontology | Questions and queries | Mapping | Ontop |
|---|---|---|---|---|
| Oil and gas (`energia`) | `ontology/energia/energia.ttl` | `ontology/energia/` | `mappings/energia.r2rml.ttl` | :8082 (`ontop-energia`) |
| Suppliers (`proveedores`) | `ontology/proveedores/proveedores.ttl` | `ontology/proveedores/` | `mappings/proveedores.r2rml.ttl` | :8081 (`ontop-proveedores`) |
| Oncology (`oncologia`) | `ontology/rastro.ttl` | `ontology/` | `mappings/rastro.r2rml.ttl` | :8080 (`ontop`) |

Domain prefixes: `energia:`, `proveedores:`, `oncologia:`.

## Definitions written in the question (oil and gas)

Questions that depend on a definition say it: for example «operadora» (operator) or «no convencional» (unconventional).

## Source values as they are

- Oil and gas: `"vaca muerta"` (formation), `"SHALE"` (resource type).
- Oncology: `"TERMINATED"` (trial status).

## Validate a query (oil and gas)

```bash
curl -s -H 'Accept: text/csv' --data-urlencode "query@ontology/energia/queries/cq<N>.rq" http://localhost:8082/sparql
```

## A question for Rastro Lab (oil and gas)

The gas model for new Vaca Muerta shale wells only uses data from before the well started: the operator and well type of
the month it started, and the fracturing reported up to that month (skill `rastro-lab`).
