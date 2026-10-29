---
name: evaluate
description: Measure a domain's evaluation questions with the three paths (without Rastro, SQL with links, with Rastro), score, adjudicate and publish the number, for any domain of the registry (layer/dominios.yaml). Use it when adding or changing an evaluation question, after changing data or rules, or before showing a number.
---

# Evaluate a domain

Read `docs/method-contracts.md` for lifecycle states, gates and experiment evidence; record time, interventions and caught errors as you work.

Step 6 of the method (`docs/method.md`). The evaluation compares three paths on the same questions, with the same AI assistant:

- **B, without Rastro:** SQL over the sources as they were loaded.
- **D, SQL with Rastro's links:** the fair baseline. Always reported.
- **C, with Rastro:** SPARQL over the domain's Ontop.

Where each piece lives for a domain is in its entry in `layer/dominios.yaml`: the folder is `method.evaluation.folder` (below, `<folder>`) and the command is `method.evaluation.run` (below, `<run>`; usually `docker compose run --rm -T layer-eval python /layer/evaluar.py <domain>`). A domain on an older harness has a different command and folder layout: use what its registry entry says, and move it to the current harness when it is next measured. The same entry has the read-only users (`readers`) and the notes each path reads (`sql_notes`, `links_notes`, `sparql_notes`).

The files: questions in `<folder>/eval/questions.yaml`, saved answers in `<folder>/respuestas/<q>-<n>-<B|D|C>.json`, result in `<folder>/resultados.json` (the app reads it) and `<folder>/resultados.md`. The script is `layer/evaluar.py` (its docstring has the details).

## Constraints

- **One prompt per evaluator:** each subagent gets one wording of one question for one path, never several wordings together.
- **The evaluator never sees** the reference or the other paths' answers.
- **A failure caused by the dictionary is recorded,** never silently fixed before publishing.
- **A number is provisional until the publication gate passes:** independent reference evidence covers every question, including agreement cases, and a person approves adjudications.
- **Saved answers are never edited by hand:** they change only by running the evaluation again (`try`, `rerun`).

## Measure a new or changed question

