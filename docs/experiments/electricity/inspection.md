# Electricity source inspection

Inspector: Codex/GPT, 2026-10-22. Reviewer: Claude, review pending.

Status: **read-only inspection complete; no domain, business question or implementation approved**.
Authorization: the user's decision in [the shared discussion](../countrycodes/discussion.md).
Working time is recorded separately in `inspection-time.yaml`; the ceiling was three agent working hours.

## Finding and recommendation

There is enough accessible material to propose a bounded electricity case, but not to call its scope ready for
implementation. The best inspected candidate is **2024 generation records linked to the plant portfolio described
in Pampa's 2024 annual report**, with the Secretariat's plant registry as supplementary geographic/identity evidence.
This is an inspector's recommendation, not a selection approved by the user.

The primary workbook is substantially more useful than the government resource titled “Generación últimos años”:
that CSV's observed content ends in February 2020. A recent catalog modification does not establish recent data.
The registry mostly repeats CAMMESA-origin information for MEM plants. Neither a different web host nor the
company's republication of a CAMMESA chart establishes independent corroboration of generation.

Before implementation, Claude should review the evidence and the user should decide whether this bounded case
is useful. Resolve the source reuse terms and appoint a business-definition reviewer before accepting its scope.
Do not introduce another source or a fresh domain service merely to get past those decisions.

## Access, licenses and version policy

All successful downloads are in ignored `data/raw/electricity-inspection/`. `source-profile.json` records their
source URLs, byte counts and SHA-256 hashes. The official CKAN APIs redirect HTTPS requests to HTTP; the downloaded
metadata and CSV snapshots therefore do **not** have end-to-end verified HTTPS transport. Response headers are
retained locally, not versioned; they can contain temporary cookies. No authentication or credentials were used.

