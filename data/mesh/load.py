"""Loads MeSH (NLM's RDF) into the GraphDB repository `rastro`.

mesh<year>.nt.gz is downloaded to data/raw/mesh/ (only once), split into chunks of
CHUNK triples, and GraphDB imports them one by one from its import folder,
mounted on that same path, into the graph http://id.nlm.nih.gov/mesh/<year>. Importing
the 15 M triples in a single transaction runs a laptop out of memory.
Re-importing replaces that graph.

At the end it (re)creates the Lucene connector `mesh` (lucene-connector.json): text search
over descriptors by label, synonyms and tree number. And it copies to Postgres
(schema `mesh`) the descriptors and their hierarchy, so that Ontop answers without federating.

Run with: docker compose run --rm mesh-loader
Only the connector, without re-importing: docker compose run --rm mesh-loader python /data/mesh/load.py --connector-only
Only the copy to Postgres:                docker compose run --rm mesh-loader python /data/mesh/load.py --postgres-only
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
CHUNK = 500_000  # triples per import transaction


def download():
    target = RAW / FILE
    if target.exists():
        print(f"Ya descargado: {target.name}")
        return
    print(f"Descargando {URL}...")
    tmp = target.with_suffix(".part")
    with requests.get(URL, stream=True, timeout=600) as r:
        r.raise_for_status()
        # NLM answers with Content-Encoding: x-gzip; the bytes are saved as they come
        # so that requests does not decompress them and the .gz really is gzip
        with tmp.open("wb") as f:
            while chunk := r.raw.read(1 << 20, decode_content=False):
                f.write(chunk)
    tmp.rename(target)


def split():
    """Splits the file into chunks of CHUNK lines (N-Triples: one triple per line)."""
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
        # If GraphDB goes down in the middle of a chunk (it restarts on its own), wait and
        # retry that chunk: re-importing triples already loaded does not duplicate them.
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
    """Recreates the Lucene connector `mesh`; it indexes what is already in the repository."""
    if sparql(LUCENE + "SELECT ?c WHERE { inst:mesh con:listConnectors ?c }"):
        update(LUCENE + "INSERT DATA { inst:mesh con:dropConnector [] }")
    definition = Path(__file__).with_name("lucene-connector.json").read_text()
    print("Creando el conector Lucene mesh...")
    update(LUCENE + "INSERT DATA { inst:mesh con:createConnector '''" + definition + "''' }")


def copy_to_postgres(conninfo):
    """Copies descriptors (id and label) and the 'broader' relation to Postgres."""
    def rows(query):
        r = requests.post(f"{GDB}/repositories/rastro", data={"query": query},
                          headers={"Accept": "text/tab-separated-values"}, timeout=600)
        r.raise_for_status()
        return [line.split("\t") for line in r.text.splitlines()[1:]]

    def mesh_id(iri):
        return iri.strip("<>").rsplit("/", 1)[-1]

    prefix = "PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
    # Some descriptors have labels in several languages: the English one is kept, which AACT uses
    descriptors = [(mesh_id(d), en.rsplit("@", 1)[0].strip('"')) for d, en in rows(prefix + f"""
        SELECT ?d ?en WHERE {{ GRAPH <{GRAPH}> {{
            ?d a meshv:TopicalDescriptor ; rdfs:label ?en . FILTER (LANG(?en) = "en")
        }} }}""")]
    # Only the hierarchy between topical descriptors (publication types and the like are left out)
    known = {d for d, *_ in descriptors}
    broader = [(mesh_id(d), mesh_id(b)) for d, b in rows(
        prefix + f"SELECT ?d ?b WHERE {{ GRAPH <{GRAPH}> {{ ?d meshv:broaderDescriptor ?b }} }}")
        if mesh_id(d) in known and mesh_id(b) in known]

    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        for table, data in (("descriptor", descriptors), ("broader", broader)):
            with conn.cursor().copy(f"COPY mesh.{table} FROM STDIN") as copy:
                for row in data:
                    copy.write_row(row)
            conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                         "VALUES ('mesh', %s, %s, %s)", (f"MeSH {YEAR}", f"mesh.{table}", len(data)))
            print(f"  mesh.{table:<12}{len(data):>8} filas")
        n = conn.execute("""
            INSERT INTO mesh.ancestor
            WITH RECURSIVE up(id, ancestor_id) AS (
                SELECT id, id FROM mesh.descriptor
                UNION
                SELECT up.id, b.broader_id FROM up JOIN mesh.broader b ON b.id = up.ancestor_id
            )
            SELECT id, ancestor_id FROM up""").rowcount
        conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                     "VALUES ('mesh', %s, 'mesh.ancestor', %s)", (f"MeSH {YEAR}", n))
        print(f"  mesh.ancestor    {n:>8} filas")


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    if "--connector-only" in sys.argv:
        create_lucene_connector()
        return
    if "--postgres-only" in sys.argv:
        copy_to_postgres(conninfo)
        return
    RAW.mkdir(parents=True, exist_ok=True)
    download()
    import_into_graphdb()
    triples = count(f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{GRAPH}> {{ ?s ?p ?o }} }}")
    descriptors = count(f"""PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
        SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{GRAPH}> {{ ?d a meshv:TopicalDescriptor }} }}""")
    print(f"Triples: {triples}, descriptores: {descriptors}")

    with psycopg.connect(conninfo) as conn:
        conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                     "VALUES ('mesh', %s, %s, %s)", (f"MeSH {YEAR}", f"graphdb:<{GRAPH}>", triples))
        print(conn.execute("SELECT * FROM rastro_meta.source_counts WHERE source_id = 'mesh'").fetchone())

    create_lucene_connector()
    copy_to_postgres(conninfo)


if __name__ == "__main__":
    main()
