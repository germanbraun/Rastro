# Blind source reference review — GPT / Codex

Date: 2026-10-26. Status: **AI-reviewed reference annotation; human confirmation pending.**

## Scope and model identity

Three fresh Codex reviewers identified by the session as based on GPT-6 reviewed disjoint source-only partitions. An exact runtime model snapshot/version was not exposed and is not asserted. Reviewer task identifiers: `/root/blind_reference_a`, `/root/blind_reference_b`, `/root/blind_reference_c`. They received no parent conversation and no Rastro implementation context.

The annotation review spans 2026-10-26 20:16:05 UTC to 20:19:12 UTC (17:16:05–17:19:12 America/Argentina/Salta), using the reviewers’ recorded clock readings. Receipt assembly and commit occurred afterward. These overlapping intervals are not summed as person-hours.

## Coverage

- strings: 962
- screen: 766
- original_full: 196
- screen_yes: 4
- screen_no: 762
- fully_reviewed: 200
- ambiguous: 8

Partition assignment: reviewer A receives numeric IDs n with (n−1) mod 3 = 0, B with remainder 1, C with remainder 2. Each read all assigned source strings semantically, using source-name indexes only to assist identification. Exact ROR forms and clear but unlisted references remain distinct. Institutes do not automatically imply their parents. Ambiguous cases retain explicit notes.

## Blindness and assembly

The coordinating chat is **not blind**: it has reviewed affiliations implementation in previous turns and, while discovering the task, searched `docs/decisions.md`, `docs/plan.md`, `CLAUDE.md`, the shared discussion and `conclusions.md` for handoffs. It did not use its own domain judgments as annotations. Instead, three fresh reviewers independently opened only the permitted blind-review source folder and temporary files; each reports its exact access below. No implementation details, provisional answers, scores or source-specific hints were passed to them.

The coordinator read the permitted instructions, CSV headers, source metadata and `reference.py` to validate the output. It mechanically concatenated the three outputs in original source order without changing judgments. Four empty-organization notes needed the literal protocol marker «ninguna»; reviewer A corrected those notes without changing assignments. All three reviewers confirmed their outputs final before assembly.

No web search, database, Ontop query, Rastro linker output or evaluation answer was used by the source reviewers. This is a source-blind AI annotation, not a human approval or an independently certified accuracy score.

## Mechanical validation

- All 962 IDs occur exactly once, in source order, with the original review mode unchanged.
- All emitted organizations and other references are among the 538 supplied Argentine ROR organizations.
- Every emitted ID has evidence; every «quoted excerpt» is contained literally in its source string.
- Screening decisions, empty-organization notes and ambiguity flags satisfy `reference.py`’s `check()` function.
- The validation function was called without executing `main()`: no reference answers were derived, no saved answers were scored and no evaluation output was changed. Claude owns that next step after this annotation is committed.

## Fingerprints

| File | SHA-256 |
|---|---|
| `instructions.md` | `90a82e7fd7ee6074bf78e0663ea722540b6d70fea88894884db4e8ce4c22d671` |
| `strings.csv` | `50c470a190ea311e49d13c923751c761d90e3d03a777b245e667f8aff0804fc4` |
| `ror-argentina.csv` | `98233299b063a467673894d31e2f9517aa0c6227f884f9ac607dc386a1bd4960` |
| `mentions.csv` | `c79a894264d24796179a2a841103c5e34d4d0e226d312c40e42a2f1eeced256a` |
| `annotations.csv` | `7450b423e21b22bfdf4b3e034ff4e244ca69d346f8fcfc17394a6a9c4f8f1633` |

## Reviewer receipts

### Reviewer A

#### Blind source annotation receipt — reviewer A

- Model identity available: Codex, based on GPT-6 (session identity); no exact runtime model version is exposed, so none is invented.
- Actual UTC start: 2026-10-26 20:16:05 UTC (clock reading immediately after opening instructions.md first).
- Actual UTC end: 2026-10-26 20:19:03 UTC (clock reading after final CSV formatting validation).
- Assigned partition: numeric string_id n with (n-1)%3 = 0, preserving source order.
- Completed: 321 rows, comprising 255 screening decisions and 66 original full-review rows.
- Screening: 254 no, 1 yes (s883), 0 unsure. Full annotation completed for 67 rows including the screen=yes row.
- Ambiguous: 2 rows, s172 and s634.

## Methods

Read instructions.md first. Read every assigned string semantically in two displayed batches, then reviewed all 66 full rows and s883 against the supplied ROR names. Used Python's csv module and a source-only accent/case/punctuation-normalized candidate index to assist lookup; individually rejected foreign-country acronym collisions (UK, ICA, SEA, IL, and French CIC). Candidate lookup was assistance, not the screening decision. Examined relevant catalog names and relationships to distinguish exact recorded names/acronyms from missing forms and institutions absent from the supplied catalog. Counted only organizations explicitly named in the affiliation, without inheritance from institutes to parents. Leading A/E affiliation markers in s055/s412 do not obscure the literal complete organization names. Status withdrawn does not erase IDEHU's literal recorded acronym in s586.

