# Preliminary implementation review

Reviewer: Codex/GPT, 2026-10-22. Reviewed changes from `05428c5` through `84b3ed7`.

**Assessment: the initialization and approved-requirement scaffold are consistent with the agreed scope. No
blocking defect found at this stage. Claude can continue to source loading and the dictionary/mapping proposal.**
This is not runtime validation, reference approval or a completed transfer experiment.

## Verified

- Registry check passes. The ontology checker passes across all registered domains; the new ontology correctly
  has zero classes/properties and no competency queries yet. This establishes scaffold consistency only.
- All three approval artifacts bind the current proposals' SHA-256 values, and the lifecycle status command returns
  `approved` for each. The approval records cite the user's exact approval in the Claude session; software checks
  verify artifact bindings, not the human's identity or an independent review of answers.
- The registry declares lifecycle/source-manifest paths and omits capabilities not yet implemented. The isolated
  Ontop service has its own profile. The experiment log explicitly records that an empty mapping cannot start
  Ontop; no live runtime readiness is claimed. I did not start containers or repeat the reported startup failure.
- The sample has 100 distinct selected works. With the same algorithm and seed, I reproduced the committed DOI
  list using my separately fetched Crossref capture, without changing the authoritative capture or draw outputs.
  Its DOI-file SHA-256 is `e6dd13e0ff184d72b3d11903320c15f60e5d474dd444f4e97a5452f882c6b911`.
- More strongly, the selected raw records reproduce exactly: SHA-256
  `707ec8cc38e325d9edada4b4e375146208e86a527e28e06a5f12e77e2c402e76`, matching the inspector's sample.
  The reviewer copy stays ignored as `data/raw/research-affiliations/reviewer-sample-100.json`.
  This verifies the selected records, not identity of the two full captures.
- Reproduced 1,204 authors, 1,456 mentions, 962 distinct nonblank strings, 358 Argentina-text mentions and two
  mentions with ROR identifiers. The draw script passes Ruff. No redraw or exclusion was made for complexity.

## Reference workload and conditions for the next stage

The workload increase from an estimated 200 strings to 962 is material and correctly exposed. The shared discussion
records the user's revised reference plan: full review for 196 Argentina-text strings and screening of the other
766, with every positive proceeding to full review. This retains all strings rather than shrinking the cohort.

Screening must be an actual blind reviewer judgment, not a text filter or a heuristic link result. Uncertain cases
should proceed to full review rather than defaulting to no. Keep the screening dispositions traceable; a negative
is part of the reference. Exact Q2 totals still depend on complete, adequately evidenced reference coverage, not
merely on every row receiving some label. The independent reference reviewer remains pending and is needed before
validating references or publishing accuracy.

Before later implementation/validation receipts, the loader should refresh `sources.yaml` with the selected DOI
list and raw-record fingerprints, full ROR SHA-256, actual loaded versions and load evidence. The current
`loaded: false` manifest is honest for this stage; the final manifest must bind the selected records, not only the
larger capture's hash and file paths. Replacing a sample or source must invalidate downstream checks.

Continue with the existing method: approved questions drive the minimal terms, mappings and links. Keep candidate
and confirmed identifications distinct and retain unresolved mentions. Required reader users, app metadata,
quality, evaluation and change-test capabilities remain pending until built and checked. Do not infer completion
from this scaffold review. Freeze scoring/retry rules, correction scenario and traceability sampling before the
measurement; those details are not yet evidence of an executed check.

The experiment log's question-session text still says it was waiting for exact-proposal approval, while the current
state and intervention list say approval arrived. This is a historical session note, not a lifecycle failure;
clarify that chronology when next updating the log rather than implying approval is still pending.

## Source-loader update — review of `7f149fa`

**Assessment: the source transformation reproduces the reported counts; no current-sample count discrepancy
found.** This is an offline code/data review, not an independent verification of Claude's database execution.
The loader has not been run against this reviewer's database and no tables were truncated during the review.

Using the independently verified sample (matching the approved selected-record fingerprint) and ROR archive,
called the loader's row-building functions without opening a database connection. Results:

| Output | Reproduced rows |
|---|---:|
| Crossref works | 100 |
| Crossref affiliation occurrences | 1,456 |
| ROR organizations | 146,716 |
| ROR names | 349,589 |
| ROR relationships | 78,918 |

Registry and loader Ruff checks pass. Inputs are checked before entering the database transaction; source inserts,
truncation, COPY and load-run evidence use one connection transaction. Raw affiliation text and occurrence positions
are retained. ROR is loaded across countries/statuses rather than only the Argentine subset, supporting gap searches.
The committed source manifest now includes the loaded sample and ROR SHA-256 values. Process notes distinguish
proposed method improvements from changes actually made during the frozen experiment.

### Follow-ups before relying on the loaded layer

1. **Keep load evidence and source-manifest refresh connected.** `load.py` writes `rastro_meta.load_run` but never
   refreshes `layer/afiliaciones/sources.yaml`; the committed loaded date, hashes and counts were recorded separately.
   A manifest entry is therefore not proof that a future loader run succeeded or loaded those versions. Add an
   explicit post-success manifest-generation/check step, or have the loader emit a receipt used to refresh it.
   Include the DOI-list hash alongside the existing sample fingerprint. Bind source-version changes before later
   lifecycle validation; don't update the manifest on a failed/rolled-back load.
2. **Document or preserve multiple ROR locations.** `ror_rows()` selects only `locations[0]`. The pinned archive
   contains 142 organizations with multiple locations. I checked every Argentine-location record: all 538 also
   have Argentina in their first location, so this flattening loses no Argentine organizations in this release.
   Nevertheless it discards source locations and would not implement the approved any-Argentine-location meaning
   for arbitrary future releases. Preserve locations in a separate source table or derive country membership over
   the full list and state how the display location is chosen. Do not infer historical location from a current city.
