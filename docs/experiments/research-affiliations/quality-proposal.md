# Quality rules proposal: research affiliations

Step 5 of the method (`quality-rules`). Status: **approved by the user on 2026-10-22** (local time, UTC-3; 2026-10-23 in UTC), as shown in the session
(the three terms in Turtle and the seven rules with their messages): «Apruebo los tres términos y las siete reglas tal
como los mostraste.» Counts measured on the loaded data on 2026-10-22. Revised the same day after GPT's review of `386d825`
(`implementation-review.md`): both sources required, the IDEHU case framed as a registry-status finding, AI review kept
apart from human confirmation. No numeric thresholds: every rule checks completeness or consistency against the
approved definitions.

| Concept | Condition | Evidence | Would flag today | Severity | Open question |
|---|---|---|---|---|---|
| Identification | Has exactly one mention, exactly one organization, a rule, non-empty evidence, and derives from **both** Crossref and ROR | 539 identifications, all complete, each with both sources | 0 | violation | — |
| Identification | Its organization has a ROR location in Argentina (checked on the country value, since `identifies` implies the class) | 539, all in Argentina | 0 | violation | — |
| Identification | **Registry-status review:** its organization is not active in the pinned ROR release (v2.15) | 1: IDEHU (`ror.org/0425cyr19`), withdrawn in v2.15; ROR names CONICET (`ror.org/03cqe8w59`) as its successor | **1** | warning | Keep IDEHU, add the successor, or neither? A person decides |
| Doubtful candidate | Has a decision («accept» or «reject») and the reason for it | 91, all decided, each with its reason | 0 | violation | — |
| Doubtful candidate | **Human confirmation pending:** the decision was made by an AI assistant and no person has confirmed it | 91: decided by Claude, checked by GPT, no person yet | **91** | info | — |
| Affiliation mention | Has exactly one publication and non-empty text | 1,456, all complete | 0 | violation | — |
| Publication | Has exactly one DOI, with the DOI format (`10.` + registrant + `/` + suffix) | 100, all valid | 0 | violation | — |

**The IDEHU finding is not an impossible value.** The 2025 publication names IDEHU, and a later registry status does
not make that affiliation wrong. The rule says so: «el registro está retirado en ROR v2.15; su sucesor en ROR es
CONICET; una persona decide», with the release in the message and the successor read from ROR's own record. The
identification is not redirected, removed from cq1 or cq2, or hidden.

**The human-confirmation rule** keeps two facts apart that the decision column mixes: who decided (an AI assistant)
and whether a person confirmed it. It does not block the answers. The rule passes for a candidate once a person replaces
«pending» in the `human_confirmation` column of `correcciones.csv`.

What the rules do not do: change an identification, take it out of an answer, or lower a threshold. Each finding
stays visible with what uses it (the cq1 and cq2 answers).

Each rule gets a good and a broken example, from the real case where there is one: IDEHU for registry status and a
reviewed UK candidate for human confirmation.

## Dictionary terms the rules need (approved)

The mapped dictionary has none of these yet. GPT pointed out that a technical-view reader can see why a candidate
was generated, but not why it was rejected.

| Term | Label (es) | On | From |
|---|---|---|---|
| `afiliaciones:decisionReason` | motivo de la decisión | DoubtfulCandidate | `correcciones.csv` reason and source URL (already loaded in `afiliaciones.dudosa.decision_reason`) |
| `afiliaciones:humanConfirmation` | confirmación de una persona | DoubtfulCandidate | `correcciones.csv` `human_confirmation` («pending» for all 91 today) |
| `afiliaciones:successor` | sucesora en ROR | Organization | ROR v2.15 `relationships` of type successor (already loaded in `ror.relationship`) |

## Corrections after GPT's review of the rules (`2c84127`)

Same seven rules and the same findings today, made to say exactly what they check:

- **Registry status:** the warning severity now sits on the shape, so a withdrawn record reports a warning, not a
  violation. A missing or unknown status is now a violation instead of passing as active. The message gives the
  successor's ROR identifier and one of its ROR names (not ROR's display-name policy).
- **Human confirmation:** free text no longer passes. Until a confirmation record is approved, «pending» is the only
  valid state (checked in the doubtful-candidate rule), and the informational rule only flags what is pending.
- **Blank values:** rule, evidence, decision reason and mention text must contain a non-space character.
- **Extra cases with their severity:** `quality-cases.py` (16 cases, receipt `quality-cases.json`), since the shared
  runner checks one pair per rule and keeps no severity.

Still to decide, when a person confirms the first decision: a confirmation record with who confirmed, when, and the
evidence or approval it rests on. It needs new dictionary terms, so it comes back for approval then; no reviewer or
date is invented before that.
