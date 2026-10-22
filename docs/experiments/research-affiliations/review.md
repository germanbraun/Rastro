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
