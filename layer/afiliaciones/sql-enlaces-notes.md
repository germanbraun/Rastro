# Notes for the assistant: research affiliations (SQL over the sources plus Rastro's links)

- `crossref.work` (`doi`, `container_title`, `publisher`, `member`, `issn`, `issued`): the 100 works of the set, one
  row each; `doi` in lowercase.
- `crossref.affiliation` (`doi`, `author_position`, `affiliation_position`, `author_given`, `author_family`, `name`,
  `ror_id`, `asserted_by`): one row per affiliation text of one author in one work, as the publisher deposited it
  (`name` is the raw text). Positions start at 0. The same text can appear in many rows. `ror_id` is the ROR
  organization the publisher added, when it did (only 2 rows): a control, not proof.
- `ror.organization` (`id`, `status`, `types`, `established`, `country_code`, `country_name`, `city`): every
  organization in ROR v2.15, any country or status; `id` is the ROR identifier (`https://ror.org/...`); the location
  columns are only the first location.
- `ror.name` (`id`, `value`, `types`, `lang`): every name of an organization; `types` lists one or more of
  `ror_display`, `label`, `alias`, `acronym` separated by commas. Several organizations can share an acronym.
- `ror.location` (`id`, `position`, `geonames_id`, `country_code`, `country_name`, `city`): every location.
- `ror.relationship` (`id`, `type`, `related_id`, `label`): `type = 'parent'` gives an organization's parents.
- **Argentine organization:** an organization with at least one row in `ror.location` with `country_code = 'AR'`
  (538). The word "Argentina" in an affiliation text never decides it.
- **Parents never add credit:** a work counts for an organization only if its text names it.
- Which organizations an affiliation names (Rastro's identifications, with their rule and evidence) is not built yet.
