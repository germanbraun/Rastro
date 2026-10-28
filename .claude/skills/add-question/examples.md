# Worked examples from Rastro's domains

Concrete cases for the skill `add-question`. The generic procedure is in `SKILL.md`; every path comes from
`layer/dominios.yaml` (oncology, for example, keeps its questions in `ontology/`, not `ontology/oncologia/`).

## Definitions written in the question (oil and gas)

Questions that depend on a definition say it: for example «operadora» (operator) or «no convencional» (unconventional).

## Source values as they are

- Oil and gas: `"vaca muerta"` (formation), `"SHALE"` (resource type).
- Oncology: `"TERMINATED"` (trial status).

## Validate a query (oil and gas)

```bash
curl --fail-with-body --show-error -H 'Accept: text/csv' \
  --data-urlencode "query@ontology/energia/queries/cq<N>.rq" http://localhost:8082/sparql
python layer/method.py verify energia --expectations layer/energia/query-checks.yaml
```

Suppliers and oncology have no `query-checks.yaml` yet: their questions are not executably validated.

## The full lifecycle (research affiliations)

`afiliaciones` declares `method.lifecycle: layer/afiliaciones/lifecycle.json`. Each question has its proposal and its
human review in `layer/afiliaciones/requirements/` (`cq1.proposal.yaml`, `cq1.approval.yaml`, …), its query in
`ontology/afiliaciones/queries/`, and its checks in `layer/afiliaciones/query-checks.yaml`; `lifecycle.json` keeps each
transition with the fingerprints of those files. The checks there are invariants from the approved definitions, not
accuracy: the blind reviewer's reference comes later (`evaluate`).

## A question for Rastro Lab (oil and gas)

The gas model for new Vaca Muerta shale wells only uses data from before the well started: the operator and well type of
the month it started, and the fracturing reported up to that month (skill `rastro-lab`).
