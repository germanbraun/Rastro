# Process notes: what the method and its skills got right, missed, or should flag

Written as the experiment runs, not reconstructed afterwards. Each note says where it happened, what happened, and
what to change. The user asked for this alongside the deliverable: a simple semantic layer for the three approved
questions, plus conclusions to improve the skills. Method frozen at `05428c5`; changes proposed here are not applied
to the skills during the experiment (they would count as method changes).

Severity: **important** (can make a result wrong or unverifiable), **gap** (missing guidance that cost time or a
decision), **minor** (friction).

| # | Step and skill | What happened | Severity | Proposed change |
|---|---|---|---|---|
| 1 | Inspection, `inspect-sources` | The bounded set was estimated at "about 200 strings" by counting only strings that mention Argentina; the approved questions cover every affiliation, so the real set has 962. Caught at the draw, after scope approval. | important | `inspect-sources`: size the set in the **unit the questions count** (here, every affiliation of the selected works), and show reviewer workload before scope approval. |
| 2 | Inspection, `inspect-sources` | The first probe mixed raw and normalized string counts, kept one organization per shared acronym, and read e-mail domains as evidence. The reviewer caught all three. | important | `inspect-sources`: state the counting unit of every number; strip contact data before any name probe; index acronyms to sets. A reviewer step was essential, keep it mandatory. |
| 3 | Inspection, `inspect-sources` | The first capture of a live API (Crossref) had no request ledger, so it could not be reviewed; a re-capture was needed. | gap | `inspect-sources`: for live APIs, capture with a request ledger from the start (query, pages, totals, termination, hashes). |
| 4 | Initialize, `start-domain` | `method.py experiment --init` records `git HEAD` as the frozen method version, so it must run before committing anything else. The skill does not say so. | gap | `start-domain`: say "initialize the log before your first commit", or let `--init` take the method commit explicitly. |
| 5 | Initialize, `start-domain` | The skill says both "omit capabilities not built" and "declare `method.app` for new domains"; declaring it requires an app file that does not exist yet. Resolved by omitting it. | minor | `start-domain`: declare `method.app` when the app step starts. |
| 6 | Initialize, `start-domain` | Ontop does not start with an empty mapping (the skill anticipates this). Runtime readiness can only be checked after the first mapped term. | minor | Keep as is; optionally a minimal placeholder mapping so the service health can be checked at initialization. |
| 7 | Experiment log | Session times, hours and interventions are edited by hand in YAML. Two errors in this run: a duplicated `reason` key (silently keeps only the last value) and an end time written before the work ended. Both caught and fixed. | important | A small command to open and close sessions and append interventions (`method.py experiment <domain> --start/--stop/--note`), and `--check` should reject duplicate keys. |
| 8 | Questions, `add-question` and lifecycle | The approval record has one `reviewer`. In this experiment the person who approves business definitions (the user) and the person who adjudicates references (a named reviewer, still pending) are different roles. | gap | Contracts: name both roles, the business owner for requirements and the reference reviewer for evidence; the lifecycle should not let one stand in for the other. |
| 9 | Sources, `add-source` | The skill assumes the loader downloads its data. Here the loader must load the **approved snapshot** from the inspection, because a fresh request to a live API is a different snapshot. | gap | `add-source`: when an inspection snapshot was approved, load that snapshot and check its fingerprint; never re-download silently. |
| 10 | Sources, `add-source` | Step 1 asks a person to approve a source profile, which the inspection and the scope approval already covered. Reused, as the contracts allow. | minor | `add-source`: say explicitly that an approved inspection profile satisfies step 1. |
