---
name: show-in-app
description: Show a domain's semantic layer in the Rastro app - the business view (questions in plain words, why each number, sources, what can be trusted) and the technical view (queries, the SQL Rastro generates, data as tables and as RDF, dictionary, mappings, links and quality rules), plus optional modules such as questions over texts (graph-grounded RAG). Use it when a domain is ready to be shown, when touching app/dominios/*.yaml or app/dominio.py, or when a number or a question in the app changes.
---

# Show a domain in the app

Read `docs/method-contracts.md` for lifecycle states, executable gates, approval reuse and experiment evidence.
For a new domain, run `start-domain` first. Record measured time, interventions and caught errors as work happens.


The step "Show" of the method (`docs/method.md`), between "Measure" and "Maintain": the semantic layer is delivered as an
app that a business person can use and a technical person can audit. The app is a template: what belongs to a domain is
described in its configuration file, not programmed.

## Contract

- **Takes:** a domain whose competency questions answer in Rastro (skills `add-question`, `map-source`), with its
  measurements done (skill `evaluate`) and, if it has them, its quality rules (skill `quality-rules`).
- **Returns:** the domain's app configuration (`app/dominios/<domain>.yaml`), its entry in the app's domain list
  (`app/dominios.yaml`), and the domain working in both views of the app.
- **Does not:** write a measured number by hand, or show a question that has not been checked against its query.

## Constraints

- **Never type a measured number by hand:** use placeholders filled from the measurement files.
- **Never show a question that has not been checked against its query** today.
- **No internal class or table names in the business view:** columns, glossary and texts use the users' words.
- **A saved text summary is regenerated,** never edited by hand.

## What the app shows, and where it comes from

**Business view** (the default; plain words, no jargon, in the users' language):

| Piece | What the user sees | Key in the domain's YAML |
|---|---|---|
| Summary and sources | What the domain is about; each source with its license | `resumen`, `fuentes`, `nota_rastro` |
| Example questions | The question in plain words; the answer as a table with readable columns | `preguntas[].simple`, `query`, `columnas`, `formatos` |
| Why this number | For a row of the answer, the records and evidence behind it | `preguntas[].porque` (a query with `{valor}`) |
| Where the answer comes from | The sources used, what Rastro added, a sample of the evidence | `preguntas[].ventaja`, `evidencia`, `definicion` |
| Glossary | The business terms of the question | `preguntas[].terminos` |
| Before and after | The same question without and with Rastro | `preguntas[].antes_despues` |
| What can be trusted | Cards with the measured numbers; the change test; quality rules; what happens when data is missing | `tarjetas` (filled from `evaluacion`, `cambio`, `evidencia`), `cambios`, `calidad`, `fuera` |
| Guided demo | A few moments, one sentence each | `demo`, `demo_porque` |
| Frequent questions | Domain FAQ next to the general one | `faq` |

**Technical view** (behind «Ver detalles técnicos»; the same answers, opened up):

| Piece | What the technical user sees |
|---|---|
| Each answer | The SPARQL query over the dictionary's concepts; the SQL Rastro generated and ran on the database; a plain-words explanation of the query; which source each column comes from; the business rule in the ontology when the answer depends on a deduced class; the evidence query and its rows |
| Data views | The answer table with the source of each column; the evidence as a table; the data behind "why this number" |
| A record as a graph | One record of each important class, drawn as a graph and shown in Turtle (RDF) |
| Query console | A SPARQL console over the domain, with its competency queries as examples and the generated SQL |
| Dictionary, links and mappings | The ontology with its labels and diagram; the link tables read live with their rule and evidence; the R2RML blocks that build them |
| Quality rules | Each rule in SHACL, a real record in RDF that passes it, a broken example and what SHACL says, the failures and the predictions that use them |
| Measurement detail | Each evaluation question with the three approaches, their queries and the adjudication |

**Optional modules,** switched on only if the domain has the piece:

| Module | When | Key |
|---|---|---|
| Questions over texts (graph-grounded RAG) | The domain has free-text records (reports, studies, descriptions) and a question that needs to read them | `texto` |
| Check a claim | There are claims worth checking against the data (holds, does not hold, no data) | `afirmaciones` |
| Enrichment from an outside source | A shared key with an outside source (live and saved) | `externo` |
| Map | The domain has geometries (points, outlines, lines) | `mapa` in a question |
| Predictions | The domain has a model whose predictions are stored in Rastro | `lab` |

## Steps

1. **Choose, and write the proposal.** Pick 3 to 6 example questions from the competency questions that show what
   integration adds. Before touching any file, write a short table, one row per question:

   | Question in plain words | Main column for "why this number" | What Rastro adds | Glossary terms | Evidence (competency question and query) | Open question |
   |---|---|---|---|---|---|

   Below it, one line per optional module: whether the domain gets it and why (the piece it has). A person reviews it;
   the table goes into the decision or the experiment log.
2. **Register the domain** in `app/dominios.yaml` (id, name in the users' language, configuration file) and copy the
   shape of an existing configuration. The first domain in the list is the one the app opens with.
3. **Business view first:** write the example questions of the proposal. For each: the question in plain words (`simple`), the technical wording (`tecnica`), the query file, readable
   column names, "why this number" for its main column, what Rastro added, the glossary. Use the users' words, never
   class or table names.
4. **What can be trusted:** require `python layer/method.py publication <domain>` before showing new accuracy claims. Missing independent evidence means provisional, not published. point the cards and sections to the domain's measurement files (`evaluacion`, `cambio`,
   `evidencia`, `calidad`, `fuera`). Card texts use placeholders filled from those files (`{c_correct}`, `{b_correct}`),
   never typed numbers.
5. **Technical view:** register the domain's pieces for the technical view (the console's queries folder and port,
   two to five example records, the ontology file, the link tables and mapping blocks to show). Write the
   plain-words explanation of each example query (`explicacion`).
