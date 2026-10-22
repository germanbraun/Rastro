---
name: link-entities
description: Link entities across sources in Rastro (the same company, place or asset with different names or keys), each link with its rule and its evidence, plus the reviewed corrections. Use it when touching a domain's linker (links.sql, link.py), the corrections CSVs, or when a new source names things that are already in Rastro.
---

# Link across sources, with evidence

Step 4 of the method (`docs/method.md`). It is the step that adds the most value and the one that hides the most business
decisions: saying that two records are the same thing, or that a company "operates" or "owns" something, is a rule, and
the rule has to stay visible.

## Contract

- **Takes:** two or more loaded sources that name the same things, and the question that needs to join them.
- **Returns:** a link table in the domain's linker, one row per link, with **the rule** (in words) and **the
  evidence** (the text that justifies it, with the values from each source); its mapping as a `prov:Entity`; and, if
  needed, reviewed corrections in a CSV.
- **Does not:** join by name what has a better key, or silently decide between two definitions.

## Constraints

- **Never join by name what has a better key:** if both sources share an identifier, the link uses it, and only the
  matches that share it.
- **Never equate two entities on their name alone:** a name match needs a second piece of evidence (a key, a place, a
  date, a document) or it goes to the reviewed CSV.
- **No link without rule and evidence:** every link row carries the rule in words and the values from each source that
  justify it, and its source (`prov:wasDerivedFrom`).
- **Doubtful cases are visible:** they go to the reviewed CSV with their reason, never hidden inside a rule or a special
  case in the code.
- **The evidence never includes what a model predicts:** only what was known when the case started.

Where it lives comes from the domain's `method.linker` in `layer/dominios.yaml`: `folder` (the link tables in SQL, and a
`link.py` for what is not done in SQL, such as placing a point in a polygon, and for loading the CSVs), `corrections`
(the reviewed CSVs) and `service` (run it with `docker compose run --rm <method.linker.service>`). A linker may rebuild
its whole schema (`DROP`): anything that cannot be rebuilt goes in its own schema. If the registry has no
`method.linker`, the domain has no links yet; create one following the existing pattern (see `examples.md`).

## Steps: narrow down, decide, test

1. **Narrow down with the strongest thing available, and write the proposal.** In this order:
   - a **shared key** (a registry identifier such as the LEI, the source's own identifier);
   - a **domain rule** (a point falls inside an outline; whoever reports the latest period rules);
   - the **normalized name** (uppercase, without accents, punctuation or legal form), with one normalization function
     per domain, reused by every rule.

   Look at both sources: their keys, how many records share them, sample names. Write the result as a short table,
   one row per kind of entity to link, before touching any file:

   | Entity | Key or rule (shared key, domain rule or normalized name) | Sample pairs (3-5) with their evidence text | Expected doubtful cases | How sure | Open question |
   |---|---|---|---|---|---|

   A person reviews it at a glance; the rule and the doubtful cases are decided here. The table goes into the decision
   or the experiment log.
2. **Decide the rule and write it** in the link table: a `regla` column with the rule in words and an `evidencia`
   column with the values that justify it (for example, the normalized name that matched, quoted). When two sources
   disagree, **a written rule wins and the other version stays visible** (both values are kept, each with its source).
3. **Doubtful cases go to a reviewed CSV,** never to a hidden rule: `nombre, grupo, motivo` (or the document that
   backs it). If an AI assistant reviewed it, the reason says so: «Revisado por un asistente de IA, a confirmar por una
   persona» (reviewed by an AI assistant, to be confirmed by a person), and the app flags it.
4. **Map the link** (skill `map-source`): a link class with `prov:wasDerivedFrom` (the source),
   `prov:wasGeneratedBy` (the rule's activity), and the domain's rule and evidence-text properties
   (`<prefix>:rule` / `<prefix>:sourceText` or the names the domain already uses; see `term_sources`). Add the class to
   `link_sources` in `layer/dominios.yaml` and to the domain's list of links in `layer/evidencia.py`, so it counts in
   the evidence coverage.
5. **Test** (the checks below).

## The check that decides

- **Every link has a source and evidence:** the quality rule for link evidence (skill `quality-rules`, run with the
  domain's `method.quality.run`). Empty evidence is a link that cannot be audited. If the domain has no quality runner
  yet, check it with `layer/evidencia.py` and a SPARQL count of links without `prov:wasDerivedFrom` or evidence text.
- **Count per rule:** how many links come from each rule and how many from corrections. A big jump after a change is
  explained before moving on.
- **A known case, by hand:** pick one and check in both sources that the link is correct.
- **The questions that use it answer, and what was measured does not change by accident:** the domain's evaluation
  (`method.evaluation.run`) with `rerun` and `puntaje`. If a question changes, adjudicate it with the data from each
  source (`layer/<domain>/adjudicacion.md`).

## A person approves

- **The proposal:** the key or rule for each entity, its sample pairs and its open questions, before the linker is
  written.
- **The rule**, when it defines something about the business: who is responsible for an asset, what share belongs to a
  partner, since when a company holds something.
- **Each correction** in the CSV. The ones an AI assistant reviewed stay flagged until a person confirms them.

## Grounding

- **The theory of record linkage:** compare records by their attributes and decide with an explicit rule, separating
  sure matches, non-matches and cases for manual review (Fellegi and Sunter, «A Theory for Record Linkage»,
  *Journal of the American Statistical Association* 64(328), 1969). The three groups are Rastro's: rule, rule and
  reviewed correction.
- **Language models help decide, not replace the rule:** they compare entities well without training, but the
  best prompt changes with the model and the data (Peeters, Steiner and Bizer, «Entity Matching using Large Language Models»,
  EDBT 2025, doi:10.48786/edbt.2025.42). That is why they propose and a person confirms the doubtful cases.
- **Evidence as data:** each link is a `prov:Entity` with its origin and the activity that generated it (PROV-O,
  W3C recommendation, 2013).

## Watch out for

- **Concatenating a NULL wipes out the whole evidence:** in SQL, `'text ' || NULL` gives `NULL`. Records with an
  optional part missing end up with no evidence at all. Use `coalesce` on each part.
- **Same name is not the same company:** an outside source can have several entities with the same name (a foreign
  group, a homonym). Join by a shared key when there is one, and use only the matches that share it.
- **The evidence cannot carry what is being predicted:** if the link feeds a model, the evidence says only what was
  known at that moment; otherwise the target leaks into the features (skill `rastro-lab`).
- **A rule that discards data also decides:** a filter inside the rule (for example, skipping empty periods) changes
  the answer. Write down what it leaves out.
- **Company history** (mergers, sales, changes of legal name) goes in as a correction with its document and its
  date, not as a special case in the code.

Real cases, with their numbers: see `examples.md`.
