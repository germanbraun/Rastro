# Worked example: oil and gas (`energia`)

`app/dominios/energia.yaml`, keys `ejemplo_integracion` (tab «Paso a paso») and `ejemplo_lab` (inside «Rastro Lab»).
Slides: `e-ejemplo-mapeo`, `e-ejemplo-enlace` and `e-ejemplo-respuesta` open the technical appendix (11–13),
followed by the bridge `e-ejemplo-ia` (14: B 7, D 10 and C 10 of 10 from `layer/energia/resultados.json`);
`e-lab-entrada`, `e-lab-aportes` and `e-lab-evidencia` follow the Rastro Lab slide (19–21). Script: the two optional sections at the end of `docs/demo-guion-energia.md`.

## The case

Well 164166 of the Compañía General de Combustibles (CGC), in Cañadón Seco, Santa Cruz. It crosses all three parts:

| Step | Part of Rastro | What the audience sees | Queries |
|---|---|---|---|
| 1 · Un pozo, dos tablas | Dictionary and mappings | The well registry and the production declarations describe the same well with different columns and company names; Rastro joins them by the official well id | SQL on `capitulo4.pozo` and `capitulo4.produccion`; SPARQL on `energia:Well` (id, operator, declarations) |
| 2 · Una empresa, dos nombres | Links with evidence | «CGC ENERGIA SAU» and «COMPAÑÍA GENERAL DE COMBUSTIBLES S.A.» are one company by a reviewed correction, AI-reviewed and pending a person | SPARQL on `energia:CompanyName` with rule, evidence and `prov:wasDerivedFrom` |
| 3 · La respuesta y su origen | The answer and its origin | How much gas the company declared in 2025: in SQL each name finds a part; Rastro counts one company | SQL grouped by declared name; SPARQL summing `energia:WellProduction` by `energia:declaredBy` |

On 23/10/2026: «CGC ENERGIA SAU» had 78,621 declarations and «COMPAÑÍA GENERAL DE COMBUSTIBLES S.A.» 8,684; Rastro
counted 87,305 for one company.

## The model (Rastro Lab)

The example well of the Lab tab (`modelo.pozo_ejemplo`; 165404 on 23/10/2026).

- **Step 3** says where the formula comes from: a linear regression whose coefficients are learned on the earlier
  wells. It then shows the real calculation variable by variable (`modelo.detalle`: value, training average,
  coefficient, contribution) and grouped by concept (`lab.show_calculation`). That day it was
  51.64 − 3.57 + 6.80 − 0.72 = 54.15 million m³. Lateral length had a negative coefficient and stages a large
  positive one: a good moment to explain why the explanation groups correlated variables.
- **Step 4** queries the published prediction of that well (`{pozo_ejemplo}` in the query): its value and range, the
  contributions stored with it, and the four records it used (`prov:used`), each with its rule, evidence and source.
  The fracturing was reported before the well started but loaded after it: the flag for late data.

## What was replaced

The first version used invented wells, names and a maintenance report that Rastro does not load. It was rebuilt on
the case above, because next to real data the invented records were hard to tell apart and the last question sold a
source the domain does not have.
