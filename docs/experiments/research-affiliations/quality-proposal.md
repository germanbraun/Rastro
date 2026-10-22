# Quality rules proposal: research affiliations

Step 5 of the method (`quality-rules`). Status: **proposed, for the user's approval before the rules file is
written**. Counts measured on the loaded data on 2026-10-22. No numeric thresholds: every rule checks completeness or
consistency against the approved definitions.

| Concept | Condition | Threshold | Evidence | Would flag today | How sure | Open question |
|---|---|---|---|---|---|---|
| Identification | Has exactly one mention, exactly one organization, a rule, non-empty evidence and at least one source | — | 539 identifications, all complete | 0 | sure | — |
| Identification | Its organization has a ROR location in Argentina (checked on the country, not on the class, since `identifies` implies the class) | — | 539, all in Argentina | 0 | sure | — |
| Identification | Its organization is **active** in ROR; otherwise it is flagged with its successor, for a person to decide | — | 1 to a withdrawn record: IDEHU (`ror.org/0425cyr19`), whose successor in ROR is CONICET | **1** | sure | Keep IDEHU (the text names it) or redirect to the successor? A person decides; the rule does not change it |
| Doubtful candidate | Has a reviewed decision, «accept» or «reject» | — | 91, all decided | 0 | sure | — |
| Affiliation mention | Has exactly one publication and non-empty text | — | 1,456, all complete | 0 | sure | — |
| Publication | Has exactly one DOI, with the DOI format (`10.` + registrant + `/` + suffix) | — | 100, all valid | 0 | sure | — |

What the rules do not do: change an identification, remove it from the answers, or redirect IDEHU. Each finding
stays visible with what uses it (the cq1 and cq2 answers), and a person records the disposition.

Each rule gets a good and a broken example, taken from the real case where there is one (IDEHU for the active-status
rule).
