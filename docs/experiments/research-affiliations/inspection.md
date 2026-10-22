# Research affiliations: source inspection

Inspector: Claude, 2026-10-22, using the `inspect-sources` skill (introduced in `002a39d`). Reviewer: GPT.
First version reviewed in `review.md` (revisions requested); this is the revised version, review of the revision
pending. Authorization, budget, roles and stop criteria: the user's decision in
[the shared discussion](../countrycodes/discussion.md). Working time: `inspection-time.yaml`.

Status: **read-only inspection; no domain, business question, link or implementation approved**.

## Finding and recommendation

**Suitable, conditionally.** The three stop criteria fixed before inspecting pass, and the join shows real
heterogeneity: Spanish and English names, word-order variants, acronyms shared by several organizations, addresses
and e-mails inside the strings, strings naming several organizations, institutes with two parents, and suspected
registry gaps. Conditions are listed at the end: a named reviewer, a bounded and fully adjudicated record set (or a
sample estimate with its uncertainty), and a parent and child counting rule, all fixed before measuring.

## Stop criteria

| Criterion (fixed before inspecting) | Measured (capture of 2026-10-22, see below) | Result |
|---|---|---|
| At least 30 % of the cohort's author affiliations carry a usable raw string | 49,484 of 51,928 authors (95.29 %) have at least one affiliation with nonblank text; all 62,216 affiliation entries have nonblank text | Passes, with the cohort bias below |
| At most 80 % of raw strings already carry a ROR identifier | Per entry: 65 of 20,888 Argentina-text entries (0.31 %). Per distinct raw string: 24 of 9,561 carry ROR in every occurrence (0.25 %); 6 more carry it in some occurrences only | Passes clearly by either measure |
| Open reuse terms for the fields used, as published | Crossref: factual metadata public domain (CC0), abstracts excluded and not used; ROR: CC0 | Passes |

**Cohort bias:** the cohort is defined by a Crossref query on affiliation text ("Argentina"), so every work in it
has deposited affiliations by construction. The 95.29 % describes authors inside this cohort, not Argentine research
output in general; works whose publishers deposit no affiliations are invisible, and their share is unknown.

**Argentina-text candidates:** "Argentina-text" means a string containing "Argentin". It is a candidate, not a
verified Argentine affiliation: "Lithium Argentina AG, Zug, Switzerland" is a Swiss company.

## Snapshot, terms and versions

