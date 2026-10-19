"""Busca en GLEIF el LEI de las matrices y de los proveedores que más facturan.

Lee los nombres de USAspending (cargado antes): las matrices actuales con contratos por
MIN_GROUP_AMOUNT o más y los proveedores que más facturan (TOP_PROVIDERS). Cada nombre se busca con
filter[fulltext], que también mira nombres anteriores (Leidos aparece al buscar
SCIENCE APPLICATIONS INTERNATIONAL CORPORATION), y se guardan los primeros 5
candidatos con su matriz final (include=ultimate-parent). No se decide el enlace:
eso es la Fase P2.

La API pide no pasar de 60 consultas por minuto. Cada respuesta se guarda en
data/raw/gleif/ y no se vuelve a pedir, así que la descarga es reanudable.

Se corre con: docker compose run --rm gleif-loader
"""

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import requests
from requests.adapters import HTTPAdapter, Retry

API = "https://api.gleif.org/api/v1/lei-records"
CACHE = Path("/data/raw/gleif")
TOP_PROVIDERS = 1000
MIN_GROUP_AMOUNT = 50_000_000  # grupos con contratos por US$50 millones o más: el 98 % del monto
CANDIDATES = 5
PAUSE = 1.05  # 60 consultas por minuto como máximo

http = requests.Session()
http.headers["User-Agent"] = "RastroMVP/0.1"
http.mount("https://", HTTPAdapter(max_retries=Retry(total=4, backoff_factor=5, backoff_max=30,
                                                     status_forcelist=[429, 500, 502, 503, 504])))


def search(name):
    """La respuesta de GLEIF para un nombre, o None si sigue fallando (se reintenta en la próxima corrida)."""
    f = CACHE / f"{hashlib.sha1(name.encode()).hexdigest()}.json"
    if not f.exists():
        time.sleep(PAUSE)
        try:
            r = http.get(API, timeout=60, params={
                "filter[fulltext]": name, "page[size]": CANDIDATES, "include": "ultimate-parent"})
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  sin respuesta para {name!r}: {e}")
            return None
        f.write_text(json.dumps({"name": name, "fetched_at": datetime.now(timezone.utc).isoformat(),
                                 "response": r.json()}))
    return json.loads(f.read_text())


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
        names = dict(conn.execute("""
            SELECT r.parent_name, 'matriz' FROM usaspending.contract c JOIN usaspending.recipient r USING (recipient_id)
            WHERE r.parent_name IS NOT NULL GROUP BY r.parent_name HAVING sum(c.amount) >= %s""",
                                  (MIN_GROUP_AMOUNT,)).fetchall())
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
        if n % 250 == 0:
            print(f"  {n}/{len(names)}")
    if failed:
        print(f"{failed} nombres sin respuesta de GLEIF: corré de nuevo el cargador para completarlos.")
    # Matrices finales que no vinieron completas en la respuesta
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
                            ("lei_record", list(records.values()))):
            with conn.cursor().copy(f"COPY gleif.{table} FROM STDIN") as copy:
                for row in rows:
                    copy.write_row(row)
            conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                         "VALUES ('gleif', %s, %s, %s)",
                         (f"golden copy del {published}", f"gleif.{table}", len(rows)))
            print(f"  gleif.{table:<12}{len(rows):>8} filas")


if __name__ == "__main__":
    main()
