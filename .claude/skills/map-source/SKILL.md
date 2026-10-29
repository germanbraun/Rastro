---
name: map-source
description: Map a source that is already loaded to Rastro's business dictionary, in any domain - the ontology terms the questions need and the R2RML mapping that fills them. Use it when touching the ontologies, the R2RML mappings or the dictionary notes (sparql-notes.md), or when a competency question needs a term or a mapping that Rastro does not have yet.
---

# Map a source to the dictionary

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

If an inspection left a `semantic-layer-proposal.md`, start from it; it is a proposal, so the approvals below still apply.

Steps 2 and 3 of the method (`docs/method.md`): the dictionary and the mappings go together, because a new concept without
a mapping answers nothing, and a mapping without a concept does not exist for the assistant.

## Contract

- **Takes:** the competency questions that need the data (skill `add-question`) and the source already loaded in
  Postgres (skill `add-source`).
- **Returns:** the new terms in the domain ontology, their mapping, the notes the assistant reads, and the questions
  answering in Rastro.
- **Does not:** change the meaning of an existing term without a person, or link entities across sources
  (that is the skill `link-entities`).

## Constraints

- **Never invent** a source column, a table or an ontology term: everything the mapping references must exist.
- **No term as a side effect:** a new or changed term is always a visible proposal, approved before it is written.
- **Keep the source's identifiers** in the IRIs (`{id}` from the source), so every record can be traced back to its row.
- **Mark what is uncertain:** an unsure mapping goes into the proposal's open questions, never into the mapping as
  "probably right".

Where each piece lives comes from the domain's entry in `layer/dominios.yaml`:

| Piece | Registry key |
|---|---|
| Ontology | `ontology` |
| Mapping (one R2RML file per domain) | `method.mapping` |
| Notes for the assistant (dictionary) | `sparql_notes` |
| Notes for SQL with links | `links_notes` |
| Competency questions and their queries | `method.questions`, `method.queries` |
| Ontop service and port | `method.ontop.service`, `method.ontop.port` |
| Namespace and prefix | `namespace` (the prefix is the domain name, `<prefix>:`; never the empty prefix) |

A new domain gets its own entry, following the existing ones.

## Steps: narrow down, decide, test

1. **Narrow down, and write the proposal.** List what the question needs and look in the dictionary first: labels
   (`rdfs:label`), comments, types and the mappings that already exist. Reuse before creating. Look at the source table:
   columns, types, sample values, units and nulls. Write the result as a short table, before touching any file:

   | Source field | Term (existing or new) | Evidence (name, type, sample values, unit) | How sure | Open question |
   |---|---|---|---|---|

   A person reviews it at a glance; new terms and open questions are decided here. The table goes into the decision
   or the experiment log.
2. **Decide the term,** only if it is missing:
   - The name in English (`<prefix>:lengthM`), the label in Spanish and a short comment saying what it is and
     which source it comes from. If it has a unit, put it in the name or in the label.
   - An attribute before a new class. One single property per relationship (one property, and only one, links
     something to a given kind of thing).
   - **A property used by two classes has no `rdfs:domain`.** With a domain, Rastro deduces that everything that uses it
     belongs to that class.
   - If the definition can be read two ways, do not choose: it is a business
     decision.
3. **Write the mapping,** in the source's section of the domain's mapping (`method.mapping`):
   - One `rr:TriplesMap` per linker table or view, with the domain's IRI template
     (`https://w3id.org/rastro/<domain>/<thing>/{id}`) and the class.
   - `rr:datatype` on numeric and date columns (especially if they come from a `GROUP BY` or `DISTINCT`).
   - The source values as they are, without translating them.
   - If it is a link, `prov:wasDerivedFrom` (the source), `prov:wasGeneratedBy` (the rule), and the domain's rule and
     evidence-text properties (see the skill `link-entities`).
   - A domain started with `method.py new-domain` already maps its sources (`<#DataSource>`, from `rastro_meta.source`);
     keep that map and add the source's id to its `WHERE` (skill `add-source`).
4. **Tell the assistant:** the term in the dictionary notes (`sparql_notes`), said the way a business person would
   say it, and how to reach it from what already exists. **The same, at the same level, in the SQL-with-links notes**
   (`links_notes`): if one of the paths knows more, the evaluation is not fair. Add the term to `term_sources` (and to
   `link_sources` if it is a link) in `layer/dominios.yaml`.
5. **Test** (the checks below). Restart the domain's Ontop after changing the ontology or the mapping.

## The check that decides

- **Rastro starts:** `docker compose restart <method.ontop.service>` and the service is `healthy`. If it does not start,
  the error is in the mapping (a column that does not exist, a term that is not in the ontology):
  `docker compose logs <method.ontop.service>`.
- `docker compose run --rm ontology-check` is OK: each query uses only declared terms, in every domain.
- **Every competency question of the domain answers** and the answer makes sense to a business person:
  `python layer/method.py verify <domain> --expectations layer/<domain>/query-checks.yaml`. If the domain has no
  query-checks file yet, query each competency question with `curl` (see `add-question`) and record the executable
  check as pending.
- **The counts match the source:** `SELECT (COUNT(DISTINCT ?x) AS ?n) WHERE { ?x a <prefix>:<Class> }` against
  `SELECT count(*)` on the table. If Rastro counts too many, it is almost always an extra `rdfs:domain`.
- **What was measured does not change by accident:** run the domain's evaluation (`method.evaluation.run`) with
  `rerun` and `puntaje` for the current harness (the declared legacy runner otherwise); review the generated diffs
  without resetting other people's edits. No `method.evaluation` in the registry means the domain is not measured yet.
- **Lifecycle:** if the domain declares `method.lifecycle`, a changed ontology or mapping makes its questions'
  validations stale; validate them again with `layer/lifecycle.py validate` (see `add-question`).

## A person approves

- **The proposal:** its new terms and its open questions, before the mapping is written.
- Each new term that is a **business definition** (what a business word means in that domain).
- Changing the meaning of a term already used in questions, in the app or in the model.

## Watch out for

- **`rdfs:domain` on a shared property:** if a second class also uses the property, Rastro types every subject of the
  second class as the first one too, and the counts double. Compare the class count with the table count; a quality
  rule that checks too many values shows it.
- **One note missing from the dictionary:** if the notes do not describe a term, the assistant reaches the data by
  another path and gets a different answer. Fix it with one line in the notes, and the same line in the SQL-with-links
  notes.
- **Two similar words for the same thing:** the assistant picks the wrong one. Keep only one.
- **Ontop does not support `*` or `+` paths:** anything that needs a closure (a hierarchy, a "within") is precomputed in
  Postgres and mapped as a plain property.
- **After changing something, restart the domain's Ontop;** the app does not reload imported modules:
  `docker compose restart app`. Texts shown in the app change through `show-in-app`.

Real cases, with their numbers: see `examples.md`.