1. **The question, and the plan.** Before touching any file, write the plan as a short table, one row per question to
   measure:

   | Question | Reference | Where the reference comes from | Approaches | How it is scored | Open question |
   |---|---|---|---|---|---|

   Where the reference comes from is either independent of Rastro (a source's own total, a published figure) or from
   Rastro, and then it is marked to be adjudicated. The approaches are B, D and C. How it is scored: a number with 5 %
   tolerance, or a list with F1. A person reviews it; the table goes into the decision or the experiment log.
   Then write the question in `eval/questions.yaml`, in business words, with the definitions it uses and its reference
   query (SPARQL over Rastro). That reference is provisional: an independent one goes in `<folder>/eval/referencias.json`
   (`{"nota": who made it and its status, "answers": {question id: answer}}`), and `puntaje` uses it instead. If it has paraphrases, in `consistencia/parafrasis.yaml`. It usually starts as a competency question (skill `add-question`).
2. **One subagent per path, which only sees the prompt:** generate the prompt with
   `<run> prompt <q> 0 <B|D|C>` (it is also kept in `<folder>/prompts/`: commit it with the answers, it is evidence
   of the run),
   give it to a new subagent with no other context, and test what it returns with
   `<run> try <q> 0 <B|D|C> < query.sql`. Up to 3 attempts, giving it back the error message. Never show it the reference or other answers. **One prompt per subagent:** if a subagent sees the four forms of a question together, it repeats the same query and consistency stops measuring anything (this happened once, and that check was discarded).
3. **Score:** `<run> puntaje`. Tolerance: 5 % for numbers; for lists, F1 of 80 % or more.
4. **Independently validate every reference**, even when all paths agree (in `eval/referencias.json`; an AI-made
   reference says so in its `nota` and waits for a person). Preserve the checked answer, source/version, supporting artifact and fingerprint, reviewer and date.
   For a person outside, `docker compose run --rm -T layer-eval python /layer/review_packet.py <domain> build` writes the packet
   (`<folder>/revision/paquete.md`: per question, Rastro's answer, the three approaches, the adjudications, the source
   tables with their loaded version and the SQL query over the sources to start from) and the form
   (`revision/formulario.csv`). When the person has filled every row, `record` writes `eval/referencias.json`, scores
   again and writes the references and source versions into `reference-evidence.yaml`; with a row pending it writes
   nothing. Never fill in the form yourself. **Adjudicate** each question where the paths differ, with each source's data, in `<folder>/adjudicacion.md`: who was right and why. The reference comes from Rastro, so Rastro's advantage can be circular until adjudicated.

5. **Publication gate:** write the model and version that answered in `<folder>/eval/run.yaml`; `review_packet.py
   record` copies them, the saved prompts, the answers, the source versions and the result into
   `<folder>/reference-evidence.yaml` (format in `docs/method-contracts.md`), then run
   `python layer/method.py publication <domain>`. Missing or stale evidence blocks publication, not exploratory
   scoring. Never invent reviewer approval. The gate covers new claims; numbers already published stay as they are,
   labelled provisional until the gate passes.

## After changing data, mappings or rules

```bash
<run> rerun     # the same saved queries, without asking for anything new
<run> puntaje
git diff <folder>/resultados.md
```

Preserve pre-existing edits; review generated diffs, including date-only changes, without Git checkout/reset. If a score changed, explain why in `docs/decisions.md`. Before re-running, check that Rastro starts and answers (skill `verify`).

## Other question sets

One domain can have more than one question set (for example, questions about a model's predictions, separate from the Layer evaluation), each with its own read-only users and SQL notes. A new set is an entry in `layer/dominios.yaml` (it can inherit from another with `<<: *ancla`) and its folder with `eval/questions.yaml`, `consistencia/parafrasis.yaml` and `reader.sql`.

## When it does not have the data

`layer/fuera.py` measures whether the assistant says what is missing instead of making things up: questions the data cannot answer and one control question that it can (`<folder>/fuera/preguntas.yaml`). One subagent per path (A, B, D and C) with all the questions together:
`docker compose run --rm -T layer-eval python /layer/fuera.py <domain> prompt <A|B|D|C>`, then `guardar <A|B|D|C>` with its JSON on stdin and, at the end, `puntaje`. All paths have the same rule: if the data is not enough, «SIN DATOS:» (NO DATA:) and what is missing (`NO_DATA_RULE` in `layer/answer.py`).

## Classify each failure

Each failing answer is classified, to know which step of the method to strengthen (`docs/method.md`): **missing data**
(another source, skill `add-source`, or say so), **wrong link** (skill `link-entities`), **wrong mapping** or **wrong query** (skill
`map-source`: the mapping or the dictionary notes), **ambiguous definition** (the question, skill `add-question`, or the dictionary), or **impossible
value from the source** (skill `quality-rules`). Write the type down in the adjudication.

## A person approves

- **The plan:** its questions, their references and where each reference comes from, before anything is measured.
- The adjudication of each question where the paths differ.
- Publishing a number (in the app, the script or the slides).

## Grounding

- **Score by the result of running the query,** not by how it is written, as in text-to-SQL benchmarks
  (Spider: Yu et al., EMNLP 2018).
- **The same question with and without a knowledge graph over an enterprise database:** the assistant gets it right much
  more often with the graph (Sequeda, Allemang and Jacob, «A Benchmark to Understand the Role of Knowledge Graphs on Large Language
  Model's Accuracy for Question Answering on Enterprise SQL Databases», 2023, arXiv:2311.07509). Rastro adds the fair
  baseline (SQL with the same links), because much of the advantage comes from integration done once.

## Rules

- A fix after measuring (to the dictionary, to a rule) is measured again only on what it affects, with new subagents, and is stated as such in `docs/decisions.md`.
- What is reproducible is the saved answers, not the model's temperature.
- The test with questions we did not write is in `docs/preguntas-a-ciegas.md`.

Worked examples from the existing domains (commands, folders, the predictions question set, the discarded check): `examples.md`.
