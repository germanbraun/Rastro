Generated on 2026-10-28 from docs/decisions.md; the log stays the source of truth.

# Rastro: decisions for an outside review

## 1. What Rastro is

Rastro is two commercial MVPs built on semantic technologies and public data. **Rastro Layer** answers business
questions over several integrated sources and gives the provenance of every value. **Rastro Lab** is a machine-learning
model whose predictions are explained with that same evidence. Today it predicts the gas output of new Vaca Muerta
shale wells.

The stack: sources are loaded into Postgres, R2RML mappings and a minimal OWL ontology per domain, and Ontop serving a
virtual knowledge graph over SPARQL. A triplestore is used only for a full vocabulary (MeSH) and for federation. The
app is in Streamlit, and an LLM writes the queries for free-form questions.

The demo domain is oil and gas in Argentina. US federal suppliers, oncology trials and research affiliations show that
the same approach generalizes. The audience is consultants who know SQL and do not know semantic technologies. The
project's main rule is **simple**: someone in sales must be able to explain it in three minutes.

Labels used below: **B** = an LLM writing SQL over the raw sources; **D** = an LLM writing SQL over the raw sources
plus Rastro's link tables (the "fair baseline"); **C** = an LLM writing SPARQL over Rastro.

## 2. Decisions to review

### A. Scope and positioning

**A1. Simplicity as the governing rule** (2026-10-16)
- **Decision:** do the minimum that works for the demo or for one of its numbers. Use business names and make every
  step end in something visible. SHACL and PROV-O were left out at first; both were added later (2026-10-18, 2026-10-21).
- **Why:** it is a commercial MVP that someone in sales has to understand.
- **Q1.** Pieces first left out as "not simple" (provenance, quality rules) later became central to the pitch. Is
  "simple" the right filter for an MVP whose value is trust, or does it delay the parts that make the claim credible?

