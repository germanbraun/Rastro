# Blind reference review: research affiliations

**Reviewer:** GPT, chosen by the user on 2026-10-26. This is the reference for scoring the evaluation (step 6). It is
an AI review: its results are reported as «revisadas por IA, falta que una persona las confirme» until a person
checks them.

## What you get

Everything here comes from the two sources as loaded, not from Rastro (`build.sh` rebuilds it):

- `strings.csv`: the 962 distinct affiliation strings of the 100 works (1,456 mentions). `review` is `full` for the
  196 strings whose text contains «argentin» (accents and case ignored) and `screen` for the other 766.
- `ror-argentina.csv`: the 538 organizations with at least one ROR v2.15 location in Argentina, with every name
  (`[ror_display]`, `[label]`, `[alias]`, `[acronym]`) and their relationships.
- `mentions.csv`: each of the 1,456 mentions with its string (you do not need it; `reference.py` uses it).
- `annotations.csv`: the template you fill, one row per string.

## Stay blind

Until your annotation is committed, do **not** open, query or read the history of: `layer/afiliaciones/`,
`linking/afiliaciones/`, `mappings/afiliaciones.r2rml.ttl`, `ontology/afiliaciones/`, `app/dominios/afiliaciones*`,
the rest of `docs/experiments/research-affiliations/`, `docs/experiments/afiliaciones.yaml`, the `afiliaciones`
schema in Postgres or the Ontop endpoint on :8083. Use only this folder. If you open any of them by mistake, say so
in the receipt; the review is then not blind for those strings.

## The rule (from the approved evaluation questions)

An affiliation **names** an Argentine organization (one in `ror-argentina.csv`) when its text contains the
organization's name, a ROR label or alias, or an acronym that only that Argentine organization uses. Ignore
differences of case, accents and punctuation. A parent organization does not receive its institutes' mentions: mark
only what the text itself names (a string that names an institute and CONICET gets both; one that names only the
institute gets only the institute).

## What to write in `annotations.csv`

- **`screen`** (only `screen` rows): `no` if the string names no Argentine organization, `yes` or `unsure` otherwise.
  Every `yes` or `unsure` row then gets the full columns below, like a `full` row. A `no` is the reference for that
  string: decide it by reading, not by a name filter.
- **`organizations`** (`full` rows, and `yes`/`unsure` rows): the ROR ids it names under the rule, separated by a
  space (`https://ror.org/03cqe8w59 https://ror.org/0081fs513`). If none, leave it empty and write «ninguna» in
  `note`, so a reviewed row is told apart from a skipped one.
- **`other_references`**: ROR ids the text clearly refers to with a form that ROR does not have (an official name or
  an abbreviation missing from ROR, for example «Hospital de Pediatría Prof. Dr. Juan P. Garrahan»). These do not
  count under the rule; they let us report how much the rule leaves out.
- **`evidence`**: for each id, the words of the text that name it: `https://ror.org/03cqe8w59=«CONICET»; …`.
- **`ambiguous`**: `yes` when you are not sure (an acronym two organizations could use, a name that also exists
  abroad), and say why in `note`.

## When you finish

Commit only `annotations.csv` and a `receipt.md` with: the model and version, start and end times, how many strings
you screened and fully reviewed, the ambiguous cases, and a sentence on blindness (what you opened). Then add a short
handoff to `docs/experiments/countrycodes/discussion.md`. Claude derives the five references from your annotation
with `reference.py` and scores the 33 saved answers; nothing is scored before your commit.
