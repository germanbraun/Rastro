# Research affiliations: source inspection

Inspector: Claude, 2026-10-22, using the `inspect-sources` skill (introduced in `002a39d`). Reviewer: GPT, review
pending. Authorization, budget, roles and stop criteria: the user's decision in
[the shared discussion](../countrycodes/discussion.md). Working time: `inspection-time.yaml`.

Status: **read-only inspection complete; no domain, business question, link or implementation approved**.

## Finding and recommendation

**Suitable, conditionally.** All three stop criteria fixed before inspecting pass, and the join has real,
inspectable heterogeneity: Spanish and English names, word-order variants, acronyms, addresses and e-mails inside
the strings, double affiliations, institutes with two parents, and organizations missing from the registry. The
conditions are listed at the end: a named reviewer, an approved counting rule for parent and child organizations,
and a reference plan based on a sample, because the cohort has 9,062 distinct Argentine affiliation strings.

## Stop criteria

| Criterion (fixed before inspecting) | Measured | Result |
|---|---|---|
| At least 30 % of the cohort's author affiliations carry a usable raw string | 49,484 of 51,928 authors (95 %) have at least one affiliation; all 62,216 affiliation entries carry a text string | Passes, with the cohort bias below |
| At most 80 % of raw strings already carry a ROR identifier | 65 of 20,888 Argentine affiliation entries (0.3 %); 286 of 62,216 entries overall | Passes clearly |
| Open reuse terms for the fields used, as published | Crossref: factual metadata public domain (CC0), abstracts excluded; ROR: CC0 | Passes |

**Cohort bias:** the cohort is defined by a Crossref query on affiliation text ("Argentina"), so every work in it
has deposited affiliations by construction. The 95 % describes authors inside this cohort, not Argentine research
output in general. Works whose publishers deposit no affiliations are invisible here; their share is unknown.

## Access, terms and versions

