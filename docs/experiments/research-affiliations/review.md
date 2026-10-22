# Review of the research-affiliations inspection

Reviewer: Codex/GPT, 2026-10-22. Reviewed commit: `a87a242`.
Authorization and roles: the research-affiliations decision in `../countrycodes/discussion.md`.

**Assessment: promising candidate; revise the inspection evidence before scope approval.** This is an inspection,
not an implemented experiment or a published B/D/C measurement. The source pairing has a plausible integration
problem. The report correctly retains cohort bias, multiple organizations per string and unapproved counting rules.
The findings below do not reject the domain; they limit what this inspection establishes.

## Verification performed and limits

Read the inspection, time log, profiler, committed source profile and authorization. Independently recomputed the
profile's count sums and ratios, and ran Ruff on the profiler (passed). None of the six ignored input artifacts is
present in this checkout. I did not re-download a replacement cohort or claim its mutable contents reproduce the
original bytes. Original hashes, page completeness, ROR checksum and the concrete organization claims have therefore
**not been independently verified** in this review. The committed profile supports arithmetic and code review, not
independent raw-source reproduction.

## Corrections and evidence needed

1. **Separate raw strings from normalized strings.** `crossref.distinct_argentine_strings` is 9,062 after `norm()`;
   `join_probe.distinct_argentine_strings` is 9,561 because the probe iterates `sorted(set(ar))`. Its outcomes sum
   to 9,561: 13 + 4,480 + 2,651 + 2,417. The report's statement that the probe operates over 9,062 strings is wrong.
   Choose and label the counting unit consistently, including any reference-sampling frame. Normalization can
   collapse distinct source strings; preserve the original records even if normalized forms are grouped.
2. **The naive probe is not sound evidence of candidate multiplicity or absence.** Its acronym dictionary maps each
   acronym to a single organization, silently overwriting collisions. Index acronyms to sets if retaining the probe.
   Tokenizing an entire string also treats pieces of addresses and e-mails as organization evidence: the committed
   example containing an `uba.ar` e-mail produces a UBA candidate even though the affiliation text names CONICET.
   Keep such results labeled heuristic hits. Several hits can be false candidates, rather than several organizations
   actually named. The current counts establish probe behavior, not the true number of ambiguous affiliations.
3. **No name match does not establish a registry gap.** Instituto Sabato and the other apparent missing organizations
   require checks across aliases, locations, inactive/withdrawn records, parent/child scope and the full registry,
   followed by independent organization evidence. Until that is retained, label them suspected gaps. Q3's distinction
   between a missing organization and an unrecorded variant is useful, but not yet demonstrated by absence in this
   name/containment probe. A future curation request is a separate external action, not authorized here.
4. **Make snapshot recovery and cohort completeness reviewable.** The Crossref artifact URL is a generic endpoint;
   the ROR URL is not the exact immutable release record or file. Record the concrete ROR record/file URL and retain
   its published checksum evidence. Preserve the original Crossref capture through an accessible approved artifact
   location outside Git, plus the retrieval script or request/page ledger, pagination termination, reported totals,
   query parameters and request dates. Re-fetching mutable API data is a new snapshot, not restoration of an old hash.
   The profiler silently omits missing files from its artifact manifest; required evidence should fail explicitly.
   No source file needs to be committed to fix this.
5. **Define the gate denominators precisely.** The 95.29% author share and 0.31% identifier share follow from the
   committed counts, but `authors_with_at_least_one_affiliation` tests a nonempty list, not usable text directly.
   All entries reportedly have text in this capture, which makes those measures agree here; use nonblank text for
   the gate itself. The identifier threshold is reported on repeated entries, whereas the approved criterion says
   raw strings. Report entry-weighted and distinct-string measures, with a policy for strings whose occurrences have
   conflicting/missing IDs. Call the `argentin` substring subset Argentina-text candidates, not verified Argentine
   affiliations. The report's own Swiss-company example demonstrates why that distinction matters.
6. **Sampling cannot validate an unrestricted exact total.** Blind stratified sampling is a reasonable link-quality
   evaluation, with a fixed seed/frame, sample sizes and weighting specified before measurement. It does not
   independently validate Q2's exact full-cohort organization totals when most links remain unreviewed. Either bound
   the experiment to a fully adjudicated record set, or publish a correctly designed sample-based estimate with its
   uncertainty. Independently recomputing a total using unreviewed links only checks arithmetic. Do not tune the
   cohort after observing which approach wins.

## Handoff

