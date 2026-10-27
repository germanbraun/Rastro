# Holdout: the linking fixes on affiliations they were not tuned on

Date: 2026-10-27. **Reference reviewed by AI; a person still has to confirm it.** The five linking fixes
(2026-10-26) were found by comparing with the first blind reference, so their re-measured score was optimistic. This
tests them on new data.

## How

1. `draw.py`: 100 more works from the same approved Crossref capture, none of the original 100 (seed 20261027, fixed
   before drawing): 886 mentions, 556 distinct strings, 227 with «argentin». Only 2 strings were also in the original
   sample.
2. `link.py`: the linker's rules run on them in a temporary table, so Rastro's data is untouched. Two versions: the
   current `linking/afiliaciones/link.py` (`links-after.csv`) and the one before the fixes, `git show
   db6c95b^:linking/afiliaciones/link.py` (`links-before.csv`). Rules alone: there are no reviewed corrections for
   these mentions, so doubtful candidates are counted as not linked.
3. Blind annotation (`annotations.csv`): three fresh Claude reviewers, one third each, saw only `instructions.md`,
   the strings and the ROR list (`../blind-review/ror-argentina.csv`), in a folder apart from the repository; each
   said it opened nothing else. Same rule as the first review, with the readings the first adjudication settled
   (glued footnote letter, a name inside a longer one).
4. `compare.py` → `resultados.json` and `differences.json`.

## Result

| Rules | Mentions that agree (of 886) | Precision | Recall |
|---|---|---|---|
| Before the fixes | 854 (96.4 %) | 0.961 | 0.979 |
| After the fixes | 866 (97.7 %) | 0.985 | 0.977 |

The fixes generalize: fewer wrong links (21 → 8) for one more missed. On the 554 strings not seen before the numbers
are the same.

## The 15 strings that still differ (after)

| Cause | Strings | Who is right |
|---|---|---|
| A footnote **digit** glued to the name («11Hospital Privado…», «3CEMIC») | h003, h007, h037, h038, h048, h050 | The reviewer: a new case of the first defect; the fix handles only a letter. |
| A short ROR name inside a longer one when the next word is not «de/del/of» («Instituto de Ciencias Físicas») | h355, h356 | The reviewer: the fix is too narrow. |
| A unique acronym with another meaning here («IAA-FADU», a UBA institute, not the Instituto Antártico) | h081 | Debatable, like «CCT»: Rastro's rule holds literally. |
| No second evidence («National University of Cuyo», without «Argentina» or the city) | h159 | Rastro under its rule (it stays a candidate); the reviewers' rule does not ask for it. |
| Reviewer errors: «UNC» is shared by two Argentine organizations; «Universidad Nacional de San Luis (UNSL)» names it | h358, h555, h556 | Rastro. |
| A typo in the source («Hospital de ClínicasJosé…») | h146 | The reviewer, by reading. |
| A current name ROR lacks («Universidad del CEMA») | h533 | Debatable; marked ambiguous. |

The two real defects (glued digit, longer name) are not fixed here: a fix would be tuned on this holdout, and testing
it fairly needs another unseen set. 17 strings are marked ambiguous.

## Limits

- The reviewers are Claude, the same family as the assistant that built Rastro, though they saw nothing of it. Three
  of their calls were wrong (h358, h555, h556); a person's spot check is still due.
- This scores links, not the five evaluation questions: their references and saved answers are for the original
  sample.
