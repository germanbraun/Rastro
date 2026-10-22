# Worked examples from Rastro's domains

The domain-specific content of the `quality-rules` skill. The skill itself is generic; these are the real cases behind
it.

## Where it exists today

Only for oil and gas (`energia`):

- Rules: `ontology/energia/calidad/reglas.ttl`
- Examples: `ontology/energia/calidad/ejemplos.yaml`
- Result: `layer/energia/calidad.json`
- Runner: `ontology/calidad.py energia` (paths, prefix, CONSTRUCT queries and endpoint come from the registry;
  `ONTOP_ENERGIA` remains a runtime endpoint override), service `calidad`: `docker compose run --rm calidad`, about 3 minutes.

Suppliers (`proveedores`) and oncology (`oncologia`) have no quality rules yet.

In the app: «Por qué confiar» (why trust it) and, with «Ver detalles técnicos» (see technical details), «Bajo el capó →
Reglas de calidad (SHACL)» (under the hood → quality rules), with a real value from Rastro and a broken one.

## The rules, by type (oil and gas)

| Type | Example in Rastro | In SHACL |
|---|---|---|
| Evidence completeness | Every link says which source it comes from and why (`calidad:EnlaceConEvidencia`) | `sh:targetSubjectsOf energia:rule`, `sh:minCount` |
| Possible values | Pressure up to 20,000 psi, depth from 1,000 to 6,000 m | `sh:minInclusive`, `sh:maxInclusive` |
| Cardinality | Each company, at most one LEI | `sh:maxCount`, `sh:pattern` |
| Consistency between values | The range minimum is not greater than the prediction | `sh:lessThanOrEquals` |
| Aggregates | A concession's working interests add up to 100 % or less | `sh:sparql` with `GROUP BY` and `HAVING` |
| What the model uses | Each prediction comes from a well start | `sh:qualifiedValueShape` |

## Watch out for: what happened (oil and gas)

- **Rules found a dictionary error:** an extra `rdfs:domain` (`energia:fracStages` with domain `energia:Fracturing`)
  made every fracturing record count as a fracturing. It showed because the rule was checking 9,732 fracturings when
  there are 4,733.
- **The first error was found by the simplest rule:** 5 well trajectories without evidence, from concatenating an
  empty value.
- **An impossible value reaches the model:** 4 predictions of the current run use 537,184 m³ of water or 111,515 psi.
  The rule flags them and says which ones; removing them from the model is a separate decision.
- **What points to a value:** if the target is a concession (`sh:targetObjectsOf`), the real example also shows the
  working interests that point to it.
