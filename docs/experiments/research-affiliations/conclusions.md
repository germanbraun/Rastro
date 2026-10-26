# Conclusions from the process notes: research affiliations

Written on 2026-10-26 from the 49 notes in [process-notes.md](process-notes.md), before the evaluation is scored (the
blind reference is with GPT; see `blind-review/`). The score does not change these conclusions: they are about the
method, not about Rastro's accuracy.

## In one paragraph

The method transferred: a second, very different domain (publications and research organizations, not oil and gas)
went from inspection to a working app, quality rules and a measured change test in about 1.9 agent-hours, with the
user approving each step. It did not transfer **without changes**: 26 of the 49 notes are important (they could make
a result wrong or unverifiable), 15 are gaps and 8 are friction. Five generic changes were made during the run with
the user's approval (quality severity, registry-driven evaluation harness and change guard, the unmeasured state of
«Por qué confiar», widget keys per tab). Almost every important defect was caught by the **second reviewer** or by
**reading records by hand**, not by the automated gates.

## What worked

- **The skill sequence and the approvals.** Every step ended in something visible, and every approval bound a written
  proposal (questions, dictionary, links, quality, app, evaluation, change test).
- **The second-evidence rule for links** (note 19): it rejected a Brazilian homonym and «UK» in London addresses.
- **Fix in one place** (note 46): a source correction reached Rastro and the link tables with zero edits; raw SQL
  missed it because of its own string matching.
- **The independent reviewer after each stage** (note 14): 8 real defects in the first four stages alone, none caught
  by the gates.

## What to change, by priority

**1. Stop hand-editing the experiment log** (notes 7, 30, 47: four errors, one commit without its log). A command to
open and close sessions and append interventions; `--check` rejects duplicate keys, overlaps, and declared hours that
differ from the intervals; `close-phase` refuses to commit when the log does not parse.

**2. Make "validated" mean what it says** (notes 29, 31, 32, 8, 18, 25). Name two levels: technical validation (query
invariants) and accuracy validation (independent references). Let `query-checks.yaml` express key coverage and
per-row bounds, bind each question to its own expectations, keep the business owner and the reference reviewer as
separate roles, and keep what Rastro counts apart from what the blind reviewer checks.

**3. Test rules the way GPT broke them** (notes 37, 38, 48, 26, 35). One broken case per constraint, assert the
reported severity, exact expectations in change tests with a broken fixture, and never check a value against a class
that a range already implies.

**4. Linking: spend review time on real doubts** (notes 20, 22, 23, 24, 21). Read a sample of the **unlinked** records
after every run; decode markup entities in the one normalization function; reject short acronyms that are also place
codes with a written rule; look for gaps per named thing, not per record; allow a second review of corrections.

**5. Sources: load what was approved** (notes 9, 11, 12, 3, 13). Load the approved snapshot and check its fingerprint;
the loader writes the source manifest; multi-valued fields keep their own table; live APIs are captured with a request
ledger; credentials go as connection parameters.

**6. Say no more than the evidence** (notes 33, 49, 38). Heuristic outputs are «candidatos»; «who decided» is kept
apart from «a person confirmed»; reports say what each number does not measure.

**7. Smaller watch-outs** for the skills' examples: Ontop's «FAILED TO PARSE» line and reserved words (15), `FILTER NOT
EXISTS` inside `UNION` and `SAMPLE` (27), DataSource name and licence in every first mapping (40), the app log after
the browser check (39), readers' grants after a link rebuild (45), sizing a set in the unit the questions count (1, 2).

## Already applied

Notes 34 (quality severity), 41 (unmeasured «Por qué confiar»), 43 (evaluation harness in the registry) and 44 (change
guard in the registry) were applied during the run as recorded method changes. Since then, outside the experiment:
the oil and gas domain got a query gate (`layer/energia/query-checks.yaml`), and the scorer reads an independent
reference when one exists (`eval/referencias.json`, used for this blind review).

## What it means for a new dataset

The skills are enough to build a first semantic layer for new data with a person approving each step. What makes it
fast is not more automation of the modelling, which needs judgment, but removing the error-prone bookkeeping
(priority 1) and making the checks strong enough (priorities 2 and 3) that the second reviewer finds less. Applying
priorities 1 to 3 is the next step before another domain.
