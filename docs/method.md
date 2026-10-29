# The Rastro method

How to build and maintain a semantic layer people can trust, in any domain. It is what was already done for oil and gas,
US federal suppliers and oncology, written down as a method. It is not automated yet: this document is the sketch.

## The idea

**An agent builds and maintains the semantic layer; every decision keeps its evidence; a person approves what is a
business decision.** The agent does the work; the checks decide whether it is right; the person decides what it means.

Three principles:

1. **Questions first.** What to map, and how to measure whether it works, comes from the business questions.
2. **Correctness is decided by tests that run**, not by a model's opinion: it loads, it answers, it passes the quality
   rules, it gets the questions right against independent references.
3. **What a value means is decided by a person.** Whether a company "operates", "owns", "has a share in" or "reports
   production for" something is not interchangeable. The agent proposes, with evidence and alternatives; it does not
   decide silently.

The executable handoffs, evidence formats and gates are specified in [method-contracts.md](method-contracts.md).

## The steps

Each step has a skill that does it, a check that decides whether it passes, a human approval only where there is a
business decision, and the evidence that remains.

| # | Step | Done by (skill) | Check that decides | A person approves | Remains as evidence |
|---|---|---|---|---|---|
| 0 | **Business questions** | `add-question`: each question with its definitions and answer type | Every question has a definition, an expected answer and its query | The client: which questions matter and what each word means | `ontology/<domain>/competency-questions.md` |
| 1 | **Connect the sources** | `add-source`: download, load, record the load | Count per source, fingerprint of each file, repeatable load | The scope: what goes in and what doesn't | `rastro_meta.load_run` |
| 2 | **Minimal dictionary** | `map-source`: only the concepts the questions need | `ontology-check`: every term exists; a property used by two classes has no domain | The definitions (for example, operated or by share) | The ontology, with comments |
| 3 | **Mappings** | `map-source`: how each source translates to the dictionary | Rastro starts and every competency question answers | — | The R2RML mapping |
| 4 | **Links with evidence** | `link-entities`: join companies, wells and concessions across sources, with their rule and text | Quality rule: every link has a source and evidence | The doubtful corrections («revisado por IA, a confirmar»), in the app: «Por qué confiar» → «Uniones para confirmar» | `prov:wasDerivedFrom`, rule and evidence on every link; reviewed CSVs |
| 5 | **Quality rules** | `quality-rules`: rules and possible values | `calidad` (SHACL) after every load, with the predictions that use what fails | The thresholds, and whether the source is corrected | `layer/<domain>/calidad.json` |
| 6 | **Measure** | `evaluate`: three approaches (without Rastro, SQL with links, with Rastro); what it does when the data is missing; change test | Independent evaluators that only see their prompt; references that don't come only from Rastro | The adjudication where approaches differ; the blind tests | `layer/<domain>/resultados.json`, `adjudicacion.md` |
| 7 | **Show** | `show-in-app`: the business view (questions in plain words, why each number, what can be trusted) and the technical view (queries, generated SQL, data as tables and RDF, dictionary, links, quality rules); optional modules such as questions over texts | The app loads the domain in both views; every example question runs; every number on screen comes from its file | The wording for business users; the demo questions; the themes and citations of text summaries | `app/dominios/<domain>.yaml` |
| 7b | **Explain how** | `walkthrough`: a «Paso a paso» that follows one real case through each part of Rastro (dictionary and mappings, links with evidence, the answer and its origin; for a model, its inputs, calculation and evidence), read live, with what each step shows and its slides | Every step renders in both views with its queries; every number in the text and slides matches a query today | The case, the purpose and the wording of each step | `ejemplo_integracion` and `ejemplo_lab` in `app/dominios/<domain>.yaml`; the «Paso a paso» slides |
| 8 | **Maintain** | `change-tests`: when a source changes, the smallest fix | Re-run the saved queries; the affected predictions, through `prov:used` | The fix | `layer/<domain>/cambio/*.json` |

