# Candidate domains for the generalization experiment

The experiment in `docs/method.md` needs a public domain Rastro has never seen. Criteria: at least three open sources of
manageable size; sources that name the same things differently, so linking with evidence is needed; business questions
with exact answers that need two or more sources, with at least one ambiguous definition; and a domain different from oil
and gas. Researched on 22/10/2026; every source below was opened or downloaded, except where marked "not verified".
Decision pending: which domain, and who writes the questions.

## Ranking

1. **Mining in Argentina:** the hardest and most realistic linking, with "operated vs controlled" built into the data,
   companies that changed their legal name and ownership that changes over time. Small, current, open and a different
   subject. Weakness: no output by company; the numbers come from taxes, EITI payments, the project portfolio and
   investment announcements.
2. **Public procurement in Argentina:** large, current and open, exact numbers, real ambiguities (joint ventures,
   business groups, restructured agencies). But the tax id (CUIT) makes much of the linking easy, and its shape repeats
   the US federal suppliers domain, so it tests less.
3. **Power generation in Argentina:** a good linking problem, but the open data stops in February 2020, the current
   data has a license that forbids reproduction, and it sits next to oil and gas.

Ruled out: agriculture (only places to link, several datasets stopped in 2019–2020) and health facilities (old files,
close to oncology).

## 1. Mining in Argentina (recommended)

**Sources**

