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
