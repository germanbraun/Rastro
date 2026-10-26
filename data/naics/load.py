"""Loads the Census NAICS 2022 sector hierarchy (2 to 6 digits).

The Census publishes it only as an Excel spreadsheet; it is read with the standard library
(an .xlsx is a zip with XML) so as not to add dependencies. A code's parent is
the same code with one digit less; the 3-digit codes that start with 31, 32 or 33
hang from the grouped sector "31-33" (likewise 44-45 and 48-49).

Run with: docker compose run --rm naics-loader
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import psycopg
import requests

URL = "https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx"
RAW = Path("/data/raw/naics/2-6_digit_2022_Codes.xlsx")
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_xlsx(path):
    """Rows of the first sheet, as lists of texts."""
    with zipfile.ZipFile(path) as z:
        shared = [("".join(t.text or "" for t in si.iter(f"{{{NS['x']}}}t")))
                  for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("x:si", NS)]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    for row in sheet.iter(f"{{{NS['x']}}}row"):
        values = []
        for c in row.findall("x:c", NS):
            v = c.find("x:v", NS)
            text = "" if v is None else v.text
            values.append(shared[int(text)] if c.get("t") == "s" else text)
        yield values


def main():
    if not RAW.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(URL, headers={"User-Agent": "RastroMVP/0.1"}, timeout=120)
        r.raise_for_status()
        RAW.write_bytes(r.content)

    sectors = {}
    for values in read_xlsx(RAW):
        if len(values) < 3 or not re.fullmatch(r"\d{2,6}|\d{2}-\d{2}", (values[1] or "").strip()):
            continue
        code, title = values[1].strip(), values[2].strip()
        sectors[code] = title

    # 2-digit sector each prefix belongs to: "31" -> "31-33"
    two = {}
    for code in sectors:
        if "-" in code:
            a, b = map(int, code.split("-"))
            two.update({str(n): code for n in range(a, b + 1)})
        elif len(code) == 2:
            two[code] = code

    rows = []
    for code, title in sectors.items():
        level = 2 if "-" in code else len(code)
        parent = None if level == 2 else (two[code[:2]] if level == 3 else code[:-1])
        rows.append((code, title, level, parent))

    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        with conn.cursor().copy("COPY naics.sector (code, title, level, parent_code) FROM STDIN") as copy:
            for row in sorted(rows, key=lambda r: r[2]):  # parents before children
                copy.write_row(row)
        n = conn.execute("""
            INSERT INTO naics.ancestor
            WITH RECURSIVE up(code, ancestor_code) AS (
                SELECT code, code FROM naics.sector
                UNION
                SELECT up.code, s.parent_code FROM up JOIN naics.sector s ON s.code = up.ancestor_code
                WHERE s.parent_code IS NOT NULL
            )
            SELECT code, ancestor_code FROM up""").rowcount
        for table, count in (("naics.sector", len(rows)), ("naics.ancestor", n)):
            conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                         "VALUES ('naics', 'NAICS 2022', %s, %s)", (table, count))
            print(f"  {table:<16}{count:>8} filas")


if __name__ == "__main__":
    main()
