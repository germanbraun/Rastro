# Worked example: oil and gas (`energia`)

`app/dominios/energia.yaml`, keys `ejemplo_integracion` (tab «Paso a paso») and `ejemplo_lab` (inside «Rastro Lab»).
Slides: `e-ejemplo-mapeo`, `e-ejemplo-enlace`, `e-ejemplo-respuesta`, `e-lab-entrada`, `e-lab-aportes`,
`e-lab-evidencia`. Script: the two optional sections at the end of `docs/demo-guion-energia.md`.

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

The example well of the Lab tab (`modelo.pozo_ejemplo`; 165404 on 23/10/2026). Step 3 shows the model's real
calculation (`lab.show_calculation`): the training average plus the contributions grouped as concession with
operator and partners, fracturing and depth. That day it was 51.64 − 3.57 + 6.80 − 0.72 = 54.15 million m³.

## What was replaced

The first version used invented wells, names and a maintenance report that Rastro does not load. It was rebuilt on
the case above, because next to real data the invented records were hard to tell apart and the last question sold a
source the domain does not have.
