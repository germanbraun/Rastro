# Dictionary and mapping proposal: research affiliations

Step 2 and 3 of the method (`map-source`), for the approved questions cq1–cq3. Starts from
[semantic-layer-proposal.md](semantic-layer-proposal.md); differences are listed at the end. Status: **proposed, for
the user's approval before the mapping is written**. The identification links (mention → organization, with rule and
evidence) come next, with `link-entities`; they are not part of this proposal.

Prefix `afiliaciones:` (`https://w3id.org/rastro/afiliaciones#`). Names in English, labels in Spanish.

## Terms

| Source field | Term | Evidence | How sure | Open question |
|---|---|---|---|---|
| `crossref.work` row | **`afiliaciones:Publication`** «Publicación» | 100 rows, one per work | sure | — |
| `crossref.work.doi` | `afiliaciones:doi` «DOI» | lowercase text, e.g. `10.1001/jamaneurol.2025.0023` | sure | — |
| `crossref.affiliation` row | **`afiliaciones:AffiliationMention`** «Mención de afiliación» | 1,456 rows; key DOI + author position + affiliation position | sure | — |
| `crossref.affiliation.doi` | `afiliaciones:inPublication` «de la publicación» → Publication | every mention has its work | sure | — |
| `crossref.affiliation.name` | `afiliaciones:affiliationText` «texto de la afiliación» | raw text as deposited, never blank here | sure | — |
| `author_position`, `affiliation_position` | `afiliaciones:authorPosition`, `afiliaciones:affiliationPosition` (integers) | 0-based positions; identify an occurrence, not a person | sure | — |
| `crossref.affiliation.ror_id` | `afiliaciones:suppliedOrganization` «organización indicada por la editorial» → Organization | 2 mentions; publisher-asserted, a control, not a reference | sure | — |
| `ror.organization` row | **`afiliaciones:Organization`** «Organización de investigación» | 146,716 rows, all countries and statuses | sure | — |
| `ror.organization.status` | `afiliaciones:status` «estado en ROR» | active, inactive, withdrawn | sure | — |
| `ror.name` (types other than acronym only) | `afiliaciones:name` «nombre» | display names, labels and aliases, any language | sure | — |
| `ror.name` (types including acronym) | `afiliaciones:acronym` «sigla» | 65,412 acronyms; some shared by several organizations | sure | — |
| `ror.location.country_code` | `afiliaciones:country` «país (código ISO)» | every location kept; 142 organizations have several | sure | — |
| `ror.location` where `country_code = 'AR'` | **`afiliaciones:ArgentineOrganization`** «Organización argentina», subclass of Organization | the approved definition: any ROR location in Argentina; 538 | sure | — |
| `ror.relationship` where `type = 'parent'` | `afiliaciones:hasParent` «depende de» → Organization | 30,807 parent links; shown for explanation, never used to add credit | sure | — |
| `rastro_meta.source` (crossref, ror) | `afiliaciones:DataSource`, and `prov:wasDerivedFrom` on every Publication, Mention and Organization | as in the other domains | sure | — |

## Identifiers in the IRIs

- **Publication:** `https://doi.org/{doi}`, the DOI's own resolver address.
- **Organization:** the ROR identifier itself (`https://ror.org/00xpayr72`), so any tool that knows ROR understands it.
- **Mention:** `https://w3id.org/rastro/afiliaciones/mention/{doi}/{author_position}/{affiliation_position}`.

## Not mapped (not needed by the questions)

Authors' names, journal, publisher, publication date, ROR organization types and founding year, the other
relationship types (child, related, predecessor, successor) and city. `child` is the inverse of `parent`, so it
adds nothing.

## Differences from the semantic-layer proposal

- **`ArgentineOrganization` as a class** instead of only a country value, so the questions say «organización
  argentina» directly; it is the approved definition, mapped from every location.
- **`acronym` separate from `name`,** because shared acronyms need their own evidence rule in `link-entities`.
- **Only `hasParent` among the relationships:** enough to explain and to check suspected gaps; no closure is
  needed, since parents get no credit.

## Checks after mapping

Ontop of the domain starts and is healthy; `ontology-check` passes in every domain; counts in Rastro equal the
tables (100 publications, 1,456 mentions, 146,716 organizations, 538 Argentine); no `rdfs:domain` on shared
properties (`name` and `status` could be shared later, so they get none).