| Source | Publisher | Format, size | Update | Notes |
|---|---|---|---|---|
| [SIACAM project portfolio](https://datos.gob.ar/dataset/cartera-de-proyectos-mineros-en-argentina-del-siacam) | Secretaría de Minería | 2 XLSX, 175 KB | Current | 235 metal and lithium projects with stage, mineral, province, coordinates and up to 3 controlling companies with their %; 95 have two or more |
| [Mining projects map](https://datos.gob.ar/dataset/proyectos-mineros-ubicacion-aproximada) | Secretaría de Energía | CSV/SHP, 16 KB | Current | 82 projects with their local operating company |
| [Tax payments of large mining companies, 2019–2023](https://datos.gob.ar/dataset/pago-de-impuestos-nacionales-de-grandes-empresas-mineras-siacam) | Secretaría de Minería | CSV, 8 KB | Yearly | 18 companies, by tax |
| [EITI Argentina](https://eiti.org/countries/argentina) (payments by company, with CUIT) | EITI | XLSX, 185 KB per year | Yearly | 2017–2021; license not verified (EITI recommends CC BY 4.0); also covers oil companies, filtered out |
| [Investment announcements](https://datos.gob.ar/dataset/anuncios-de-inversion-en-el-sector-minero-de-argentina-del-siacam) | Secretaría de Minería | CSV, 5 KB | 2025 | 55 announcements, company and project in loose form ("Barrick Gold-Shandong Gold") |
| [Company registry](https://datos.jus.gob.ar/dataset/registro-nacional-de-sociedades), GLEIF, Wikidata, IGN departments | Ministerio de Justicia, GLEIF, Wikidata, IGN | Registry 890 MB CSV (filtered by CUIT); the rest APIs | Varies | Open (CC BY 4.0; GLEIF and Wikidata CC0) |
| SEGEMAR deposits (WFS) | SEGEMAR | WFS | Not stated | Content and license not verified |

Under 5 MB without the company registry. Technical notes: `mecon.gob.ar` files need the system `curl` (incomplete
certificate chain).

**What needs linking, and why it is hard**

- **Project:** the portfolio and the map share only 58 of 82 names after normalizing ("Chinchillas-Pirquitas" vs
  "Puna Operation").
- **Company, at three levels each source mixes differently:** the local company that operates the mine (map, taxes,
  EITI), the controlling shareholders with their % (portfolio) and the group as written in announcements. Veladero:
  "MINERA ARGENTINA GOLD S.R.L" in the map, "MINERA ANDINA DEL SOL S.R.L." in taxes (the same company, renamed),
  "Barrick 50 % / Shandong Gold 50 %" in the portfolio.
- **Ownership changes over time:** Orocobre → Allkem → Arcadium → Rio Tinto.
- **Keys:** the CUIT only in EITI and the company registry; GLEIF covers the parents, rarely the local companies.

**Draft business questions** (in Spanish, as a client would ask them; to be written with someone from the sector)

| # | Question | Definitions it depends on | Sources |
|---|---|---|---|
| 1 | ¿Cuántos proyectos de litio están en producción o construcción, por provincia? | Etapa «producción» (¿incluye «reingeniería»?) | 1 |
| 2 | ¿Qué grupos controlan proyectos en producción, con su porcentaje? | Controlante vs operadora | 1 |
| 3 | ¿Cuánto pagó en impuestos nacionales en 2022 la operadora de Veladero? | Operadora; cambio de razón social | 2+ |
| 4 | ¿Qué parte de los impuestos de 2021 corresponde a empresas controladas por grupos chinos? | Origen del controlante; ¿mayoría o cualquier participación? | 2+ |
| 5 | ¿Cuánto pagaron en impuestos las operadoras de proyectos de oro, por provincia? | Mineral principal; provincia del proyecto vs domicilio fiscal | 2+ |
| 6 | ¿Qué proyectos anunciados con inversión desde 2020 siguen sin producir? | Proyecto (anuncio ↔ cartera); «sin producción» | 2 |
| 7 | ¿Qué grupo tiene más proyectos de litio, contando su participación? | Proyecto completo vs ponderado por % | 1–2 |
| 8 | ¿Qué empresas pagan impuestos mineros pero no figuran como operadoras de ningún proyecto? | Operadora; CUIT ↔ nombre | 2+ |
| 9 | ¿Cuántos proyectos en producción caen en provincias con más empleo minero? | Empleo solo por provincia (a "no data" case at department level) | 2+ |

**Definitions a person must decide:** operated vs controlled vs owned; a project counted once for its controller or
weighted by %; who owns it on which date; whether "in production" includes "re-engineering" or "maintenance"; whether a
tax payment belongs to the project's province or to the company's fiscal address.

**Risks:** no output by company; EITI's API stops at 2021; two sustainability files return 404.

**A later prediction question** (for a second Lab case, not part of this experiment): which announced projects reach
production, and when.

## 2. Public procurement in Argentina

**Sources:** [COMPR.AR calls, awards and supplier registry 2016–2026](https://datos.gob.ar/dataset/sistema-de-contrataciones-electronicas)
(CSV, about 200 MB; awards with the supplier's CUIT, the buying office, categories, amount and currency);
[public works investment map](https://datos.gob.ar/dataset/mapa-de-inversiones-argentina) (CSV, 8 MB, contractor often
without CUIT); the company registry, GLEIF, IGN departments, Wikidata.

**What needs linking:** joint ventures (their own CUIT; members only in the legal name), business groups (several
CUITs), contractors without CUIT in the works map, agencies renamed by each restructuring, catalog codes vs free-text
categories.

**Draft questions:** awards by procedure type; top 10 suppliers by group; awards to companies less than a year old;
suppliers from another province than the buyer; direct awards outside the supplier's registered activity; public works
contractors that also win purchases; awards by ministry under the current structure; joint ventures and their members.

**Definitions to decide:** contracted vs awarded vs formalized; how a joint venture's award counts for each member;
business group; agency before or after a restructuring; currency and inflation.

**Risks:** large company registry; amounts as text in mixed currencies; a test supplier in the registry; the same shape
as the US suppliers domain.

## 3. Power generation in Argentina

**Sources:** [power plant registry](https://datos.gob.ar/dataset/generacion-electrica-centrales-de-generacion) (474
rows, current); [wholesale market data published by the Secretaría de Energía](https://datos.gob.ar/dataset/publicaciones-cammesa)
(stops in February 2020); [renewable projects](https://datos.gob.ar/dataset/centrales-energia-renovables) (180, with their
own ids). Current monthly data from the market administrator forbids reproduction without permission.

**What needs linking:** plants (269 of 385 share a code with the registry; renewables mostly by name and location) and
companies (the market agent, abbreviated, vs the owning group).

**Definitions to decide:** agent vs owner vs operator; installed vs enabled capacity; net vs gross generation; when a
renewable project counts as finished.

**Risks:** open data frozen in 2020; same publisher and neighbouring subject as oil and gas.

## Still to verify before choosing

The EITI Argentina license; the content and license of the SEGEMAR deposit layers; the license of the Buenos Aires
company registry (IGJ) records.