6. **Optional modules,** only those of the proposal. For questions over texts:
   - an exact query (`.rq`) that selects the records by the dictionary's concepts, not by words;
   - an assistant reads only those records' texts and groups them into themes, each theme citing its records by id;
   - the summary is saved with its date (`.json`, with `consulta`, `simple`, `como`, `temas`); the records are read
     live, so anyone can open a cited record and read the original text;
   - if the data changes, the summary is generated again; a person checks that each citation says what the theme says.
7. **Check** (below), in both views with the real runner: `docker compose run --rm --no-deps -T app python /app/check_domain.py <domain>`. Then inspect the visual layout in the browser.

## The check that decides

- **The app loads the domain** after `docker compose restart app` (the app does not reload imported modules), in both
  views, with no error on screen or in `docker compose logs app`.
- **Every example question runs** and returns rows (the app precomputes them at start; a failing one shows an error).
- **Every number on screen comes from its file or its query.** Search the domain's YAML for digits in prose
  (`muestra`, `ventaja`, `antes_despues`, `faq`): each one must match its source today, or be replaced by a
  placeholder. After any re-measurement, check them again.
- **Questions over texts:** the selected records' count matches the query today; every cited id exists among them.
- **A look in the browser,** at desktop and phone width: the business view has no jargon; the technical view shows
  query, SQL, sources and evidence for each answer.

## A person approves

- **The proposal:** its example questions, what each one shows and which optional modules the domain gets, before the
  configuration is written.
- The wording of the business view, in the users' language: questions, column names, glossary, FAQ.
- Which questions go into the guided demo.
- For questions over texts: that the themes and their citations say what the records say.

## Grounding

- **Retrieval-augmented generation:** a language model answers from retrieved documents instead of only from what it
  memorized, and can cite them (Lewis et al., «Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks»,
  NeurIPS 2020).
- **Graph-based RAG:** a knowledge graph organizes what the model reads, which helps with questions over a whole
  collection (Edge et al., «From Local to Global: A Graph RAG Approach to Query-Focused Summarization», 2024,
  arXiv:2404.16130). Rastro's variant goes one step further: the graph does not suggest what to read, an exact query
  decides it, so the selection is repeatable and auditable and only the summary comes from the model.
- **Provenance shown to the user:** the evidence on screen is the PROV-O record of each link (W3C, 2013).

## Watch out for

- **Numbers typed in prose drift:** a number written into a sentence of the configuration stays when the measurement
  changes. Prefer placeholders; when prose needs a number, check it after every re-measurement.
- **All technical-view configuration is data:** register `method.app` and use the domain YAML's
  `technical.instances`, `technical.pieces` and optional `technical.map`. The registry supplies the ontology,
  query folder and port. A new domain must not add Python lists. A map uses the existing polygon/point/line
  result schema and configurable queries, view state, tooltip and caption.
- **A saved text summary goes stale** when the records it read change; its date is on screen, and it is regenerated,
  not edited by hand.
- **Jargon leaks into the business view** through column names and error messages; check the business view as a
  business user would.

Real cases, with their numbers: see `examples.md`.