| Source | Access and content | Terms and version |
|---|---|---|
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | `works`, polite pool with a contact address, cursor paging, no credentials. Query: `query.affiliation=Argentina`, journal articles published 2025-01-01 to 2025-12-31, fields DOI, authors with affiliations, journal, publisher, date, member, ISSN. 5,039 works, retrieved 2026-10-22T18:00:28Z. | [Crossref's licensing statement](https://www.crossref.org/documentation/retrieve-metadata/): almost all metadata reusable without restriction; facts are public domain (CC0); abstracts keep the publisher's or author's license (not used). Records are mutable: publishers update deposits, so the saved file and its hash are the version. |
| [ROR data dump](https://ror.readme.io/docs/data-dump), [Zenodo release](https://zenodo.org/api/communities/ror-data/records?q=&sort=newest&size=3) | Release v2.15, 2026-10-20 (two days before inspection), schema 2; JSON and CSV in one ZIP. MD5 matches Zenodo's (`5522990688eb1b94811a8145e131b41e`). 146,716 records. | CC0 1.0 for all IDs and metadata, as stated in the data-dump documentation and the Zenodo record. Versioned releases. |

`ror.org/registry` returned HTTP 429 (rate limit) once; the same terms were read from the data-dump documentation.
File sizes and SHA-256 hashes for every artifact are in `source-profile.json`. Raw files stay in ignored
`data/raw/research-affiliations/`.

## Grain, coverage and quality

- **Crossref:** one record per work (DOI), no duplicate DOIs. 51,928 authors, 62,216 author-affiliation entries.
  Affiliation entries are free text deposited by publishers; a few carry an identifier (all ROR, asserted by the
  publisher). 20,888 entries mention Argentina; 9,062 distinct strings after a simple normalization.
- **Publishers:** spread across Wiley (1,434 works), MDPI (939), Wolters Kluwer (260), SAGE (248), SciELO (245)
  and others, so the strings follow many publishers' conventions.
- **ROR, Argentina:** 538 organizations (532 active, 3 inactive, 3 withdrawn). Types: education 173, facility 139,
  funder 76, healthcare 67, nonprofit 62, government 54. Names: 538 display names, 718 labels, 236 aliases, 426
  acronyms. Relationships: 272 parent links, 262 child, 92 related; 184 organizations have a parent.
- **Country detection is itself a trap:** "Lithium Argentina AG, Zug, Switzerland" contains "Argentina" but is a Swiss
  company. Filtering on the word must not decide that an affiliation is Argentine.

## Integration: what the join looks like

A naive structural probe (normalized name equality, then containment of ROR names and acronyms) over the 9,062
distinct Argentine strings. These counts indicate difficulty only; none of the candidates is a proposed link.

| Probe outcome | Distinct strings |
|---|---|
| Exactly one ROR name equal to the whole string | 13 (0.1 %) |
| One candidate organization contained in the string | 4,480 |
| Several candidate organizations contained in the string | 2,651 |
| No candidate | 2,417 |

Concrete cases that need evidence and review rather than name equality:

| String in Crossref | What ROR says | Why it matters |
|---|---|---|
| "(UNS - CONICET), Planta Piloto de Ingeniería Química (PLAPIQUI), Camino La Carrindanga Km. 7, Bahía Blanca" | PLAPIQUI (`ror.org/00xpayr72`) has two parents: Universidad Nacional del Sur and CONICET's Bahía Blanca science centre | One string names three organizations; whether a publication counts for PLAPIQUI, UNS, CONICET or all three needs an approved rule |
| "National Scientific and Technical Research Council, Godoy Cruz 2290, Autonomous City of Buenos Aires" | CONICET (`ror.org/03cqe8w59`) lists this English label among eight names, and 81 relationships | English and Spanish names, acronym, address noise; CONICET is also the parent of many institutes |
| "National Commission of Atomic Energy of Argentina, Av. Gral. Paz 1499" | CNEA (`ror.org/01xz39a70`) is labelled "National Atomic Energy Commission" | A word-order variant: no naive candidate, a reviewed rule or alias is needed |
| "Instituto Sabato, UNSAM/CNEA" and "Instituto Patagónico de Geología y Paleontología" | Not found by name in this ROR release | Real registry gaps, not join errors; they should stay visible |
| "Lithium Argentina AG, Zug, Switzerland" | Not Argentine | Country filtering by text alone is wrong |

**Controls:** the 65 Argentine entries with a publisher-asserted ROR identifier (for example Universidad de Buenos
Aires, `ror.org/0081fs513`) are a small control set, equally available to every approach. They are not an
independent reference: publishers may have obtained them from ROR's own matching service.

**Independence:** affiliation strings come from authors through publishers' deposits; ROR is curated by its
community. They are maintained independently, apart from the few publisher-asserted ROR identifiers.

**Familiarity:** the vocabulary (publications, affiliations, research organizations and their hierarchies) is new to
Rastro; none of its existing domains covers it. The entity-linking machinery (rules, evidence, reviewed corrections)
is familiar method, as the candidate proposal said.

## At most three proposed questions

All proposed, not approved. Definitions, counting rules and references are pending.

| Question | Proposed definitions and output | Independent verification plan |
|---|---|---|
| 1. In the 2025 cohort, which affiliation strings name which Argentine organizations in ROR, with what evidence, and which remain ambiguous or unmatched? | Integration and exception question. A table per distinct string: the organizations named, the rule and evidence for each, and the ambiguous or missing cases kept explicit. A string can name several organizations. | A reviewer codes a stratified random sample of strings (by probe outcome and publisher) from the original records, without seeing any approach's links. Agreement is measured on that sample; disagreements are adjudicated and recorded. |
| 2. How many cohort publications carry each confirmed organization, counting double affiliations under an approved parent and child rule? | Integration count. A publication counts once per organization; whether a child institute also counts for its parents is decided before measuring. Describes this cohort only, not institutional output or quality. | Recomputed from the original records and the reviewed links of question 1, with the approved rule, by a separate calculation. Totals are checked against simple invariants (no publication counted twice for the same organization). |
| 3. Which affiliations name an organization ROR does not list, or name it in a form ROR does not record? | Exception table: the string, the organization it names, and the evidence; distinguishes a registry gap (Instituto Sabato) from a missing name variant (CNEA's word order). | Each case is checked by the reviewer against ROR's current release and the organization's own sources. Useful output for a research office: candidates for curation requests to ROR. |

## Conditions before approving scope

1. **A named reviewer** with research-management or library experience, who did not build Rastro, to approve the
   counting rule and adjudicate the sample.
2. **A bounded cohort for the experiment.** All of 2025 has 9,062 distinct strings; a narrower slice (one quarter,
   or one field) would keep the reference sample and adjudication within a reasonable budget.
3. **The parent and child counting rule** decided before measuring, since CONICET is the parent of many institutes.
4. **The non-accuracy checks and the stop budget** from Rounds 4 and 5, fixed before execution, and the method
   version frozen at `002a39d` or later.

No source, link, question or domain was approved or created by this inspection. Accuracy ties between the three
approaches remain a valid result.
