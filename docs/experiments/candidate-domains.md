# Candidate domains after the electricity review

Proposed by Codex/GPT, 2026-10-22. Claude's shortlist review is pending.

Status: **two candidates for discussion; no domain, inspection budget, roles or questions approved**.
This follows the user's request to propose two or three candidates. The approved `inspect-sources` skill informs
the selection criteria; its full source-inspection workflow has not been executed for either candidate.

Scope of this work: publisher documentation and catalog discovery only. No data files downloaded, record samples
profiled, links calculated, domain registered or services started. Reported freshness and terms below are publisher
or catalog statements, not verification of the underlying files. Open/download attempts for the charity register
returned 403; its indexed official documentation was available. Data access remains unverified.

## Recommendation

**Inspect research affiliations first; keep charitable grant recipients as the second candidate.** Research has a
clear naming/organization problem and a manageable bounded API-based starting point. Grants has an immediately
understandable funding question, but source-file terms/access and the extent of nontrivial linking need confirmation.
Both are outside Rastro's existing oil-and-gas, federal-supplier and oncology cases. Organization linking is familiar
method machinery; neither candidate is therefore an assertion of unfamiliarity in every respect.

I have not padded the list with a third weak candidate. England's school register and Ofsted inspections have recent
official releases, but a simple shared-identifier join could repeat the countrycodes weakness. That pair would need
an additional case for meaningful identity work before it displaced either candidate below.

## 1. Research affiliations and institutional output

**Who might use it:** a university research office reconciling organization names in deposited publication metadata.
A research-information manager or librarian would be a suitable business reviewer; no person has been appointed.

**Sources to inspect:**

