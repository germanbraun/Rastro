---
name: start-domain
description: Initialize a new Rastro domain and its experiment log before adding questions, sources or mappings. Use for a domain not yet registered in layer/dominios.yaml.
---

# Start a domain

Read `docs/method.md` and `docs/method-contracts.md`. This skill owns the step before step 0. Record time,
interventions and caught errors as you work.

When the domain or sources are still being selected, use `inspect-sources` first without registering a domain.
Reuse its findings and actual approvals; a favorable inspection alone does not approve scope.

## Contract

- **Takes:** a proposed domain, source candidates and the person responsible for its business definitions.
- **Returns:** an approved scope, domain registry entry, scaffold and experiment log; each runtime capability is
  explicitly pending or verified, never assumed from a copied configuration.
- **Does not:** invent questions, business definitions, reference answers or approvals.

## Steps

1. **Scope.** Start measuring agent and human time now; keep notes until the log exists. Propose the name/prefix,
   region, period, sources and business-question owner. Reuse an existing scope approval; ask a person only for
   missing business decisions.
2. **Scaffold and registry entry.** Check free ports and existing services. Add the folders, ontology header, empty
   mapping, notes, read-only users and Ontop service described in `docs/method.md` ("Before step 0"). Add the registry
   entry. Leave out capabilities not built; do not copy another domain's evaluation command or constants.
3. **Lifecycle.** Declare `method.lifecycle` (a JSON state file), `method.source_manifest` (the source versions,
   written by the loaders) and `method.app`. Every question goes through `layer/lifecycle.py`
   (`propose`, `approve`, `implement`, `validate`); never synthesize a human approval artifact.
4. **Experiment log.** Only after the registry entry passes (the command refuses an unknown domain), and before your
   first commit (it records `git HEAD` as the frozen method):
   ```bash
   python layer/method.py experiment <domain> --init
   python layer/method.py experiment <domain> --start <step>
   python layer/method.py experiment <domain> --stop <step> --work "what the session did" [--status completed] [--evidence <path>]
   python layer/method.py experiment <domain> --append intervention|error|method-change --field key=value ...
   ```
   Steps are exactly `initialize`, `questions`, `sources`, `mapping`, `links`, `quality`, `evaluate`, `show`,
   `maintain` (the command accepts any name; a typo only fails at `--check`). Sessions and appended entries always go
   through the command. No command sets `sources`, `question_author`, `ended_on`, `human_hours` or `result` yet:
   until one exists, fill those header/result fields by hand, then run `experiment <domain> --lint`.
5. **Check the shell.** Run `python layer/method.py registry <domain>`. Start the Ontop service: an empty mapping is
   not proof of a healthy service. If it cannot start without mappings, record it as pending and build the first
   approved question's minimal implementation before claiming readiness.
6. **Hand off** to `add-question` at proposed/approved, not with an invented query.

## Check that decides

Registry validation passes; the log exists and lints; scope decisions have evidence; runtime checks pass with output
or stay explicitly pending. A new domain does not pass the full method until its questions, quality, measurement,
app and maintenance checks have their own evidence.
