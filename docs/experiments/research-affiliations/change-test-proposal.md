# Change test proposal: research affiliations

Step 8 of the method (`change-tests`). Status: **approved by the user on 2026-10-23**, as written, with option (b) for the guard. **Result** at the end.
The approved scope predeclared the scenario: after the first measurement, one missing alias is added once, as a
controlled source change applied equally to B, D and C. It also fixed a traceability check on 30 answer cells. The
exact alias was not chosen then, so it is chosen here, before running.

## The correction

**Add the alias «Hospital de Pediatría Prof. Dr. Juan P. Garrahan» to ROR's record of the Garrahan hospital
(`https://ror.org/051mda743`).** This is the hospital's official name. ROR v2.15 records only «Garrahan Hospital» and
«Hospital de pediatria Garrahan», so the official name in the text matches neither. The change simulates ROR's next
release adding the alias: one row is inserted in `ror.name`, the same source every approach reads.

- **Affected records,** computed from the source texts (normalized text contains the normalized alias), not from
  Rastro: two affiliations of `10.1002/epd2.70126` (authors 4 and 5, affiliation 0). Both mention Argentina, and
  today neither has an identification.
- **Rastro's rule that would apply:** R1 (a full ROR name of 12 characters or more plus «Argentina»). Garrahan has no
  identification and no doubtful candidate today.

| What is corrected | Expected to change | By how much | Evidence | How sure | How it is undone |
|---|---|---|---|---|---|
| ROR alias for Garrahan | cq1: the two affiliations show Garrahan, with rule R1 and evidence | 2 rows change from «sin organización» to identified; rows stay 1,675 | the normalized text contains the alias; R1 | sure | delete the inserted `ror.name` row, rerun the linker, restart Ontop |
| | cq2: Garrahan appears with 1 publication | 69 → 70 organizations | 2 affiliations in one publication | sure | same |
| | cq3: the two affiliations leave «menciona Argentina sin organización identificada» | 125 → 123 rows | same | sure | same |
| | e3 (distinct Argentine organizations) | +1 for D and C | as cq2 | sure | same |
| | e5 (Argentina-text affiliations with no organization) | −2 for D and C | as cq3 | sure | same |
| | e1, e2, e4 | no change | Garrahan is not CONICET or UBA, and not in the e2 publication | sure | same |
| | B's saved queries | depends on each query's own matching: they read `ror.name` live, so they may pick it up with no edit | measured, not assumed | unsure | same |

**What is measured for each approach:** the places edited (saved queries, mapping, linker, corrections), the steps run
(linker, Ontop restart) and their minutes, and whether every affected answer changed as expected. Every saved query
is rerun before and after. The expectation for D and C is zero edited queries: the linker rerun and an Ontop restart
are the only steps.

**Undo and checks:** before the change, snapshot the `ror.name` row count and checksum, the `afiliaciones` tables
(checksums), `linking/afiliaciones/correcciones.csv`, and the saved answers (`layer/afiliaciones/respuestas/`, bytes).
After the undo, all of them must match the snapshot exactly. The result goes to `layer/afiliaciones/cambio/correccion.json`.

## Traceability check (30 cells)

- **Selection, fixed now:** 30 identified (affiliation, organization) cells of cq1, drawn with
  `random.Random(20261022).sample` over the cells sorted by DOI, author, affiliation position and ROR identifier.
- **Rubric per cell and approach:** traceable if what that approach returns, or keeps as evidence, gives three things:
  1. the Crossref record (DOI and positions);
  2. the ROR record;
  3. the rule that joined them.
- **How each approach is read:** C from the identification's PROV-O record (source, rule, evidence), D from the link
  tables, and B from what its saved queries return.
- **Result:** the share per approach, in `layer/afiliaciones/cambio/trazabilidad.json`.

## Open question for the user: the guard is oil-and-gas code

`layer/change_guard.py` snapshots and restores the change tests' files and tables, but its lists name only oil and gas
files and tables.

- **(a) A small afiliaciones script** with its own snapshot, restore and check.
- **(b) The guard reads the files and tables of each test from the domain's registry entry** (`method.change_tests`),
  with oil and gas keeping its current lists. It's a generic change, recorded as a method change, like the evaluation
  harness and the quality runner.

Recommendation: (b), for the same reason as before: the skills and their scripts are meant to be domain-generic.

## Result (2026-10-23)

Measured with `layer/afiliaciones/cambio/correccion.sh registrar` under the guard. The numbers come from
`layer/afiliaciones/cambio/correccion.json` and `trazabilidad.json`.

- **With Rastro (C) and SQL with links (D):** 11 of 11 saved runs each changed exactly as declared: e3 69 → 70,
  e5 42 → 40, e1, e2 and e4 unchanged. cq1 shows Garrahan in the two affiliations, cq2 has 70 organizations
  (Garrahan with 1 publication), cq3 has 123 rows. No query or mapping line was edited. The source change took 1 s;
  rerunning the linker and restarting Ontop took 15 s.
- **Without Rastro (B):** none of its saved answers changed (e3 stayed at 62, e5 at 49). Its queries compare ROR names
  with the text literally, punctuation included, so the alias «Prof. Dr. Juan P.» does not match the text «Prof Dr.
  Juan P». Reaching the corrected answer would need edits to each B query that matches names. That was not measured,
  since no B query was edited.
- **Restoration:** the corrections file, the saved answers and the five tables matched the starting fingerprints exactly.
- **Traceability (30 cells):** C 30, D 30, B 0. In B, 16 of the 30 values appear in some saved answer, but none comes
  with its Crossref record and rule.
- **Not counted as a result:** a first run measured D after the rebuild without the read-only grants (the linker
  recreates the schema). That was a defect in the test script, fixed and rerun, and the result above is the rerun.
