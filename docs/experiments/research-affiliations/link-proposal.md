# Link proposal: which Argentine organizations each affiliation names

Step 4 of the method (`link-entities`), for cq1–cq3. Status: **proposed, for the user's approval before the linker is
written**. Numbers measured on the 1,456 loaded mentions (one probe run, before any linker exists).

Entity: an **identification**, one row per affiliation mention and Argentine organization it names. Each row carries
the rule in words, the evidence (the values from each source that justify it), its source, and its status.

## Rules, strongest first

| Rule | Key or rule | Sample pairs with their evidence | Measured | How sure |
|---|---|---|---|---|
| **R0. Key from the publisher** | The ROR identifier the publisher added to the mention, when that organization is Argentine | 2 mentions; e.g. `10.5194/hess-29-2901-2025` → `ror.org/02c21vy68` | 2 | sure (a shared key) |
| **R1. Full name with a second piece of evidence** | A ROR display name, label or alias of an Argentine organization (at least 12 characters, normalized: lowercase, no accents or punctuation, e-mails and web addresses removed) appears as a whole phrase in the text, **and** the text also contains "Argentina" or one of the organization's ROR cities | "IQUIFIB, CONICET/University of Buenos Aires, Buenos Aires, Argentina" → Universidad de Buenos Aires; "... Hospital Italiano de Buenos Aires ..." → Hospital Italiano de Buenos Aires | about 320 identifications | sure |
| **R2. Unique acronym with a second piece of evidence** | An acronym that **only one** Argentine organization uses appears as a separate word, **and** the text contains "Argentina" or that organization's city | "Department of Neurology, Fleni, Buenos Aires, Argentina" → FLENI; "... (IQUIFIB), CONICET/..." → IQUIFIB and CONICET | 146 | fairly sure |

Normalization is one function for every rule, kept in the linker.

## Doubtful cases: to a reviewed CSV, never a hidden rule

| Case | Example | Measured |
|---|---|---|
| A full name **without** a second piece of evidence | "Instituto de Ciências Biológicas, Universidade de Brasília, Brazil" contains the Argentine "Instituto de Ciencias" once accents are removed | 3 |
| An acronym **shared** by several Argentine organizations, or **without** a second piece of evidence | "AstraZeneca, Cambridge UK": "UK" is the acronym of Universidad Argentina John F. Kennedy | 87 |

They go to `linking/afiliaciones/correcciones.csv` (`mention, organization, decision, reason`) as **rejected or
accepted with a reason**. Reviewed by an AI assistant, they say «Revisado por un asistente de IA, a confirmar por una
persona». The reference reviewer does not see this file (they stay blind).

## What is not linked

- **Parents:** never added; a mention of PLAPIQUI does not create a CONICET identification.
- **Mentions with no identification** (about 1,160, mostly foreign institutions) stay visible as mentions; Q1 lists
  the Argentina-text ones among them as unresolved.
- **Suspected gaps** (Q3): Argentina-text mentions that name an organization no rule finds in ROR. They are not
  links; the linker lists them as candidates for Q3 with the reason, and the reviewer decides.

## Status of each identification

- `rule` (R0, R1, R2), `correction-accepted`, `correction-rejected`. Rastro's answers count only `rule` and
  `correction-accepted`.

## Open question for the user

**cq2 says "only identifications accepted by the reviewer count".** The reference reviewer must stay blind to Rastro's
links, so the proposal reads it as: **Rastro's answer** counts its own accepted identifications (rules and accepted
corrections); **the reference** counts the reviewer's; and the evaluation compares the two. If that is the intended
meaning, approving this proposal records it; if not, cq2's definition has to be changed and re-approved.

## Mapping (after approval)

A class `afiliaciones:Identification` (a `prov:Entity`), with `afiliaciones:ofMention`, `afiliaciones:identifies` →
ArgentineOrganization, `afiliaciones:rule`, `afiliaciones:sourceText` (the evidence), `afiliaciones:linkStatus`,
`prov:wasDerivedFrom` both sources, `prov:wasGeneratedBy` the rule. New terms, shown as Turtle before writing.
