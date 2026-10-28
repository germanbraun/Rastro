---
name: verify
description: Verify a domain with executable registry and query assertions, quality outcomes, evaluation and app checks. Use after a change and before closing a phase or publishing a number.
---

# Verify Rastro

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

Report passed, failed, pending and not applicable separately; never infer readiness from a PID or port.

## Contract

- **Takes:** a registered domain and fingerprinted competency-query expectations based on approved invariants or
  independent reference evidence.
- **Returns:** commands, outputs and outcomes for each required capability; a failure or missing check blocks only
  the readiness or claim that depends on it.
- **Does not:** change expected answers to make a check pass or erase pre-existing local edits.

## Steps

1. **Start the required services** (the domain's Ontop and what it needs; see `method.ontop`) and check actual
   readiness, logs and source counts against the approved scope. An unexplained zero count is a failure. Preserve
   which services were already running and stop only those you started.
2. **Run the gates in one command** (the default path), from the repository root with the development environment
   active:
   ```bash
   python layer/experiment.py <domain> --expectations layer/<domain>/query-checks.yaml [--measure] [--publish]
   ```
   It runs, in order, and keeps each exit code, output and duration under `data/cache/experiments/<domain>/<run>/`
   (`report.json`):
   - the registry (`layer/method.py registry`) and the ontology check (`ontology/check.py`);
   - if `method.quality` exists: the good/bad examples (`--examples-only`) and the rules over the data
     (`method.quality.run`);
   - the query gate (`layer/method.py verify`): one fingerprinted entry per competency query, each with its
     `evidence` level, `invariant` or `independent`. Report the level; «validated» alone does not mean «correct»;
   - if `method.app` exists and is not legacy: both app views and every example query (`app/check_domain.py`);
   - `--measure`: re-runs the saved evaluation queries and scores them, with the declared harness;
   - `--publish`: the publication gate (step 5).
   A missing capability is pending, not passed. If a gate fails, re-run it alone to read it (commands in
   `docs/method-contracts.md`).
3. **Read what the runner does not decide:**
   - quality: tell runner failure from a detected data defect; record each relevant defect's human disposition and
     the claims it affects; do not demand defect-free sources;
   - evaluation: compare answers and scores with the preserved starting files and explain changes. Never use
     `git checkout` to discard date changes; preserve user edits;
   - the model's own consistency checks, when the domain has one.
4. **App:** `docker compose run --rm --no-deps -T app python /app/check_domain.py <domain>` (the runner calls it
   too). A legacy app screen is exercised by hand in both views. A health endpoint alone does not validate the
   screens; restart imported modules when they changed.
5. **Before publishing accuracy claims:** `python layer/method.py publication <domain>` (or `--publish`). Missing
   independent review or stale artifacts keep scores provisional. The gate covers new claims; numbers already
   published stay as they are, labelled provisional until the gate passes. Before closing a new-domain experiment,
   run `python layer/method.py experiment <domain> --check`.

## Report

For each capability: expected behavior, command, observed result and evidence path. Quality defect dispositions,
unrun checks and unavailable services are explicit. Do not say a domain is validated while its required checks are
pending. No full data-dependent readiness claim is established by lint or unit tests alone.

Historical domain commands and results are in `examples.md`; they are evidence, not fixed expected scores.
