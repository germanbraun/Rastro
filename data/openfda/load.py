"""Descarga de openFDA los eventos adversos agregados de los fármacos del recorte.

Fármacos = familias de ChEMBL (esquema `chembl`, cargado antes) que tienen UNII.
Por familia se consultan, buscando por sus UNII en patient.drug.openfda.unii:
reportes por día (todos, serios y con muerte), agregados luego por año, y las
100 reacciones más reportadas. El UNII matchea el fármaco en cualquier rol del reporte
(sospechoso o concomitante): openFDA no permite exigir ambas condiciones sobre el
mismo fármaco del reporte.

Cada respuesta se guarda en data/raw/openfda/<familia>.json y no se vuelve a pedir,
así que la descarga es reanudable. Sin OPENFDA_API_KEY el límite es 1000 requests
por día: el script se detiene al llegar, carga lo que haya y sigue en la próxima corrida.

Se corre con: docker compose run --rm openfda-loader
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import requests
from requests.adapters import HTTPAdapter, Retry

API = "https://api.fda.gov/drug/event.json"
CACHE = Path("/data/raw/openfda")
API_KEY = os.environ.get("OPENFDA_API_KEY") or None
PAUSE = 0.3  # 240 requests/minuto como máximo, con o sin key
TOP_REACTIONS = 100  # máximo sin key; fijo para que el caché sea homogéneo con o sin key

http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2,
                                                     status_forcelist=[500, 502, 503, 504])))


class DailyLimit(Exception):
    pass


def query(search, **params):
    """Devuelve (results, meta), o (None, None) si no hay reportes que coincidan."""
    if API_KEY:
        params["api_key"] = API_KEY
    time.sleep(PAUSE)
    r = http.get(API, params={"search": search, **params}, timeout=120)
    if r.status_code == 404:
        return None, None
    if r.status_code == 429:
        raise DailyLimit()
    r.raise_for_status()
    data = r.json()
    return data["results"], data["meta"]


def fetch(uniis):
    # Espacios y no "+": requests codifica "+" como %2B y openFDA lo toma literal
    by_unii = "patient.drug.openfda.unii:(" + " ".join(f'"{u}"' for u in uniis) + ")"
    daily, meta = query(by_unii, count="receivedate")
    if daily is None:
        return {"uniis": uniis, "total": 0}
    serious, _ = query(f"{by_unii} AND serious:1", count="receivedate")
    deaths, _ = query(f"{by_unii} AND seriousnessdeath:1", count="receivedate")
    reactions, _ = query(by_unii, count="patient.reaction.reactionmeddrapt.exact", limit=TOP_REACTIONS)
    return {
        "uniis": uniis,
        "total": sum(d["count"] for d in daily),
        "data_updated": meta["last_updated"],
        "daily": daily,
        "daily_serious": serious or [],
        "daily_deaths": deaths or [],
        "reactions": reactions or [],
    }


def by_year(daily):
    years = defaultdict(int)
    for d in daily:
        years[int(d["time"][:4])] += d["count"]
    return years


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        families = conn.execute("""
            SELECT m.parent_chembl_id, array_agg(DISTINCT u.unii ORDER BY u.unii)
            FROM chembl.unii_xref u JOIN chembl.molecule_dictionary m USING (chembl_id)
            GROUP BY 1 ORDER BY 1""").fetchall()

    CACHE.mkdir(parents=True, exist_ok=True)
    pending = [(f, u) for f, u in families if not (CACHE / f"{f}.json").exists()]
    only = os.environ.get("OPENFDA_ONLY")  # para pruebas: familias separadas por coma
    if only:
        pending = [(f, u) for f, u in pending if f in only.split(",")]
    print(f"Familias con UNII: {len(families)}, por descargar: {len(pending)}"
          f"{'' if API_KEY else ' (sin API key: máximo ~250 familias por día)'}")

    done = 0
    try:
        for family, uniis in pending:
            result = fetch(uniis)
            result["fetched_at"] = datetime.now(timezone.utc).isoformat()
            (CACHE / f"{family}.json").write_text(json.dumps(result))
            done += 1
            if done % 50 == 0:
                print(f"  descargadas {done}/{len(pending)}")
    except DailyLimit:
        print(f"Límite diario de openFDA alcanzado tras {done} familias; "
              "la próxima corrida sigue desde ahí.")

    rows = {"drug_query": [], "reports_by_year": [], "reactions": []}
    for f in sorted(CACHE.glob("*.json")):
        d = json.loads(f.read_text())
        rows["drug_query"].append((f.stem, d["uniis"], d["total"], d["fetched_at"],
                                   datetime.strptime(d["data_updated"], "%Y-%m-%d").date()
                                   if d.get("data_updated") else None))
        if not d["total"]:
            continue
        reports, serious, deaths = (by_year(d.get(k, [])) for k in ("daily", "daily_serious", "daily_deaths"))
        rows["reports_by_year"] += [(f.stem, y, n, serious[y], deaths[y]) for y, n in sorted(reports.items())]
        rows["reactions"] += [(f.stem, r["term"], r["count"]) for r in d["reactions"]]

    version = max((r[4] for r in rows["drug_query"] if r[4]), default=None)
    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        for table, data in rows.items():
            with conn.cursor().copy(f"COPY openfda.{table} FROM STDIN") as copy:
                for row in data:
                    copy.write_row(row)
            conn.execute(
                "INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                "VALUES ('openfda', %s, %s, %s)", (f"datos al {version}", f"openfda.{table}", len(data)))
            print(f"  {table:<20}{len(data):>10} filas")
        print(f"Familias descargadas: {len(rows['drug_query'])} de {len(families)}")
        for r in conn.execute("SELECT * FROM rastro_meta.source_counts WHERE source_id = 'openfda'"):
            print(r)


if __name__ == "__main__":
    main()
