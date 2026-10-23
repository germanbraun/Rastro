---
name: walkthrough
description: Build a «Paso a paso» walkthrough for a domain - a few steps on real data, read live, that show how the semantic layer turns sources into an auditable answer (and, for a model, into an explained prediction), each step saying which part of Rastro it shows, with matching appendix slides and demo-script lines. Use it after show-in-app, when a domain needs a teaching example for consultants, or when touching ejemplo_integracion or ejemplo_lab in app/dominios/*.yaml or their «Paso a paso» slides.
---

# A walkthrough: Paso a paso

Read `docs/method-contracts.md` for lifecycle states, executable gates, approval reuse and experiment evidence.
For a new domain, run `start-domain` first. Record measured time, interventions and caught errors as work happens.

Part of the step "Show" of the method (`docs/method.md`), after `show-in-app`. The demo answers «what does Rastro
do for me»; a walkthrough answers «how does it do it», for someone who knows SQL. It follows **one real case** through
the semantic layer, one step per part of Rastro, and every number on screen comes from a query that runs.

## Contract

- **Takes:** a domain shown in the app (`show-in-app`), with its mapping, links and, if it has one, its model.
- **Returns:**
  - the walkthrough in the domain's app configuration: `ejemplo_integracion` for the semantic layer, and
    `ejemplo_lab` for a model, if the domain has one;
  - one appendix slide per step;
  - a few lines in the domain's demo script, outside the timed demo.
- **Does not:**
  - use invented records or numbers;
  - show a capability the domain does not have (a source that is not loaded, a question it cannot answer);
  - claim accuracy that has not been measured.

## Constraints

- **Real data, read live.** Each step runs its own queries in the app: SQL over the raw sources as they come (the
  «without Rastro» reader) and SPARQL over Rastro. Text never repeats a number that a query on screen does not show.
- **Say what it is for.** The walkthrough opens with `para_que` (what it wants to show, in one or two sentences) and
  each step has `parte`: the part of Rastro it shows, in business words (dictionary and mappings, links with
  evidence, the answer and its origin, the model, the explanation, traceability).
- **One case through every step.** The same record (a well, a company, a publication) from the first step to the
  last, so the audience follows one thread.
- **Pending stays pending.** If a link in the case was reviewed by an AI assistant, the step says that a person still
  has to confirm it.
- **Explanations are not causes.** A model's explanation says how it reached the number, not why the world is so.
- **Slides are a snapshot.** The slide repeats the values of the day and its notes (`aside`) say which query and date
  they come from, and to show them live in the app if the data changed.

## Steps

1. **Choose the case, and write the proposal.** Look in the data for one record that crosses the parts of Rastro that
   matter in this domain. Good cases: the same thing under different column names (mapping), the same thing under
   different names with a reviewed link (links with evidence), and a question whose answer changes because of that
   link (the answer and its origin). Before touching any file, write the table:

   | Step | Part of Rastro | What the audience sees | Queries (raw SQL / SPARQL) | Open question |
   |---|---|---|---|---|

   Add `para_que` above it. A person reviews it.
2. **Write the configuration** in `app/dominios/<domain>.yaml`, under `ejemplo_integracion` (and `ejemplo_lab` for
   a model):
   - for the walkthrough: `titulo` (the tab), `encabezado`, `para_que`, `aviso` (which real case, read live) and
     `selector`;
   - for each step in `pasos`: `titulo`, `parte`, `contenido`, `consultas` (each with `titulo` and `sql` or
     `sparql`), and optionally `tecnico` with `lenguaje` (shown only in the technical view) and `calculo_pozo` (the
     model's real calculation for its example record).

   `app/dominio.py` (`show_integration_example`) renders it; a domain needs no code.
3. **Slides and script:** one slide per step in `docs/slides/slides/`, kicker «Paso a paso · Datos reales · Parte de
   Rastro: …» and a «Para qué» line, added at the end of the domain's appendix (`docs/slides/mazos/<domain>.json`),
   then `python3 docs/slides/build.py` (skill `decks`). In the demo script, one short optional section: its purpose,
   and one line per step with its part of Rastro.

## The check that decides

- **Every step renders in both views, with its queries:** select each step with Streamlit's AppTest and check there
  is no exception and that the number of tables equals the number of queries. Then run
  `docker compose run --rm --no-deps -T app python /app/check_domain.py <domain>`.
- **Every number in the text and the slides matches a query today.** Search the step texts and the slides for digits,
  and compare each one with its query's output.
- **The slides fit:** the content ends above the footer.
- **A look in the browser,** at desktop width: the purpose box, one step with its tables, and the technical view.

## A person approves

- The case and the proposal table, before the configuration is written.
- The wording of `para_que` and of each `parte`.

## Watch out for

- **A fictional example is easier to write and costs trust.** Next to real data, invented records are hard to tell
  apart. If no real case shows a step, drop the step.
- **The question in the last step must be one Rastro answers today.** Otherwise the walkthrough sells a feature.
- **Keys of the tables:** the same answer drawn in two tabs at once needs distinct widget keys; the renderer adds the
  tab and the step to them.

Real cases, with their queries: see `examples.md`.
