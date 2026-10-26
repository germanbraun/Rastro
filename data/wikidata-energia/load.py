"""Enriches the oil and gas companies with what Wikidata knows, and saves it in the database (materialized).

The same as the app's live query (layer/energia/externo/wikidata.rq), but saved: it looks up in Wikidata the
companies by their LEI (P1278), with their headquarters (P159), the stock exchange they are listed on (P414), their
owner or parent (P749 or P127) and their website (P856). The full response is saved in
data/raw/wikidata-energia/<date>.json and its fingerprint stays in rastro_meta.load_run: so we know what Wikidata
said and when. It needs Rastro's LEIs (energia.empresa_lei), so it runs after the linker.

Run with: docker compose run --rm wikidata-energia-loader   (and then energia-linker, to link it)
"""

import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun import copiar, http  # noqa: E402

API = "https://query.wikidata.org/sparql"
CACHE = Path("/data/raw/wikidata-energia")
QUERY = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?lei ?wikidata (GROUP_CONCAT(DISTINCT ?sedeL; separator=", ") AS ?sede)
       (GROUP_CONCAT(DISTINCT ?bolsaL; separator=", ") AS ?bolsa)
       (GROUP_CONCAT(DISTINCT ?duenioL; separator=", ") AS ?duenio) (SAMPLE(?web) AS ?sitio) WHERE {
  VALUES ?lei { %s }
  ?wikidata wdt:P1278 ?lei .
  OPTIONAL { ?wikidata wdt:P159/rdfs:label ?sedeL . FILTER (LANG(?sedeL) = "es") }
  OPTIONAL { ?wikidata wdt:P414/rdfs:label ?bolsaL . FILTER (LANG(?bolsaL) = "es") }
  OPTIONAL { ?wikidata wdt:P749|wdt:P127 ?d . ?d rdfs:label ?duenioL . FILTER (LANG(?duenioL) = "es") }
  OPTIONAL { ?wikidata wdt:P856 ?web }
} GROUP BY ?lei ?wikidata
"""


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    hoy = date.today()
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        leis = [lei for (lei,) in conn.execute("SELECT DISTINCT lei FROM energia.empresa_lei ORDER BY 1")]
        archivo = CACHE / f"{hoy.isoformat()}.json"
        if not archivo.exists():   # one query per day: that day's response stays saved
            time.sleep(1)
            r = http.post(API, data={"query": QUERY % " ".join(f'"{lei}"' for lei in leis)}, timeout=120,
                          headers={"Accept": "application/sparql-results+json",
                                   "User-Agent": "RastroMVP/0.1 (https://github.com/germanbraun/Rastro)"})
            r.raise_for_status()
            archivo.write_text(r.text)
        filas = json.loads(archivo.read_text())["results"]["bindings"]

        def valor(f, k):
            return (f.get(k) or {}).get("value") or None

        conn.execute("TRUNCATE wikidata_energia.empresa")
        copiar(conn, "wikidata_energia.empresa",
               ([valor(f, "lei"), valor(f, "wikidata"), valor(f, "sede"), valor(f, "bolsa"), valor(f, "duenio"),
                 valor(f, "sitio"), hoy] for f in filas),
               "wikidata", f"consulta del {hoy:%d/%m/%Y} ({len(leis)} LEI de petróleo y gas)", archivo=archivo)


if __name__ == "__main__":
    main()
