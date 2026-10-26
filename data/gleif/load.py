"""Looks up in GLEIF the LEI of the parent companies and of the suppliers that bill the most.

Reads the names from USAspending (loaded before): the current parent companies with contracts of
MIN_GROUP_AMOUNT or more and the suppliers that bill the most (TOP_PROVIDERS). Each name is searched with
filter[fulltext], which also looks at former names (Leidos shows up when searching
SCIENCE APPLICATIONS INTERNATIONAL CORPORATION), and the first 5 candidates are saved
with their ultimate parent (include=ultimate-parent). If no candidate matches
the name, it searches again with the normalized name (candidates 6 to 10) and, for the
groups of BIG_GROUP_AMOUNT or more, by legal name (candidates 11 to 20). Names that no
search finds can go, reviewed, in lei-revisados.csv: their LEI is requested directly. The link is not decided here:
that is Phase P2.

The API asks not to exceed 60 queries per minute. Each response is saved in
data/raw/gleif/ and is not requested again, so the download can be resumed.

Run with: docker compose run --rm gleif-loader
"""

import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import requests
from requests.adapters import HTTPAdapter, Retry

API = "https://api.gleif.org/api/v1/lei-records"
CACHE = Path("/data/raw/gleif")
TOP_PROVIDERS = 1000
MIN_GROUP_AMOUNT = 50_000_000  # groups with contracts of US$50 million or more: 98 % of the amount
BIG_GROUP_AMOUNT = 250_000_000  # third search, by legal name: groups of US$250 million or more (92 %)
CANDIDATES = 5
PAUSE = 1.05  # at most 60 queries per minute

http = requests.Session()
http.headers["User-Agent"] = "RastroMVP/0.1"
http.mount("https://", HTTPAdapter(max_retries=Retry(total=4, backoff_factor=5, backoff_max=30,
                                                     status_forcelist=[429, 500, 502, 503, 504])))


def search(name, by="fulltext", size=CANDIDATES):
    """GLEIF's response for a name, or None if it keeps failing (retried on the next run).
    by: "fulltext" (also looks at former names) or "entity.legalName" (by legal name)."""
    key = name if by == "fulltext" else f"{by}:{name}"
    f = CACHE / f"{hashlib.sha1(key.encode()).hexdigest()}.json"
    if not f.exists():
        time.sleep(PAUSE)
        try:
            r = http.get(API, timeout=60, params={
                f"filter[{by}]": name, "page[size]": size, "include": "ultimate-parent"})
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  sin respuesta para {name!r}: {e}")
            return None
        f.write_text(json.dumps({"name": name, "fetched_at": datetime.now(timezone.utc).isoformat(),
                                 "response": r.json()}))
    return json.loads(f.read_text())


# Company legal forms that do not tell one company from another (the same as proveedores.normalize)
LEGAL_FORMS = (r"\b(THE|INC|INCORPORATED|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|LP|LLP|PLC|PLLC|PC"
               r"|GMBH|AG|SA|NV|BV|SPA|SRL|SAS|PTY|SE)\b")


def normalize(name):
    """Upper case, no punctuation and no company legal forms: «Leonardo S.p.A.» → «LEONARDO»."""
    text = re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper().replace(".", "").replace("&", " AND "))
    return " ".join(re.sub(LEGAL_FORMS, " ", text).split())


def matches(name, x):
    """Does the record's legal name or a former name match the searched name?"""
    e = x["attributes"]["entity"]
    names = [e["legalName"]["name"]] + [o["name"] for o in e.get("otherNames") or []]
    return any(normalize(n) == normalize(name) for n in names)