| Source | Snapshot | Terms |
|---|---|---|
| Crossref REST API `works` | Captured by [`fetch.py`](fetch.py) with a request ledger (`crossref-ledger.json`): query `query.affiliation=Argentina`, journal articles published 2025-01-01 to 2025-12-31, selected fields DOI, authors with affiliations, journal, publisher, date, member, ISSN. 7 requests with cursor paging, 5,039 items of 5,039 reported, terminated by an empty page. Each page's cursor, size, time and SHA-256 are in the ledger. | [Crossref licensing](https://www.crossref.org/documentation/retrieve-metadata/): almost all metadata reusable without restriction; facts are public domain (CC0); abstracts keep their license (not used). The API is live: every run is a new snapshot. |
| ROR data dump v2.15, 2026-10-20 | [Zenodo record 23500708](https://zenodo.org/records/23500708), DOI 10.5281/zenodo.23500708, file `v2.15-2026-10-20-ror-data.zip`; MD5 `5522990688eb1b94811a8145e131b41e` matches Zenodo's published checksum. 146,716 records. | CC0 1.0 for all IDs and metadata ([data-dump documentation](https://ror.readme.io/docs/data-dump)). Versioned releases. |

Every artifact's size and SHA-256 is in `source-profile.json`; `profile.py` fails if any input is missing.

**First capture, superseded:** the first version of this inspection used a capture without a request ledger
(SHA-256 `e723ce28f96910833b867207f0b21aef53af1d5ac98de6819b6325e02be2d5e7`). It is kept locally but not used:
re-fetching cannot restore it. The new capture gives the same counts.

**Where raw captures are kept:** outside Git, in ignored `data/raw/research-affiliations/` on the inspector's
machine. A location the reviewer can access is a pending decision for the user.

## Grain, coverage and quality

- **Crossref:** one record per work (DOI), no duplicate DOIs. 51,928 authors, 62,216 author-affiliation entries.
  Affiliation entries are free text deposited by publishers; 286 carry an identifier, all ROR, asserted by the
  publisher. 20,888 entries are Argentina-text candidates: 9,561 distinct raw strings, 9,062 after a simple
  normalization (lowercase, accents and punctuation removed). Normalization groups strings; the original records
  are kept.
- **Publishers:** Wiley (1,434 works), MDPI (939), Wolters Kluwer (260), SAGE (248), SciELO (245) and others, so
  the strings follow many publishers' conventions.
- **ROR, Argentina:** 538 organizations (532 active, 3 inactive, 3 withdrawn). Types: education 173, facility 139,
  funder 76, healthcare 67, nonprofit 62, government 54. Names: 538 display names, 718 labels, 236 aliases, 426
  acronyms. Relationships: 272 parent links, 262 child, 92 related; 184 organizations have a parent.

## Integration: what the join looks like

A heuristic probe over the 9,561 distinct raw Argentina-text strings, after removing e-mails and URLs: whole-string
equality with a ROR name or acronym, then containment of long ROR names, then acronyms among the string's tokens.
Acronyms keep every organization that uses them; five are shared by two Argentine organizations (UM, YPF, IDIM,
INECO, CIC). **These counts describe the probe's behaviour, not the true number of ambiguous or unmatched
affiliations: several hits can be false candidates, and none is a link.**

| Probe outcome | Distinct raw strings |
|---|---|
| Whole string equals one organization's name | 13 |
| One heuristic hit | 4,499 |
| Several heuristic hits | 2,630 |
| No heuristic hit | 2,419 |

Concrete cases that need evidence and review rather than name equality:

| String in Crossref | What ROR says | Why it matters |
|---|---|---|
| "(UNS - CONICET), Planta Piloto de Ingeniería Química (PLAPIQUI), Camino La Carrindanga Km. 7, Bahía Blanca" | PLAPIQUI (`ror.org/00xpayr72`) has two parents: Universidad Nacional del Sur and CONICET's Bahía Blanca science centre | One string names three organizations; whether a publication counts for PLAPIQUI, UNS, CONICET or all three needs an approved rule |
| "(peter@df.uba.ar) National Scientific and Technical Research Council of Argentina, Buenos Aires" | CONICET (`ror.org/03cqe8w59`) lists this English label among eight names, and 81 relationships | The e-mail domain points to UBA but the text names CONICET; e-mails are removed before matching, and the probe now gives CONICET only |
| "National Commission of Atomic Energy of Argentina, Av. Gral. Paz 1499" | CNEA (`ror.org/01xz39a70`) is labelled "National Atomic Energy Commission" | A word-order variant: no heuristic hit; a reviewed rule or alias is needed |
| "Instituto Sabato, UNSAM/CNEA" | No record with "Sabato" in any name, alias, acronym or relationship label, across all 146,716 records and all statuses | A **suspected** registry gap; confirming it needs independent evidence of the organization and a check of parent records |
| "Instituto Patagónico de Geología y Paleontología, Puerto Madryn" | No such name across the full release; the only "IPGP" records are institutes in Paris and Guadeloupe | A suspected gap, and an acronym collision across countries |
| "Lithium Argentina AG, Zug, Switzerland" | Not Argentine | Country filtering by text alone is wrong |

**Controls:** the 65 Argentina-text entries with a publisher-asserted ROR identifier (for example Universidad de
Buenos Aires, `ror.org/0081fs513`) are a small control set, equally available to every approach. They are not an
independent reference: publishers may have obtained them from ROR's own matching.

**Independence, by field:** raw affiliation strings come from authors through publishers' deposits; ROR records
are curated by its community. Embedded ROR identifiers can share upstream evidence with ROR itself.

**Familiarity:** the vocabulary (publications, affiliations, research organizations and their hierarchies) is new to
Rastro. The entity-linking method is familiar. One overlap: YPF appears in ROR as two organizations sharing the
acronym, and YPF is in Rastro's oil and gas domain; that knowledge must not be reused as a link.

## At most three proposed questions

All proposed, not approved. Definitions, counting rules and references are pending, and must be fixed before
measuring, without tuning the cohort after seeing which approach wins.

| Question | Proposed definitions and output | Independent verification plan |
|---|---|---|
| 1. In a bounded set of 2025 records, which affiliation strings name which Argentine organizations in ROR, with what evidence, and which remain ambiguous or unmatched? | Integration and exception question. A table per raw string: the organizations named, the rule and evidence for each, ambiguous and unmatched cases explicit. A string can name several organizations. | The reviewer adjudicates every string in the bounded set from the original records, without seeing any approach's links. If the set is too large, a blind stratified sample with a fixed frame, seed, sample sizes and weighting decided before measurement, reported as a link-quality estimate. |
| 2. How many publications in that set carry each confirmed organization, counting double affiliations under an approved parent and child rule? | Integration count, once per publication and organization. Valid as an exact total **only over a fully adjudicated set**; over a sample it is an estimate with its uncertainty. Describes the set, not institutional output or quality. | Recomputed from the original records and the adjudicated links of question 1 with the approved rule, by a separate calculation. Recomputing with unreviewed links checks arithmetic only. |
| 3. Which affiliations name an organization that ROR may not list, or name it in a form ROR does not record? | Exception table of suspected gaps and missing name variants, with evidence for each. | The reviewer checks each case against the full ROR release (names, aliases, statuses, parents) and the organization's own sources. Any curation request to ROR would be a separate external action, not authorized here. |

## Sizing the bounded set

Works and distinct raw Argentina-text strings per 2025 publication month, from the inspector's capture (works
without a month in their date are listed separately):

| Month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | none |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Works | 346 | 302 | 326 | 360 | 357 | 395 | 394 | 353 | 358 | 391 | 397 | 578 | 453 |
| Distinct strings | 725 | 636 | 745 | 750 | 739 | 840 | 785 | 699 | 732 | 832 | 861 | 1,102 | 628 |

A single month means adjudicating about 640 to 860 strings by hand. A random sample of works drawn with a fixed
seed before measuring (for example 100 works, about 200 strings) is cheaper; question 2 would then be exact over
that set, not over the month.

## Conditions before approving scope

1. **A named reviewer** with research-management or library experience, who did not build Rastro.
2. **A bounded record set** small enough to adjudicate fully (for example one month, or one field), so question 2
   can be an exact total; otherwise question 2 becomes a sample estimate.
3. **The parent and child counting rule**, the sampling design if any, and the geography rule fixed before
   measuring.
4. **The non-accuracy checks and stop budget** from Rounds 4 and 5, and the method version frozen at `002a39d` or
   later.
5. **A location for raw captures** that the reviewer can access, or the reviewer re-runs `fetch.py` and accepts it
   as a new snapshot.

No source, link, question or domain was approved or created by this inspection. Accuracy ties between the three
approaches remain a valid result.
