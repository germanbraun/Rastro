-- The afiliaciones links: which Argentine organizations each affiliation mention names, with rule and evidence.
-- Rebuilt on every run (link.py fills the tables with the approved rules: docs/experiments/research-affiliations/
-- link-proposal.md). Nothing here is a source: it can always be rebuilt from crossref.* and ror.*.
DROP SCHEMA IF EXISTS afiliaciones CASCADE;
CREATE SCHEMA afiliaciones;

-- One row per mention and Argentine organization it names. status: 'rule' (R0, R1, R2) or 'correction-accepted';
-- Rastro's answers count both. Rejected corrections stay in afiliaciones.dudosa with their decision.
CREATE TABLE afiliaciones.identificacion (
    doi text, author_position int, affiliation_position int,
    organization text,                   -- the ROR identifier
    rule text,                           -- the rule in words
    evidence text,                       -- the values from each source that justify it
    status text,
    PRIMARY KEY (doi, author_position, affiliation_position, organization)
);

-- Doubtful candidates: a full name without a second piece of evidence, or a shared acronym, or an acronym without a
-- second piece of evidence. They become identifications only through linking/afiliaciones/correcciones.csv.
CREATE TABLE afiliaciones.dudosa (
    doi text, author_position int, affiliation_position int, organization text,
    reason text, decision text, decision_reason text,
    PRIMARY KEY (doi, author_position, affiliation_position, organization)
);

-- Mentions that contain "Argentina" and have no accepted identification: unresolved for cq1, candidates for cq3.
CREATE TABLE afiliaciones.sin_identificar (
    doi text, author_position int, affiliation_position int, text text, reason text,
    PRIMARY KEY (doi, author_position, affiliation_position)
);