Rastro Lab adds a separate step (`rastro-lab`): the same model with raw and Rastro variables, without using the future,
and every prediction saved with the data it used.

## Before choosing a domain or source: inspect candidates

Use `inspect-sources` when source feasibility or the candidate domain is still uncertain. Inspect original files,
access and reuse terms, versions, actual observation periods, record grain, units, keys and concrete join ambiguities.
Record upstream dependencies and what is already familiar from Rastro. A different publisher does not by itself
provide independent evidence. Return a recommendation and, when requested, candidate questions with definitions and
independent verification plans. Keep timings, source URLs and snapshot fingerprints with the inspection report.

After inspection, when questions and source evidence are sufficient, propose the minimal semantic layer in
`semantic-layer-proposal.md` alongside the report: concepts tied to questions and fields, grain, identifiers,
relationships, a schema diagram and a worked example, with counting, provenance and uncertainty rules. Otherwise
record why it remains pending. This is a conceptual handoff to `map-source`, not an implemented ontology or a new
approval gate; reuse approvals and bring only new or changed business definitions to a person.

This is read-only discovery: downloads and local profiling, without a registered domain, services or database load.
It can precede scope approval and the domain experiment log. Follow an approved inspection budget and report limits
or partial results honestly. An inspection does not approve scope, business questions, sources or implementation.
Reuse existing approvals; when the selected scope is approved, hand off to `start-domain` or, for an existing domain,
`add-question` and `add-source` as needed. If sources are already understood, no separate inspection is required.

## Before step 0: start a domain

The `start-domain` skill owns initialization. A new domain starts as a minimal scaffold, written by
`python layer/method.py new-domain <domain> --title "..."` (items 2 to 4 below; `layer/new_domain.py`). Runtime readiness must be
checked, not assumed from an empty mapping. Record pending capabilities until the first minimal implementation runs.

1. **Name and prefix:** a short name in lowercase (`<domain>`), which is also the SPARQL prefix (`<prefix>:`) and the
   namespace `https://w3id.org/rastro/<domain>#`.
2. **Registry entry** in `layer/dominios.yaml`, copying the shape of an existing one: `base` (what the assistant is told
   the domain is about), `ontop`, `ontology`, the notes (`sparql_notes`, `sql_notes`, `links_notes`), `readers`,
   `namespace`, `term_sources`, `link_sources` and the `method:` block. Keys whose piece does not exist yet are left
   out; the skills read a missing key as "not built yet".
3. **Folders:** `ontology/<domain>/` (ontology with only its header, `competency-questions.md`, `queries/`),
   `mappings/<domain>.r2rml.ttl` (empty), `linking/<domain>/`, `layer/<domain>/` (notes, `eval/questions.yaml`,
   `reader.sql`) and `data/<source>/` per source.
4. **Its own Ontop service** in `infra/docker-compose.yml`, copying an existing one, with the domain's ontology and
   mapping and a free port; and the read-only database users for the evaluation (`reader.sql`).
5. **Check that the shell runs:** the Ontop service starts and is healthy, and `ontology-check` passes. If the runtime needs its first mapping, record that dependency and proceed with an approved question; do not claim readiness yet.

**A person approves:** the domain's scope (which sources, which period, which region) and who answers the business
questions.

In the app, the technical view's «Método» section reads this table for a domain: each step's evidence, what waits
for a person and who approves (`app/dominio/method_view.py`).

## Where each domain keeps its pieces

The skills are generic. What changes from one domain to another (its questions, mapping, Ontop service, loaders, linker,
quality rules, evaluation and change tests) is registered once, in the domain's `method:` block in
`layer/dominios.yaml`. A new domain is a new entry there, not new skills. Each skill keeps the real cases from Rastro's
domains in its own `examples.md`, as evidence, not as instructions.

## How mappings and links are proposed

