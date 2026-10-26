"""Downloads from USAspending the contracts in scope and the profile of each supplier.

Scope: contracts (award_type_codes A, B, C, D) with activity in fiscal year 2025
(Oct 2024 to Sep 2025) and an amount of more than US$10 million; about 36,000 of them.

1. Contracts: POST /api/v2/search/spending_by_award/ 100 at a time, sorted by amount.
   Each page is saved in data/raw/usaspending/awards/.
2. Suppliers: GET /api/v2/recipient/{recipient_id}/ for each distinct supplier;
   it brings the current parent and the "parents" list with the parents it had. Each response
   is saved in data/raw/usaspending/recipient/ and is not requested again.

Both downloads can be resumed. To download the contracts again, delete the awards/ folder.

Run with: docker compose run --rm usaspending-loader
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg
import requests
from requests.adapters import HTTPAdapter, Retry

API = "https://api.usaspending.gov/api/v2"
CACHE = Path("/data/raw/usaspending")
FILTERS = {
    "award_type_codes": ["A", "B", "C", "D"],
    "time_period": [{"start_date": "2024-10-01", "end_date": "2025-09-30"}],
    "award_amounts": [{"lower_bound": 10_000_000}],
}
FIELDS = ["Award ID", "Contract Award Type", "Recipient Name", "Recipient UEI", "recipient_id",
          "Awarding Agency", "Awarding Sub Agency", "NAICS", "Award Amount", "Start Date", "End Date",
          "Description"]

PAUSE = 0.3

http = requests.Session()
http.mount("https://", HTTPAdapter(pool_maxsize=4, max_retries=Retry(
    total=10, backoff_factor=2, backoff_max=30, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=None)))


def download_page(page):
    f = CACHE / "awards" / f"page-{page:04d}.json"
    if not f.exists():
        r = http.post(f"{API}/search/spending_by_award/", timeout=300, json={
            "filters": FILTERS, "fields": FIELDS, "limit": 100, "page": page,
            "sort": "Award Amount", "order": "desc"})
        r.raise_for_status()
        f.write_text(r.text)


def download_awards():
    """Pages are requested 4 at a time in parallel: each one takes several seconds."""
    (CACHE / "awards").mkdir(parents=True, exist_ok=True)
    r = http.post(f"{API}/search/spending_by_award_count/", json={"filters": FILTERS}, timeout=120)
    r.raise_for_status()
    total = r.json()["results"]["contracts"]
    pages = range(1, (total + 99) // 100 + 1)
    print(f"  {total} contratos en {len(pages)} páginas")
    with ThreadPoolExecutor(4) as pool:
        for n, _ in enumerate(pool.map(download_page, pages), 1):
            if n % 50 == 0:
                print(f"  contratos: página {n}/{len(pages)}")
    return total


def download_recipient(recipient_id):
    """The supplier's profile, or None if the API keeps failing (retried on the next run)."""
    f = CACHE / "recipient" / f"{recipient_id}.json"
    if not f.exists():
        time.sleep(PAUSE)
        try:
            r = http.get(f"{API}/recipient/{recipient_id}/", timeout=120)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  sin perfil para {recipient_id}: {e}")
            return None
        f.write_text(r.text)
    return json.loads(f.read_text())


def main():
    print("Descargando contratos...")
    total = download_awards()
    contracts = {}
    for f in sorted((CACHE / "awards").glob("page-*.json")):
        for a in json.loads(f.read_text())["results"]:
            naics = a["NAICS"] or {}
            contracts[a["generated_internal_id"]] = (
                a["generated_internal_id"], a["Award ID"], a["Contract Award Type"], a["recipient_id"],
                a["Recipient Name"], a["Recipient UEI"], a["Awarding Agency"], a["Awarding Sub Agency"],
                naics.get("code"), naics.get("description"), a["Award Amount"], a["Start Date"],
                a["End Date"], a["Description"])
    print(f"  {len(contracts)} contratos distintos de {total}")

    ids = sorted({c[3] for c in contracts.values() if c[3]})
    (CACHE / "recipient").mkdir(parents=True, exist_ok=True)
    pending = [i for i in ids if not (CACHE / "recipient" / f"{i}.json").exists()]
    print(f"Proveedores: {len(ids)}, por descargar: {len(pending)}")
    with ThreadPoolExecutor(2) as pool:  # with more threads the API cuts connections
        for n, _ in enumerate(pool.map(download_recipient, pending), 1):
            if n % 500 == 0:
                print(f"  perfiles: {n}/{len(pending)}")

    missing = [i for i in ids if not (CACHE / "recipient" / f"{i}.json").exists()]
    if missing:
        print(f"Faltan {len(missing)} perfiles: corré de nuevo el cargador para completarlos.")
    recipients, parents = [], []
    for i in ids:
        if i in missing:
            continue
        d = download_recipient(i)
        loc = d.get("location") or {}
        recipients.append((i, d["name"], d.get("alternate_names") or [], d["uei"], d["duns"],
                           d["recipient_level"], d["parent_id"], d["parent_name"], d["parent_uei"],
                           d["parent_duns"], loc.get("city_name"), loc.get("state_code"),
                           loc.get("country_code"), d.get("business_types") or []))
        seen = set()
        for p in d.get("parents") or []:
            if p["parent_id"] and p["parent_id"] not in seen:
                seen.add(p["parent_id"])
                parents.append((i, p["parent_id"], p["parent_name"], p["parent_uei"], p["parent_duns"]))

    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    version = "año fiscal 2025, contratos > US$10 millones"
    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        for table, rows in (("contract", contracts.values()), ("recipient", recipients),
                            ("recipient_parent", parents)):
            rows = list(rows)
            with conn.cursor().copy(f"COPY usaspending.{table} FROM STDIN") as copy:
                for row in rows:
                    copy.write_row(row)
            conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                         "VALUES ('usaspending', %s, %s, %s)", (version, f"usaspending.{table}", len(rows)))
            print(f"  usaspending.{table:<18}{len(rows):>8} filas")


if __name__ == "__main__":
    main()
