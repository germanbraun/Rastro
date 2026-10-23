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

## Identification mapping, queries and quality proposal — review of `386d825`

**Assessment: the link mapping and Q1/Q2 logic are coherent, and reported query results reproduce offline.
Before measurement, strengthen structural checks and Q3's evidence/wording. The quality proposal is sensible
with the clarifications below; its business disposition still belongs to the user.**

### Checks and prior findings

Replayed the current linker on the verified source sample and ROR release: 532 rule identifications, 91 doubtful
candidates, 539 accepted identifications after corrections, and 83 candidate segments. Executed the actual three
SPARQL files against a local RDF projection of those source/link rows, preserving names and source occurrences.
The projection was built independently for query review; it does not execute R2RML SQL or replace a live Ontop check.

| Query | Reproduced result |
|---|---|
| CQ1 | 1,675 rows; 1,456 distinct DOI/author-position/affiliation-position keys, covering every source mention |
| CQ2 | 69 organization rows; maximum 63 distinct publications; no parent traversal |
| CQ3 | 125 candidate rows from the two declared branches |

Registry, all-domain ontology/query checks and linker Ruff pass. CQ2 now has a revised requirement, hash-bound
approval reusing the recorded user decision, and preserved lifecycle history. The status command reports validated.
This fixes the previous business-contract mismatch; I did not rerun its live HTTP validation receipt.

The three new mapping classes stay separate. Shared `ofMention` and `sourceText` have no domain, and identification
provenance includes both sources and a rule activity. The `identifies` range implies ArgentineOrganization, so
checking that inferred class would be circular; checking the pinned source country is the right direction.

### Responses to Claude's review questions

1. **CQ1 wording is appropriately cautious.** “No Argentine organization identified” does not claim none is named.
   The Argentina-text disposition is descriptive, not a geography judgment. Include unresolved doubtful candidates
   if they remain undecided later, without turning them into identifications. The 91 current decisions are already
   accepted/rejected; absence of an accepted link does not by itself establish an ambiguous organization.
2. **CQ3 should not blindly include all doubtful candidates.** Rejected UK/homonym matches are not registry gaps.
   Surface genuinely unresolved naming candidates or variants with their reasons, without relabeling every rejected
   match. The current segment heuristic is a useful candidate generator, not an exhaustive answer: context filtering,
   institutional-word prefixes and substring suppression can miss real gaps or name variants. Measure that limitation
   against the blind reference rather than claiming complete coverage.
3. **CQ3 needs evidence in its returned table.** Its approved answer includes evidence, but the SELECT exposes only
   text and `kind`; the mapped gap `sourceText` is not returned. Include the candidate reason/evidence and distinguish
   a heuristic miss from a reviewed gap. Replace “sin nombre en ROR” with wording such as “sin coincidencia en la
   búsqueda heurística”; the current labels imply absence more strongly than the underlying search establishes.
4. **The current assertions are smoke checks, not full coverage checks or accuracy.** `min_rows: 1456` allows an
   output that repeats some mentions while omitting others. Add a structural coverage check comparing the exact
   source-key set to CQ1's projected key set, and check the distinct DOI/organization count is within 1–100 per CQ2
   row. Independently derive those invariants from the pinned selected records. Keep their receipts with the
   experiment evidence; do not hard-code 1,675/69/125 just because this implementation returns them. CQ3's
   `min_rows: 1` is only justified by independently establishing a candidate in this selected set, not by a suspected
   gap somewhere in the larger inspection cohort. None of these checks substitutes for independent answer references.
5. **Technical lifecycle validation can remain distinct from accuracy publication**, as the contracts allow, but
   explicitly state which invariants were tested. The current validated state does not prove all mentions appear,
   that Q3 finds every exception, or that any proposed identification is correct. Query edits invalidate those
   receipts and require revalidation. Do not promote the smoke checks into claims of those stronger properties.

### Quality proposal

The six rule categories fit the domain. Active-status findings should remain visible with affected answers and
a reviewed disposition; **do not automatically redirect IDEHU to CONICET**. A withdrawn ROR record can still be
explicitly named by a publication, and a later registry status does not prove the 2025 affiliation is wrong. Call
this a registry-status review finding, not an impossible source value. Preserve the pinned release date and supply
successor context from actual ROR records. The current ontology maps parents, not successors; any extra successor
data needed for quality evidence must be deliberately exposed and checked.

For identification completeness, require the two declared source references (Crossref and ROR), the rule/activity
and nonblank evidence, rather than accepting any single arbitrary source. For doubtful decisions, distinguish an
AI accept/reject from human confirmation; a populated decision field does not prove independent review. Existing
good/bad-example tests and real target coverage still apply. An inactive-status finding is not a reason to weaken
thresholds or suppress an answer silently.

### Text normalization and review evidence

HTML entity decoding and separating non-ASCII punctuation address the observed bugs. Add focused good/bad examples
for contacts, accented names, entity-encoded text, HTML line breaks/tags and multiword acronyms when those forms
occur. HTML tags are not currently stripped, while only single-token acronym matches are recognized. Preserve raw
text; treat these as normalization/candidate-generation limitations rather than silently broadening approved rules.
Changes that alter links require rerunning the affected saved queries and refreshing their evidence.

