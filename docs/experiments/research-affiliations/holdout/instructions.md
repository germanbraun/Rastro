# Blind annotation of research affiliation strings

You annotate affiliation strings from scientific publications (2025, at least one Argentine author). Your annotation
is the reference against which an automatic matcher will be scored, so read every string yourself.

## What you get (this folder only)

- `strings-partN.csv`: your strings. `review` is `full` when the text contains «argentin», `screen` otherwise.
- `ror-argentina.csv`: the 538 organizations with a location in Argentina in the ROR registry (v2.15), with every
  name (`[ror_display]`, `[label]`, `[alias]`, `[acronym]`), their city and relationships.

## The rule

An affiliation **names** an Argentine organization (one in `ror-argentina.csv`) when its text contains the
organization's name, a ROR label or alias, or an acronym that only that Argentine organization uses. Ignore case,
accents and punctuation. A parent organization does not receive its institutes' mentions: mark only what the text
itself names (a string naming an institute and CONICET gets both; one naming only the institute gets only it). A name
that is only part of a longer, different name does not count (e.g. «Instituto de Ciencias» inside «Instituto de
Ciencias de la Tierra…» names only the longer one, if it is in ROR). A footnote letter glued to a name
(«AUniversidad de Buenos Aires») still names it. A text that names an organization abroad with the same name does not
name the Argentine one.

## Output

Write `annotations-partN.csv` (same N as your strings) with columns:
`string_id,organizations,other_references,evidence,ambiguous,note`

- `organizations`: the ROR ids the string names under the rule, separated by a space. Empty if none, with «ninguna»
  in `note` (for `screen` strings that name nothing, «ninguna» is enough).
- `other_references`: ROR ids the text clearly refers to with a form ROR does not have (these do not count).
- `evidence`: for each id, the words that name it: `https://ror.org/03cqe8w59=«CONICET»; …`.
- `ambiguous`: `yes` when unsure (an acronym two organizations could use, a name that also exists abroad), with why
  in `note`; else empty.

One row per string, every string. Use Python's csv module to write it (texts contain commas and quotes).
