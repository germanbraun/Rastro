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
2. **Scaffold and registry entry,** in one command, once the name and scope are approved:
   ```bash
   python layer/method.py new-domain <domain> --title "<what it is about, in Spanish>"
   ```
   It writes the folders, the ontology header (with the domain's `DataSource`, `name` and `license`), a mapping whose
   only map reads the domain's sources (none until the first one, but Ontop starts), the notes, `reader.sql`, the
   registry entry with only the keys whose piece exists, the app's file and list entry (hidden until the first
   question), the Ontop service on the next free port and its customer
   settings. It refuses to overwrite anything. Do not copy another domain's evaluation command or constants.
3. **Lifecycle.** `new-domain` declares `method.lifecycle` (the state file appears with the first transition);
   declare `method.source_manifest` (the source versions, written by the loaders) with the first loader, and
   `method.app` with `show-in-app`. Every question goes through `layer/lifecycle.py`
   (`propose`, `approve`, `implement`, `validate`); never synthesize a human approval artifact.
4. **Experiment log.** Only after the registry entry passes (the command refuses an unknown domain), and before your
   first commit (it records `git HEAD` as the frozen method):
   ```bash
   python layer/method.py experiment <domain> --init
   python layer/method.py experiment <domain> --start <step>
   python layer/method.py experiment <domain> --stop <step> --work "what the session did" [--status completed] [--evidence <path>]
   python layer/method.py experiment <domain> --append intervention|error|method-change --field key=value ...
   python layer/method.py experiment <domain> --set sources="<source, version>" --set question_author="<who>" --set result="<one line>" --set ended_on=<ISO time>
   python layer/method.py experiment <domain> --human-hours <step>=<hours as the person reports them>
   ```
   Steps are exactly `initialize`, `questions`, `sources`, `mapping`, `links`, `quality`, `evaluate`, `show`,
   `maintain` (the command accepts any name; a typo only fails at `--check`). Sessions and appended entries always go
   through the command. The header fields and human hours also go through the command (`--set`, `--human-hours`); a
   missing human time stays empty, never estimated.
5. **Check the shell.** Run `python layer/method.py registry <domain>`. Start the Ontop service: with the scaffold's
   sources map it starts and answers (0 sources until the first one); Ontop refuses a mapping with no map at all.
   A healthy service answering nothing is not a working domain: readiness comes with the first approved question's
   minimal implementation.
6. **Hand off** to `add-question` at proposed/approved, not with an invented query.

## Check that decides

Registry validation passes; the log exists and lints; scope decisions have evidence; runtime checks pass with output
or stay explicitly pending. A new domain does not pass the full method until its questions, quality, measurement,
app and maintenance checks have their own evidence.
