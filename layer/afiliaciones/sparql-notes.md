# Notes for the assistant: research affiliations (Rastro, SPARQL)

Prefix: `PREFIX afiliaciones: <https://w3id.org/rastro/afiliaciones#>`. Ontop does not support `*` or `+` paths.

- **Publication** (`afiliaciones:Publication`): one of the 100 works of the set. Its IRI is `https://doi.org/<doi>`;
  `afiliaciones:doi` holds the DOI in lowercase.
- **Affiliation mention** (`afiliaciones:AffiliationMention`): one affiliation text of one author in one publication,
  as the publisher deposited it. `afiliaciones:inPublication` gives its publication, `afiliaciones:affiliationText` the
  raw text, `afiliaciones:authorPosition` and `afiliaciones:affiliationPosition` its place (from 0). The same text can
  appear in many mentions. `afiliaciones:suppliedOrganization` is the ROR organization the publisher added, when it did
  (only 2 mentions): a control, not proof.
- **Organization** (`afiliaciones:Organization`): every organization in ROR v2.15, any country or status. Its IRI is
  its ROR identifier (`https://ror.org/...`). `afiliaciones:name` holds display names, labels and aliases;
  `afiliaciones:acronym` its acronyms (several organizations can share one); `afiliaciones:status` is active, inactive
  or withdrawn; `afiliaciones:country` one ISO code per location; `afiliaciones:hasParent` its parent organizations.
- **Argentine organization** (`afiliaciones:ArgentineOrganization`): an organization with at least one ROR location in
  Argentina (538). The word "Argentina" in an affiliation text never decides it.
- **Parents never add credit:** a publication counts for an organization only if its text names it.
- **Identification** (`afiliaciones:Identification`): that a mention (`afiliaciones:ofMention`) names an Argentine
  organization (`afiliaciones:identifies`), with `afiliaciones:rule`, `afiliaciones:sourceText` (the evidence) and
  `afiliaciones:linkStatus` («rule» or «correction-accepted»). **These are what Rastro counts.** A mention can have
  several identifications, or none.
- **Doubtful candidate** (`afiliaciones:DoubtfulCandidate`): an organization a mention might name without enough
  evidence (`afiliaciones:candidate`, reason in `afiliaciones:sourceText`), with `afiliaciones:reviewDecision`
  («accept» or «reject»). Accepted ones are already identifications; doubtful candidates are never counted.
- **Possible gap** (`afiliaciones:PossibleGap`): a segment of a mention's text (`afiliaciones:segmentText`) that names
  an institution no Argentine ROR name covers. A candidate, not proof that ROR lacks it; it can appear in mentions
  that also have identifications.
