"""Traceability of 30 answer cells, scored per approach with the approved rubric (change-test-proposal.md).

Cells: 30 identified (affiliation, organization) cells of cq1, drawn with random.Random(20261022).sample over the
cells sorted by DOI, author position, affiliation position and ROR identifier. A cell is traceable for an approach if
what that approach returns or keeps as evidence gives (1) the Crossref record (DOI and positions), (2) the ROR record
and (3) the rule that joined them. Read-only. Run in the layer-eval service:
python /layer/afiliaciones/cambio/trazabilidad.py. Writes trazabilidad.json next to it.
"""
import json
import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, "/layer")
from answer import DOMAINS, READER, run_sparql_table  # noqa: E402

import os  # noqa: E402

import psycopg  # noqa: E402

HERE = Path(__file__).parent
DOMAIN = "afiliaciones"
CROSSREF, ROR = "https://w3id.org/rastro/source/crossref", "https://w3id.org/rastro/source/ror"


def cells():
    columns, rows = run_sparql_table(Path("/ontology/afiliaciones/queries/cq1.rq").read_text(), DOMAIN)
    found = {(r["doi"], int(r["authorPosition"]), int(r["affiliationPosition"]), r["organization"])
             for r in (dict(zip(columns, row)) for row in rows) if r["organization"]}
    return random.Random(20261022).sample(sorted(found), 30)


def with_rastro(cell):
    doi, author, position, org = cell
    _, rows = run_sparql_table(f"""
        PREFIX afiliaciones: <https://w3id.org/rastro/afiliaciones#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        SELECT ?rule ?source WHERE {{
          ?i a afiliaciones:Identification ; afiliaciones:identifies <{org}> ; afiliaciones:ofMention ?m ;
             afiliaciones:rule ?rule ; prov:wasDerivedFrom ?source .
          ?m afiliaciones:authorPosition {author} ; afiliaciones:affiliationPosition {position} ;
             afiliaciones:inPublication/afiliaciones:doi "{doi}" .
        }}""", DOMAIN)
    sources = {r[1] for r in rows}
    rule = next((r[0] for r in rows if r[0]), None)
    return {"traceable": bool(rule) and {CROSSREF, ROR} <= sources, "rule": rule, "sources": sorted(sources)}


def with_links(cell, conn):
    doi, author, position, org = cell
    row = conn.execute("""
        SELECT i.rule, a.name IS NOT NULL, o.id IS NOT NULL FROM afiliaciones.identificacion i
        JOIN crossref.affiliation a USING (doi, author_position, affiliation_position)
        JOIN ror.organization o ON o.id = i.organization
        WHERE i.doi = %s AND i.author_position = %s AND i.affiliation_position = %s AND i.organization = %s""",
                       (doi, author, position, org)).fetchone()
    return {"traceable": bool(row and row[0] and row[1] and row[2]), "rule": row[0] if row else None}


def without_rastro(cell):
    """B keeps no link records: its saved answers are counts or identifier lists, with no record key or rule."""
    doi, _, _, org = cell
    returned = []
    for path in sorted((HERE.parent / "respuestas").glob("*-B.json")):
        answer = json.loads(path.read_text()).get("answer")
        if isinstance(answer, list) and (org in answer or doi in answer):
            returned.append(path.stem)
    return {"traceable": False, "returned_by": returned,
            "why": "the value can appear in an answer, but no saved answer gives its Crossref record and rule"}


def main():
    sample = cells()
    user = DOMAINS[DOMAIN]["readers"]["D"]
    with psycopg.connect(READER.format(user) % os.environ["PG_DB"]) as conn:
        scored = [{"cell": {"doi": c[0], "author": c[1], "affiliation": c[2], "organization": c[3]},
                   "C": with_rastro(c), "D": with_links(c, conn), "B": without_rastro(c)} for c in sample]
    totals = {a: sum(s[a]["traceable"] for s in scored) for a in "BDC"}
    (HERE / "trazabilidad.json").write_text(json.dumps(
        {"fecha": date.today().isoformat(), "cells": len(scored), "traceable": totals, "detail": scored},
        ensure_ascii=False, indent=1) + "\n")
    print(totals)


if __name__ == "__main__":
    main()
