---
name: add-question
description: Add or change a competency question with its SPARQL query, in any domain of the registry (layer/dominios.yaml), and extend the ontology only if needed. Use it when touching ontology/**/competency-questions.md, the ontologies or ontology/**/queries/.
---

# Add a competency question

Read `docs/method-contracts.md` for lifecycle states, executable gates, approval reuse and experiment evidence.
For a new domain, run `start-domain` first. Record measured time, interventions and caught errors as work happens.


Step 0 of the method (`docs/method.md`). Questions rule: the ontology only has what some question needs.

## Contract

- **Takes:** a business question from a client or from the demo, and the domain it belongs to.
- **Returns first:** an approved business requirement (definitions, scope, answer type and verification plan).
- **Returns after data and mappings exist:** its implemented query, then validated executable expectations.
- **Does not:** add terms or mappings on its own (that is the skill `map-source`), or load data (skill `add-source`).

## Constraints

- **Allow useful single-source questions and controls.** Label which questions demonstrate cross-source integration.
- **No internal names in the question:** it is said in business words, as a client would say it, without table,
  column or ontology names.
- **Definitions are written into the question,** not assumed: what counts as an operator, which category is included,
  which period.
- **The query uses only existing terms:** a missing term goes through the skill `map-source`, never invented in the
  query.
- **Mark what is uncertain:** an ambiguous word goes into the proposal's open questions, never resolved silently in the
  query.

Where each piece lives for a domain is in its entry in `layer/dominios.yaml`:

| What | Registry key |
|---|---|
| Ontology | `ontology` |
| Questions | `method.questions` (`competency-questions.md`) |
| Queries | `method.queries` (`cq<N>.rq`) |
| Mapping | `method.mapping` |
| Ontop service and port | `method.ontop.service`, `method.ontop.port` |
| Namespace (the domain prefix) | `namespace` |
| Notes the assistant reads | `sparql_notes` |

Below, `<domain>` is the registry entry, `<prefix>:` its prefix and `<port>` its `method.ontop.port`.

## Steps: narrow down, decide, test

1. **Narrow down the question, and write the proposal.** The question in business words, as a client would say it. Identify whether it tests cross-source integration or is a useful single-source requirement/control. If it depends on a definition (what counts as an operator, which category is included), write it in the question. Look in the existing questions and the dictionary first: maybe it is already asked or almost. Write the result as a short table, one row per question, before touching any file:

   | Question (plain words) | Definitions it depends on | Sources it needs | Expected answer type | Ambiguous words | How sure | Open question |
   |---|---|---|---|---|---|---|

   A person reviews it at a glance; definitions and ambiguous words are decided here. The table goes into the decision or the experiment log.
2. **Add it to the table** in the domain's questions file (`method.questions`), with number, sources and what it is for (demo, Layer or Lab).
3. **After approved requirements have their data and mappings, write the query** in `method.queries` as `cq<N>.rq`:
   - First line: `# <N>. <the question>`.
   - The domain prefix (`<prefix>:`), never the empty prefix.
   - No `*` or `+` paths: Ontop does not support them. Whatever needs closure is precomputed in Postgres.
   - Source values as they are (same spelling and case as the source).
4. **If a term or a value is missing,** follow the skill `map-source` (dictionary and mapping together, with their checks). In short: add it to the ontology with an `rdfs:label` in Spanish and a short comment. Prefer an attribute over a new class; a property used by two classes has no `rdfs:domain` (otherwise Ontop infers wrong classes). Add it to the domain's `term_sources` (and to `link_sources` if it is a link) in `layer/dominios.yaml`, and to the notes the assistant reads (`sparql_notes`). If it joins things across sources, the skill `link-entities`.
5. **If it needs new data,** load it first (skill `add-source`), then add its mapping (with `rr:datatype` if the column comes from a `GROUP BY` or `DISTINCT`) and restart the domain's Ontop (`docker compose restart <method.ontop.service>`).
6. **Validate:** `docker compose run --rm ontology-check` returns OK, and the query against Ontop gives an answer that makes sense to someone from the business:
   `curl --fail-with-body --show-error -H 'Accept: text/csv' --data-urlencode "query@<method.queries>cq<N>.rq" http://localhost:<port>/sparql`
   Then add fingerprinted assertions to `layer/<domain>/query-checks.yaml`, with their `evidence` (`invariant` or
   `independent`), and run the executable gate in `verify`. HTTP success alone is insufficient. Name the level when
   you report: technical validation (invariants) is not accuracy validation (independent references). Keep what
   Rastro counts (the system's definition) apart from what a blind reviewer checks (the reference's); if the business
   reading changes, re-propose and re-approve the requirement, never only a note in a discussion.
7. **If it goes to the app,** add it to `preguntas` in `app/dominios/<domain>.yaml` (simple question, technical wording and, if possible, «¿Por qué este número?» (Why this number?)). If it goes to the evaluation, follow the skill `evaluate`. If it touches values the source can get wrong, the skill `quality-rules`.
8. **If it is for a predictive model** (Rastro Lab), use only data known at prediction time: nothing that arrived after the case started (see the skill `rastro-lab`).

## A person approves

- **The proposal:** each question, its definitions and its ambiguous words, before the query is written.
- Each definition that is a **business decision** (what a word means in that domain), and changing a question already used in the app or in the evaluation.

Worked examples from the existing domains (paths, prefixes, ports, definitions): `examples.md`.