**A2. The value is the reviewed integration, not SPARQL** (2026-10-16, 2026-10-17, confirmed 2026-10-19 and later)
- **Decision:** the message is "integrate once and maintain it as a standard layer". The fair baseline D (SQL plus
  Rastro's link tables) is reported alongside C in every domain.
- **Why:** D ties C on accuracy everywhere it was measured. Oncology: B 18/20, C 20/20, D 20/20. Suppliers
  (2026-10-19): B 4/9, D 8/9, C 8/9. Oil and gas (2026-10-20): B 7/10, D 10/10, C 10/10. The claimed advantages of the
  semantic layer are therefore: a source change is fixed in one place, every value carries its evidence, and outside
  graphs can be joined live. The project says up front that a layer of SQL views would solve part of this.
- **Q2.** If plain SQL over the same link tables scores the same, what does an ontology, R2RML and Ontop add that a
  well-documented SQL schema with lineage tables and views would not? Are the three claimed advantages enough to
  justify the extra stack for an SQL-literate buyer?

**A3. Oil and gas in Argentina as the demo; other domains only in the technical view** (2026-10-19, 2026-10-21)
- **Decision:** the app opens only on oil and gas. Suppliers, oncology and affiliations appear behind «Ver detalles
  técnicos» as proof of generality.
- **Why:** the target audience is operators and sector consultants. The data used is the 2025 file (69 operators,
  83,172 wells), because the 2026 file had only 21 operators.
- **Q3.** Does hiding the other domains weaken the "works for any data" claim in front of a buyer? Is a single-sector
  demo the right first market, given that all of the data is public?

**A4. The opening: "one question, two correct answers"** (2026-10-21)
- **Decision:** the deck opens with "who produced the most gas in Argentina in 2025?". By what each company operates:
  Total Austral 12.3, YPF 11.7 (billion m³). By ownership share: YPF 12.3, Tecpetrol 6.4, Total Austral 5.2. Rastro
  writes the definition once and shows both answers.
- **Why:** an earlier opening compared Rastro with an AI assistant answering from memory. An AI assistant with web
  search returned the published ranking, which matches SQL over the declarations, so that comparison was dropped as a
  weak rival.
- **Q4.** Is "operated vs. attributable share" a real differentiator, or a definition any analyst would write once in
  SQL? Is there a stronger opening that does not depend on a definitional difference?

### B. Architecture

**B1. A pragmatic virtual knowledge graph** (2026-10-16)
- **Decision:** every source is loaded (ETL) into Postgres. Links and hierarchies are precomputed in SQL. Ontop exposes
  a virtual graph over them, so queries are translated to SQL over the original tables and no triples are materialized.
- **Why:** Ontop answers everything itself, with simple joins. The SQL that Rastro generates is shown next to the
  LLM's own SQL, to make the point that Rastro does not copy data.
- **Q5.** With ETL into Postgres and precomputed links, how much of the "virtual" benefit is left? Would a materialized
  graph, or plain SQL views, be simpler for the same demo?

**B2. R2RML mappings, one file per domain; one Ontop per domain, each with a named prefix** (2026-10-16, 2026-10-18,
2026-10-19)
- **Decision:** mappings use the W3C standard rather than Ontop's native format. Each domain has its own Ontop service
  (ports 8080/8081/8082), ontology and namespace. The empty prefix is never used.
- **Why:** portability to "other knowledge-graph platforms or tools", and isolation between domains.
- **Q6.** The portability claim has not been tested on a second engine. Is it worth stating to buyers before it is?
  Does one engine per domain scale, or should domains share one endpoint?

**B3. Closures precomputed, and a triplestore used only on the side** (2026-10-15, 2026-10-16)
- **Decision:** Ontop does not support `*` or `+` property paths. Anything that needs a closure is precomputed in
  Postgres. For example, the MeSH hierarchy was copied in (30,512 descriptors; 245,641 descriptor–ancestor rows) and
  exposed as one `within` property. The full MeSH (15.4 M triples), its text search and the federated Wikidata queries
  stay in a separate triplestore. Federation with `SERVICE` was rejected for the core questions.
- **Q7.** Precomputing closures moves reasoning out of the ontology and into SQL. Does that undercut the argument that
  "knowledge lives in the model"? When would native SPARQL federation be worth its cost?

**B4. Business rules as OWL 2 QL classes** (2026-10-17, 2026-10-19)
- **Decision:** some classes have no mapping and Ontop infers their members from `rdfs:subClassOf`. Examples are
  "targeted therapy" and "supplier to review" (147, later 173 suppliers with a foreign ultimate parent, plus 8
  watchlist matches). `ConcessionToReview` (45 concessions) is the class of the union of two rules precomputed in SQL.
- **Why:** to show that a definition changes in one line of the ontology.
- **Q8.** In a test with 3 questions, this showed no accuracy difference against SQL with the same documented
  definition. Is inference a real selling point here, or a demonstration of capability?

**B5. "A property used by two classes has no rdfs:domain"** (repo rule; applied 2026-10-20, 2026-10-21, 2026-10-22)
- **Decision:** when two classes use a property, it carries no `rdfs:domain`.
- **Why:** domains caused unwanted inferences. 303 pipeline segments were typed as links. Fracturing records were
  typed as fracturings (9,732 instead of 4,733). Three more cases in oil and gas were found by a checker on 2026-10-22.
- **Q9.** Is dropping domains the right fix, or should those properties be split per class or constrained with SHACL?
  What is lost for an LLM that reads the ontology to write queries?

**B6. No PostGIS** (2026-10-19)
- **Decision:** point-in-polygon tests and distances to pipelines are computed in Python with a planar approximation,
  and the result is stored as a link with evidence.
- **Why:** there are about 300 polygons, and it avoids adding a dependency.
- **Q10.** Geometries are exposed with GeoSPARQL `geo:asWKT`, but the computations are not done through GeoSPARQL. Is
  that inconsistency acceptable, and is the planar approximation defensible for distances near 10 km thresholds?

**B7. Enrichment from outside sources, live and saved** (2026-10-17, 2026-10-19, 2026-10-21)
- **Decision:** Wikidata is joined through the LEI. This is done live, with a federated query, and also saved as
  `energia:Enrichment` with the query date and a file fingerprint. It is called "enrichment", not "augmentation".
- **Why:** to show the pattern with provenance. In oil and gas only 3 of the 12 companies with an LEI are in Wikidata
  under that LEI, and 2 of them have their stock exchange recorded.
- **Q11.** With 3 of 12 matches, is this feature worth showing at all? Does it risk suggesting more coverage than
  exists?

### C. Entity linking

**C1. Rules in readable SQL and Python, no LLM** (2026-10-16, applied in every domain)
- **Decision:** links use normalized names, ordered rules and unambiguous synonyms. An LLM for ambiguous cases was
  planned and then not used.
- **Why:** the rules are explainable, repeatable and free per query. Oncology drug links: 74.4 % coverage, then 81 %
  after the whole-word rule, which scored 94 % precision on an AI-reviewed sample. The first rules scored 99/100 on an
  AI-reviewed sample. Supplier→LEI links: 92–98 % on a sample of 50, also AI-reviewed. Stop-reason classification: 45
  of 49 correct (92 %).
- **Q12.** All of these precision samples were reviewed by an AI, not by a person. Is rule-based linking validated by
  AI samples strong enough to be the core product claim? Where would an LLM step, with its output stored as evidence,
  be justified?

**C2. Conservative over complete** (2026-10-19)
- **Decision:** suppliers are not grouped by their parent history. When two rules tie on different LEIs, no link is
  made.
- **Why:** history without dates cannot tell an acquisition from a spin-off. Using it would put today's SAIC inside
  Leidos (332 contracts, US$34.3 billion). Known limit: 1,341 suppliers are listed as their own parent but have another
  parent in their history, and they are left for manual review.
- **Q13.** Is a precise but incomplete group the right default for compliance and spend questions, where missing
  members also cost money?

**C3. Reviewed corrections, with "AI-reviewed, a person still has to confirm"** (2026-10-19, 2026-10-20, 2026-10-26)
- **Decision:** corrections live in reviewed CSVs, each with a reason or a document. Every link shows one of three
  marks: automatic rule; reviewed by AI, awaiting a person; confirmed by a person with a document. A document-backed
  stake replaces the map's stake. For example, the ownership split of Aguada Pichana Este comes from a provincial
  legislature agreement.
- **Why:** some groups (Chevron, Pluspetrol, CGC, Vista) are not recorded in any registry.
- **Q14.** Demo numbers for Chevron and Vista rest on corrections still awaiting a person, and the app says so. Is
  showing the flag enough, or should unconfirmed links be kept out of headline answers?

**C4. Every link is a PROV-O entity** (2026-10-18, 2026-10-19, measured 2026-10-20)
- **Decision:** each link is a `prov:Entity` with `prov:wasDerivedFrom` its sources, plus its rule and its matched text.
- **Why:** per-column provenance can be imitated in SQL; per-record evidence is what convinces. Measured coverage: oil
  and gas 107,795 of 107,795 links (the deck later cites 107,841), suppliers 9,108 of 9,108, oncology 112,461 of
  112,461 trial→drug links.
- **Q15.** "100 % of links have evidence" is true by construction, because the linker writes the evidence. Does that
  number mean anything to a buyer, or should the metric be the correctness of the evidence?

### D. Measurement

**D1. Three approaches, the same model, saved answers** (2026-10-16, 2026-10-17)
- **Decision:** the same LLM (Claude Opus 5.5) answers each question three ways: B, D and C. Settings are the same for
  all three, with up to three attempts each. A number counts as correct within 5 % of the reference; a list needs
  F1 ≥ 0.8. Answers are saved in the repo, so scores can be recomputed without an API key. D was added after an
  external review.
- **Q16.** Is a 5 % tolerance and F1 ≥ 0.8 strict enough for business answers such as "how many m³ belong to YPF"?
  With 5–20 questions per domain, are the score differences (for example 7/10 vs 10/10) meaningful at all?

**D2. References made by AI from Rastro, then adjudicated** (2026-10-16, applied in every domain)
- **Decision:** reference answers come from hand-written SPARQL over Rastro. Where the approaches differ, the case is
  adjudicated against the source data before any number is published.
- **Why:** this avoids pure circularity, and adjudication found real Rastro errors. In oncology B was right in several
  cases. In oil and gas, e09 had 55 operator changes before the fix and 64 after it. Distances (e05) were also fixed.
  The adjudications were done by an AI and a person has not confirmed them.
- **Q17.** The references, the adjudication and the fixes were all done by the same AI that built Rastro. How much of
  each published score should be treated as circular? What minimal human check would make the scores defensible?

**D3. One prompt per evaluator** (2026-10-16, repo rule from 2026-10-22)
- **Decision:** each answer comes from a fresh subagent that sees only its own prompt.
- **Why:** on 2026-10-22, a control run gave each subagent all the questions at once. The subagents then reused one
  query across the four wordings, so that run's consistency result (B 4/5 instead of 3/5) was not used.
- **Q18.** Using subagents of the same model family as both builder and evaluator: is "fresh context" enough
  independence, or is a different model family needed for the evaluators?

**D4. Fixes after measuring are re-measured only where they apply, and said so** (2026-10-19, 2026-10-21, 2026-10-26)
- **Decision:** after a fix, only the affected answers are re-measured, and the published result says so.
- **Examples:** in oil and gas, merging `concession`/`inConcession` took C from 6/7 to 7/7. In Lab, a dictionary note
  took l01 from 22 to 24, correct, and C from 4/5 to 5/5. In affiliations, C and D went from 4/5 to 5/5 after five
  linking fixes; the log calls this "optimistic" because the fixes were guided by the same reference.
- **Q19.** Each fix improves C or D and never B. Over time, does this practice turn the evaluation into a
  tuning set? Should the published number always be the first blind one?

**D5. Blind tests and a holdout to break circularity** (2026-10-20, 2026-10-27)
- **Decision:** a protocol lets a sector person who has not seen Rastro write 5–10 questions, and the dictionary is not
  fixed before publishing. A separate blind test covers the Lab explanations: 20 mixed explanations scored on three
  1–5 scales. No person has taken either test yet.
- **Holdout (affiliations, 2026-10-27):** 100 unseen works (886 mentions). Mentions in agreement went from 854 to 866
  after the fixes, precision from 0.961 to 0.985, recall from 0.979 to 0.977. The reference was annotated by three
  fresh AI reviewers. Two new defects were found and deliberately not fixed, so the holdout stays a fair measurement.
- **Q20.** Is the holdout design (same capture, different seed, AI annotators) independent enough to say "the fixes
  generalize"? What is the smallest human-run blind test that would be convincing?

**D6. Say when the data is missing** (2026-10-21, control 2026-10-22)
- **Decision:** every approach is told to return «SIN DATOS:» ("no data") and say what is missing instead of guessing.
- **Measured:** 5 unanswerable sector questions plus 1 control question. The LLM alone scored 5/6; SQL, SQL with links
  and Rastro each scored 6/6. A control run of the 10 main questions with the new prompt gave 7, 10 and 10, the same
  as before.
- **Honest reading (from the log):** with this rule even the LLM alone did not invent answers.
- **Q21.** Since all approaches behave the same here, does this test support any claim about Rastro, or is it only a
  safety check on the prompt?

**D7. Change and correction tests** (2026-10-17, 2026-10-19, 2026-10-20, 2026-10-21)
- **Decision:** simulate a source changing, and a value corrected once, then restore everything and verify against
  fingerprints.
- **Oil and gas, column rename:** 3 queries break without Rastro. With Rastro, 3 fail loudly, and one mapping line
  restores 9/9.
- **Oil and gas, unit change (barrels):** both approaches return a wrong number without an error. Rastro's unit check
  raises a warning.
- **Correction test:** one corrected stake reaches the answer, the model input and its explanation. Without Rastro the
  value is read from the map in 5 places.
- **Limit:** real changes between the 2023, 2024 and 2025 files could not be tested, because there were none to
  measure.
- **Q22.** These changes are simulated, and in oncology D broke just like B. Is "fixed in one mapping line" a fair
  comparison against "rewrite each SQL query", given that a SQL view layer would also centralize the fix?

**D8. A publication gate** (2026-10-22, 2026-10-26)
- **Decision:** no new accuracy claim is published without independently reviewed references for every question.
  The reference reviewer must not be the person who approved the requirements.
- **Why:** to stop the circularity going forward. Numbers already published were not re-adjudicated; for example, the
  oil and gas trust cards show the status "AI-reviewed references, a person still has to confirm".
- **Q23.** Is it consistent to keep showing the older numbers under a new gate that they would not pass?

### E. Rastro Lab

**E1. Explanation is the measured value; accuracy only shows nothing is lost** (2026-10-20, 2026-10-21)
- **Decision:** the same model is trained on features from the raw tables (A) and from Rastro (B). It is a ridge
  linear regression written in numpy, not trees with SHAP, so each feature's contribution is exact. Concession effects
  are grouped into one factor, backed by Rastro's facts.
- **Numbers:** A and B are equal. On 2025 wells, MAE is 16.7 million m³ and R² is 0.44, later 0.45–0.46. Depending on
  the cut, R² ranges from 0.06 to 0.44. The median per concession alone gives R² 0.42 (2026-10-21).
- **Q24.** If the concession (location) explains almost everything the model knows, what does a "Rastro-backed
  explanation" add beyond "wells in this concession produce about X"? Is the model strong enough to carry the Lab
  pitch?

**E2. No future data, and late data is flagged** (2026-10-20, 2026-10-21)
- **Decision:** a well's operator and type are those of its first production month (`WellStart`). Fracturing counts
  only what was reported up to that month. Data loaded later is flagged. Data loaded only for Lab lives in its own
  schema, and a re-run of the evaluation confirms that Layer is unchanged.
- **Numbers:** for 36 of 43 wells of 2025, the fracturing record was loaded after the well started. When it arrives,
  the prediction moves by 4.8 million m³ on average.
- **Q25.** The split is chronological, but the walkthrough admits the example "is retrospective". Is the leakage
  control complete, and is the late-data flag a selling point or an admission that the input is unreliable?

**E3. Predictions stored in the graph with lineage** (2026-10-21)
- **Decision:** each model run is a `prov:Activity` (versioned by a code fingerprint), with its predictions (`prov:used`
  links to the source records) and their contributions. Each run also keeps its input table, and each downloaded file
  keeps its SHA-256. Full sources are not versioned.
- **Impact test:** Rastro predicted that correcting fracturing report 4703 would change exactly one prediction. It
  changed from 22.7 to 30.2 million m³, and no other prediction changed.
- **Q26.** Is lineage through `prov:used` worth its complexity compared with a predictions table that has foreign keys,
  which the log shows plain SQL can also query (on the predictions questions B scored 4/5, and D and C 5/5)?

**E4. Trees evaluated and not adopted** (2026-10-24, 2026-10-26)
- **Decision:** ridge stays the model. Tree models appear only in the technical view, with neutral wording.
- **Numbers:** Random Forest was selected on 2023–2024 data. On 2025 it gave MAE 16.274 vs. 16.672 for ridge, and R²
  0.430 vs. 0.457. A replay of a published thesis pipeline gave R² of about 0.69, against the thesis's 0.7539 on an
  interleaved split; on later years the thesis reports 0.254.
- **Q27.** Is keeping the weaker but explainable model the right call for a product about explanation? Or does it
  invite the objection "your explanations are of a model nobody would deploy"?

**E5. A Colab notebook for the explanation** (2026-10-28)
- **Decision:** `lab/notebooks/rastro-lab.ipynb` runs the same model code on a saved snapshot of its inputs (the one
  exception to keeping data out of the repo), shows one prediction explained as columns and as concepts with
  evidence, the predictions to review and what a correction changes, and checks itself against the published run.
- **Q24b.** For a technical reviewer, is a snapshot-based notebook convincing evidence of the explanation claim, or
  does it need a live connection to the layer to show that the evidence is not prepared in advance?

### F. App and demo

**F1. Two views: business by default, technical on request** (2026-10-18)
- **Decision:** no jargon in the main view ("business dictionary", "evidence"). The switch «Ver detalles técnicos»
  adds, next to each answer, its SPARQL query, the SQL Rastro generates and its RDF evidence, and opens the other
  domains. It also adds the tab **«Bajo el capó»** (Under the hood), with three parts: a **SPARQL console** (an editor
  to write and run any query over the domain, plus one instance drawn as a graph); **«Diccionario, enlaces y
  mapeos»** (the ontology with its labels and diagram, the link tables with their rule and evidence, and the R2RML
  mapping blocks that build them); and **«Reglas de calidad (SHACL)»** (each rule, what it checked and what failed).
  Visible texts say "Rastro deduces", and tools are named only where they are explained.
- **Q28.** The audience knows SQL. Does hiding the SQL, the mappings and the SPARQL console behind a switch help
  them, or does it hide the thing they would trust most? Is one «Bajo el capó» tab the right home for the editor,
  the dictionary and the quality rules, or should a consultant reach them from the answer they are looking at?
- **Added 2026-10-28:** the console became a code editor (line numbers, colors) that checks the query before it runs
  (syntax error on its line, terms the dictionary lacks), and a fourth part, **«Editor de mapeos (R2RML)»**, loads the
  domain's mapping or an uploaded one, checks it (Turtle, R2RML structure, dictionary terms), shows the diff and saves
  it to the real file with a backup and one-click undo; Ontop reloads it in about two seconds.
- **Q28b.** Editing the live mapping from the app makes the layer tangible for a consultant, but it changes what every
  answer reads. Are a passing check, a diff, a backup and git enough, or should a save go through a review step?

**F2. The demo in four moments, three minutes** (2026-10-21)
- **Decision:** ask (an ownership share, with evidence), the source changes (a renamed column), predict (Lab), and
  one correction reaches every result.
- **Why:** earlier versions had too many pieces to remember.
- **Q29.** Is this the right order and selection for a three-minute pitch? Which moment would a skeptical SQL
  consultant find weakest?
- **Changed 2026-10-28:** the deck opens with the problem (operated vs. share), then a schema of a semantic layer;
  the six reasons became the closing summary, and «Qué es Rastro» left the deck. Story: 9 slides.
- **Q29b.** Is a schema slide before the first live moment the right frame for SQL consultants, or should the
  schema come only after they have seen one answer traced to its sources?

**F3. Numbers are read, never typed** (repo rule; 2026-10-16, 2026-10-26, 2026-10-28)
- **Decision:** app texts are in YAML. Measured numbers are read from their JSON files. Contrast cards run their own
  queries live, and slides fill tokens from a generated JSON file.
- **Guards:** a test fails if a card that has queries types a number. Another test fails if a slide has a placeholder
  with no number.
- **Q30.** Is this level of guarding proportionate for an MVP, or a sign of over-engineering?

**F4. "Grounded GraphRAG" for text** (2026-10-19)
- **Decision:** the graph selects the relevant records with an exact query, and an LLM summarizes only those texts,
  with a citation for each record. No graph is built from text by an LLM. When counting matters, the texts are
  classified by rules into graph data (stop reasons: 92 %).
- **Why:** in suppliers, the 40 largest Leidos-group contracts: a text search finds 33 of 40 and misses 7 contracts
  worth US$5,607 million; the graph finds 40 of 40.
- **Q31.** The summaries are saved AI outputs. Is "the graph selects, the AI summarizes" distinct enough from ordinary
  RAG with metadata filters to be named as a feature?

**F5. Spanish UI with an English overlay** (2026-10-26)
- **Decision:** a language switch, with Spanish as the default. English overlays hold only the texts and fall back to
  Spanish. Evaluation prompts stay in Spanish. A snapshot test checks that every Spanish text stayed identical.
- **Q32.** Source data, rules and evidence stay in Spanish in the English UI. Is that acceptable to a non-Spanish
  buyer?

### G. Method and skills

**G1. Method before agents** (2026-10-22)
- **Decision:** no multi-agent orchestration yet. The method is written down instead: about ten steps, each with a
  skill, an executable check that decides, and a person who approves only business decisions. One agent uses the
  skills; separate agents are used only where independence matters (evaluation, blind tests).
- **Why:** in Rastro, the errors were caught by checks, and the hard decisions were business decisions.
- **Q33.** Is "one agent plus written skills plus gates" a sellable method, or an internal workflow? What evidence would
  show it beats a skilled engineer without it?

**G2. Skills generic per domain; technical work in English** (2026-10-22, 2026-10-27)
- **Decision:** the method skills name no domain or source outside their `examples.md` files. Code, documentation and
  skills are in English; what users see stays in Spanish.
- **Q34.** Are the skills generic in fact, or only in wording? The evidence comes from a single transfer domain (G3).

**G3. Transfer experiment on an unfamiliar domain** (2026-10-22 to 2026-10-27)
- **Decision:** the electricity domain was rejected after inspection, because the key data's terms prohibit
  reproduction. A research-affiliations domain was chosen instead: 100 Crossref works and ROR.
- **Result (2026-10-26):** the method transferred in about 1.9 agent-hours, but not unchanged. Of 49 process notes, 26
  are important. Almost every important defect was caught by a second reviewer or by reading records by hand, not by
  the automated gates.
- **Q35.** If the gates miss most important defects, what is the real role of the gates, and is human or second-AI
  review the actual quality mechanism?

**G4. Gates, logs and checks as code** (2026-10-22, 2026-10-26)
- **Decision:** lifecycle states for each question (proposed, approved, implemented, validated). The experiment log is
  written by commands, and a lint checks the hours. Validation has two levels: invariant checks and independent
  checks. Quality rules carry a broken example for each constraint.
- **Oil and gas:** 2 of 15 query checks are independent; 13 are invariants.
- **Q36.** Is this machinery proportionate to a two-MVP project? Does "invariant" validation risk being read as
  "validated"?

### H. Code structure (2026-10-27, 2026-10-28)

**H1. Split the screen code, and document how to trace a number** (2026-10-27)
- **Decision:** a 1,598-line module was split by a script into six modules. The split was checked on the syntax tree:
  71 of 71 functions are identical. An onboarding guide traces one demo number from the raw tables to the screen. CI
  runs lint and tests.
- **Q37.** Is splitting by screen part (answers, trust, technical view) the right axis, or would splitting by feature
  per domain be easier to debug?

**H2. Decouple domains into extensions; keep oncology on its own screen** (2026-10-28)
- **Decision:** the shared template knows no domain. Domain code lives in extension classes declared in each domain's
  YAML; units, change warnings and slide numbers became configuration; there is no default domain. `app/app.py` went
  from 913 lines to 45.
- **Why oncology stays apart:** the user chose to keep its screen as it is instead of rebuilding it on the template.
  Rebuilding would change its look and its demo script.
- **Q38.** Is an extension interface with about eight hooks the simplest way to keep the core generic? Does keeping
  oncology on its own screen leave a second code path that will rot?

**H3. Guard tests for genericity and slide format** (2026-10-28)
- **Generic-code test:** fails if shared code names a domain, a known source or a business word (the word list is read
  from the registry).
- **Slide-format test:** fails if a slide has a `<style>` block, a class or a margin. Slides use inline styles only,
  because the shared deck drops anything else.
- **Q39.** Are word-list guards robust (false positives, easy to bypass)? Is "inline styles only" a reasonable cost to
  pay for one deck tool?

## 3. Open decisions

1. **A person confirms the references.**
   - **Open:** the oil and gas adjudication, the affiliations blind references (including the holdout), oncology's
     human check, and the supplier and drug link samples. All were reviewed by AI only.
   - **Options:** a person spot-checks a sample, or a full human review.
   - **Blocks:** the publication gate. The affiliations accuracy cards stay hidden, and any external accuracy claim
     waits on it.
2. **A person confirms the AI-reviewed corrections.**
   - **Open:** Chevron, Vista, Pluspetrol and CGC in oil and gas; the «CIC»/«CCT» decisions and the 13 rejected
     candidates in affiliations; Kudu Dynamics and Aranea Solutions in suppliers.
   - **Options:** confirm each with a document, or drop the unconfirmed ones from headline answers.
   - **Blocks:** removing the "awaiting a person" flag from demo numbers.
3. **Blind tests with sector people.** Both protocols (blind questions, blind Lab explanations) are ready, and the
   invitation is written.
   - **Open:** no participant yet.
   - **Blocks:** the only non-circular evidence for Layer questions and for the Lab explanation claim (Q24).
4. **Human minutes per step.**
   - **Open:** experiment logs record agent hours, and human time stays null because only the person may log it.
   - **Options:** the person logs time going forward, or the claim stays agent-hours only.
   - **Blocks:** any claim about the cost of the method (G1, G3).
5. **Commands to fill the experiment log's header fields** (2026-10-27).
   - **Open:** today the header is filled by hand and checked with `--lint`.
   - **Options:** add the commands, or keep doing it by hand.
   - **Blocks:** fully command-written logs.
6. **A guard for the suppliers change test** (2026-10-27).
   - **Open:** suppliers has no snapshot-and-restore guard, so its skill says not to run the test.
   - **Options:** add its `change_guard` entry to the registry, or retire the test.
   - **Blocks:** re-running the suppliers change numbers.
7. **The two affiliation linking defects found by the holdout** (2026-10-27): a footnote digit glued to a name (6
   strings), and a short name inside a longer one not followed by «de/del/of» (2 strings).
   - **Open:** both were left unfixed on purpose, to keep the holdout fair.
   - **Options:** fix them and draw a new holdout; or fix them and say the holdout is consumed.
   - **Blocks:** nothing urgent, but they are known wrong links.
8. **Oncology on its own screen or on the shared template** (2026-10-28).
   - **Open:** it is kept as an extension for now.
   - **Options:** rebuild it on the template, which changes its look and its script; or leave it as it is.
   - **Blocks:** a single rendering path for all domains.
9. **Which walkthrough belongs in the timed demo.**
   - **Open:** this was listed as "not decided" on 2026-10-26. The same day the first moment went back to YPF and the
     Chevron walkthrough moved to the appendix, but the log does not record an explicit decision on the timed demo.
10. **Demo readiness** (plan).
    - **Open:** the three-minute demo has not been rehearsed with a non-technical person, a salesperson has not given
      it from the script alone, and there is no backup video.
    - **Blocks:** the plan's final checkpoint.
11. **Lab next steps** (2026-10-21).
    - **Open:** location, intensity per metre and start year as features; bootstrap intervals (the current range
      covers 71 of 100 wells, against a target of 80); error by well size.
    - **Blocks:** a better-calibrated Lab claim.
12. **Slides that still type figures** (2026-10-26) — **resolved 2026-10-28.**
    - Every measured number on the oil and gas slides is now a placeholder filled from the measured files
      (the last one, the B/D/C scores on the AI slide, moved on 2026-10-28); `tests/test_slides_format.py` fails on a
      placeholder without its number. Kept here so the reviewer sees it was closed.
13. **A second unfamiliar domain for the transfer experiment** (2026-10-22).
    - **Open:** the experiment plan asks for a repeat on a second unfamiliar domain, and none is approved.
    - **Blocks:** any "the method generalizes" claim beyond one case.
14. **A licence for the repository.**
    - **Open:** this was named an owner's decision on 2026-10-21. The repository became public on 2026-10-27, and it
      has no licence file.

## 4. Known limits we already state

- The evaluation references, the adjudications and the link-precision samples were made by an AI (Claude Code). A
  person has not confirmed them.
- The references come from Rastro itself, so C's advantage over B can be partly circular. D (SQL with Rastro's links)
  ties C on accuracy in every domain.