3. **Use connection keyword parameters.** The loader interpolates database credentials into a libpq connection
   string. Pass `host`, `port`, `dbname`, `user` and `password` as `psycopg.connect` keyword arguments, following
   the repository convention. This also handles spaces/quotes in valid passwords without hand-built escaping.

The source text retains only the first publisher ROR identifier per mention. I checked this selected sample:
no affiliation occurrence carries multiple identifiers, so nothing is lost here. Preserve an explicit limitation
or support repeated identifiers if the source scope later changes. This is not a reason to alter the approved sample.

No generic method/skill changes were made in this review. Dictionary/mapping and link proposals remain the next
implementation stage; live Ontop, quality, query and app checks have not become valid merely because row counts agree.

## Dictionary and linker update — review of `55388d9`

**Assessment: loader follow-ups are addressed; all 91 correction decisions are supported as AI-reviewed decisions,
with human confirmation still pending. Fix the CQ2 contract inconsistency before implementing/validating that
question. Q1/Q3 must retain coverage beyond the linker's Argentina-only no-match helper.**

### What was independently checked

- The loader now preserves all locations in `ror.location`, uses connection keyword parameters and writes a
  manifest after the database transaction commits. These address the three previous follow-ups. I reviewed the
  code; I did not rerun the loader or independently verify its live database receipt.
- Replayed `link()` offline against rows reconstructed from the verified raw sample and ROR release. A small
  in-memory adapter supplied the four SELECT result sets; it did not simulate SQL execution or database writes.
  The result reproduces **532 rule identifications and 91 doubtful candidates**. Every doubtful candidate has
  exactly one correction in the CSV, with no missing or extra candidate keys. There are seven accepts and 84 rejects.
- Read all 91 correction cases (57 distinct raw strings, four distinct accepted strings). Row-level review is in
  [`corrections-review.csv`](corrections-review.csv). This is technical AI validation, not the blind reference:
  I have seen approach links and cannot act as the independent blind adjudicator for this set.
- Registry, ontology checker and Ruff for the loader/linker pass. The ontology now has five classes, three object
  properties and eight datatype properties. The source mapping preserves the approved any-AR-location definition
  and does not infer parent credit. Identification terms/mappings and competency queries are not yet present.
  I did not run live Ontop checks; the experiment log's healthy service/count evidence is Claude's reported result.

### Accepted corrections: external supporting evidence

These checks support acronym disambiguation, not independent reference approval or historical operational claims:

| Source case | Accepted target and occurrences | Supporting primary source |
|---|---|---|
| LIDTUA / Universidad Austral, `(CIC)` | Comisión de Investigaciones Científicas; two occurrences | [Universidad Austral](https://www.austral.edu.ar/laboratorios/lidtua/) explicitly identifies the provincial commission as LIDTUA's associated CIC. |
| CEQUINOR, `Asociado a CIC` | Same commission; two occurrences | [CEQUINOR](https://cequinor.conicet.gov.ar/personal-de-apoyo/) identifies its CIC association; the institutional context supports the provincial commission rather than the cardiovascular centre. |
| LIOMM, `Centro de Investigaciones Científicas (CIC)` | Same commission; two occurrences | [The commission's own LIOMM entry](https://www.cic.gba.gob.ar/centros/laboratorio-de-investigaciones-en-osteopatias-y-metabolismo-mineral-liomm/) states CIC–UNLP dependence. This supports the interpretation despite the deposited name saying Centro rather than Comisión. |
| `INENCO - UNSa` | Universidad Nacional de Salta; one occurrence | [INENCO's contact page](https://inenco.conicet.gov.ar/contacto/) expands UNSa and locates INENCO there. UNSa is explicitly named in the string; this does not grant automatic CONICET credit. |

The rejected cases are acronym/location or partial-name false candidates: UK, foreign city names and foreign
institutes do not identify their Argentine homonyms. Rejections of the cardiovascular CIC in the accepted provincial
commission cases are supported by the context above. Keep human-confirmation flags. Add these source URLs to the
relevant correction evidence so the rationale travels with the links rather than living only in this review.

### Items to resolve before query validation

1. **CQ2's meaning changed but its requirement artifact did not.** The user explicitly approved Rastro counting
   its own accepted identifications and the reference counting the blind reviewer's identifications. Yet
   `cq2.proposal.yaml` still defines confirmed as only identifications accepted by the reviewer. The discussion
   deliberately leaves that old fingerprint intact. The executable lifecycle cannot bind the new meaning from
   that side note. Update the requirement and its bound approval/history using the approval already recorded;
   do not request the same decision again or claim the old hash proves the revised definition.
2. **The no-match helper is not the Q1 universe.** `sin_identificar` contains only mentions whose text matches
   `argentin`, while the approved set includes every affiliation occurrence. Implement Q1 from all mentions with
   optional identifications and explicit dispositions, rather than omitting non-Argentina-text no-match strings.
   The approved linker helper can remain a useful subset if clearly labeled.
3. **Q3 must check partial gaps too.** A string can identify a known university and also name an institute absent
   from ROR or use an unrecorded name variant. Such a string is not in `sin_identificar` because some link exists.
   Use a candidate/exception procedure that can retain these cases; zero accepted links is not the definition
   of a suspected gap. Continue to distinguish heuristic absence from confirmed registry evidence.

The accepted rules are heuristics whose accuracy remains to be measured. Geographic text is not necessarily
independent of the matched name itself; do not interpret the label “second evidence” as independently verified
ground truth. This review does not approve all 532 rule-generated identifications. The seven AI-reviewed accepted
corrections can proceed in the proposed-answer layer under the user's approved rule policy, with independent human
references still required for evaluation/publication.
