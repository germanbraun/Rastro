---
name: inspect-sources
description: Inspect candidate public data sources read-only before choosing a domain or approving a new source, and propose grounded questions and a minimal conceptual semantic layer. Use it when a domain is not chosen yet, or when an existing domain needs a source whose access, terms, keys or joins are still unknown.
---

# Inspect candidate sources

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

Optional discovery before `start-domain` (a new domain) or `add-source` (an unfamiliar source for an existing domain).
It replaces neither, and it approves nothing.

## Contract

- **Takes:** the objective, candidate domain or sources, existing questions if any, and any approved time budget,
  scope and reviewer roles. Reuse those decisions.
- **Returns:** a source profile with evidence, a recommendation, open decisions, candidate questions when asked, and
  a minimal conceptual semantic-layer proposal when the evidence supports it.
- **Does not:** load a database, register a domain, start services, change the app, implement mappings or links, or
  evaluate answers. Downloads and local profiling within the authorized scope are allowed.

## Steps

1. **Objective and budget.** Stop at the agreed budget and report partial findings. There is no registered domain
   yet, so `method.py experiment` cannot log time: keep start, stop and pauses in an `inspection-time.yaml` in the
   report folder, filled as you work. Missing human time stays missing.
2. **Original publishers and real access.** Record source and download URLs, access date, failures and redirects. A
   catalog page or an HTTP 200 does not prove a usable data file.
3. **Snapshot.** Download only what the inspection needs into `data/raw/`. Record bytes, SHA-256 and source version
   of every file behind a finding. Raw files and credentials never go into the repo.
4. **Content and meaning.** Grain, candidate keys, nulls, duplicates, units, period, geography and source
   definitions. Tell reporting year, upload date and effective date apart. Look for mixed tables, aggregates and
   partitions before proposing a join or a sum. A sample is reported as a sample.
5. **Reuse terms.** The publisher's actual license, refresh policy and versioning; a catalog's license may not cover
   files hosted elsewhere. Unclear terms stay open questions.
6. **Integration.** Compare keys and real records across sources: matches, misses, ambiguous candidates, grain
   mismatches. Trace upstream origin: two publishers repeating the same data are not independent evidence. Note what
   Rastro already knows.
7. **Recommendation:** suitable, conditional, unsuitable or incomplete, with findings and open decisions. Candidate
   questions get plain wording, definitions, answer type, sources, whether they test integration, and an independent
   verification plan. Do not shape questions to favor Rastro.
8. **Conceptual semantic layer**, only when questions and inspected fields support it: `semantic-layer-proposal.md`
   beside the report, with a concept/source/question table, grain and identifiers, relationships, a small diagram
   and one worked source example. Label illustrative text; never invent records or approvals. Otherwise say what is
   missing. It is a proposal for `map-source`, not an ontology.

## Evidence and handoff

Keep it in `docs/experiments/<candidate>/` for a new domain; for an existing domain, in its source notes and an entry
in `docs/decisions.md`. Keep: the report (facts, measurements and hypotheses told apart), a snapshot manifest with
URLs and fingerprints, the profiling code that reproduces the numbers, the time file, and the proposal or why it is
pending. Unreadable files and unconfirmed units are limits, not passed checks.

After a person approves the scope: a new domain goes to `start-domain`, questions to `add-question`, loaders to
`add-source`.

Real inspections: [examples.md](examples.md).