- The question sets are small: 20 in oncology, 9 in suppliers, 10 in oil and gas, 5 in affiliations and 5 for Lab
  predictions.
- Some demo numbers (Chevron's and Vista's shares) rest on AI-reviewed corrections that await a person. The app marks
  them.
- All data is public. Some sources have known gaps: the map's ownership stakes can be out of date (the human check
  found 2 of 4 out of date), GLEIF records no parents for the Argentine companies, and Wikidata has the LEI for only 3 of 12 companies.
- The change tests are simulated. No real schema change occurred between the 2023 and 2025 source files.
- Lab: R² about 0.46. Most of the signal is the concession (the median baseline gives 0.42). Prediction ranges cover
  71 % of the wells against a target of 80 %. The example walkthrough is retrospective.
- Re-measurements after fixes are optimistic, and the log says so. The first blind measurement is the one to read.
- Geometry is computed with a planar approximation, without PostGIS. Pipeline distances do not include in-field
  pipelines: they are "a hint, not a conclusion".
- The free-text summaries (grounded GraphRAG) are saved AI outputs. The records they cite are read live.
- The portability of the R2RML mappings to other engines is claimed from the standard, not tested.

## 5. How to answer

- Answer per question number (Q1–Q39). Skip any you have no view on.
- For each answer, say whether you **agree, disagree or would change** the decision, and why. Name the alternative
  you would choose and what it would cost.
- **Flag any claim that looks circular or unsupported:** a number whose reference, check or fix came from the same
  party that built Rastro, or a benefit that is asserted rather than measured.
- Separately, list the **three decisions you consider most at risk** with an SQL-literate commercial audience, and the
  **one open decision** (section 3) you would resolve first.
- Keep it short: a few sentences per question is enough.