One traceability improvement remains: DoubtfulCandidate maps the candidate reason and decision but omits the
reviewed `decision_reason` (where rejection rationale and source URLs live). Expose that rationale as appropriate
so a technical-view reader can understand why a candidate was rejected, not just why it was initially generated.

No live database, Ontop or production quality run was performed in this review. No implementation or skill files
were changed. The independent reference reviewer and publication evidence remain pending.

## Quality rules and structural-check update — review of `6f3e970`

**Assessment: the structural-check and Q3 changes address the earlier review. Quality examples pass, but severity
and confirmation semantics need corrections before the quality result is described as satisfying the proposal.**

### What was checked

- Read the structural checker and its receipt. All three receipt query hashes match current files; eight checks
  are recorded as passed. Exact source mention-key/text comparison is now present, Q2 has distinct-organization
  and 1–100 count bounds, and Q3 checks source membership/evidence. These are technical invariants, not accuracy.
  The live endpoint was not rerun in this review.
- Q3 now returns evidence and labels heuristic candidates cautiously. Rejected candidates are not called gaps.
  The exact Sabato presence check is a specific regression case, not proof of complete Q3 exception discovery.
- New terms expose decision rationale, human-confirmation text and successor relations; dictionary/mapping changes
  are recorded as user-approved. Registry and changed-script lint pass.
- Ran `tests/test_calidad.py`: **3 tests pass**, including all seven good/bad pairs for afiliaciones. Then ran
  additional direct pySHACL checks against the actual isolated shapes, with inference disabled. These expose the
  findings below despite those example pairs passing.

### 1. Severity: fix the rule and retain it in the result

`RegistroActivo` places `sh:severity sh:Warning` on the `sh:sparql` constraint node. Direct validation of a withdrawn
record produces **sh:Violation**, not Warning. Put the severity on the owning NodeShape (or an appropriate property
shape); extend the example check to assert the report's `sh:resultSeverity`, not only pass/fail.

The shared runner separately discards result severity: it counts every finding as `fallas` and sets the aggregate
status to `defects_detected`. `ConfirmadaPorPersona` actually produces sh:Info correctly, but that distinction is
lost in the saved result. A process note alone is insufficient if the report is presented as distinguishing source
defects, registry warnings and pending human review. Preserve severity beside each finding/rule, and summarize
violations, warnings and informational findings separately. This is a deliberate shared-runner method change if
implemented there; record it in the frozen experiment's method-change log. Do not silently rewrite historical
results or lower thresholds to make the result green. After the severity fix, the intended current outcome is
zero violation findings, one registry warning and 91 pending-confirmation informational findings, subject to rerun.

### 2. Human confirmation needs a real record

The current `sh:not [ sh:in ("pending") ]` passes for **empty text**, `"no"`, `"banana"` and `"confirmed"`.
I executed those cases; only `"pending"` failed. The rule therefore checks a string inequality, not whether a
person confirmed anything. Keep all current pending decisions pending. Before accepting a confirmed state,
require an explicit confirmation disposition with reviewer identity, date and evidence/reference to the real
approval, tied to the reviewed decision. Existing evidence may be reused; no invented reviewer or timestamp.

A minimal constrained confirmation record is preferable to interpreting arbitrary free text as proof. If adding
fields/terms changes the approved dictionary, present that narrowly scoped refinement under the existing method.
The current rule can honestly be labeled a pending-marker check in the meantime, not confirmation validation.

### 3. Registry status, successor naming and geography

- Keep IDEHU visible and do not redirect it. The `HAVING(COUNT(?s)>0)` guard avoids an empty aggregate result, but
  a **missing status passes** the current rule (executed). Add status completeness/allowed-value checks, or state
  explicitly that this rule checks only supplied non-active statuses. Missing status must not be described as active.
- `MIN` over ROR aliases is deterministic and acceptable for a display string. It is not ROR's designated display
  name. Prefer the actual display name when useful, or label it simply as a name and retain the successor ROR ID in
  the evidence so the target is unambiguous. Do not infer publication-time succession from a later ROR snapshot.
- `OrganizacionEnArgentina` avoids the inference circularity: an organization with type ArgentineOrganization and
  only `country "GB"` **fails** the isolated rule. An actual mapped AR country value is required. This confirms the
  rule's mechanics, not independent truth of all source locations.

### Other limits before moving to evaluation

Identification completeness requires both sources, as requested. Its rule/evidence constraints should reject blank
or whitespace-only values too; `minCount` and `minLength 1` alone do not establish meaningful evidence or a valid
rule activity. Good/bad fixtures should exercise those concrete constraints, not merely a missing source.

The two new terms about decisions expose AI rationale and pending status; they do not transform GPT's technical
correction review into the blind human reference. Evaluation/publication remains dependent on that reference and
reviewed dispositions. Preserve the structural receipts in the experiment's actual verification workflow rather
than assuming the ordinary row-bound gate reruns them automatically.

Metadata follow-up: several new approval/result entries are dated 2026-10-23 while this chat's client date is
2026-10-22. Reconcile the source timestamps/timezone in the log; do not invent or silently rewrite historical
approval dates. This is separate from the executable findings above. No source/rule/implementation files were
modified during this review.
