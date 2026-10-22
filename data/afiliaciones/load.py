"""Load the research-affiliations sources: the bounded set of Crossref works and the ROR v2.15 release.

The inputs are the approved snapshots, not fresh downloads: Crossref is a live API, so a new request would be a new
snapshot. Both files are checked against their approved fingerprints; if they are missing or different, the load
stops. To produce them: docs/experiments/research-affiliations/fetch.py, then draw.py (see their docstrings).

After a successful load (the transaction committed), the loader rewrites the domain's source manifest
(layer/afiliaciones/sources.yaml) from what it actually loaded: fingerprints, versions and row counts. A failed load
leaves the manifest as it was. Only the first publisher ROR identifier per affiliation is kept; the sample has none
with several.

Run with: docker compose run --rm afiliaciones-loader
"""

import hashlib
import json
import os
import sys
import zipfile
from datetime import date
from pathlib import Path

import psycopg
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun import copiar  # noqa: E402

RAW = Path("/data/raw/research-affiliations")
SAMPLE = RAW / "sample-100.json"
SAMPLE_SHA256 = "707ec8cc38e325d9edada4b4e375146208e86a527e28e06a5f12e77e2c402e76"
ROR_ZIP = RAW / "ror-v2.15.zip"
ROR_MD5 = "5522990688eb1b94811a8145e131b41e"
DOIS = Path("/data/doi-list/sample-dois.txt")
MANIFEST = Path("/manifest/sources.yaml")


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
    orgs, locations, names, relations = [], [], [], []
    for r in records:
        place = (r.get("locations") or [{}])[0].get("geonames_details", {})
        orgs.append((r["id"], r.get("status"), ",".join(r.get("types", [])), r.get("established"),
                     place.get("country_code"), place.get("country_name"), place.get("name")))
        for k, loc in enumerate(r.get("locations", [])):
            g = loc.get("geonames_details", {})
            locations.append((r["id"], k, str(loc.get("geonames_id") or ""), g.get("country_code"), g.get("country_name"),
                              g.get("name")))
        names += [(r["id"], n["value"], ",".join(n.get("types", [])), n.get("lang")) for n in r.get("names", [])]
        relations += [(r["id"], x["type"], x["id"], x.get("label")) for x in r.get("relationships", [])]
    return orgs, locations, names, relations


def main():
    check(SAMPLE, "sha256", SAMPLE_SHA256)
    check(ROR_ZIP, "md5", ROR_MD5)
    works = json.loads(SAMPLE.read_text())
    counts = {}
    with psycopg.connect(host="postgres", port=5432, dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
                         password=os.environ["PG_PASSWORD"]) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        conn.execute("""
            INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
              ('crossref', 'Crossref works metadata (2025 journal articles, bounded set of 100)',
               'https://www.crossref.org/documentation/retrieve-metadata/rest-api/',
               'Public domain (CC0) for factual metadata; abstracts not used', 'crossref'),
              ('ror', 'Research Organization Registry, data dump v2.15', 'https://ror.org/', 'CC0 1.0', 'ror')
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, license = EXCLUDED.license""")
        conn.execute("TRUNCATE crossref.work, crossref.affiliation, ror.organization, ror.location, ror.name, "
                     "ror.relationship")
        work_rows, affiliation_rows = crossref_rows(works)
        version = f"capture 9d328bbe, sample {SAMPLE_SHA256[:12]}"
        orgs, locations, names, relations = ror_rows()
        for table, rows, source, ver, path in [
                ("crossref.work", work_rows, "crossref", version, SAMPLE),
                ("crossref.affiliation", affiliation_rows, "crossref", version, SAMPLE),
                ("ror.organization", orgs, "ror", "v2.15 (2026-10-20)", ROR_ZIP),
                ("ror.location", locations, "ror", "v2.15 (2026-10-20)", ROR_ZIP),
                ("ror.name", names, "ror", "v2.15 (2026-10-20)", ROR_ZIP),
                ("ror.relationship", relations, "ror", "v2.15 (2026-10-20)", ROR_ZIP)]:
            copiar(conn, table, rows, source, ver, archivo=path)
            counts[table] = len(rows)
    write_manifest(counts)   # only reached after the transaction committed


def write_manifest(counts):
    """The source manifest, from what this load actually used; changing it invalidates downstream checks."""
    today = date.today().isoformat()
    manifest = {
        "crossref": {
            "description": 'Crossref works: the 100 works drawn from 2025 journal articles with "Argentina" in an affiliation',
            "capture_sha256": "9d328bbe41ad3ba27092cf08532a70007e38f5ec4aca4cb389d7c8ed6428e526",
            "ledger": "docs/experiments/research-affiliations/crossref-ledger-inspector.json",
            "doi_list": "docs/experiments/research-affiliations/sample-dois.txt",
            "doi_list_sha256": hashlib.sha256(DOIS.read_bytes()).hexdigest(),
            "loaded_file": SAMPLE.name, "loaded_sha256": SAMPLE_SHA256,
            "terms": "public domain (CC0) for factual metadata; abstracts not used",
            "loaded": today, "tables": {k: v for k, v in counts.items() if k.startswith("crossref.")}},
        "ror": {
            "description": "Research Organization Registry data dump", "version": "v2.15",
            "release": "https://zenodo.org/records/23500708", "md5": ROR_MD5,
            "loaded_sha256": hashlib.sha256(ROR_ZIP.read_bytes()).hexdigest(), "terms": "CC0 1.0",
            "loaded": today, "tables": {k: v for k, v in counts.items() if k.startswith("ror.")}},
    }
    MANIFEST.write_text("# Source manifest, written by data/afiliaciones/load.py after a successful load.\n"
                        "# A change here invalidates implemented and validated questions.\n"
                        + yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
