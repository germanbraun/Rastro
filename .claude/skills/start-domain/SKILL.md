---
name: start-domain
description: Initialize a new Rastro domain and its experiment log before adding questions, sources or mappings. Use for a domain not yet registered in layer/dominios.yaml.
---

# Start a domain

Read `docs/method.md` and `docs/method-contracts.md`. This skill owns the pre-step-0 handoff.

When the domain or sources are still being selected, use `inspect-sources` first without registering a domain.
Reuse its findings and actual approvals; a favorable inspection alone does not approve scope.

## Contract

- **Takes:** a proposed domain, source candidates and the person responsible for its business definitions.
- **Returns:** an approved scope, domain registry entry, scaffold and experiment log; each runtime capability is
  explicitly pending or verified, never assumed from a copied configuration.
- **Does not:** invent questions, business definitions, reference answers or approvals.

## Steps

1. Start measuring agent and human time immediately; retain live notes until the log is initialized. Propose the name/prefix, region, period, sources and business-question owner. Reuse an existing scope approval;
   ask a person only for missing business decisions.
2. Inspect ports and existing services. Add the minimal folders, ontology header, mapping, notes and read-only user
   configuration described in the method. Add a registry entry. Omit capabilities not built; do not inherit another
   question set's evaluation command. Do not copy domain-specific constants into generic code.
3. Declare `method.lifecycle` (a JSON state file), `method.source_manifest` (a file recording source versions), and
   `method.app` for new domains. Use `layer/lifecycle.py` for every question handoff; update the source manifest when
   data changes, so prior validation receipts become stale. Do not synthesize human approval artifacts.
4. Run `python layer/method.py experiment <domain> --init` before domain implementation. Record initialization time,
   approvals and any framework changes as they occur. Never overwrite another experiment log.
5. Run `python layer/method.py registry <domain>`. Test the actual Ontop configuration: an empty mapping is not proof
   of a healthy service. If the runtime cannot start without mappings, record it as pending and build the first
   approved question's minimal implementation before claiming runtime readiness.
6. Hand off to `add-question` at **proposed/approved**, not with an invented executable query. Follow the lifecycle
   in `docs/method-contracts.md`; sources, mappings and links follow approved requirements.

## Check that decides

Registry validation passes; the log exists; scope decisions have evidence; runtime checks either pass with output or
remain explicitly pending. A new domain does not pass the full method until its questions, quality, measurement,
app and maintenance checks have their own evidence.
