#!/usr/bin/env bash
# Builds the blind reviewer's package from the two sources as loaded (crossref, ror): nothing from Rastro's schema,
# links, mappings or answers. Run from the repo root with the stack up:
#   docs/experiments/research-affiliations/blind-review/build.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
psql() { docker compose exec -T postgres psql -U rastro -v ON_ERROR_STOP=1 -q "$@"; }

# Every distinct raw affiliation string of the 100 works, with an id stable under sorting. «full» marks the 196
# strings whose text contains «argentin» (accents and case ignored, as in profile.py); the other 766 are screened.
psql -c "\copy (
  SELECT 's' || lpad(row_number() OVER (ORDER BY name)::text, 3, '0') AS string_id,
         CASE WHEN lower(translate(name, 'ÁÉÍÓÚáéíóúÜü', 'AEIOUaeiouUu')) LIKE '%argentin%' THEN 'full' ELSE 'screen' END AS review,
         mentions, name AS text
  FROM (SELECT name, count(*) AS mentions FROM crossref.affiliation WHERE name IS NOT NULL GROUP BY name) s
  ORDER BY name) TO STDOUT WITH CSV HEADER" > "$HERE/strings.csv"

# The 538 organizations with at least one ROR v2.15 location in Argentina: every name with its types, and their
# relationships (a parent does not receive its institutes' mentions; successors explain renamed organizations).
psql -c "\copy (
  SELECT o.id, o.status, o.types, o.city,
         string_agg(DISTINCT n.value || ' [' || n.types || ']', ' | ') AS names,
         (SELECT string_agg(r.type || ': ' || r.related_id || ' ' || r.label, ' | ' ORDER BY r.type, r.related_id)
            FROM ror.relationship r WHERE r.id = o.id) AS relationships
  FROM ror.organization o JOIN ror.name n ON n.id = o.id
  WHERE o.id IN (SELECT id FROM ror.location WHERE country_code = 'AR')
  GROUP BY o.id, o.status, o.types, o.city ORDER BY o.id) TO STDOUT WITH CSV HEADER" > "$HERE/ror-argentina.csv"

# Each of the 1,456 mentions with its string, so the references can be derived from the annotation (reference.py)
psql -c "\copy (SELECT doi, author_position, affiliation_position, name AS text FROM crossref.affiliation
  WHERE name IS NOT NULL ORDER BY doi, author_position, affiliation_position) TO STDOUT WITH CSV HEADER" > "$HERE/mentions.csv"

wc -l "$HERE/strings.csv" "$HERE/ror-argentina.csv" "$HERE/mentions.csv"
shasum -a 256 "$HERE/strings.csv" "$HERE/ror-argentina.csv" "$HERE/mentions.csv"
