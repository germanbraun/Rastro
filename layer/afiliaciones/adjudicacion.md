# Adjudication: research affiliations

Date: 2026-10-26. **References reviewed by AI; a person still has to confirm them.** The reference is GPT's blind
annotation (`docs/experiments/research-affiliations/blind-review/`, three fresh reviewers on disjoint thirds of the
962 strings, source files only; annotation SHA-256 `1bc6a056…f1a2`). This adjudication was written by Claude, which
built Rastro: it is not independent either.

## Score

From `resultados.json` (`evaluar.py afiliaciones puntaje`), against `eval/referencias.json`:

| | Without Rastro (B) | SQL with Rastro's links (D) | With Rastro (C) |
|---|---|---|---|
| Correct (of 5) | 3 | 4 | 4 |
| Same answer in 4 wordings (of 2) | 1 | 2 | 2 |

- **e1** (CONICET, 63 publications), **e2** (organizations of one publication) and **e4** (UBA, 22 publications):
  all three paths are correct. B's e2 has 3 of 4 organizations (F1 0.86, above the 0.8 threshold).
- **e3** (distinct Argentine organizations): reference 70; C and D 69 (within 5 %), B 62 (wrong).
- **e5** (Argentina-text affiliations that name no Argentine organization): reference 38; C and D 42, B 49. All
  wrong.

## Where the reference and Rastro differ

30 of the 1,456 mentions have a different set of organizations. Grouped by cause:

| Cause | Strings (mentions) | Who is right | Effect |
|---|---|---|---|
| A footnote letter glued to the name («AUniversidad de Buenos Aires», «EConsejo Nacional…», one publication) | s055, s096, s412 (5) | The reviewer: the full name is there. Rastro's matching needs a word boundary. | e5: Rastro +5 |
| The acronym «CCT»: ROR lists it only for the Bahía Blanca centre, but the texts name the La Plata, San Juan, Mendoza or Tandil centres | s147, s157, s181, s544, s569, s634, s641 (12) | The reviewer, by meaning. Rastro's rule (unique acronym in ROR plus a second piece of evidence) is satisfied literally, so this is a gap in the rule: the city should agree. | e3: Rastro counts Bahía Blanca, misses 3 other centres |
| «CONICET Bahía Blanca» matched across a parenthesis and a comma («(UNS-CONICET), Bahía Blanca») | s734 (3) | The reviewer: the text does not name the centre. Normalization joined two segments. | e3 |
| «CIC», shared by two Argentine organizations | s147, s172, s638 (6) | The reviewer under the rule (a shared acronym does not name). Rastro's choice for s638 comes from a correction reviewed by AI, still pending a person. | e3 |
| «Instituto de Ciencias» inside «Instituto de Ciencias de la Tierra y Ambientales de La Pampa» | s579 (1) | The reviewer: it is part of a longer name. | e3: Rastro +1 |
| «Hospital Italiano» inside the name of its university | s764, s902 (5) | Debatable: the text contains the hospital's name literally (Rastro), but names the university (reviewer). | e5 |

**Sensitivity.** With the literal reading of «Hospital Italiano», e5's reference is 37; giving Rastro every case the
reviewer marked ambiguous makes e3 71. Under both, C and D stay correct on e3 and wrong on e5, and B wrong on both:
the score does not depend on these readings.

## What it says about Rastro

- The blind reference agrees with Rastro on 1,426 of 1,456 mentions, and on the three list or count questions that
  matter most for the demo (e1, e2, e4).
- It found five real linking defects that the method's checks did not: glued footnote letters, a generic acronym
  without its city, matching across segment boundaries, a short name inside a longer one, and a shared acronym. All
  are in the normalization or the rule, so each is fixed in one place, then e3 and e5 are re-measured (only where
  they apply, and said so). They are not fixed in this commit: the experiment's measurement stays as it was taken.
- D equals C on every question: with Rastro's link tables, plain SQL is as good. What Rastro adds here is building and
  keeping those links once, with their evidence, not a better query language.

## Re-measurement after fixing the five defects (2026-10-26)

The user asked to fix the five defects in one place and re-measure e3 and e5. The fixes are in
`linking/afiliaciones/link.py` (footnote letter, segment boundaries, a name that continues into a longer one, the
generic acronym «CCT» only with the centre's own ROR acronym) and in `correcciones.csv` (the six «CIC» acceptances
become rejections under the approved definition; 13 new candidates rejected; all AI-reviewed, pending a person).

- **Agreement with the blind reference:** 30 → 5 mentions differ. The 5 left are «Hospital Italiano» inside the
  name of its university, the debatable reading above.
- **Score, re-running the same saved queries** (no new model answers): with Rastro and SQL with Rastro's links
  4/5 → **5/5** (e3 69 → 70; e5 42 → 37, within 5 % of 38); without Rastro 3/5, unchanged, because raw SQL does not
  use the links. Only e3 and e5 of C and D changed; e1, e2, e4 and consistency are as before.
- **Read it as optimistic.** The defects were found by comparing with this same reference, so the fixes fit it by
  construction. The first measurement (4/5, 4/5, 3/5) is the one taken blind. A fair test of the fixes needs
  affiliations the fixes were not tuned on.
- The first version of the fixes lost two correct identifications («… de Buenos Aires», «… de la Provincia de …») and
  the second matched an address («UNR-CONICET Rosario»); both were caught by comparing the links before and after,
  and corrected before measuring.

## Re-test on unseen affiliations (2026-10-27)

The fair test the re-measurement asked for: 100 more works from the same capture, linked with the rules before and
after the fixes, against a new blind annotation (three fresh Claude reviewers, AI-reviewed, pending a person). Details
in `docs/experiments/research-affiliations/holdout/README.md`.

- Mentions that agree with the reference: 854 → **866 of 886** (96.4 % → 97.7 %); precision 0.961 → 0.985, recall
  0.979 → 0.977. The fixes generalize.
- Two defects remain on new data: a footnote digit glued to a name (6 strings) and a short name inside a longer one
  not followed by «de/del/of» (2). Not fixed: the holdout stays as measured.
- It scores links, not the five questions, so the 5/5 above stays optimistic until a person confirms the references.

## Limits

- The reference is AI work. The three reviewers took about three minutes each for ~320 strings; their receipt says
  they read every string, but speed like that calls for a person's spot check before any number is published.
- The coordinating GPT session had seen Rastro's implementation; it assembled the rows without changing judgments.
- 8 strings are marked ambiguous and 25 keep `other_references` (clear forms that ROR lacks); they are counted only
  under the rule, as the questions define.
- No accuracy number is published until a person confirms the references (`python layer/method.py publication
  afiliaciones` stays pending).
