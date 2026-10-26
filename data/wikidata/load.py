"""Looks up in Wikidata the companies with the LEIs loaded from GLEIF, their headquarters and whether they are listed.

Reads the LEIs from gleif.lei_record (loaded before) and queries Wikidata's public SPARQL
endpoint 200 LEIs at a time: P1278 (LEI), P414 (stock exchange) and P159 (headquarters). Each response is
saved in data/raw/wikidata/.

Run with: docker compose run --rm wikidata-loader
"""

import hashlib
import json
import os
import time
from datetime import date
from pathlib import Path

import psycopg
import requests
from requests.adapters import HTTPAdapter, Retry

API = "https://query.wikidata.org/sparql"
CACHE = Path("/data/raw/wikidata")
BATCH = 200
QUERY = """
SELECT ?item ?lei ?label (GROUP_CONCAT(DISTINCT ?exchangeLabel; separator="|") AS ?exchanges)
       (SAMPLE(?hqLabel) AS ?hq) WHERE {
  VALUES ?lei { %s }
  ?item wdt:P1278 ?lei .
  OPTIONAL { ?item rdfs:label ?label FILTER (LANG(?label) = "en") }
  OPTIONAL { ?item wdt:P414 ?exchange . ?exchange rdfs:label ?exchangeLabel FILTER (LANG(?exchangeLabel) = "en") }
  OPTIONAL { ?item wdt:P159 ?hqPlace . ?hqPlace rdfs:label ?hqLabel FILTER (LANG(?hqLabel) = "en") }
}
GROUP BY ?item ?lei ?label
"""

http = requests.Session()
# Wikidata requires identifying yourself
http.headers["User-Agent"] = "RastroMVP/0.1 (https://github.com/germanbraun/Rastro)"
http.mount("https://", HTTPAdapter(max_retries=Retry(total=6, backoff_factor=5, allowed_methods=None,
                                                     status_forcelist=[429, 500, 502, 503, 504])))


def run(leis):
    query = QUERY % " ".join(f'"{lei}"' for lei in leis)
    f = CACHE / f"{hashlib.sha1(query.encode()).hexdigest()}.json"
    if not f.exists():
        time.sleep(1)
        r = http.post(API, data={"query": query}, headers={"Accept": "application/sparql-results+json"},
                      timeout=300)
        r.raise_for_status()
        f.write_text(r.text)
    return json.loads(f.read_text())["results"]["bindings"]


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        leis = [lei for (lei,) in conn.execute("SELECT lei FROM gleif.lei_record ORDER BY lei")]

    CACHE.mkdir(parents=True, exist_ok=True)
    rows = {}
    for i in range(0, len(leis), BATCH):
        for b in run(leis[i:i + BATCH]):
            qid = b["item"]["value"].rsplit("/", 1)[-1]
            exchanges = [x for x in b.get("exchanges", {}).get("value", "").split("|") if x]
            rows[qid, b["lei"]["value"]] = (qid, b["lei"]["value"], b.get("label", {}).get("value"), exchanges,
                                            b.get("hq", {}).get("value"))
    print(f"LEI consultados: {len(leis)}, con empresa en Wikidata: {len({k[1] for k in rows})}")

    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        with conn.cursor().copy("COPY wikidata.company FROM STDIN") as copy:
            for row in rows.values():
                copy.write_row(row)
        conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                     "VALUES ('wikidata', %s, 'wikidata.company', %s)", (f"consulta del {date.today()}", len(rows)))
        print(f"  wikidata.company  {len(rows):>6} filas, {sum(bool(r[3]) for r in rows.values())} cotizan en bolsa")


if __name__ == "__main__":
    main()
