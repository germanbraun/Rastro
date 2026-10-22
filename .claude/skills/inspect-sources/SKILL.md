---
name: inspect-sources
description: Inspect candidate public data sources before choosing a domain or approving a new source. Propose grounded questions and a minimal conceptual semantic layer without registering a domain or building a loader.
---

# Inspect candidate sources

Read `docs/method.md` and `docs/method-contracts.md`. This is the optional discovery handoff before `start-domain`,
or before `add-source` when an existing domain needs an unfamiliar source. It does not replace either workflow.

## Contract

- **Takes:** the user's objective, candidate domain or sources, existing questions if any, and any approved time
  budget, scope and reviewer roles. Reuse those decisions; do not restart their approval.
- **Returns:** an evidence-backed source profile, a feasibility recommendation, unresolved decisions and candidate
  business questions when requested; then a minimal conceptual semantic-layer proposal when questions and inspected
  sources support it. No source, question, model or implementation is approved by the inspection itself.
- **Does not:** load a database, register a domain, start services, change the app, implement mappings/links, or
  evaluate model answers. Inspection downloads and local profiling are allowed within the authorized scope.

## Workflow

1. **Record the objective and working interval.** Use the agreed budget and stop at its limit, reporting partial
   findings. Log actual session start/stop times and pauses as work happens. Separate session elapsed time,
   automated process duration and human effort; missing human time stays missing. Do not count another chat's time.
2. **Find original publishers and inspect actual access.** Consult connected sources or browse official catalogs,
   APIs and documentation. Record source and download URLs, access date, response failures and final transport
   after redirects. A search snippet, accessible catalog or HTTP success alone does not prove a usable data file.
3. **Preserve the inspected snapshot.** Download only what is useful for inspection into ignored `data/raw/`.
   Record byte count, SHA-256 and source version for every artifact supporting the findings. Keep public metadata
   and reproducible profiling scripts in the report folder when useful; keep raw files, credentials and response
   headers containing cookies outside version control. Do not change project dependencies solely to read a file.
4. **Profile content and meaning.** Establish record grain, candidate keys, nulls and duplicates, units, observation
   period, geography and relevant source definitions. Distinguish reporting year, upload/modification time and
   effective date. Check for multiple tables, aggregates, market/category partitions and temporal role changes
   before proposing a join or sum. Report bounded samples as samples, not full-file measurements.
5. **Check reuse and reproducibility.** Record the publisher's actual license/access terms, refresh policy and
   version mechanism. Distinguish the license on a catalog from terms on separately hosted files. State unclear
   permissions and mutable/unpinned inputs as unresolved; do not infer permission or immutable versions from access.
6. **Inspect the integration.** Compare keys and concrete records across sources. Show matched candidates, missing
   keys, ambiguous alternatives, grain mismatches and what evidence could resolve them. Candidate links remain
   unapproved. Trace upstream origin: two publishers repeating the same data are not independent measurements.
   Complementary sources can still be useful; an independently calculated original-record reference can verify an
   answer without a second publisher reporting the same number. Record overlap with Rastro's existing knowledge.
7. **Return a bounded recommendation.** Say suitable, conditional, unsuitable or incomplete, with supporting
   findings and remaining decisions. When proposing questions, give plain wording, definitions, answer type,
   required sources, integration/control role and an independent verification plan. Respect the requested count;
   do not manufacture questions to favor Rastro or assume B/D/C accuracy must differ.
8. **Propose the semantic layer after inspection.** Ground a minimal conceptual model in proposed questions and
   inspected fields. Save `semantic-layer-proposal.md` beside the report: purpose, a concept/source/question table,
   entity grain and candidate identifiers, relationships/cardinality, a small diagram and a worked source example
   alongside it. Explain counting, deduplication, time, provenance and unresolved links. Label illustrative text
   and unreviewed identifications; never invent source records or approvals. Show why each concept is needed; reuse
   the dictionary for domain extensions. If evidence or questions are insufficient, mark the model pending and say
   what is missing. This proposes business meaning, not executable ontology/R2RML or permission to implement it.
   Reuse recorded approvals; new or changed meanings follow the existing business-approval rules.

## Evidence and handoff

For a candidate experiment, use `docs/experiments/<candidate>/`; for existing-domain upkeep, use its source notes
and record the decision in `docs/decisions.md`. Do not require a registry entry or initialize a domain experiment
merely to inspect sources. Retain:

- A concise report covering access, terms, versions, grain, keys, coverage, join examples, independence, familiarity
  and recommendation; distinguish observed facts, derived measurements and hypotheses.
- A snapshot manifest with source URLs and fingerprints, plus enough commands or profiling code to reproduce
  reported measurements. Never copy response values into future expected answers just to make checks pass.
- The measured time, actual interventions and unresolved decisions. Identify review as pending until it happens.
- The conceptual semantic-layer proposal, diagram and grounded example when feasible; otherwise why it is pending.
  Hand it to `map-source` to refine from approved questions and loaded data.

Check hashes and reproducibility of the reported measurements; validate any new scripts. Unreadable files and
unconfirmed units remain explicit limits, not successful checks. A metadata-only result can be useful but must say so.

After the user approves the selected scope, hand a new domain to `start-domain`; questions go through `add-question`
and loaders through `add-source`. Reuse real approvals and keep their exact boundaries. The inspection alone
establishes neither answer accuracy nor transfer of the method. Do not retroactively claim this skill was used for
an earlier inspection; record when it was introduced if it affects an experiment's frozen method version.

Read [examples.md](examples.md) for the electricity inspection that motivated this skill, not for domain rules.