Recorded literal source excerpts for every assigned ROR ID, including other_references. Validated literal excerpt containment, exact column order, 321 assigned rows, and that every organization/other-reference ID exists in the supplied catalog. All full rows with empty organizations explicitly say ninguna, including those with other_references. No web browsing was used.

## Ambiguity notes

- s172: CIC belongs to two catalog organizations (Comisión de Investigaciones Científicas and Centro de Investigaciones Cardiovasculares). LIDTUA is not in the catalog. Retained CONICET and Universidad Austral, marked ambiguous, and assigned neither CIC candidate.
- s634: Centro Científico Tecnológico (CCT) is generic, followed by a Mendoza postal location. The literal acronym CCT on the Bahía Blanca catalog record must not force that assignment. Counted IMBECU, Universidad Nacional de Cuyo and CONICET; retained ambiguity for the unnamed CCT.
- s157: UNCPBA, CICPBA and CCT‐Tandil are clear referential forms missing from the corresponding ROR names, retained in other_references. CIFICEN itself is absent from the catalog.
- s538: INENCO is missing from ROR, which records INECO; catalog city Salta and its two stated parents corroborate the reference, retained as other_references rather than an exact-name match.
- s106, s415, s490, s517 and s886 also use clear forms absent from the target records, retained as other_references.
- Institutes and hospitals with no corresponding supplied catalog record are identified in notes where useful, without invented ROR IDs. In particular, CECOAL, CITeQ, CIFICEN, IEGEBA, INFIQC, INECOA, IPVet, InMiBo, IPADS and Instituto Sabato do not imply additional parents.
- s574: CONICET followed by Rosario as the postal city is not treated as an explicit reference to the CCT Rosario.

## Every file opened

Source files, all inside the permitted blind-review directory:

1. instructions.md
2. annotations.csv (columns/template only)
3. ror-argentina.csv
4. strings.csv

Temporary files created/read:

5. /tmp/rastro-review-a.py (annotation construction and literal-evidence validation)
6. /tmp/rastro-blind-reference-a.csv (review output, validated)
7. /tmp/rastro-blind-reference-a-receipt.md (this receipt, created)

Blindness statement: I opened no project files outside docs/experiments/research-affiliations/blind-review/, no git history, app, DB, Ontop, mappings, linking outputs, evaluation answers, or sibling experiment material. I used no web or external organizational sources. No repository file was modified or committed. This is an AI source review awaiting human confirmation.


### Reviewer B

#### Blind reference review B receipt

- Start UTC: 2026-10-26 20:16:12 UTC (clock tool immediately after instructions read).
- End UTC: 2026-10-26 20:18:00 UTC (clock tool after annotation output was written; receipt followed).
- Model identity available: Codex agent, identified by session instructions as based on GPT-6. Exact runtime model/version is not exposed; no version inferred.
- Assigned and completed: 321 rows, s002 through s962, numeric IDs satisfying (n-1)%3 = 1, in source order.
- Screened: 263 screen rows, each read semantically. 261 no, 2 yes (s173, s539), 0 unsure.
- Fully reviewed: 60 rows (58 source full rows and 2 positive screen rows).
- Ambiguous: 3 rows, s542, s638, s641.

## Methods

Read instructions first, then the exact CSV schemas and assigned strings. Read every assigned text; source-only normalization of case, diacritics and punctuation plus a candidate index of all supplied ROR names assisted lookup, with candidates individually accepted or rejected. Foreign affiliations, generic partial-name hits, UK as a country marker, Ica as a city and foreign INM/ICB uses were rejected by reading their actual meaning. Final organization assignments and literal evidence were explicitly curated per row. ROR names not supplied were not invented. Parents were not inferred from institute affiliations. Embedded hospital names inside university names were interpreted as part of the named university, not separate hospital mentions. Literal evidence and validity of every assigned ROR ID were mechanically checked; assignment, uniqueness, counts and output schema were checked.

## Ambiguity notes

- s542: CONICET La Plata could name CCT La Plata or give the city for a UNLP-CONICET affiliation. CCT ID withheld; explicit UNLP, CONICET and INIBIOLP retained.
- s638: CIC is shared by the Commission and a cardiovascular center. The full wording Centro de Investigaciones Científicas differs from ROR Comisión de Investigaciones Científicas. Commission retained only as other_reference and uncertainty preserved.
- s641: CCT occurs with Mendoza, while the only supplied ROR using the acronym CCT is Bahía Blanca. No CCT ID guessed; IMBECU and CONICET retained.

