"""Loads trade.gov's Consolidated Screening List (a ~16 MB CSV).

The day's file is saved in data/raw/csl/ and loaded whole: there are about 26,000
entries, and the suppliers are compared against all of them in Phase P2.

Run with: docker compose run --rm csl-loader
"""

import csv
import io
import os
import re
from datetime import date
from pathlib import Path

import psycopg
import requests

URL = "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv"
RAW = Path("/data/raw/csl")


def split(text):
    return [x.strip() for x in (text or "").split(";") if x.strip()]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"consolidated-{date.today()}.csv"
    if not path.exists():
        r = requests.get(URL, headers={"User-Agent": "RastroMVP/0.1"}, timeout=300)
        r.raise_for_status()
        path.write_bytes(r.content)

    rows = {}
    for d in csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8-sig"))):
        # The country is the last element of each address: "Havana, CU"
        last = (a.rsplit(",", 1)[-1].strip() for a in split(d["addresses"]))
        countries = sorted({c for c in last if re.fullmatch(r"[A-Z]{2}", c)})
        rows[d["_id"], d["source"]] = (d["_id"], d["source"], d["type"] or None, d["name"], split(d["alt_names"]),
                          countries, d["programs"] or None, d["addresses"] or None, d["ids"] or None,
                          d["start_date"] or None, d["source_list_url"] or None)

    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        with conn.cursor().copy("COPY csl.entry FROM STDIN") as copy:
            for row in rows.values():
                copy.write_row(row)
        conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                     "VALUES ('csl', %s, 'csl.entry', %s)", (f"archivo del {path.stem[-10:]}", len(rows)))
        print(f"  csl.entry       {len(rows):>8} filas")
        for source, n in conn.execute("SELECT source, count(*) FROM csl.entry GROUP BY 1 ORDER BY 2 DESC"):
            print(f"    {n:>6}  {source}")


if __name__ == "__main__":
    main()
