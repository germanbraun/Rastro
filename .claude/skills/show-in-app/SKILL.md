---
name: show-in-app
description: Show a domain's semantic layer in the Rastro app - the business view (questions in plain words, why each number, sources, what can be trusted) and the technical view (queries, the SQL Rastro generates, data as tables and as RDF, dictionary, mappings, links and quality rules), plus optional modules such as questions over texts (graph-grounded RAG). Use it when a domain is ready to be shown, when touching app/dominios/*.yaml or app/dominio/, or when a number or a question in the app changes.
---

# Show a domain in the app

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

The step "Show" of the method (`docs/method.md`), between "Measure" and "Maintain": the semantic layer is delivered as an
app that a business person can use and a technical person can audit. The app is a template: what belongs to a domain is
described in its configuration file, not programmed.

## Contract

- **Takes:** a domain whose competency questions answer in Rastro (skills `add-question`, `map-source`), with its
  measurements done (skill `evaluate`) and, if it has them, its quality rules (skill `quality-rules`).
- **Returns:** the domain's app configuration (`app/dominios/<domain>.yaml`) and its English overlay
  (`app/dominios/<domain>.en.yaml`), its entry in the app's domain list (`app/dominios.yaml` and `app/dominios.en.yaml`),
  and the domain working in both views and both languages.
- **Does not:** write a measured number by hand, or show a question that has not been checked against its query.

## Constraints

- **Never type a measured number by hand:** use placeholders filled from the measurement files.
- **Never show a question that has not been checked against its query** today.
- **No internal class or table names in the business view:** columns, glossary and texts use the users' words.
- **A saved text summary is regenerated,** never edited by hand.
- **Only the open section is drawn:** the screen's sections are a radio styled as tabs (`screen.show_sections`), because Streamlit draws every `st.tabs` panel on every click. Do not add `st.tabs` at the top level of a domain's screen; inside a section they are fine.
- **Every visible text in Spanish and English:** edit the Spanish text and its English counterpart together
  (`app/dominios/<domain>.en.yaml`, `app/dominios.en.yaml`, and `app/textos/*.yaml` for texts the code uses). The overlay
  holds only texts; anything missing falls back to Spanish.

## What the app shows, and where it comes from