Other source-only limitations are in row notes: institute acronyms absent from supplied ROR, truncated Consejo Nacio, missing forms for the Garrahan/El Cruce/Fleming hospitals, INENCO, UNS, UNNE translation, Universidad Nacional de Buenos Aires, university Hospital Italiano and J. A. Maza. s560 IMIT is not in the supplied ROR names, so screened no with an explicit absence note.

## Files opened

Repository files (all within authorized blind-review folder):
- docs/experiments/research-affiliations/blind-review/instructions.md
- docs/experiments/research-affiliations/blind-review/strings.csv
- docs/experiments/research-affiliations/blind-review/ror-argentina.csv
- docs/experiments/research-affiliations/blind-review/annotations.csv (schema and initial empty template rows only)

Temporary working/output files opened or created:
- /tmp/rastro-b-rows.txt
- /tmp/rastro-b-rows.json
- /tmp/rastro-b-review.py
- /tmp/rastro-b-annotate.py
- /tmp/rastro-blind-reference-b.csv
- /tmp/rastro-blind-reference-b-receipt.md

Blindness statement: no project files outside the authorized blind-review folder, git history, application, mappings, linking, evaluation answers, DB or Ontop were opened or consulted. No web access was used. No repository files were modified or committed. Candidate lookup and judgments used only the supplied source strings and Argentine ROR CSV. This is an AI review requiring human confirmation.


### Reviewer C

#### Blind source review C receipt

Model identity available: Codex, an agent based on GPT-6, as identified by the session instructions. No exact model build/version was exposed; none is invented here.

Actual UTC start: 2026-10-26 20:16:19 UTC (clock tool immediately after reading instructions.md first).
Actual UTC end: 2026-10-26 20:19:12 UTC.

Assignment: numeric string_id n with (n-1)%3 == 2. Completed all 320 assigned rows, in source order. Screened 248 rows by individually reading their complete affiliation text; 247 no and 1 yes (s534). Fully reviewed 73 rows: 72 full-designated strings and the screen-positive s534. Marked 3 ambiguous rows: s147, s156, s597. Seven rows have other_references. This is an AI review requiring human confirmation.

Method: read instructions.md first; read every assigned source string semantically in displayed batches, re-reading the middle batch after initial display truncation. Inspected the supplied ROR name catalog and used a local accent/case/punctuation-normalized candidate index and targeted source-name searches as aids. Independently decided which organization each literal text actually names; rejected acronym collisions with foreign organizations, country/state abbreviations, and generic prefixes of longer institute names. Did not infer parents. Manually specified all full decisions and literal evidence in a temporary Python script, then checked all emitted IDs against the source catalog and every evidence quotation against its original text. Validated row count, assignment, uniqueness, screen completion and no-organization notes.

Ambiguity notes:
- s147: CIC is shared by Comisión de Investigaciones Científicas and Centro de Investigaciones Cardiovasculares. Both withheld; the remaining directly named entities are retained. CCT context is La Plata, not Bahía Blanca.
- s156: CIFEVA resembles IFEVA but the text does not establish identity. Withheld the institute; retained explicitly named UBA and CONICET.
- s597: CAC could be Centro Atómico Constituyentes, but its expansion is absent and CAC is not a supplied ROR form. Withheld that candidate; retained CNEA and CONICET.
- Address strings in s207, s600 and s915 do not name the respective CCT merely because a CONICET token is followed by the city.
- s096 includes Universidad de Buenos Aires literally after an attached B marker; treated this as the named university and documented the source typography.
- Other references preserve unlisted English translations or shortened forms in s300, s450, s519, s552, s591, s672 and s924.

Every file opened:
- /Users/germanbraun/Documents/MyProjects/Rastro/docs/experiments/research-affiliations/blind-review/instructions.md (first)
- /Users/germanbraun/Documents/MyProjects/Rastro/docs/experiments/research-affiliations/blind-review/strings.csv
- /Users/germanbraun/Documents/MyProjects/Rastro/docs/experiments/research-affiliations/blind-review/ror-argentina.csv
- /Users/germanbraun/Documents/MyProjects/Rastro/docs/experiments/research-affiliations/blind-review/annotations.csv (column template only)
- /tmp/rastro-review-c.py (created and executed temporary review/validation script)
- /tmp/rastro-blind-reference-c.csv (created and read for validation)
- /tmp/rastro-blind-reference-c-receipt.md (this newly created receipt)

Blindness statement: Used only the supplied blind-review folder and /tmp. No other project file, git history, linking/mapping implementation, evaluation answer, application file, database, Ontop endpoint or web source was opened. No repository file was modified or committed. Primary reviewer may mechanically assemble these rows without changing judgments.