- **Crossref works metadata**, using its [REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
  and [reuse terms](https://www.crossref.org/documentation/retrieve-metadata/). Crossref describes publisher/member
  deposits, open public API access and unrestricted factual bibliographic metadata; it separately identifies
  Crossref-generated data as CC0 and warns that abstracts retain other copyrights. Candidate scope excludes
  abstracts and full text. The [2026 release announcement](https://www.crossref.org/blog/2026-public-data-file-now-available/)
  establishes a recent release exists; inspect a bounded recent publication cohort through the API rather than
  downloading the entire corpus. Snapshot publication dates and metadata-update dates separately.
- **Research Organization Registry (ROR)**, using the [registry's curation and licensing description](https://ror.org/registry),
  [versioned data releases](https://ror.readme.io/docs/data-dump) and [name/relationship schema](https://ror.readme.io/docs/ror-data-structure).
  ROR declares CC0, community curation and at least monthly releases. Its schema documents multilingual aliases,
  organizational relationships and status. Inspect the current release and preserve its version and fingerprint.

**Why two sources:** publisher-deposited affiliation assertions describe research outputs; ROR curates organization
identities. These are different maintenance workflows, not two copies of a publication table. They are connected
infrastructure, however: Crossref may already carry or enrich ROR identifiers. Inspection must distinguish raw
deposited strings, supplied identifiers and derived matches. Existing IDs are useful controls and must be equally
available to B/D/C; do not strip them to make linking look difficult. ROR-backed matching output is not an
independent ground truth for a newly proposed ROR link.

**Proposed join and useful questions:** raw affiliation text, organization names, location and supplied ROR IDs
where present. The expected challenge is abbreviations, languages, department/parent distinctions and historical
names; the frequency of those cases is unmeasured.

1. In a bounded recent publication cohort, which deposited affiliation strings can be linked to which organizations,
   with what evidence, and which remain ambiguous?
2. How many distinct publications in that cohort are associated with each confirmed organization, preserving
   multiple affiliations and an approved parent/child counting rule?

These questions describe the selected metadata cohort, not total institutional productivity or research quality.
Independent review would check original deposited records and organization evidence, with source-record references
and approved counting invariants; it must not merely endorse the mapping's own answers.

**Inspection must decide:** enough records actually have usable raw affiliations; real nontrivial cases exist;
source-field terms satisfy the approved open-reuse requirement; names and relationships have adequate evidence;
the cohort is bounded independently of which approach wins. If the pair reduces to prelinked IDs or lacks usable
affiliations, report that and reject or narrow the candidate honestly. An Argentine institution/cohort is possible,
but geographic coverage and reviewer usefulness are not yet established.

## 2. Charitable grant recipients and register identity

**Who might use it:** a grantmaking team checking which organizations received awards and how recipients appear in
the charity register. A grant-program or charity-data specialist would review definitions; no person is appointed.

**Sources to inspect:**

- **National Lottery Community Fund award data**, located through its [publisher entry on 360Giving](https://grantnav.threesixtygiving.org/org/360G-tnlcomfund?_redirect_src=int).
  That entry attributes the data to the funder, links original datasets and lists OGL 3.0 for them. It includes
  award-period titles through July–September 2026. Retrieval timestamps are not award dates or proof of complete
  coverage. The selected source file and the publisher's terms must still be checked directly. 360Giving is the
  discovery/standardization route, not an independent second grant source.
- **Charity Commission for England and Wales**, using its [official bulk-extract documentation](https://register-of-charities.charitycommission.gov.uk/en/register/full-register-download)
  and [official API terms](https://api-portal.charitycommission.gov.uk/terms). The documentation describes daily
  JSON/tab-delimited extracts and separate charity/other-name records. API terms reference OGL, but inspection
  must confirm terms for the actual selected bulk files rather than transfer an API license by assumption.

**Why two sources:** a funder maintains award/recipient assertions, while a regulator maintains registration and
charity identity. A common charity identifier is useful evidence; naming differences, missing identifiers and linked
charities could require reviewed reconciliation. Their actual prevalence is not established. GrantNav's cleaned or
enriched recipient records must not become a hidden ready-made linker or independent reference.

**Proposed questions:**

1. For one recent award period and a bounded England/Wales program, which recipient records can be identified in
   the charity register, and which have no unique supported match?
2. What award amounts and grant counts are associated with each confirmed charity, retaining the original recipient
   name, award date, identifier and the register snapshot date?

An award is not a payment. Current registration is not registration at award time. Missing register matches may
be legitimate unregistered groups or organizations outside the regulator's jurisdiction; do not label them invalid
recipients. Independent references would reconcile original award records and regulator records, review uncertain
identities and separately calculate approved totals. No financial-risk or compliance judgment is proposed.

**Inspection must decide:** original-file access and open terms are confirmed; recent award observations are present;
recipient identity has enough checkable heterogeneity; linked charities do not cause duplicate award counting;
program/geographic filtering is possible without pretending recipient address is the place benefited. This is a new
nonprofit-funding domain, although organization names and monetary aggregation are familiar method problems.

## Review and selection

Claude should challenge the ranking, licensing evidence, source dependence, reviewer usefulness and likely linking
work before a candidate is selected. These are plausible candidates, not a finding that either meets every gate.
In particular, publisher documentation cannot establish actual access, completeness or join ambiguity.

Then the user chooses a candidate, a fresh inspection time budget and who inspects/reviews. The electricity
three-hour budget does not carry over automatically. Only that bounded inspection should produce snapshots,
fingerprints, concrete join examples and the final question/definition table. Domain implementation remains a later
decision. Preserve B/D/C fairness, allow accuracy ties, and freeze the method version before an approved experiment.

## Review of the shortlist — Claude (2026-10-22)

**Ranking: agree.** Research affiliations first, grant recipients second.

**Research affiliations (Crossref + ROR):**

- **For:** both sources declare open terms (CC0) and versioned, recent releases. The heterogeneity is the kind
  Rastro is built for: free-text affiliation strings on one side, curated organizations with aliases, languages and
  parent/child relationships on the other.
- **Main risks:** few records may carry usable raw affiliation strings, and many may already carry a ROR
  identifier, which would make the join nearly trivial. Both must be measured early.
- **Proposal: an Argentine cohort** (CONICET and national universities, for example). Affiliations there often
  combine two institutions ("CONICET – UBA"), mix Spanish and English names and abbreviations, and include institutes
  with two parents. That gives real identity work, a better chance of finding a local reviewer, and a result that
  can be shown in Argentina. Geographic coverage still has to be checked.
- **Fix the stop criteria before inspecting**, so they do not depend on which approach would win: reject or narrow
  the candidate if usable raw affiliations fall below an agreed share of the cohort, or if nearly all records
  already carry ROR identifiers. Supplied identifiers stay available to B, D and C alike, as you proposed.

**Grant recipients (360Giving + Charity Commission):** keep as second. It risks reducing to a join on charity
number (the countrycodes weakness), direct access returned 403, and it is far from Rastro's audience, which makes
a reviewer harder to find.

**Roles:** GPT proposed the research candidate, so by the same rule as for electricity, Claude inspects and GPT
reviews.

**For the user:** choose the candidate, the inspection budget and the roles. Nothing is approved by this review.
