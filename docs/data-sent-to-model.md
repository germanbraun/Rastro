# What data reaches the language model

For a customer's security review: every place Rastro sends something to a language model, what it sends, and how to
run without any. Checked against the code on 2026-10-29; when a feature changes, this page changes with it.

## In short

- **Most of Rastro never calls a model:** the example questions, «¿Por qué este número?», the demo, the quality rules,
  the change tests, Rastro Lab and the app's sources and method pages run on the customer's machine only.
- **Three app features call one,** only when a person uses them and a model is configured: the chat, «Explicame la
  consulta» and oncology's free question.
- **Building the layer** (the method's skills, run by a consultant with Claude Code) reads source structure, samples
  and evidence: that work happens in the consultant's session, under the customer's agreement for the pilot.
- **Without a model** (no key), everything else works; with a local model, nothing leaves the machine.

## The app, at run time

The app calls the model configured in `.env` (`RASTRO_PROVIDER`, `ANTHROPIC_API_KEY` or
`OPENAI_API_KEY`, `RASTRO_MODEL`), through `layer/answer.py` (`ask`): the Claude API by default, the OpenAI API with
`RASTRO_PROVIDER=openai`, or a local model. Whichever is configured receives everything in the table below; the
large context goes in the system prompt, and the Claude API caches it for a short time.

| Feature (where) | What is sent | Customer data in it? | Code |
|---|---|---|---|
| **Conversar con los datos** (Preguntar), step 1: write the query | The domain's description (`base`), its SPARQL notes and its whole ontology; the conversation so far (each question, the query it got and the answer in words); the new question | The ontology and notes are the business dictionary (names of concepts, no rows). Earlier answers in words carry numbers from the data. | `layer/chat.py` `write_query` |
| **Conversar con los datos**, step 2: answer in words | The domain's description, the question and **the query's result: up to 50 rows** | **Yes:** the values of those rows | `layer/chat.py` `write_answer` (`MAX_ROWS`) |
| **Explicame la consulta** (a button under an answer) | The SPARQL notes, the query and the SQL Ontop generated. Only for a query without a saved explanation (the chat's); the example questions bring theirs | Table and column names, no rows | `layer/answer.py` `explain_query` |
| **Oncology's free question** (its own screen) | The ontology, its notes and the question | No rows | `layer/answer.py` `ask_rastro` |

Nothing else in the app calls a model. A saved summary of texts (Preguntar → «Una pregunta sobre textos») is read
from its file; the model was called when it was generated (below).

## Building the layer (the consultant's work)

The method's skills run in a Claude Code session, on the customer's machine or on a copy of the data. Following the
method, the agent reads:

| Step | What the agent reads |
|---|---|
| Inspect sources, map them, link entities | Table and column names, documentation, **sample rows**, and the texts that link candidates are decided on (company names, affiliation strings) |
| Questions over texts (generating the saved summary) | **The selected records' texts** (for oil and gas, the short texts of the environmental studies listing) |
| Evaluate (independent evaluators) | Each evaluator's prompt: the domain description and either the SQL schema (table and column names, their documentation) or the ontology, and the question; its queries run locally and only errors go back. Oncology's older runner calls the configured model itself (`layer/answer.py` `answer`, from `layer/eval/run.py`), with the same prompts |
| Measure the chat (`layer/chat_eval.py`, no API key) | Each chat call as a file: the same content the app would send (table above), up to 50 result rows included; a fresh assistant in the consultant's session answers it |
| Review doubtful links (when an assistant reviews them) | The candidate and its evidence text |

Agree before the pilot which of this may be read (docs/customer-deployment.md, section 2.1), and write it in
`docs/decisions.md`. Data never goes to the model through files of the repository: the repository keeps scripts,
rules and decisions; the data stays in the customer's database (`data/raw/` is not versioned).

## Running without a model, or with a local one

- **No model:** leave `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` and `RASTRO_PROVIDER` empty. The app cannot call any model: the chat
  and the explanation of a new query say a model is needed, and everything else works. With `RASTRO_NO_MODEL=1` in `.env`,
  `infra/customer/check.py` fails if the app has a key or a provider configured, so the setting can be shown to
  the customer's security team.
- **A local model:** `RASTRO_PROVIDER=ollama` and `OLLAMA_URL` pointing to a model on the customer's network. Nothing
  leaves it. Expect weaker queries from a small local model: measure them with the domain's questions before
  relying on them.
- **OpenAI instead of Claude:** `RASTRO_PROVIDER=openai`, `OPENAI_API_KEY` and `RASTRO_MODEL` (the model's name;
  `OPENAI_BASE_URL` for another server with the same API). The same features send the same content, to OpenAI.
  Rastro's numbers were measured with Claude: measure the chosen model with the domain's questions before quoting
  them for it.
- **The customer's own cloud:** Claude is also offered through the large cloud providers; whether a given feature is
  available there, and under which terms, is checked for that customer before the pilot.

## Keeping this page true

When a feature that calls the model is added or changed (`layer/answer.py`, `layer/chat.py`, or any new `ask(`), its
row here changes in the same commit; the test `tests/test_data_sent_to_model.py` lists the code that calls the model
and fails if a new call appears that this page does not name.