**Business view** (the default; plain words, no jargon, in the users' language). At most four tabs: Demo, Preguntar,
Por qué confiar and the model's tab; the walkthrough opens inside «Por qué confiar» and the FAQ from a sidebar button.
The first screen says what Rastro is and how to read each screen (question → answer → «¿Por qué este número?»).

| Piece | What the user sees | Key in the domain's YAML |
|---|---|---|
| Summary and sources | What the domain is about; each source with its license | `resumen`, `fuentes`, `nota_rastro` |
| Example questions | The question in plain words; the answer as a table with readable columns; quantities in one unit, the exact figure in the technical view | `preguntas[].simple`, `query`, `columnas`, `formatos` (`numero`, `dinero`, `porcentaje`, or a unit the domain declares in `unidades` with its `escala`) |
| Why this number | For a row of the answer, the records and evidence behind it | `preguntas[].porque` (a query with `{valor}`; `numeros` lists its numbers, or maps each to one of the domain's `unidades`) |
| Link status | One mark per link in every table with a `regla` column: 🔹 automatic rule, 🟠 reviewed by AI and a person must confirm, ✅ confirmed by a person with a document | derived from the rule and evidence (`app/enlaces.py`); nothing to configure |
| Where the answer comes from | The sources used, what Rastro added, a sample of the evidence | `preguntas[].ventaja`, `evidencia`, `definicion` |
| Glossary | The business terms of the question | `preguntas[].terminos` (an English overlay gives an entry as `{term, text}` to translate the term too) |
| Before and after | The same question without and with Rastro, its numbers read now, with each source's latest load date | `preguntas[].antes_despues`: `valores` (one-row `sql` over the sources as they come, or `sparql`), `calculos`, `decimales`, `fuentes`; texts name the values in braces (`app/contraste.py`, which also exports them for the slides) |
| What can be trusted | Cards with the measured numbers, each with one status line (when it was measured; references confirmed by a person or not, decided by the publication gate); the change test; quality rules; what happens when data is missing | `tarjetas` (filled from `evaluacion`, `cambio`, `evidencia`), `cambios` (a scenario with `valor` is told in the demo with one recorded answer: `pregunta`, `texto`, `escala`, `unidad`), `avisos_cambio` (the pattern of the change test's check and its English text), `calidad`, `fuera` |
| Guided demo | A few moments, one sentence each, optionally grouped in acts; the first moment of an act may open with a bridge sentence | `demo` (`paso`, `titulo`, `muestra`, optional `acto`, `puente`), `demo_porque` |
| Frequent questions | Domain FAQ next to the general one, from a sidebar button (a tab in the technical view) | `faq` |
| The data sources | A sidebar button in both views: per source, who publishes it, what it is, what Rastro uses it for and what is worth knowing; the license, link, rows and last load are read from `rastro_meta.source` and `load_run`, never typed; the technical view adds each table and a technical note | `fuentes_detalle[]`: `id` (the source id in `rastro_meta.source`), `nombre`, `organismo`, `que_es`, `que_usa`, `cuidado` (a list), optional `tecnico`, and `esquemas` when a source is shared with another domain (only those schemas are counted) |

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
| Check a claim (technical view only) | There are claims worth checking against the data (holds, does not hold, no data) | `afirmaciones` |
| Enrichment from an outside source (technical view only) | A shared key with an outside source (live and saved) | `externo` |
| Map | The domain has geometries (points, outlines, lines) | `mapa` in a question |
| Predictions (or any screen of the domain's own) | The domain has a model whose predictions are stored in Rastro | `extension`: a class in `app/extensions/<name>/` that subclasses `Extension` (`app/dominio/extension.py`) |

What a domain needs beyond these keys goes in its extension, never in the shared code: `tests/test_generic_code.py`
fails if `app/app.py` or `app/dominio/` names a domain, a source or a word of one domain's business.

## Steps

1. **Choose, and write the proposal.** Pick 3 to 6 example questions from the competency questions that show what
   integration adds. Before touching any file, write a short table, one row per question:

   | Question in plain words | Main column for "why this number" | What Rastro adds | Glossary terms | Evidence (competency question and query) | Open question |
   |---|---|---|---|---|---|

   Below it, one line per optional module: whether the domain gets it and why (the piece it has). A person reviews it;
   the table goes into the decision or the experiment log.
2. **Register the domain** in `app/dominios.yaml` (id, name in the users' language, configuration file) and its name
   in `app/dominios.en.yaml`, and copy the shape of an existing configuration. The first domain in the list is the one
   the app opens with.
3. **Business view first:** write the example questions of the proposal. For each: the question in plain words (`simple`), the technical wording (`tecnica`), the query file, readable
   column names, "why this number" for its main column, what Rastro added, the glossary. Use the users' words, never
   class or table names. Then write the same texts in English in `app/dominios/<domain>.en.yaml`.
4. **What can be trusted:** point the cards and sections to the domain's measurement files (`evaluacion`, `cambio`,
   `evidencia`, `calidad`, `fuera`). Card texts use placeholders filled from those files (`{c_correct}`, `{b_correct}`),
   never typed numbers. Run `python layer/method.py publication <domain>` before showing new accuracy claims: missing
   independent evidence means provisional, not published. The gate covers new claims; numbers already published stay
   as they are, labelled provisional until the gate passes.
5. **Technical view:** register the domain's pieces for the technical view (the console's queries folder and port,
   two to five example records, the ontology file, the link tables and mapping blocks to show). Write the
   plain-words explanation of each example query (`explicacion`).
6. **Optional modules,** only those of the proposal. For questions over texts:
   - an exact query (`.rq`) that selects the records by the dictionary's concepts, not by words;
   - an assistant reads only those records' texts and groups them into themes, each theme citing its records by id;
   - the summary is saved with its date (`.json`, with `consulta`, `simple`, `como`, `temas`); the records are read
     live, so anyone can open a cited record and read the original text;
   - if the data changes, the summary is generated again; a person checks that each citation says what the theme says.
   Talking to the data is not optional: it is how every domain takes a free question (Preguntar → «Conversar con los
   datos», `layer/chat.py`, `app/dominio/chat_view.py`). The context is the domain's ontology and notes; each turn
   writes a query, runs it, answers in words from the result only, and code flags any number not in the result.
   Nothing to write but `ejemplo_libre`, a first question and a follow-up the domain's data answers.
7. **Check** (below), in both views with the real runner: `docker compose run --rm --no-deps -T app python /app/check_domain.py <domain>` (it opens every section in turn, since only the open one is drawn). Then inspect the visual layout in the browser.

## The check that decides

- **The app loads the domain** after `docker compose restart app` (the app does not reload imported modules), in both
  views, with no error on screen or in `docker compose logs app`.
- **Every example question runs** and returns rows (the app precomputes them at start; a failing one shows an error).
- **Every number on screen comes from its file or its query.** A contrast card reads its numbers with `valores`;
  `tests/test_enlaces.py` fails if such a card types one. Search the rest of the domain's YAML for digits in prose
  (`muestra`, `ventaja`, `faq`): each one must match its source today, or be replaced by a placeholder. After any
  re-measurement, check them again.
- **Questions over texts:** the selected records' count matches the query today; every cited id exists among them.
- **Talk to the data:** a conversation of a few turns with a follow-up runs with no exception; ask the domain's «does
  it say when it lacks the data?» questions (`fuera`) and check it says what is missing; no answer shows a flagged
  number without its warning. Needs the model's key; until it is measured, no accuracy claim.
- **A look in the browser,** at desktop and phone width, in Spanish and in English: the business view has no jargon;
  the technical view shows query, SQL, sources and evidence for each answer.

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
