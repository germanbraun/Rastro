# Worked examples from Rastro's domains

The domain-specific content of the `link-entities` skill. The skill itself is generic; these are the real cases behind
it.

## Where the linkers live today

| Domain | Folder | Corrections | Run |
|---|---|---|---|
| Oil and gas (`energia`) | `linking/energia/` (`links.sql`, `link.py`) | `linking/energia/correcciones.csv`, `linking/energia/participaciones-revisadas.csv` | `docker compose run --rm energia-linker` |
| Suppliers (`proveedores`) | `linking/proveedores/` (`links.sql`, `entities.sql`, `link.py`) | `linking/proveedores/correcciones.csv` | `docker compose run --rm proveedores-linker` |
| Oncology (`oncologia`) | `linking/` (`drugs.sql`, `entities.sql`, ...) | `linking/regimens.csv`, `linking/generic_words.csv` | `docker compose run --rm linker` |
| Research affiliations (`afiliaciones`) | `linking/afiliaciones/` (`links.sql`, `link.py`) | `linking/afiliaciones/correcciones.csv` | `docker compose run --rm afiliaciones-linker` |

Columns of the reviewed CSVs:

- Oil and gas, `correcciones.csv`: `nombre, grupo, motivo`.
- Suppliers: `uei, grupo_lei, grupo, motivo`.
- Affiliations: `doi, author_position, affiliation_position, organization, decision, reason, source, validated_by,
  human_confirmation` (`human_confirmation` stays `pending` until a person confirms).

Link table columns: oil and gas `regla` and `evidencia`; affiliations `rule` and `evidence`
(`afiliaciones.identificacion`).

The oil and gas linker takes about 5 minutes and rebuilds the `energia` schema (`DROP`): anything that cannot be rebuilt
goes in its own schema (Rastro Lab's data, for instance).

## The order of what narrows down (oil and gas and suppliers)

- **Shared key:** the LEI (company to the GLEIF registry), the well identifier.
- **Domain rule:** the well's point falls inside the concession outline; whoever reports the last month is the
  operator.
- **Normalized name:** uppercase, without accents, punctuation or legal form, with `energia.normalizar`.

## The order of what narrows down (affiliations)

The rules are in the docstring of `linking/afiliaciones/link.py`: R0 the ROR identifier the publisher supplied (a
shared key); R1 a ROR name of 12 characters or more as a whole phrase, plus «Argentina» or one of the organization's
ROR cities as second evidence; R2 an acronym used by only one Argentine organization, with the same second evidence.
Anything else that looks like a candidate goes to `afiliaciones.dudosa`.

## A rule and its evidence (oil and gas)

Evidence text of a name match: «Coincide el nombre sin acentos, puntuación ni forma societaria: «TOTAL AUSTRAL»» (the
name matches without accents, punctuation or legal form).

When two sources disagree: the registry says one operator and the sworn statement another; both are kept.

## Rule and evidence properties per domain

- Oil and gas: `energia:rule`, `energia:sourceText`.
- Suppliers: `proveedores:linkRule`, `proveedores:sourceText`.
- Oncology: `oncologia:linkRule`, `oncologia:interventionText`.
- Affiliations: `afiliaciones:rule`, `afiliaciones:sourceText`.

Link classes in `method.evidence.link_classes` (read by `layer/evidencia.py`): oil and gas `Stake`, `OperatorLink`, `CompanyName`, `LocationLink`,
`PipelineLink`, `SurroundingsLink` and others; suppliers `GroupLink`, `LeiLink`, `WatchlistLink`; oncology `DrugLink`. Affiliations has no `method.evidence` block
yet, so its links (`Identification`) are not in the coverage count; its quality rule `calidad:IdentificacionCompleta`
checks them.

## The check, as run for oil and gas

- Quality rule `calidad:EnlaceConEvidencia`, with `docker compose run --rm calidad`.
- Evaluation: `docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun` and `puntaje`;
  adjudication in `layer/energia/adjudicacion.md`.

## Business rules a person approved (oil and gas)

Who is the operator of a well, what share of a concession belongs to a partner, since when a company operates a
concession.

## Before and after a fix, and unseen records (affiliations)

- **Before and after:** the first version of the five linking fixes (2026-10-26) lost two correct identifications
  («… de Buenos Aires», «… de la Provincia de …») and the second matched an address («UNR-CONICET Rosario»). Both
  were caught by comparing the links before and after, and corrected before measuring
  (`layer/afiliaciones/adjudicacion.md`).
- **Unseen records:** the fixes were found by comparing with the first blind reference, so the re-measured score was
  optimistic. The re-test (`docs/experiments/research-affiliations/holdout/README.md`): 100 more works from the same
  capture, the old and new rules run in a temporary table, a new blind annotation. Mentions that agree, of 886: 854
  before, 866 after; precision 0.961 → 0.985, recall 0.979 → 0.977. Two defects found there (a footnote digit glued
  to a name, a short name inside a longer one) were not fixed: a fix would be tuned on that holdout. The annotation
  was made by AI reviewers and still needs a person's spot check.

## Watch out for: what happened

- **Concatenating an empty value wiped out the evidence (oil and gas):** in SQL, `'texto ' || NULL` gives `NULL`. Five
  well trajectories without a horizontal leg ended up without evidence until a quality rule found it.
- **Same name is not the same company (oil and gas):** in Wikidata there are groups with the name of the Argentine
  company; only the ones with the same LEI were used.
- **The evidence carried what was being predicted (Rastro Lab, oil and gas):** the well's gas had leaked into the
  evidence of its start (`energia:WellStart`).
- **A rule that discards data also decides (oil and gas):** operator changes gave 55 instead of 64 because the rule
  discarded the months without production.
- **Company history (oil and gas):** mergers, sales and changes of legal name go in `linking/energia/correcciones.csv`
  with their document and date.
