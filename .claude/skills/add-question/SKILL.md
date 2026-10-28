---
name: add-question
description: Add or change a competency question - its business requirement first, then its SPARQL query and executable checks - in any domain of the registry (layer/dominios.yaml). Use it when touching ontology/**/competency-questions.md or ontology/**/queries/, or when a client asks a new business question. New ontology terms go through map-source.
---

# Add a competency question

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

Step 0 of the method (`docs/method.md`). Questions rule: the ontology only has what some question needs.

## Contract

- **Takes:** a business question from a client or from the demo, and the domain it belongs to.
- **Returns first:** an approved business requirement (definitions, scope, answer type and verification plan).
- **Returns after data and mappings exist:** its implemented query, then validated executable expectations.
- **Does not:** add terms or mappings (`map-source`), load data (`add-source`) or link entities (`link-entities`).

## Constraints

- **Business words only:** no table, column or ontology names in the question.
- **Definitions are written into the question,** not assumed: what counts as an operator, which category, which period.
- **The query uses only existing terms;** a missing term goes through `map-source`, never invented in the query.
- **Mark what is uncertain:** an ambiguous word goes into the proposal's open questions, never resolved silently.
- **Single-source questions are fine** as requirements or controls; say which questions test cross-source integration.

Paths come from the domain's entry in `layer/dominios.yaml`: `method.questions`, `method.queries` (`cq<N>.rq`),
`method.ontop.port`, `namespace` (the prefix is the domain name), and `method.lifecycle` if the domain has one.

## Steps: narrow down, decide, test

1. **Proposal.** Look in the existing questions and the dictionary first: maybe it is already asked. Write one row
   per question, before touching any file:

   | Question (plain words) | Definitions it depends on | Sources it needs | Expected answer type | Ambiguous words | How sure | Open question |
   |---|---|---|---|---|---|---|

   If the domain declares `method.lifecycle`, save it as a proposal artifact and run
   `python layer/lifecycle.py propose <domain> <qid> --artifact <proposal.yaml>`.
2. **Approval.** A person approves the definitions and ambiguous words (with lifecycle:
   `lifecycle.py approve <domain> <qid> --artifact <human-review.yaml>`, written from a real review). Then add the
   question to `method.questions`, with number, sources and what it is for (demo, Layer or Lab).
3. **Dependencies.** Missing data: follow `add-source`. Missing term or mapping: follow `map-source`. Joins things
   across sources: follow `link-entities`. Come back when they exist.
4. **Query** in `method.queries` as `cq<N>.rq`:
   - First line: `# <N>. <the question>`.
   - The domain prefix (`<prefix>:`), never the empty prefix.
   - No `*` or `+` paths (Ontop does not support them); closures are precomputed in Postgres.
   - Source values as they are (same spelling and case).

   With lifecycle: `lifecycle.py implement <domain> <qid> --artifact <method.queries>cq<N>.rq`.
5. **Validate.** `docker compose run --rm ontology-check` is OK and the answer makes sense to a business person:
   `curl --fail-with-body --show-error -H 'Accept: text/csv' --data-urlencode "query@<method.queries>cq<N>.rq" http://localhost:<port>/sparql`
   Then add the query's entry to `layer/<domain>/query-checks.yaml` (its `evidence`: `invariant` or `independent`)
   and run the gate in `verify` (with lifecycle: `lifecycle.py validate <domain> <qid> --artifact <query-checks.yaml>`).
   If the domain has no query-checks file yet, validation is pending, not passed. Say the level when you report:
   invariants are technical validation, not accuracy. If the business reading changes, re-propose and re-approve.
6. **Next:** to the app, follow `show-in-app`; to the evaluation, `evaluate`; values the source can get wrong,
   `quality-rules`; a predictive model, `rastro-lab` (only data known when the case started).

## A person approves

- **The proposal:** each question, its definitions and its ambiguous words, before the query is written.
- Each business definition, and any change to a question already used in the app or in the evaluation.

Worked examples from the existing domains: `examples.md`.
