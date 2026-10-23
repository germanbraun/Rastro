# Evaluation plan: research affiliations

Step 6 of the method (`evaluate`). Status: **proposed, for the user's approval before anything is measured**.
The blind reference review is deferred to the end (user decision, 2026-10-23). So this step prepares everything and
collects the three paths' answers now. Scoring happens only against the reviewer's reference, and no accuracy number is
published before then.

## Questions

Five questions with a single answer (a number or a list), built from the three approved competency questions. Each
one states its definitions, so that the three paths can answer it. Lists use full identifiers (ROR `https://ror.org/…`
or DOI), compared exactly with F1 ≥ 80 %. Numbers have a 5 % tolerance.

| Id | Question (es) | Kind | From | Reference now | Final reference |
|---|---|---|---|---|---|
| e1 | ¿En cuántas de las 100 publicaciones alguna afiliación nombra al CONICET (https://ror.org/03cqe8w59), contando cada publicación una vez y sin sumarle las de sus institutos? | número | cq2 | Rastro (SPARQL), to adjudicate | the reviewer's annotation |
| e2 | ¿Qué organizaciones argentinas (identificador ROR) nombran las afiliaciones de la publicación 10.1001/jamaneurol.2025.0023? | lista | cq1 | Rastro, to adjudicate | the reviewer's annotation |
| e3 | ¿Cuántas organizaciones argentinas distintas nombra al menos una afiliación de las 100 publicaciones? | número | cq2 | Rastro, to adjudicate | the reviewer's annotation |
| e4 | ¿Qué publicaciones (DOI) nombran a la Universidad de Buenos Aires (https://ror.org/0081fs513) en alguna afiliación? | lista | cq2 | Rastro, to adjudicate | the reviewer's annotation |
| e5 | De las afiliaciones que mencionan Argentina, ¿cuántas no nombran ninguna organización argentina registrada en ROR? | número | cq1, cq3 | Rastro, to adjudicate | the reviewer's annotation |

Shared definitions, written into each question: an «organización argentina» has at least one ROR v2.15 location
in Argentina. An affiliation «nombra» an organization when its text contains the organization's name, a ROR alias or
label, or an acronym that only that Argentine organization uses. A parent organization does not receive its
institutes' mentions.

**Where the final reference comes from:** the blind reviewer marks, for each affiliation, the Argentine ROR
organizations it names, with the approved plan: a full review of the 196 Argentina-text strings and a yes/no screen of
the other 766. All five answers are derived from that annotation, not from Rastro. Until then, each question's reference
is a SPARQL query over Rastro, marked «to be adjudicated».

## Approaches and runs

- **B, without Rastro:** SQL over `crossref` and `ror` as loaded. The reader user sees only those two schemas.
- **D, SQL with Rastro's links:** the same, plus the `afiliaciones` schema (identifications, doubtful candidates,
  possible gaps). This is the fair baseline.
- **C, with Rastro:** SPARQL over Ontop on :8083.
- **Who answers:** one fresh subagent per prompt, Claude Opus 5.5 (`claude-opus-5-5`), up to 3 attempts with the
  error message. It never sees the reference or the other answers.
- **Consistency:** e1 and e4 get three paraphrases each.
- **Size:** 5 questions × 3 paths + 2 × 3 paraphrases × 3 paths = **33 subagent runs**. The prompts, model, attempts and
  source fingerprints go in the evidence manifest.

No «when the data is missing» test (not in the approved app proposal).

## Open question for the user: the harness has per-domain code

`layer/evaluar.py` names each domain in two Python dictionaries: the SQL function that normalizes company names, and
the title of the results file. A new domain has to be added there.

- **(a) Add `afiliaciones` to those dictionaries.** Smallest change, but it is domain code in a shared script.
- **(b) Read both from the domain's `method.evaluation` entry in the registry,** with defaults: no normalization
  function means exact comparison. A small generic change, recorded as a method change, like the quality runner.

Recommendation: (b), since identifiers need no normalization function and the skills are meant to be domain-generic.
