# Executable contracts for the Rastro method

These contracts apply to every method skill. They make `method.md` operational; they do not turn an agent's
opinion into evidence. Existing domains are legacy evidence, not retroactively approved experiments.

## Lifecycle and handoffs

Use `start-domain` before the first question. Record each question's state alongside the question:

| State | Required evidence | Next owner |
|---|---|---|
| proposed | Business wording, scope, answer type, proposed definitions, uncertainties | A person decides business meaning |
| approved | Approved definitions and scope, reviewer and date; expected answer or an independent verification plan | `add-source`, then `map-source` and `link-entities` as needed |
| implemented | Query using loaded data and declared terms; source and mapping versions | `verify` |
| validated | Executed assertions, query fingerprint, date and output, and the level they rest on; approved reference evidence for published accuracy | `evaluate`, then `show-in-app` |

**Two levels of validation.** A question validated against invariants of its approved definitions is **technically
validated**: its query is well formed and covers what it must, but nobody has compared its answer with an independent
reference. It is validated **with independent references** only when its expectations come from the sources without
going through Rastro (SQL over the raw tables, a blind annotation). The level is declared in the expectations and
recorded in the lifecycle; never read «validated» as «correct» without it. The app's technical view says which.

**Two roles.** The business owner approves requirements and definitions. The reference reviewer provides the evidence
the answers are compared with, blind to Rastro's links. One person or record cannot stand in for the other: the
publication gate refuses a reference reviewer who approved the requirements. What Rastro counts (the system's
definition) and what the reviewer checks (the reference's) are written separately in each requirement. A changed
business reading always goes back into the requirement file and the lifecycle (re-propose, re-approve), never only
into a discussion note.

An approved question does not yet need a working query. Do not invent terms to satisfy the early stage. `add-question`
returns an approved requirement first and resumes query implementation after its dependencies exist. Failed checks
keep the question implemented or blocked, never validated. A changed definition reopens approval; a changed query
invalidates its checks. Reuse recorded approvals unless the decision changes. Routine technical work needs no new
business approval. Single-source questions are allowed as useful business requirements and controls; identify which
questions actually test cross-source integration.

## Registry and query checks

From the checkout root, with the development Python environment active:

```bash
python layer/method.py registry
python layer/method.py verify <domain> --expectations layer/<domain>/query-checks.yaml
```

`registry` checks known harnesses, evaluation targets and existing paths. Omitted capabilities mean **not built**, not
passed. Current evaluations use `prompt`, `try`, `rerun`, `puntaje`; legacy oncology uses its own runner (`--rerun`),
not current-harness subcommands. Do not migrate historical measurements merely to verify them.

`query-checks.yaml` has exactly one entry per competency query, named `cq<N>.rq`. Each has its `query_sha256`, exact
ordered `columns`, its `evidence` (`invariant` for technical checks, `independent` when the expected values come from
the sources without Rastro), and explicit assertions: `rows`, `min_rows`, `max_rows`, `values` (rows as lists),
`number: {column: ..., value: ..., relative_tolerance: ..., absolute_tolerance: ...}`, `keys: {columns: [...], file:
<repo-relative CSV derived from the sources>, repeats: true|false}` (the answer's key set equals the file's, without
repeated keys unless allowed), or `bounds: {<column>: {min: ..., max: ...}}` (every row). Multiple assertions all
apply. A question binds to its own entry: editing another query's entry does not invalidate it.
`rows: 0` expresses a deliberately empty result. Numeric tolerances default to zero. Expected values come from
independent evidence or approved business invariants, never copied from the response just to pass. A count bound is
an invariant check, not evidence of answer accuracy. Missing or stale checks block validation.

The runner requires HTTP success and CSV content, parses data rows separately from headers, and exits nonzero on any
failed assertion. Keep its output with the experiment evidence. It does not by itself validate the app or model.
Run the app's examples in both views and the model's own consistency checks separately.

## The experiment log

`docs/experiments/<domain>.yaml` is written by commands, never by hand (four hand-editing errors in the affiliations
experiment: a duplicate key, an unparseable file, an end written early, hours never updated):

```bash
python layer/method.py experiment <domain> --start <step> [--at <ISO time>]
python layer/method.py experiment <domain> --stop <step> --work "what the session did" [--at <ISO time>]
python layer/method.py experiment <domain> --append intervention|error|method-change --field key=value ...
python layer/method.py experiment <domain> --lint     # at any time; close-phase runs it before committing
python layer/method.py experiment <domain> --check    # closing: complete, and the log lints
```

A step's `agent_hours` is the sum of its sessions minus their pauses. The lint refuses duplicate keys, overlapping
sessions, an end before its start, more than one open session (none when closing) and hours that differ from the
sessions. A time given with `--at` after the fact says «approximate» in the session's work.

## Independent references and publication

Exploratory `puntaje` remains available. Its score is **provisional** until:

```bash
python layer/method.py publication <domain>
```

Create `<method.evaluation.folder>/reference-evidence.yaml` from actual evidence. It contains:

- `questions_sha256`: fingerprint of that harness's questions file.
- `run`: `model`, `model_version`, `source_versions`; `prompt_artifacts` and `attempt_artifacts`, each a list of
  `{path: <repo-relative file>, sha256: <fingerprint>}`; `result_artifact` with the same path/fingerprint shape.
- `references`: one entry keyed by every question id, even when all approaches agree. Each records `source`,
  `source_version`, `checked_answer` (zero and empty lists are valid), `independent: true`, `status: approved`,
  `reviewer`, `reviewed_on`, `artifact` (repo-relative evidence file), `sha256`, and `adjudication` (the decision or
  an explicit statement that the approaches agree).

`layer/review_packet.py <domain> build` prepares the reviewer's packet and form; `record` writes the
`references`, `questions_sha256`, `result_artifact`, `attempt_artifacts` and `source_versions` from the filled form.
It also copies `model` and `model_version` from `<folder>/eval/run.yaml` (written by whoever measured) and lists the
prompts `evaluar.py prompt` kept in `<folder>/prompts/` as `prompt_artifacts`.

Independent means checked against original source records, a separately calculated reference, or an applicable
published figure, rather than trusting the Rastro reference query. Preserve definitions, units and period. The gate
checks B/D/C coverage, that independently checked answers match the scored references, fingerprints and review records; it cannot establish a human's identity or the truth of a review.
Never invent approvals. Re-run it immediately before showing new accuracy claims; a changed result or evidence
invalidates the approval bundle. Do not silently rewrite historical published claims.

Keep B, D and C equally informed, record the exact model version and all retries, and preserve evaluator isolation.

## Quality outcomes

Distinguish **execution failure**, **detected data defect**, and **reviewed disposition**. A failed runner, missing
coverage, or a broken good/bad-example test blocks completion. A correctly detected source defect stays visible with
its affected answers/predictions. A person records whether to correct, exclude or retain it with a warning. Do not
require a defect-free source or lower a threshold to close a phase. An unreviewed defect affecting a published claim
blocks that claim. Missing domain quality rules are pending unless explicitly not applicable with a reason.

## Safe change tests

Run on an isolated development database with other writers stopped. Every domain with `method.change_guard` in
the registry (oil and gas, suppliers, affiliations) enters `layer/change_guard.py` automatically for `registrar`.
The column a `cambio` test renames is declared there too (`renamed`), so the guard checks it before and restores it. The guard takes a shared nonblocking lock, snapshots actual local files (including
pre-existing edits and untracked answers) and affected database tables, then restores them on exit or interruption.
It rebuilds the derived layer and waits for Ontop health. Tables are compared with `EXCEPT ALL` after restoration;
files are compared byte for byte. Do not use Git checkout/reset or inverse arithmetic as recovery.

`cambio` restores its saved source and mapping between acts. Standalone mutations are refused outside the guard.
On recovery failure, backups remain in ignored `data/cache/change-test-guard`; stop work and run:

```bash
python layer/change_guard.py recover
```

A killed machine cannot run cleanup: recover before starting another test. Do not delete a recovery directory to
bypass a failed restoration. Result JSONs are test evidence; test-created model runs are removed when the original
model tables are restored. Do not run other loaders, model publishers or file editors during a change test.

## Experiment evidence and closure

For a new domain experiment, initialize its log before doing domain work:

```bash
python layer/method.py experiment <domain> --init
```

This creates `docs/experiments/<domain>.yaml` exclusively: it never overwrites a log. Fill it as work happens, not by
reconstructing invented timings afterwards. Header fields: `domain`, `sources`, `question_author`, `started_on`,
`ended_on`, `method_commit`. `steps` has `initialize`, `questions`, `sources`, `mapping`, `links`, `quality`, `evaluate`,
`show`, `maintain`, each with `status` (`completed` or `not_applicable` at closure), `evidence` (paths or reason),
`agent_hours` and `human_hours` (measured nonnegative numbers).

Record `interventions` (`step`, `decision`, `reason`, `kind`, `minutes`), `errors_caught` (`step`, `check`, `failure_kind`, `fix`), and `method_changes` (`change`, `scope` set to generic or domain-only, `reason`) as lists; use `[]` explicitly for none.
`result` records B/D/C results, quality outcome and totals. Never mark unrun work completed. Missing measurements
remain pending and prevent claiming a completed generalization experiment.

At closure run `python layer/method.py experiment <domain> --check`, registry/query checks, relevant tests, and the
publication gate when publishing numbers. Check recorded business approvals and defect dispositions. Legacy upkeep
does not require fabricated experiment history: say it is not a generalization experiment and record current work
in `docs/decisions.md`. Technical checks still apply.


## Enforced lifecycle commands

New domains declare `method.lifecycle` (JSON state path) and `method.source_manifest` (a versioned source snapshot
manifest). Existing domains do not acquire fictional approvals through migration. From the repository root:

```bash
python layer/lifecycle.py propose <domain> <qid> --artifact <proposal.yaml>
python layer/lifecycle.py approve <domain> <qid> --artifact <human-review.yaml>
python layer/lifecycle.py implement <domain> <qid> --artifact <registered-query.rq>
python layer/lifecycle.py validate <domain> <qid> --artifact <query-checks.yaml>
python layer/lifecycle.py status <domain> <qid>
```

A proposal requires `question`, `definitions`, `scope`, `answer_type`, `verification_plan`. A human-review artifact
requires `actor: human`, `decision: approved`, `reviewer`, `reviewed_on` (ISO date), and `proposal_sha256` binding the
exact proposal. These are records of real approval, not identity authentication. Validation actually runs the
ontology/mapping check and every query assertion. The state file preserves transition events and artifact hashes.

Changed proposal or approval artifacts require renewed approval. Changed queries, ontology, mapping or source
manifest invalidate implementation/validation. Changed expectations invalidate validation. Loaders must refresh the
source manifest on every source version change; unchanged metadata cannot prove that an unrecorded database edit
did not happen. The app exposes only currently validated questions for adopted domains, and hides new accuracy cards and guided demos
until the independent-reference gate passes. Missing source versions cannot produce a validation receipt.

## Generic quality and app infrastructure

`ontology/check.py` discovers the registry's ontology/mapping/query paths and rejects `rdfs:domain` on properties
mapped from more than one explicit subject class. It does not infer correctness from its own inferred types.

`ontology/calidad.py <domain>` loads that domain's `method.quality` configuration. Required files: `rules`, `examples`,
`data` (CONSTRUCT query list) and `result`. Optional `prefix` overrides the domain's prefix; optional `predictions`
returns full `?prediction ?record` IRIs, filtered to the current run. No prediction module means no such query.
Good/bad examples must target actual nodes; vacuous passing examples are rejected. Multiple explicit SHACL targets
are combined. Zero-target production rules report coverage pending and exit 2; real defects remain reported without
being automatically corrected. Tests discover every configured domain, not only energy.

The app reads `method.app`; its `technical.instances`, `technical.pieces`, optional `technical.map` hold the previous
per-domain Python lists and queries. Console/ontology paths and ports come from the registry. No Lab schema is
required to invalidate the app cache: the cache tracks PostgreSQL writes. New domains use the existing template.
Legacy oncology keeps its screen, marked `method.app_mode: legacy`, while its technical metadata uses the same path.

`app/check_domain.py <domain>` executes real example queries and both Streamlit views inside the app service; it does
not use the synthetic transports used by the unit tests. Run it after starting the domain's real services.

## Repeatable experiment execution

`python layer/experiment.py <domain> --expectations <query-checks.yaml> [--measure] [--publish]` runs registry,
ontology, quality, query and app gates. `--measure` re-executes saved B/D/C queries, not fresh model responses;
new isolated evaluators remain necessary to measure a new question set. `--publish` runs the independent evidence
gate. Every check retains its exit code, output and measured execution duration under ignored
`data/cache/experiments/<domain>/<run>/`, plus a report binding the method files to their hashes. Missing real
services or evidence produce failures, not simulated success. These timings are process durations, not invented
agent/person working hours. Keep working time and human decisions in the experiment log.

The country/currency proposal and inspected public-source hashes live in `docs/experiments/countrycodes/`. It is
explicitly unapproved. Synthetic new-vocabulary tests prove machinery executes; neither those tests nor a single
technical pilot establish transfer to two independently approved unfamiliar domains.
