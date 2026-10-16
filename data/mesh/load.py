"""Carga MeSH (RDF de NLM) en el repositorio `rastro` de GraphDB.

Se descarga mesh<año>.nt.gz a data/raw/mesh/ (una sola vez), se parte en trozos de
CHUNK triples y GraphDB los importa uno por uno desde su carpeta de importación,
montada sobre esa misma ruta, al grafo http://id.nlm.nih.gov/mesh/<año>. Importar
los 15 M de triples en una sola transacción agota la memoria de una laptop.
Reimportar reemplaza ese grafo.

Al final (re)crea el conector Lucene `mesh` (lucene-connector.json): búsqueda de texto
sobre descriptores por etiqueta, sinónimos y número de árbol.

Se corre con: docker compose run --rm mesh-loader
Solo el conector, sin reimportar: docker compose run --rm mesh-loader python /data/mesh/load.py --connector-only
"""

import gzip
import os
import sys
import time
from pathlib import Path

import psycopg
import requests

YEAR = os.environ.get("MESH_YEAR") or "2026"
FILE = f"mesh{YEAR}.nt.gz"
URL = f"https://nlmpubs.nlm.nih.gov/projects/mesh/rdf/{YEAR}/{FILE}"
GRAPH = f"http://id.nlm.nih.gov/mesh/{YEAR}"
GDB = "http://graphdb:7200"
REPO = f"{GDB}/rest/repositories/rastro"
RAW = Path("/data/raw/mesh")
CHUNK = 500_000  # triples por transacción de importación


def download():
    target = RAW / FILE
    if target.exists():
        print(f"Ya descargado: {target.name}")
        return
    print(f"Descargando {URL}...")
    tmp = target.with_suffix(".part")
    with requests.get(URL, stream=True, timeout=600) as r:
        r.raise_for_status()
        # NLM responde con Content-Encoding: x-gzip; se guardan los bytes tal cual
        # para que requests no lo descomprima y el .gz sea realmente gzip
        with tmp.open("wb") as f:
            while chunk := r.raw.read(1 << 20, decode_content=False):
                f.write(chunk)
    tmp.rename(target)


def split():
    """Parte el archivo en trozos de CHUNK líneas (N-Triples: una triple por línea)."""
    for old in RAW.glob(f"mesh{YEAR}.part-*.nt.gz"):
        old.unlink()
    parts, out = [], None
    with gzip.open(RAW / FILE, "rt", encoding="utf-8") as src:
        for i, line in enumerate(src):
            if i % CHUNK == 0:
                if out:
                    out.close()
                parts.append(f"mesh{YEAR}.part-{len(parts):02d}.nt.gz")
                out = gzip.open(RAW / parts[-1], "wt", encoding="utf-8", compresslevel=1)
            out.write(line)
    if out:
        out.close()
    print(f"Partido en {len(parts)} trozos de hasta {CHUNK:,} triples")
    return parts


def import_file(name, replace):
    def status():
        return next((f for f in requests.get(f"{REPO}/import/server", timeout=60).json()
                     if f["name"] == name), None)

    settings = {"context": GRAPH}
    if replace:
        settings["replaceGraphs"] = [GRAPH]
    r = requests.post(f"{REPO}/import/server", timeout=60,
                      json={"fileNames": [name], "importSettings": settings})
    r.raise_for_status()
    while (s := status()) and s["status"] in ("PENDING", "IMPORTING", "NONE"):
        time.sleep(5)
    if not s or s["status"] != "DONE":
        raise SystemExit(f"La importación de {name} falló: {s}")


def wait_for_graphdb():
    while True:
        try:
            if requests.get(REPO, timeout=10).ok:
                return
        except requests.ConnectionError:
            pass
        time.sleep(10)


def import_into_graphdb():
    parts = split()
    print(f"Importando en GraphDB al grafo <{GRAPH}>...")
    for i, name in enumerate(parts):
        # Si GraphDB se cae a mitad de un trozo (se reinicia solo), se espera y se
        # reintenta ese trozo: reimportar triples ya cargadas no las duplica.
        for attempt in range(1, 4):
            try:
                wait_for_graphdb()
                import_file(name, replace=(i == 0))
                break
            except requests.ConnectionError:
                print(f"  GraphDB no responde durante {name}, reintento {attempt}/3")
        else:
            raise SystemExit(f"No se pudo importar {name}")
        print(f"  {name} listo")
    for name in parts:
        (RAW / name).unlink()


def sparql(query):
    r = requests.post(f"{GDB}/repositories/rastro", data={"query": query},
                      headers={"Accept": "text/csv"}, timeout=600)
    r.raise_for_status()
    return r.text.splitlines()[1:]


def update(statement):
    r = requests.post(f"{GDB}/repositories/rastro/statements", data={"update": statement},
                      timeout=3600)
    r.raise_for_status()


def count(query):
    return int(sparql(query)[0])


LUCENE = """PREFIX con: <http://www.ontotext.com/connectors/lucene#>
PREFIX inst: <http://www.ontotext.com/connectors/lucene/instance#>
"""


def create_lucene_connector():
    """Recrea el conector Lucene `mesh`; indexa lo que ya está en el repositorio."""
    if sparql(LUCENE + "SELECT ?c WHERE { inst:mesh con:listConnectors ?c }"):
        update(LUCENE + "INSERT DATA { inst:mesh con:dropConnector [] }")
    definition = Path(__file__).with_name("lucene-connector.json").read_text()
    print("Creando el conector Lucene mesh...")
    update(LUCENE + "INSERT DATA { inst:mesh con:createConnector '''" + definition + "''' }")


def main():
    if "--connector-only" in sys.argv:
        create_lucene_connector()
        return
    RAW.mkdir(parents=True, exist_ok=True)
    download()
    import_into_graphdb()
    triples = count(f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{GRAPH}> {{ ?s ?p ?o }} }}")
    descriptors = count(f"""PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
        SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{GRAPH}> {{ ?d a meshv:TopicalDescriptor }} }}""")
    print(f"Triples: {triples}, descriptores: {descriptors}")

    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                     "VALUES ('mesh', %s, %s, %s)", (f"MeSH {YEAR}", f"graphdb:<{GRAPH}>", triples))
        print(conn.execute("SELECT * FROM rastro_meta.source_counts WHERE source_id = 'mesh'").fetchone())

    create_lucene_connector()


if __name__ == "__main__":
    main()
