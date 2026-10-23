# App proposal: research affiliations

Step "Show" of the method (`show-in-app`). Status: **approved by the user on 2026-10-23**, as written: «Apruebo la propuesta de la app
tal como está (tres preguntas, calidad, sin módulos opcionales, demo de tres momentos).» The three approved competency questions, all validated on technical invariants (`query-checks.yaml`,
`structural-checks.json`). No accuracy number exists yet: the blind reference review is deferred to the end
(user decision, 2026-10-23), so the app shows no evaluation cards and says the answers are not yet checked against
a reference.

| Question in plain words (es) | Main column for "why this number" | What Rastro adds | Glossary terms | Evidence (question and query) | Open question |
|---|---|---|---|---|---|
| ¿Qué organizaciones argentinas nombra cada afiliación de las 100 publicaciones? | Organización: the identification with its rule and evidence text | Joins the affiliation text (Crossref) with the ROR registry, with the rule and evidence of each identification; says when none was found | afiliación, organización argentina, identificación, regla, evidencia | cq1, `cq1.rq` (1,675 rows, every one of the 1,456 affiliations) | — |
| ¿En cuántas publicaciones aparece cada organización argentina? | Publicaciones: the affiliations of that organization, with their evidence | Counts each publication once per organization, only with accepted identifications, never adding to parent organizations | publicación, organización madre (no suma), identificación aceptada | cq2, `cq2.rq` (69 organizations) | — |
| ¿Qué organizaciones argentinas podrían faltar en ROR, o aparecer con otro nombre? | Candidato: the text and why it is a candidate | Finds segments that no Argentine ROR name covers, as candidates for a person, not conclusions | candidato, búsqueda heurística, hueco posible | cq3, `cq3.rq` (125 candidates) | — |

**What can be trusted (business view):**
- the quality rules, from `layer/afiliaciones/calidad.json`: 0 violations, the IDEHU warning (withdrawn in ROR v2.15),
  91 decisions by an AI assistant waiting for a person;
- a plain notice that no answer has been compared yet with an independent reference.

No cards with measured numbers, no change test yet (it comes later), no «fuera» test.

**Technical view:** SPARQL, generated SQL and explanation for each answer; console over `:8083` with cq1–cq3; example
records (one publication, one affiliation, one organization, one identification, one doubtful candidate); the
dictionary; the link tables (identifications, doubtful candidates, possible gaps) with their mapping blocks; the
quality rules with a real record and a broken example.

**Optional modules:** none.
- Questions over texts: no. The affiliation texts are short and the questions are answered by links, not by reading.
- Check a claim: no claims prepared.
- Enrichment: no outside source beyond ROR, which is already a source.
- Map: no geometries are loaded (ROR coordinates are not in the approved scope).
- Predictions: no model.

**Guided demo:** three moments: an affiliation that names CONICET and a university (cq1 evidence), CONICET's count
without parent credit (cq2), Instituto Sabato as a candidate (cq3).
