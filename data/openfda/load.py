"""Downloads from openFDA the aggregated adverse events of the drugs in scope.

Drugs = ChEMBL families (schema `chembl`, loaded before) that have a UNII.
Each family is searched by its UNIIs (patient.drug.openfda.unii) or by the name of its
active ingredient (patient.drug.activesubstance.activesubstancename), in a single
search with OR: openFDA leaves the UNII empty for some drugs (for example, the
osimertinib of Tagrisso), which can only be found by name. It queries:
reports per day (all, serious and with death), then aggregated by year, and the
100 most reported reactions. The UNII matches the drug in any role in the report
(suspect or concomitant): openFDA does not allow requiring both conditions on the
same drug of the report.

Each response is saved in data/raw/openfda/<family>.json and is not requested again
while the search stays the same, so the download can be resumed. Without OPENFDA_API_KEY the limit is 1000 requests
per day: the script stops when it reaches it, loads what it has and continues on the next run.

Run with: docker compose run --rm openfda-loader
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
PAUSE = 0.3  # at most 240 requests/minute, with or without a key
TOP_REACTIONS = 100  # maximum without a key; fixed so the cache is the same with or without a key

http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2,
                                                     status_forcelist=[500, 502, 503, 504])))


class DailyLimit(Exception):
    pass


def query(search, **params):
    """Returns (results, meta), or (None, None) if no reports match."""
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


def search_for(uniis, names):
    """openFDA search for a family: by UNII or by the name of the active ingredient."""
    # Spaces and not "+": requests encodes "+" as %2B and openFDA takes it literally
    def quoted(values):
        return " ".join(f'"{v}"' for v in values)
    parts = [f"patient.drug.openfda.unii:({quoted(uniis)})"]
    if names:
        parts.append(f"patient.drug.activesubstance.activesubstancename:({quoted(names)})")
    return "(" + " OR ".join(parts) + ")"


def fetch(uniis, names):
    search = search_for(uniis, names)
    daily, meta = query(search, count="receivedate")
    if daily is None:
        return {"uniis": uniis, "names": names, "search": search, "total": 0}
    serious, _ = query(f"{search} AND serious:1", count="receivedate")
    deaths, _ = query(f"{search} AND seriousnessdeath:1", count="receivedate")
    reactions, _ = query(search, count="patient.reaction.reactionmeddrapt.exact", limit=TOP_REACTIONS)
    return {
        "uniis": uniis,
        "names": names,
        "search": search,
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
            SELECT m.parent_chembl_id,
                   array_agg(DISTINCT u.unii ORDER BY u.unii),
                   (SELECT array_agg(DISTINCT x.pref_name ORDER BY x.pref_name)
                    FROM chembl.molecule_dictionary x
                    WHERE x.parent_chembl_id = m.parent_chembl_id
                      AND x.pref_name IS NOT NULL AND position('"' IN x.pref_name) = 0)
            FROM chembl.unii_xref u JOIN chembl.molecule_dictionary m USING (chembl_id)
            GROUP BY 1 ORDER BY 1""").fetchall()

    def cached_search(family):
        f = CACHE / f"{family}.json"
        return json.loads(f.read_text()).get("search") if f.exists() else None

    CACHE.mkdir(parents=True, exist_ok=True)
    pending = [(f, u, n or []) for f, u, n in families if cached_search(f) != search_for(u, n or [])]
    only = os.environ.get("OPENFDA_ONLY")  # for tests: families separated by commas
    if only:
        pending = [p for p in pending if p[0] in only.split(",")]
    print(f"Familias con UNII: {len(families)}, por descargar: {len(pending)}"
          f"{'' if API_KEY else ' (sin API key: máximo ~250 familias por día)'}")

    done = 0
    try:
        for family, uniis, names in pending:
            result = fetch(uniis, names)
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
        rows["drug_query"].append((f.stem, d["uniis"], d.get("names", []), d["total"], d["fetched_at"],
                                   datetime.strptime(d["data_updated"], "%Y-%m-%d").date()
                                   if d.get("data_updated") else None))
        if not d["total"]:
            continue
        reports, serious, deaths = (by_year(d.get(k, [])) for k in ("daily", "daily_serious", "daily_deaths"))
        rows["reports_by_year"] += [(f.stem, y, n, serious[y], deaths[y]) for y, n in sorted(reports.items())]
        rows["reactions"] += [(f.stem, r["term"], r["count"]) for r in d["reactions"]]

    version = max((r[5] for r in rows["drug_query"] if r[5]), default=None)
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
