---
name: verify
description: Verify a domain with executable registry and query assertions, quality outcomes, evaluation and app checks. Use after a change and before closing a phase or publishing a number.
---

# Verify Rastro

Read `docs/method-contracts.md`. New domains start with `start-domain`. Report passed, failed, pending and not
applicable separately. Record evidence in the experiment log while working; never infer readiness from a PID or port.

## Contract

- **Takes:** a registered domain and fingerprinted competency-query expectations based on approved invariants or
  independent reference evidence.
- **Returns:** commands, outputs and outcomes for each required capability; a failure or missing check blocks only
  the readiness or claim that depends on it.
- **Does not:** change expected answers to make a check pass or erase pre-existing local edits.

## Steps

1. From the repository root with the development environment active, run:
   ```bash
   python layer/method.py registry <domain>
   ```
   Missing capabilities mean pending. Inspect the declared evaluation harness before choosing commands.
2. Start the required services and check actual readiness, logs and source counts against the approved scope.
   A zero count can be expected for an approved empty scope; an unexplained zero is a failure. Preserve which optional
   services were already running and stop only those you started.
3. Check the selected ontology with `docker compose run --rm ontology-check python /ontology/check.py
   /ontology/<domain>` (oncology uses `/ontology`). Before release, check every registered domain explicitly;
   the default checker discovers all registered ontologies and deduplicates shared ones. It checks declared terms
   and shared-property `rdfs:domain` against explicit mapping classes; also compare class counts with source scope.
4. Run the query gate:
   ```bash
   python layer/method.py verify <domain> --expectations layer/<domain>/query-checks.yaml
   ```
   Cover every competency query. Empty answers must be explicitly expected. The contracts document the expectation
   format. HTTP error pages, CSV headers, stale query hashes and missing expectations cannot pass.
5. Run quality rules and their good/bad-example tests. Distinguish runner failure from successfully detected data
   defects. Record each relevant defect's human disposition and affected claims; do not demand defect-free sources.
   Missing quality coverage is pending or explicitly not applicable with a reason.
6. Re-run saved evaluation queries, then score, using the declared harness:
   - current: `<method.evaluation.run> rerun`, then `<method.evaluation.run> puntaje`;
   - legacy oncology: `<method.evaluation.run> python /layer/eval/run.py --rerun` (scoring is part of that runner).
   Compare answers and scores to the preserved starting files. Explain changes. Never use `git checkout` to discard
   date changes; preserve user edits and leave reviewed generated diffs available.
7. Exercise the domain in both app views and run every example query; test the model's own consistency checks when
   applicable. A health endpoint alone does not validate screen execution. Restart imported modules when needed.
8. Before publishing accuracy claims, run `python layer/method.py publication <domain>`. Missing independent review
   or stale artifacts keep scores provisional. Before closing a new-domain experiment, run
   `python layer/method.py experiment <domain> --check`.

## Report

For each capability: expected behavior, command, observed result and evidence path. Quality defect dispositions,
unrun checks and unavailable services are explicit. Do not say a domain is validated while its required checks are
pending. No full data-dependent readiness claim is established by lint or unit tests alone.

Historical domain commands and results are in `examples.md`; they are evidence, not fixed expected scores.
