-- Research affiliations: two sources, one schema each, with the sources' own field names where they exist.
-- No DROP: the linker can run this to create empty tables; the loader empties them before loading.

-- Crossref: the 100 works of the bounded set (docs/experiments/research-affiliations/sample-dois.txt).
CREATE SCHEMA IF NOT EXISTS crossref;
CREATE TABLE IF NOT EXISTS crossref.work (
    doi text PRIMARY KEY,                -- lowercase, as in the DOI list
    container_title text, publisher text, member text, issn text,
    issued text                          -- the date parts as published (year, month, day when present)
);
-- One row per author-affiliation occurrence. Author position identifies an occurrence, not a person.
CREATE TABLE IF NOT EXISTS crossref.affiliation (
    doi text, author_position int, affiliation_position int,
    author_given text, author_family text,
    name text,                           -- the affiliation text as deposited, kept raw
    ror_id text, asserted_by text,       -- a ROR identifier when the publisher supplied one
    PRIMARY KEY (doi, author_position, affiliation_position)
);

-- ROR: the full data dump v2.15 (all countries and statuses), for identification and gap searches.
CREATE SCHEMA IF NOT EXISTS ror;
CREATE TABLE IF NOT EXISTS ror.organization (
    id text PRIMARY KEY, status text, types text, established int,
    country_code text, country_name text, city text   -- the first listed location, for display only
);
-- Every location as ROR lists it: "Argentine" means any location in Argentina, not only the first.
CREATE TABLE IF NOT EXISTS ror.location (
    id text, position int, geonames_id text, country_code text, country_name text, city text,
    PRIMARY KEY (id, position)
);
CREATE TABLE IF NOT EXISTS ror.name (id text, value text, types text, lang text);
CREATE TABLE IF NOT EXISTS ror.relationship (id text, type text, related_id text, label text);
