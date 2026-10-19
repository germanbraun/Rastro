"""Arma las tablas del dominio de petróleo y gas que leen los mapeos, y los enlaces entre fuentes.

1. Ubica cada venteo (detectado por satélite desde 2024, o declarado) dentro de su concesión:
   punto dentro de polígono, con los contornos del mapa. Postgres no tiene PostGIS acá y son
   pocos polígonos, así que se hace en Python.
2. Carga las correcciones revisadas (correcciones.csv) y corre links.sql: empresas con sus
   nombres en cada fuente, producción por pozo, participaciones, quién opera cada pozo y
   cada venteo en su concesión, todo con su evidencia.

Se corre con: docker compose run --rm energia-linker
"""

import csv
import json
import os
from pathlib import Path

import psycopg

HERE = Path(__file__).parent
DESDE = "2024-01-01"   # detecciones por satélite: los últimos dos años y medio


def inside(lon, lat, ring):
    """Punto dentro de polígono, por cruce de rayos."""
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute("DROP TABLE IF EXISTS energia.venteo_ubicado")   # se recrea en links.sql (DROP SCHEMA)
        polys = []
        for cid, anillo in conn.execute("SELECT id_concesion, anillo FROM sig_energia.concesion"):
            ring = [tuple(p) for p in json.loads(anillo)]
            xs, ys = [p[0] for p in ring], [p[1] for p in ring]
            polys.append((cid, ring, min(xs), max(xs), min(ys), max(ys)))

        def where(lon, lat):
            for cid, ring, x0, x1, y0, y1 in polys:
                if x0 <= lon <= x1 and y0 <= lat <= y1 and inside(lon, lat, ring):
                    return cid
            return None

        puntos = [(i, "detectado", f, s, None, lon, lat) for i, f, s, lon, lat in conn.execute(
            "SELECT gml_id, fecha, satelite, lon, lat FROM sig_energia.venteo_detectado WHERE fecha >= %s", (DESDE,))]
        puntos += [(i, "declarado", None, None, n, lon, lat) for i, n, lon, lat in conn.execute(
            "SELECT gml_id, nombre, lon, lat FROM sig_energia.venteo_declarado")]
        ubicados = [(*p[:5], where(p[5], p[6]), p[5], p[6]) for p in puntos]

        conn.execute("DROP SCHEMA IF EXISTS energia CASCADE")
        conn.execute("CREATE SCHEMA energia")
        conn.execute("CREATE TABLE energia.correccion (nombre text, grupo text, motivo text)")
        with conn.cursor().copy("COPY energia.correccion FROM STDIN") as cp:
            for r in csv.DictReader((HERE / "correcciones.csv").open()):
                cp.write_row((r["nombre"], r["grupo"], r["motivo"]))
        conn.execute("CREATE TABLE energia.venteo_ubicado (gml_id text, tipo text, fecha date, satelite text, "
                     "nombre text, id_concesion text, lon double precision, lat double precision)")
        with conn.cursor().copy("COPY energia.venteo_ubicado FROM STDIN") as cp:
            for row in ubicados:
                if row[5]:
                    cp.write_row(row)

        sql = (HERE / "links.sql").read_text()
        sql = sql.split("CREATE SCHEMA energia;", 1)[1]          # el esquema ya está creado, con sus tablas de entrada
        conn.execute(sql)

        for tipo in ("detectado", "declarado"):
            total = sum(1 for p in ubicados if p[1] == tipo)
            dentro = sum(1 for p in ubicados if p[1] == tipo and p[5])
            print(f"  venteos {tipo}s: {total}, dentro de una concesión: {dentro}")
        for table in ("empresa", "empresa_nombre", "produccion_pozo", "concesion", "participacion", "operador_pozo", "venteo"):
            n = conn.execute(f"SELECT count(*) FROM energia.{table}").fetchone()[0]
            print(f"  energia.{table:<16}{n:>8} filas")
        for regla, n in conn.execute("SELECT regla, count(*) FROM energia.operador_pozo GROUP BY 1 ORDER BY 2 DESC"):
            print(f"  operador del pozo, {regla}: {n}")


if __name__ == "__main__":
    main()
