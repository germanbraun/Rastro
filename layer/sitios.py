"""Arma app/sitios.yaml: el sitio web de cada empresa, para mostrar su favicon junto al nombre.

Proveedores: el sitio oficial de Wikidata (propiedad P856) de cada grupo que tiene Wikidata.
Petróleo y gas y oncología: sitios.manual.yaml, una lista corta revisada por un asistente de IA
(a confirmar por una persona). Las claves son el nombre normalizado (mayúsculas, sin acentos,
puntuación ni forma societaria), el mismo que usa app/logos.py.

    docker compose run --rm -T layer-eval python /layer/sitios.py
"""

import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

import psycopg
import requests
import yaml

HERE = Path(__file__).parent
OUT = Path("/layer/sitios.yaml")   # se copia a app/sitios.yaml (la app no ve /layer como escritura)
FORMS = (r"\b(THE|INC|INCORPORATED|LLC|L L C|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|LP|LLP|PLC"
         r"|SA|SAU|SRL|SL|AG|SE|GMBH|NV|BV|HOLDINGS?|GROUP)\b")


def normalize(name):
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().upper()
    text = re.sub(r"[^A-Z0-9 ]", " ", text.replace("&", " AND "))
    return " ".join(re.sub(FORMS, " ", text).split())


def main():
    sites = {}
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        groups = conn.execute("""SELECT g.name, w.qid FROM proveedores.group_company g
                                 JOIN proveedores.group_wikidata w USING (group_id)""").fetchall()
    http = requests.Session()
    http.headers["User-Agent"] = "RastroMVP/0.1 (https://github.com/germanbraun/Rastro)"
    qids = sorted({q for _, q in groups})
    websites = {}
    for i in range(0, len(qids), 50):
        r = http.get("https://www.wikidata.org/w/api.php", timeout=60, params={
            "action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": "claims", "format": "json"})
        for qid, e in r.json().get("entities", {}).items():
            for c in e.get("claims", {}).get("P856", []):
                url = c["mainsnak"].get("datavalue", {}).get("value")
                if url:
                    websites[qid] = urlparse(url).netloc.removeprefix("www.")
                    break
    for name, qid in groups:
        if qid in websites:
            sites[normalize(name)] = websites[qid]
    manual = yaml.safe_load((HERE / "sitios.manual.yaml").read_text())
    for domain_sites in manual.values():
        for name, site in domain_sites.items():
            sites[normalize(name)] = site
    OUT.write_text("# Generado por layer/sitios.py: nombre normalizado de la empresa → su sitio web.\n"
                   + yaml.safe_dump(dict(sorted(sites.items())), allow_unicode=True))
    print(f"{len(sites)} empresas con sitio ({len(websites)} de Wikidata)")


if __name__ == "__main__":
    main()
