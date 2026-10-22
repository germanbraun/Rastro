"""Load the research-affiliations sources: the bounded set of Crossref works and the ROR v2.15 release.

The inputs are the approved snapshots, not fresh downloads: Crossref is a live API, so a new request would be a new
snapshot. Both files are checked against their approved fingerprints; if they are missing or different, the load
stops. To produce them: docs/experiments/research-affiliations/fetch.py, then draw.py (see their docstrings).

Run with: docker compose run --rm afiliaciones-loader
"""

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun import copiar  # noqa: E402

RAW = Path("/data/raw/research-affiliations")
SAMPLE = RAW / "sample-100.json"
SAMPLE_SHA256 = "707ec8cc38e325d9edada4b4e375146208e86a527e28e06a5f12e77e2c402e76"
ROR_ZIP = RAW / "ror-v2.15.zip"
ROR_MD5 = "5522990688eb1b94811a8145e131b41e"


def check(path, algorithm, expected):
    if not path.exists():
        raise SystemExit(f"Missing {path}: run fetch.py and draw.py from docs/experiments/research-affiliations/")
    h = hashlib.new(algorithm, path.read_bytes()).hexdigest()
    if h != expected:
        raise SystemExit(f"{path} is not the approved snapshot ({algorithm} {h}); do not load another one")


def crossref_rows(works):
    work_rows, affiliation_rows = [], []
    for w in works:
        parts = (w.get("issued", {}).get("date-parts") or [[None]])[0]
        work_rows.append((w["DOI"].lower(), (w.get("container-title") or [None])[0], w.get("publisher"),
                          w.get("member"), ", ".join(w.get("ISSN", [])) or None,
                          "-".join(str(p) for p in parts if p is not None) or None))
        for i, a in enumerate(w.get("author", [])):
            for j, f in enumerate(a.get("affiliation", [])):
                ror = next((x for x in f.get("id", []) if x.get("id-type") == "ROR"), {})
                affiliation_rows.append((w["DOI"].lower(), i, j, a.get("given"), a.get("family"), f.get("name"),
                                         ror.get("id"), ror.get("asserted-by")))
    return work_rows, affiliation_rows


def ror_rows():
    with zipfile.ZipFile(ROR_ZIP) as z:
        records = json.loads(z.read(next(n for n in z.namelist() if n.endswith(".json"))))
    orgs, names, relations = [], [], []
    for r in records:
        place = (r.get("locations") or [{}])[0].get("geonames_details", {})
        orgs.append((r["id"], r.get("status"), ",".join(r.get("types", [])), r.get("established"),
                     place.get("country_code"), place.get("country_name"), place.get("name")))
        names += [(r["id"], n["value"], ",".join(n.get("types", [])), n.get("lang")) for n in r.get("names", [])]
        relations += [(r["id"], x["type"], x["id"], x.get("label")) for x in r.get("relationships", [])]
    return orgs, names, relations


def main():
    check(SAMPLE, "sha256", SAMPLE_SHA256)
    check(ROR_ZIP, "md5", ROR_MD5)
    works = json.loads(SAMPLE.read_text())
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        conn.execute("""
            INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
              ('crossref', 'Crossref works metadata (2025 journal articles, bounded set of 100)',
               'https://www.crossref.org/documentation/retrieve-metadata/rest-api/',
               'Public domain (CC0) for factual metadata; abstracts not used', 'crossref'),
              ('ror', 'Research Organization Registry, data dump v2.15', 'https://ror.org/', 'CC0 1.0', 'ror')
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, license = EXCLUDED.license""")
        conn.execute("TRUNCATE crossref.work, crossref.affiliation, ror.organization, ror.name, ror.relationship")
        work_rows, affiliation_rows = crossref_rows(works)
        version = f"capture 9d328bbe, sample {SAMPLE_SHA256[:12]}"
        copiar(conn, "crossref.work", work_rows, "crossref", version, archivo=SAMPLE)
        copiar(conn, "crossref.affiliation", affiliation_rows, "crossref", version, archivo=SAMPLE)
        orgs, names, relations = ror_rows()
        copiar(conn, "ror.organization", orgs, "ror", "v2.15 (2026-10-20)", archivo=ROR_ZIP)
        copiar(conn, "ror.name", names, "ror", "v2.15 (2026-10-20)", archivo=ROR_ZIP)
        copiar(conn, "ror.relationship", relations, "ror", "v2.15 (2026-10-20)", archivo=ROR_ZIP)


if __name__ == "__main__":
    main()
