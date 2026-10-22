# Competency questions: research affiliations

The questions this domain has to answer, over a bounded set of 100 works drawn at random (seed 20261022) from a
pinned 2025 Crossref capture, linked to the pinned ROR v2.15 release. Scope, definitions and counting rule:
`docs/experiments/countrycodes/discussion.md` (scope proposal at `4217cf8`, clarifications at `05428c5`, user
approval). Each question's lifecycle state is in `layer/afiliaciones/lifecycle.json`.

| # | Question | Answer type | Role |
|---|---|---|---|
| 1 | For each affiliation string in the set, which Argentine organizations does it name, with what rule and evidence, and which strings remain ambiguous or name no ROR organization? | table | Integration and exceptions |
| 2 | How many works in the set name each Argentine organization, under the counting rule? | number per organization | Integration count |
| 3 | Which strings name an organization that ROR may not list, or name it in a form ROR does not record? | table | Exceptions |

Questions enter the lifecycle through `add-question`; none has a query yet.