def record(x):
    a = x["attributes"]
    e = a["entity"]
    parent = (x.get("relationships", {}).get("ultimate-parent", {}).get("data") or {})
    return (x["id"], e["legalName"]["name"], [n["name"] for n in e.get("otherNames") or []],
            e["legalAddress"].get("country"), e["legalAddress"].get("region"),
            (e.get("headquartersAddress") or {}).get("country"), (e.get("headquartersAddress") or {}).get("region"),
            e.get("jurisdiction"), e.get("status"),
            a["registration"].get("status"),
            parent.get("id") if parent.get("type") == "lei-records" else None)


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        totals = dict(conn.execute("""
            SELECT r.parent_name, sum(c.amount) FROM usaspending.contract c JOIN usaspending.recipient r USING (recipient_id)
            WHERE r.parent_name IS NOT NULL GROUP BY r.parent_name HAVING sum(c.amount) >= %s""",
                                   (MIN_GROUP_AMOUNT,)).fetchall())
        names = {name: "matriz" for name in totals}
        for (name,) in conn.execute("""
                SELECT r.name FROM usaspending.contract c JOIN usaspending.recipient r USING (recipient_id)
                WHERE r.name IS NOT NULL GROUP BY r.name ORDER BY sum(c.amount) DESC LIMIT %s""",
                                    (TOP_PROVIDERS,)):
            names.setdefault(name, "proveedor")

    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"Nombres a buscar: {len(names)} ({sum(k == 'matriz' for k in names.values())} matrices)")
    queries, candidates, records, published, failed = [], [], {}, "", 0
    for n, (name, kind) in enumerate(sorted(names.items()), 1):
        d = search(name)
        if d is None:
            failed += 1
            continue
        resp = d["response"]
        queries.append((name, kind, resp["meta"]["pagination"]["total"], d["fetched_at"]))
        published = max(published, resp["meta"]["goldenCopy"]["publishDate"][:10])
        for rank, x in enumerate(resp["data"], 1):
            candidates.append((name, rank, x["id"]))
            records[x["id"]] = record(x)
        for x in resp.get("included") or []:
            if x["type"] == "lei-records" and "attributes" in x:
                records.setdefault(x["id"], record(x))
        # If no candidate matches, a second search with the normalized name: the legal
        # form weighs in the search and hides the company («LEONARDO S.P.A.» brings other S.P.A.)
        found = list(resp["data"])
        extra = []
        if not any(matches(name, x) for x in found) and normalize(name) and normalize(name) != name:
            extra.append((search(normalize(name)), CANDIDATES + 1))
        # Third search, by legal name, only for the big groups that still have no
        # match: the full-text search does not find, for example, LEONARDO S.P.A. or BOMBARDIER INC
        so_far = found + [x for d2, _ in extra if d2 for x in d2["response"]["data"]]
        if totals.get(name, 0) >= BIG_GROUP_AMOUNT and not any(matches(name, x) for x in so_far):
            extra.append((search(name, by="entity.legalName", size=10), 2 * CANDIDATES + 1))
        for d2, first_rank in extra:
            if d2 is None:
                continue
            for rank, x in enumerate(d2["response"]["data"], first_rank):
                candidates.append((name, rank, x["id"]))
                records[x["id"]] = record(x)
            for x in d2["response"].get("included") or []:
                if x["type"] == "lei-records" and "attributes" in x:
                    records.setdefault(x["id"], record(x))
        if n % 250 == 0:
            print(f"  {n}/{len(names)}")
    if failed:
        print(f"{failed} nombres sin respuesta de GLEIF: corré de nuevo el cargador para completarlos.")
    # Reviewed LEIs: requested from GLEIF directly by their LEI
    reviewed = list(csv.DictReader(Path(__file__).with_name("lei-revisados.csv").open()))
    for row in reviewed:
        f = CACHE / f"lei-{row['lei']}.json"
        if not f.exists():
            time.sleep(PAUSE)
            r = http.get(f"{API}/{row['lei']}", timeout=120)
            r.raise_for_status()
            f.write_text(r.text)
        records[row["lei"]] = record(json.loads(f.read_text())["data"])
    # Ultimate parents that did not come complete in the response
    for lei in sorted({r[10] for r in records.values() if r[10]} - records.keys()):
        f = CACHE / f"lei-{lei}.json"
        if not f.exists():
            time.sleep(PAUSE)
            r = http.get(f"{API}/{lei}", timeout=120)
            r.raise_for_status()
            f.write_text(r.text)
        records[lei] = record(json.loads(f.read_text())["data"])

    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        for table, rows in (("name_query", queries), ("candidate", candidates),
                            ("lei_record", list(records.values())),
                            ("lei_reviewed", [(r["nombre"], r["lei"], r["motivo"]) for r in reviewed])):
            with conn.cursor().copy(f"COPY gleif.{table} FROM STDIN") as copy:
                for row in rows:
                    copy.write_row(row)
            conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                         "VALUES ('gleif', %s, %s, %s)",
                         (f"golden copy del {published}", f"gleif.{table}", len(rows)))
            print(f"  gleif.{table:<12}{len(rows):>8} filas")


if __name__ == "__main__":
    main()
