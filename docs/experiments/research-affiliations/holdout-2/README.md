# Second holdout: the two fixes found on the first holdout

Date: 2026-10-28. **Reference reviewed by AI; a person still has to confirm it.** The first holdout (`../holdout/`)
found two linking defects: a footnote **number** glued to a name («11Hospital…», «3CEMIC»), and a short ROR name
inside a longer one when the next word is not «de/del/of» («Instituto de Ciencias» in «Instituto de Ciencias
Físicas»). Fixes tuned on that holdout are scored on it optimistically, so this tests them on new data.

## How

1. The two fixes were written first, in `linking/afiliaciones/link.py`.
2. `draw.py`: 100 more works from the same approved Crossref capture, none of the original sample or of the first
   holdout (seed 20261028, fixed before drawing): 993 mentions, 583 distinct strings, 226 with «argentin». 15
   strings were also in an earlier sample; the fair number is on the other 568.
3. Blind annotation (`annotations.csv`): three fresh Claude reviewers, one third each, saw only `instructions.md`
   (the first holdout's, plus «a footnote letter or number»), their strings and the ROR list, in a folder apart from
   the repository. Each said it opened nothing else; one re-read its own saved tool output and first saved a helper
   script one folder up, neither of which shows it anything of Rastro.
4. `link.py` runs the rules on a temporary table (Rastro's data untouched): `links-before.csv` is the linker at
   `cabcdd4`, `links-after.csv` the one finally kept. `compare.py` → `resultados.json`, `differences.json`.

## Result

| Rules | Mentions that agree (of 993) | Precision | Recall |
|---|---|---|---|
| Before (cabcdd4) | 955 | 1.000 | 0.909 |
| Both fixes | 942 | 1.000 | 0.886 |
| **Only the footnote number (kept)** | **955** | **1.000** | **0.909** |

- **The longer-name rule did not generalize:** on the new strings it fixed nothing and broke 11. A big
  organization's name followed by a local place not on the list of provinces («Instituto Nacional de Tecnología
  Agropecuaria Arroyo Seco», «… Famaillá») looked like a longer name, so correct links became candidates. **It was
  dropped.** This holdout is now consumed for that rule: a new version needs another unseen set.
- **The footnote number generalizes as far as this set can say:** no change here (no string needed it), and no
  harm; on the first holdout it adds 6 correct links (866 → 872 of 886 mentions agree, recall 0.977 → 0.989),
  an optimistic number since it was found there.

## What still differs (after), by cause

The 38 mentions that differ are missed links, never wrong ones. The main causes: an English name ROR lacks
(«National University of Comahue», «National University of the Littoral»), an acronym only inside a longer acronym
(«IIBBA‐CONICET», «IDES-CONICET»), a name without a second evidence («Instituto Universitario CEMIC»), and the
same organization under a longer name than ROR's («Hospital Privado Universitario de Córdoba», left as a candidate
for review, which is the safe side). The full list is in `differences.json`; 8 strings are marked ambiguous.

## Limits

- The reviewers are Claude, the same family as the assistant that built Rastro, though they saw nothing of it; a
  person's spot check is still due.
- This scores links, not the evaluation questions.