Claude should amend the report/profiler and provide recoverable snapshot evidence, then GPT can check the revised
claims. No new domain implementation is needed to resolve these points. Publisher-provided ROR IDs remain available
equally to B/D/C. Treat source independence as field-specific: raw publisher affiliation assertions and curated
organization records have different maintenance, while embedded or enriched ROR matches can share upstream evidence.

After that review, the user's scope decision still needs a named business reviewer, the bounded cohort, geography
and parent/child rules, independent references, non-accuracy checks and a separate implementation budget. Freeze
the actual method version before implementation. Accuracy ties remain acceptable; no link, question, domain or
implementation is approved by this review.

## Review time

Detailed verification was timed from 2026-10-22T18:09:47Z; its end is recorded in `review-time.yaml`. Preliminary
pulling/reading before that interval was not timed and is excluded, rather than assigned an invented duration.
No human time is supplied and no other chat's time is counted.

## Revision review — Codex/GPT, 2026-10-22

Reviewed `35fb6a9` and executed `fetch.py` under the user's recorded decision to verify a **new** snapshot.
The original review above describes `a87a242`; the findings below supersede its outstanding inspection corrections.

**Assessment: the substantive inspection revisions are addressed. Research affiliations is a supported candidate
for the user's scope decision. This accepts the inspection evidence, not the proposed business definitions,
questions, links, implementation or any claim of transfer.**

### Independent execution

- ROR v2.15 was downloaded by the script. Its MD5 is `5522990688eb1b94811a8145e131b41e`, checked independently
  against the file metadata returned by `https://zenodo.org/api/records/23500708`. Its SHA-256 is
  `7a7bf58d5ac18436ed98daf5da906913761d54869edf86d405e51966609dd133`, matching Claude's archive.
- Crossref requests ran from 2026-10-22T18:20:03Z to 18:20:25Z. The page sizes were
  **1,000, 1,000, 1,000, 1,000, 1,000, 39, 0**: 5,039 retrieved and 5,039 reported, with empty-page termination.
  Query, request count, item count and reported total match Claude's committed ledger summary. Claude's full page
  ledger is not available here, so its individual page sizes were not independently compared.
- The reviewer's capture SHA-256 is `02c8fffa28b34d8f5a36e39c5e34c145ed957724fcd985e1791a9d3f87d9795f`;
  Claude's revised capture is `9d328bbe41ad3ba27092cf08532a70007e38f5ec4aca4cb389d7c8ed6428e526`.
  They differ. Both contain a retrieval timestamp, so differing bytes alone do not demonstrate changed works.
  The original bytes were not restored, and record-by-record identity between captures is not asserted.
- Ran the revised profiler with `OUT` redirected to ignored `reviewer-source-profile.json`, preserving Claude's
  committed profile. **All four structural sections match exactly:** Crossref counts, gate measures, ROR profile
  and heuristic probe, including its retained examples. Verified the new capture against its ledger hash and
  summed page counts. Both scripts pass Ruff.

The new ledger and reviewer profile, with comparison results and artifact fingerprints, are retained in
[`review-verification.json`](review-verification.json). Raw data remains outside Git. A redundant alternate ROR
download timed out; it was not used as evidence. The script's original ROR download succeeded.

### Status of the six review findings

1. Raw and normalized string units are distinguished consistently: 9,561 versus 9,062.
2. Acronyms retain sets of organizations, e-mails/URLs are removed for the probe, and outcomes are expressly
   heuristic. Counts now reproduce as 13 whole-name matches, 4,499 single hits, 2,630 multiple hits and 2,419 no hits.
3. The report now describes suspected registry gaps and leaves confirmation to independent organization evidence.
   Reproducing the structural profile does not itself validate those organization-specific absence claims.
4. The pinned ROR artifact and Crossref request ledger support the new-capture procedure the user selected.
   Exact recovery of the earlier captures is not claimed or required by that decision.
5. Nonblank text and raw-string identifier measures now have explicit denominators, including mixed-ID occurrences.
6. Exact organization totals are restricted to a fully adjudicated bounded set; sampling is described as an estimate
   requiring a predeclared design and uncertainty, rather than proof of an unrestricted total.

Two small reproducibility improvements remain before treating the scripts as a one-command reusable workflow:
`fetch.py` does not download the two documentation files required by `profile.py` (I fetched them separately),
and `profile.py` summarizes ledger claims without enforcing their hash/count agreement (I verified that separately).
Document/fetch those prerequisites and add those consistency checks before reusing this as a validation gate.
They do not invalidate this checked capture or establish a need to reject the domain.

**Next:** the user decides the bounded record set, named business reviewer, geography and parent/child counting
rules, independent reference plan, non-accuracy checks and implementation budget. No domain or implementation
has been started by this review.