**Narrow down, decide, test.** First, deterministic methods narrow the options: labels, definitions, data types, sample
values and existing mappings. Then the language model chooses among those few options and explains why, only where there
is ambiguity. Finally, an executable test decides. This is more reliable, and scales better, than asking the model for the
whole mapping at once.

## Agents: one, with skills

- **Expertise lives in the skills**, not in different agents: each skill has its contract (what it takes, what it
  returns), examples and tests. The same agent loads the one it needs.
- **Separate agents only where independence matters:** the evaluator does not see how the answer was built, and whoever
  writes the blind questions does not see Rastro. An evaluator that sees the four wordings of a question together no
  longer measures consistency: it happened, and that measurement was discarded.
- **More agents only if a measurement calls for it:** many sources at once, or a dictionary that doesn't fit in one
  context.

## When something fails: what kind of failure

Every failure in the measurement is classified, to know which step to strengthen:

| Kind | Example in Rastro | Step to strengthen |
|---|---|---|
| Missing data | Prices, reserves, 2026 | 1 (another source) or say so |
| Wrong link | A company name joined to the wrong group | 4 |
| Wrong mapping | A domain in the dictionary that turned every fracture record into a fracturing | 2 or 3 |
| Wrong query | Rastro reached the operator through the share instead of the declared name | 2 (the dictionary notes) |
| Ambiguous definition | "Producing": what each company operates, or what it is entitled to | 0 |
| Impossible source value | A pressure of 111,515 psi | 5 |

## What is proven and what isn't

**Proven in one domain, with numbers:** 10 of 10 correct with Rastro and 8 of 10 without; a correction in 1 place
instead of 5; the quality rules found real errors; nothing was made up when the data was missing; predictions are
explained with their records. The same Rastro works in two other domains.

**Not proven:** that the method generalizes without redoing it. That is measured with the experiment below.

## The missing experiment

1. Pick a public source Rastro has never seen, from another domain.
2. Write its business questions first, with someone from that domain.
3. Build the layer only with this method's skills and checks.
4. Measure, in the experiment log (below): hours, how many times a person stepped in and why, how many errors the
   checks caught, and the correct answers with the three approaches.
5. Repeat on a second domain without rewriting the skills.

If the second domain only needs its own definitions and a few new rules, the method generalizes. If it requires changing
the process, it becomes clear what is not general yet. Whatever comes out is published.

## The experiment log

The experiment is measured with a log, one file per domain (`docs/experiments/<domain>.yaml`, following `method-contracts.md`), filled in while the work
happens, not afterwards:

**Header:** domain, sources, who wrote the business questions, start and end date, the method version (the commit).

**Time:** for each step of the method, the hours spent (agent and person separately).

**Human interventions,** one row each:

| When (step) | What was decided | Why a person was needed | Kind | Time |
|---|---|---|---|---|
| 4 | Two companies with the same name are different | The name alone did not decide it | Linking | 10 min |

Kinds: business definition, linking, scope, data access, fixing the method itself.

**Errors caught by a check,** one row each:

| Step | Check | What it caught | Kind of failure | How it was fixed |
|---|---|---|---|---|
| 5 | A quality rule | Evidence text empty for some links | Wrong mapping | One line in the linker |

Kinds of failure: the table in "When something fails".

**Changes to the method or the skills:** each change the domain forced, and whether it is generic (it goes into the
skill) or only for that domain (it goes into the domain's registry entry or its examples).

**Result:** the three approaches on the domain's questions, the quality rules' result, and the totals: hours,
interventions, errors caught, method changes.

## How it would be pitched

"An agentic semantic-layer expert for consulting teams: it builds and maintains the layer with the evidence for every
decision, and a person approves what is a business decision." First as a tool for consulting firms, to deliver
integration projects faster and with traceability; each project adds a domain to the method. The number that backs it
is the experiment's: hours, interventions and errors caught.
