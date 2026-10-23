# Quality rules proposal: research affiliations

Step 5 of the method (`quality-rules`). Status: **proposed, for the user's approval before the rules file is
written**. Counts measured on the loaded data on 2026-10-22. Revised the same day after GPT's review of `386d825`
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

## Dictionary terms the rules need (approval needed)

The mapped dictionary has none of these yet. GPT pointed out that a technical-view reader can see why a candidate
was generated, but not why it was rejected.

| Term | Label (es) | On | From |
|---|---|---|---|
| `afiliaciones:decisionReason` | motivo de la decisión | DoubtfulCandidate | `correcciones.csv` reason and source URL (already loaded in `afiliaciones.dudosa.decision_reason`) |
| `afiliaciones:humanConfirmation` | confirmación de una persona | DoubtfulCandidate | `correcciones.csv` `human_confirmation` («pending» for all 91 today) |
| `afiliaciones:successor` | sucesora en ROR | Organization | ROR v2.15 `relationships` of type successor (already loaded in `ror.relationship`) |