| Source | Actual access and useful content | Published terms and version limits |
|---|---|---|
| [Secretariat plant registry API](https://datos.energia.gob.ar/api/3/action/package_show?id=generacion-electrica-centrales-de-generacion-) | Metadata and CSV fetched, final HTTP 200. 474 rows; name, plant code, reported agent, technology, capacity in MW, geography, system and origin. | API declares CC-BY-4.0 and monthly refresh. CSV resource modified 2026-09-22; no row-level effective dates or immutable revision URL established. National search-index metadata saying no license/2023 is stale relative to this snapshot. |
| [Government CAMMESA catalog API](https://datos.energia.gob.ar/api/3/action/package_show?id=publicaciones-cammesa) | Metadata, generation CSV and MEM-agent CSV fetched, final HTTP 200. Generation: 22,444 rows, 2017-01–2020-02; agents: 10,080 rows. Both have May 2020 processing timestamps. | API declares CC-BY-4.0 and monthly refresh; resource modification dates in 2026 do not match observation recency. These are CAMMESA-derived tables, not an independent second measurement source. |
| [CAMMESA annual index](https://cammesaweb.cammesa.com/informe-anual/) and [2025 database download](https://cammesaweb.cammesa.com/?wpdmdl=52496) | HTTPS 200; the download redirects to a ZIP on `microfe.cammesa.com`, containing `Base de datos Informe Anual 2025.xlsx`. The generation sheet includes monthly 2024 and 2025 machine records, with plant and agent codes, province, market and net generation. | Dated annual artifact, HTTP Last-Modified 2026-06-30; URL/content can still change. Hash both ZIP and any later extracted input. [Access policy](https://cammesaweb.cammesa.com/politicas-de-acceso/) contains a commercial-use restriction and does not establish an open-data license for this workbook. The government catalog's CC-BY declaration must not silently be extended to this separately downloaded file. Reuse permission remains unresolved. |
| [Pampa-authored 2024 annual report](https://cdn-sites-assets.mziq.com/wp-content/uploads/sites/1438/2025/04/PESA-Memoria-Anual-2024-EXE-Edicion-Especial.pdf) | HTTPS 200; 272-page PDF. Pages 52–56 describe the generation portfolio, plant aliases, geography, interests and operational history. The [company's report index](https://ri.pampa.com/en/financial-information/investor-kit/) was also accessible; the exact archive link between this edition and the index was not established. | Named reporting year and publisher; pin downloaded bytes. No explicit open reuse license established. Facts about its own portfolio are independently maintained company assertions; the market-generation chart on page 53 explicitly cites CAMMESA and is not independent generation evidence. |
| [Pampa company-hosted 2019 sustainability report](https://pampa.com/wp-content/uploads/2024/01/PAM_Reporte2019_ESP.pdf) | HTTPS 200; 180-page PDF. Page 18 has plant aliases, location and technical specifications, useful for a historical alternative with the old generation CSV. | Report year is 2019, upload path is 2024; these dates mean different things. No explicit open reuse license established. Historical-average generation is not annual 2019 generation. Retained as an alternative, not an additional required source. |
| [Original generator authorization, Disposición 17/2019](https://www.boletinoficial.gob.ar/detalleAviso/primera/206470/20190429) | HTTPS 200, original public notice. Article 1 associates Pampa with a named wind project, locality, nominal capacity and connection point. It does not supply CAMMESA plant codes. | Stable notice identifier and publication date; preserve hash. Reuse terms not established in this inspection. The authorization is a separate administrative assertion, but its recitals also cite CAMMESA. It is not proof of observed generation or a commissioning date. |

The direct SEC copy of the 2019 filing returned 403 through curl; the web reader could not open the oversized filing.
Several guessed dataset slugs returned 404, and web-reader opens timed out. The CKAN identifiers linked above worked.
The PDFs were read locally using `pypdf==6.1.1`, installed under `/tmp/rastro-electricity-inspection-tools`; project
dependencies were not changed. Text extraction is useful for locating evidence, but multi-column tables need visual
review before their numbers become references. No complete PDF or source table is committed.

## Grain, coverage and join evidence

The offline [profiler](profile.py) reproduces the file hashes and structural findings in [source-profile.json](source-profile.json)
from the downloaded files, without network access, a database, semantic mappings or model queries.

- **Registry:** 399 MEM entries, 65 isolated and 10 interconnected non-MEM entries. All 399 MEM entries have distinct
  nonempty plant codes; the other 75 entries have none. Of the MEM entries, 363 cite CAMMESA, 35 DIE and one CRPEE.
  These origin labels alone do not establish independent collection for the latter entries.
- **Current workbook:** `GENERACIÓN`, header row 33, columns A:P, has 15,243 data rows: 7,494 for 2024 and 7,749
  for 2025. Each year covers twelve Excel month serials. Observed columns include year, month, machine, plant,
  agent, province, market and net generation. Cell A31 explicitly labels the detail table in MWh, whereas the
  overview tables use GWh. Preserve that distinction in any later calculation and reference review.
- **Market grain matters:** year/month/machine has 214 extra rows across the workbook; adding market removes
  those duplicates. Observed markets are MEM, Asignado, SPOT and MAT. All repeats occur in 2025. Do not deduplicate
  by machine/month or assume these market categories are additive without source documentation.
- **Raw exact-code overlap:** 367 of 419 distinct 2024 generation plant codes occur in the registry; 394 of 450
  in 2025. These are structural overlaps, not adjudicated links or accuracy scores. Missing matches include `ATUC`
  and `BBLA`; do not infer identities from suggestive abbreviations alone.
- **Temporal mismatch:** the registry is a 2026 snapshot without explicit row validity intervals. A 2024 record
  joined to its current name, agent or capacity must retain both dates. Current ownership cannot be applied backward.
  The workbook itself supplies province, so adding the registry merely to recover that field adds no new fact.

Examples requiring actual evidence rather than name equality:

| Observation | Why it matters | Candidate evidence; still unapproved |
|---|---|---|
| Pampa calls a plant CTG; registry calls it GUEMES with code GUEM. The 2024 workbook has agent codes CTGUEPLG and CTGUEMEG under GUEM, with different descriptions. | A plant is not an agent, and a current company name cannot replace every historical agent role. | Annual report p.54, registry GUEM row and workbook rows 276–279. Verify the role and period separately. |
| The report uses CTGEBA and CTPP; the registry uses GEBA/C.T. GENELBA and PILB/PILAR BSAS. | Abbreviation and company-group associations need a recorded rule and record-specific evidence. | Annual report p.55, matching registry rows, then inspect the actual generation records before accepting a link. |
| Pampa's report distinguishes PEPE 2 and PEPE 3; registry rows PAMEEO and BAHIEO share the same reported agent text, with further similarly named entries. | Company text alone can merge separate projects. | Report p.53 gives different locations and characteristics; original authorization gives another identity clue. The proposed pairings require review, not an automatic match. |
| The report describes HINISA and HIDISA as systems containing several plants, with ownership shares distinct from operation. | One company/concession name may map to several physical plants; joining each generation record to every system row would multiply output. | Annual report p.54 explicitly names component plants and the relationships. Scope must specify physical-plant versus system output and gross versus share-attributed amounts. |

## At most three proposed questions

All are **proposed**. References, definitions and exact answers are pending. Questions use 2024 deliberately, to
overlap the inspected company reporting year and avoid the newly observed 2025 market split. That choice must be
approved and reported as a limitation, not proof that the method handles later schema/market changes.

| Question | Proposed definitions and output | Verification plan and reviewer needs |
|---|---|---|
| 1. Which plants described as operated or co-operated in Pampa's year-end 2024 portfolio can be identified in the 2024 generation records, and which remain uncertain? | Integration question. A table of each explicitly scoped physical plant, report page, proposed machine/plant codes, stated role, evidence and unresolved alternatives. Keep owned, operated and co-operated distinct; expand systems only through documented component relationships. | A power-sector reviewer approves the portfolio inclusion rule and each ambiguous identity. Separately enumerate the report's plants and manually inspect the relevant source records, without relying on Rastro's mapping. Missing or uncertain links remain explicit. |
| 2. For the unambiguously identified plants in that portfolio, what generation do the 2024 records report by month and province? | Integration question. Values describe recorded plant generation for the selected roster, not Pampa's share of production or proof of operation throughout the year. Preserve machine and agent detail. Approve units, market coverage, missing-month handling, negative values and any pumping adjustment first. | Independent calculation over pinned workbook records, with a plant/machine inclusion ledger and checks against appropriate source subtotals. No comparison to rounded company totals unless definitions and periods agree. Reviewer confirms whether the roster-at-year-end question is useful or historical role intervals are required. |
| 3. Which selected portfolio records lack a unique link or have identity, location or date information that cannot be reconciled, and what evidence would resolve each case? | Exception table; explicitly distinguish a genuine contradiction from different roles, system-versus-plant grain and different effective dates. An empty result is not assumed. | A separately prepared exception ledger checks every included asset against both original sources. Reviewer adjudicates contradictions and exclusions; neither assistant invents approvals. |

The company roster is an additional source of portfolio semantics, not an independent meter. Independence for answer
verification can come from separately calculated original-record references under `method-contracts.md`. The
publication bundle, isolated B/D/C evaluators and human adjudication remain future work. B/D/C ties remain valid.

## Familiarity, acceptance and handoff to Claude

The electricity vocabulary, plant/system grain and market structure are new here. Pampa, YPF and some place names
overlap with Rastro's energy work; `linking/energia/` already contains oil-and-gas company/group corrections. This
is **partly familiar**, not a clean-room unfamiliar-company experiment. No existing oil-and-gas link was imported or
validated for electricity. Company evidence that itself cites CAMMESA must retain that dependency.

**Recommendation: conditional candidate, not implementation-ready.** Claude should review the access/hashes,
source dependence, market grain, date mismatch, license findings and usefulness of these questions. In particular:

1. Is a bounded company-portfolio case enough unfamiliar plant semantics for the first transfer attempt?
2. Can an acceptable, documented reuse basis be established for the chosen workbook and report? If not, consider
   the CC-BY catalog's historical case explicitly, or reject this candidate rather than silently changing sources.
3. Who can approve plant identity, company roles, period and units? What is the implementation time budget?

Before execution, fix the non-accuracy measures and correction scenario as agreed in Rounds 4–5. No corrections,
loaders, domains, questions, services, app settings or generic method/skill files were changed by this inspection.
Two approved domain experiments remain necessary before any broader transfer claim.
