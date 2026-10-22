---
name: quality-rules
description: Write, test and read Rastro's quality rules (SHACL) over a domain's integrated data, and which predictions inherit what fails them. Use it when touching a domain's quality rules (ontology/*/calidad/), the quality runner (ontology/calidad.py) or its result (layer/*/calidad.json), after adding a source or a link, or when a number looks odd.
---

# Quality rules

Step 5 of the method (`docs/method.md`). A rule says what the integrated data must look like, in the words of the
dictionary, and it is checked over all of Rastro's data after every load. **It does not fix anything:** it shows what
fails, where, and what uses it. For someone who knows SQL, these are a table's quality checks, but over all the sources
together, their evidence and what uses them.

## Contract

- **Takes:** a dictionary concept with a risk (a value that can be missing, go beyond what is possible or contradict
  another) and Rastro's data.
- **Returns:** the rule in the domain's rules file, one good and one broken sample value in its examples file, and the
  result file: how many values each rule checks, which ones fail and which predictions of the current run use them
  (`prov:used`).
- **Does not:** change the value, or remove it from the model. A person decides that, and if the model changes it is
  measured again.

## Constraints

- **Rules never change the data:** they read and report; a correction, a removal or a notice to the source is a
  separate decision, taken by a person.
- **A threshold leaves out the impossible, not the rare:** every limit comes from the data distribution and from what
  is physically or legally possible, never from "it looks too high".
- **Every rule has a good and a broken example** in the examples file, and the tests check both.
- **Check the count before blaming the data:** a failing count is compared with the table count first; too many values
  checked is a dictionary error, not a source error.
- **Mark what is uncertain:** an unsure threshold goes into the proposal's open questions, never into the rules file
  as "probably right".

Where it lives comes from the domain's `method.quality` in `layer/dominios.yaml`: `rules` (`ontology/<domain>/calidad/reglas.ttl`),
`examples` (`ejemplos.yaml`), `result` (`layer/<domain>/calidad.json`) and `run` (the command). The runner is
`ontology/calidad.py` and the tests are `tests/test_calidad.py`. **If the registry has no `method.quality` entry, the
domain does not have quality rules yet:** create them following the existing pattern (see `examples.md`): the same three
files, a runner pointed at the domain's Ontop (`method.ontop`), and the new entry in the registry. The runner today reads
one domain's paths and prefix; adding a domain means making those come from the registry, not copying the script.

The app shows the result in «Por qué confiar» (why trust it) and, with «Ver detalles técnicos» (see technical details),
under the hood, with a real value from Rastro and a broken one.

## Which rules to write

| Type | What it checks | In SHACL |
|---|---|---|
| Evidence completeness | Every link says which source it comes from and why | `sh:targetSubjectsOf <prefix>:rule`, `sh:minCount` |
| Possible values | A measurement stays within what is physically possible | `sh:minInclusive`, `sh:maxInclusive` |
| Cardinality | Each entity has at most one registry identifier, in the right format | `sh:maxCount`, `sh:pattern` |
| Consistency between values | The range minimum is not greater than the prediction | `sh:lessThanOrEquals` |
| Aggregates | The shares of something add up to 100 % or less | `sh:sparql` with `GROUP BY` and `HAVING` |
| What the model uses | Each prediction comes from the record it claims | `sh:qualifiedValueShape` |

## Steps: narrow down, decide, test

1. **Narrow down the threshold with the data, and write the proposal:** look at the distribution in Postgres (median,
   99th percentile, maximum) before choosing a limit. A threshold has to leave out the impossible, not the unusual.
   Write the result as a short table, one row per rule, before touching any file:

   | Concept | Condition | Threshold | Evidence (median, p99, max, count) | Would flag today | How sure | Open question |
   |---|---|---|---|---|---|---|

   A person reviews it at a glance; thresholds and open questions are decided here. The table goes into the decision
   or the experiment log.
2. **Write the rule,** one block per rule, separated by a blank line (the app shows each block as is):
   `rdfs:label` in business words, `rdfs:comment` with why it matters and the common values, a target
   (`sh:targetClass`, `sh:targetSubjectsOf` or `sh:targetObjectsOf`) and `sh:message` in Spanish for each condition.
3. **One good and one broken value** in the examples file. The broken one, if possible, the real case the rule found.
   The tests (`tests/test_calidad.py`) check that the rule lets the good one pass and flags the broken one.
4. **If the rule looks at new data,** add its `CONSTRUCT` to `DATOS` in `ontology/calidad.py`: only what the rule
   looks at.
5. **Run and read:** the domain's `method.quality.run`; in the result file, for each rule, how many values it checked,
   the ones that fail (the first 10) and the affected predictions.

## The check that decides

- `pytest tests/test_calidad.py`: each rule lets the good example pass and flags the broken one.
- **How many values the rule checks is what you expect:** if it looks at twice as many entities as the table has, the
  error is not in the data but in the dictionary. Always compare with the table count.
- What fails, reviewed by hand in the source, one by one, before counting it as a source error.

## A person approves

- **The proposal:** each rule's condition, threshold and open questions, before the rules file is written.
- **The thresholds** (what is impossible and what is only unusual).
- **What to do with what fails:** correct it with a document (reviewed CSV, skill `link-entities`), notify the source,
  or remove it from the model. The last one changes Rastro Lab and is measured again (skill `rastro-lab`).

## Grounding

- **SHACL**, the W3C language for validating graphs (2017 recommendation): the same rules work in other
  knowledge graph platforms or tools.
- **Executable tests for linked data quality,** as in test-driven development: test cases written as queries, which
  come with the vocabulary and always run (Kontokostas et al., «Test-driven Evaluation
  of Linked Data Quality», WWW 2014, doi:10.1145/2566486.2568002).
- **The quality dimensions** these rules cover (completeness, accuracy, consistency, provenance) are
  systematized in Zaveri et al., «Quality assessment for Linked Data: A Survey», *Semantic Web* 7(1), 2016.

## Watch out for

- **Rules find dictionary errors, not just data errors:** an extra `rdfs:domain` on a shared property types the
  subjects of another class as this one; it shows because the rule checks more values than the table has.
- **The first error is often found by the simplest rule:** evidence completeness catches links whose evidence text
  came out empty (a NULL in a SQL concatenation).
- **An impossible value reaches the model:** the rule flags the predictions that use it and says which ones; removing
  them from the model is a separate decision.
- **Affected predictions, only those of the current run:** Rastro keeps all published runs.
- **What points to a value:** if the target is an object (`sh:targetObjectsOf`), the real example also shows the
  records that point to it.

Real cases, with their numbers: see `examples.md`.
