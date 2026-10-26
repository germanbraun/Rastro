"""Builds the oil and gas domain tables that the mappings read, and the links between sources.

1. Places each venting (detected by satellite since 2024, or declared) inside its concession:
   point in polygon, with the map outlines. Postgres has no PostGIS here and there are
   few polygons, so it is done in Python.
2. Computes, for each concession, the nearest ENARGAS transport gas pipeline, and for each
   possible venting, the nearest town and whether it falls in a protected area (IGN). Distances in km
   with a flat approximation, good enough at this scale.
3. Loads the reviewed corrections (correcciones.csv, participaciones-revisadas.csv) and runs links.sql: companies with their
   names in each source and their LEI, production by well, stakes, who operates each well,
   each venting in its concession, gas pipelines and surroundings, and who operated each concession month by month
   (2023 to 2025) with its operator changes, all with their evidence. For Rastro Lab, how each new
   well started (since 2018, if the earlier years were loaded) and its fracturing.

Run with: docker compose run --rm energia-linker
"""

import csv
import json
import math
import os
from pathlib import Path

import psycopg

HERE = Path(__file__).parent
DESDE = "2024-01-01"   # satellite detections: the last two and a half years


def inside(lon, lat, ring):
    """Point in polygon, by ray casting."""
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def km(lon1, lat1, lon2, lat2):
    """Approximate distance in km (flat, with the latitude scale)."""
    dx = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, (lat2 - lat1) * 110.57)


def to_segment(px, py, ax, ay, bx, by):
    """Distance in km from a point to a segment, projecting onto flat coordinates."""
    c = math.cos(math.radians(py))
    ux, uy, vx, vy = (bx - ax) * c, by - ay, (px - ax) * c, py - ay
    t = max(0.0, min(1.0, (ux * vx + uy * vy) / (ux * ux + uy * uy))) if ux or uy else 0.0
    return km(px, py, ax + (bx - ax) * t, ay + (by - ay) * t)


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute("DROP TABLE IF EXISTS energia.venteo_ubicado")   # recreated in links.sql (DROP SCHEMA)
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

        # Nearest transport gas pipeline to each concession (0 if one crosses the outline)
        segs = []
        for name, lic, lineas in conn.execute("SELECT coalesce(nombregaso, nombretram), licenciata, lineas FROM enargas.gasoducto"):
            for line in json.loads(lineas):
                segs += [(name.strip(), (lic or "").strip(), a, b) for a, b in zip(line, line[1:])]
        gasoducto = []
        for cid, ring, x0, x1, y0, y1 in polys:
            best = (float("inf"), None, None)
            for name, lic, (ax, ay), (bx, by) in segs:
                if max(ax, bx) < x0 - 1 or min(ax, bx) > x1 + 1 or max(ay, by) < y0 - 1 or min(ay, by) > y1 + 1:
                    continue
                if inside(ax, ay, ring) or inside(bx, by, ring):
                    best = (0.0, name, lic)
                    break
                d = min(to_segment(px, py, ax, ay, bx, by) for px, py in ring[::max(1, len(ring) // 60)])
                if d < best[0]:
                    best = (d, name, lic)
            if not best[1]:   # no gas pipeline within the 1° window: measure against all of them
                for name, lic, (ax, ay), (bx, by) in segs:
                    d = min(to_segment(px, py, ax, ay, bx, by) for px, py in ring[::max(1, len(ring) // 20)])
                    if d < best[0]:
                        best = (d, name, lic)
            if best[1]:
                gasoducto.append((cid, best[1], best[2], best[0]))

        # Surroundings of each possible venting: nearest town and protected area (IGN)
        towns = list(conn.execute("SELECT fna, nom_pcia, lon, lat FROM ign.localidad"))
        areas = []
        for name, anillos in conn.execute("SELECT fna, anillos FROM ign.area_protegida"):
            for ring in json.loads(anillos):
                xs, ys = [p[0] for p in ring], [p[1] for p in ring]
                areas.append((name, ring, min(xs), max(xs), min(ys), max(ys)))
        entorno = []
        for p in ubicados:
            if p[1] != "detectado" or not p[5]:
                continue
            lon, lat = p[6], p[7]
            near = [t for t in towns if abs(t[2] - lon) < 1.5 and abs(t[3] - lat) < 1.5] or towns
            town = min(near, key=lambda t: km(lon, lat, t[2], t[3]))
            area = next((a[0] for a in areas if a[2] <= lon <= a[3] and a[4] <= lat <= a[5] and inside(lon, lat, a[1])), None)
            entorno.append((p[0], town[0], town[1], km(lon, lat, town[2], town[3]), area))

        conn.execute("DROP SCHEMA IF EXISTS energia CASCADE")
        conn.execute("CREATE SCHEMA energia")
        conn.execute("CREATE TABLE energia.correccion (nombre text, grupo text, motivo text)")
        with conn.cursor().copy("COPY energia.correccion FROM STDIN") as cp:
            for r in csv.DictReader((HERE / "correcciones.csv").open()):
                cp.write_row((r["nombre"], r["grupo"], r["motivo"]))
        conn.execute("CREATE TABLE energia.participacion_revisada (concesion text, empresa text, porcentaje numeric, "
                     "documento text, motivo text)")
        with conn.cursor().copy("COPY energia.participacion_revisada FROM STDIN") as cp:
            for r in csv.DictReader((HERE / "participaciones-revisadas.csv").open()):
                cp.write_row((r["concesion"], r["empresa"], r["porcentaje"], r["documento"], r["motivo"]))
        conn.execute("CREATE TABLE energia.venteo_ubicado (gml_id text, tipo text, fecha date, satelite text, "
                     "nombre text, id_concesion text, lon double precision, lat double precision)")
        with conn.cursor().copy("COPY energia.venteo_ubicado FROM STDIN") as cp:
            for row in ubicados:
                if row[5]:
                    cp.write_row(row)

        conn.execute("CREATE TABLE energia.concesion_gasoducto_calc (id_concesion text, gasoducto text, "
                     "licenciataria text, distancia_km double precision)")
        with conn.cursor().copy("COPY energia.concesion_gasoducto_calc FROM STDIN") as cp:
            for row in gasoducto:
                cp.write_row(row)
        conn.execute("CREATE TABLE energia.venteo_entorno_calc (id text, localidad text, provincia text, "
                     "distancia_km double precision, area_protegida text)")
        with conn.cursor().copy("COPY energia.venteo_entorno_calc FROM STDIN") as cp:
            for row in entorno:
                cp.write_row(row)

        # The Rastro Lab tables (Capítulo IV from 2018 to 2022 and fracturing): empty if not loaded yet
        conn.execute(Path("/data/lab-gas/schema.sql").read_text())
        # The materialized Wikidata enrichment: empty if not loaded yet
        conn.execute(Path("/data/wikidata-energia/schema.sql").read_text())
        sql = (HERE / "links.sql").read_text()
        sql = sql.split("CREATE SCHEMA energia;", 1)[1]          # the schema is already created, with its input tables
        conn.execute(sql)
        # Rebuilding the schema drops the permissions of the evaluation users (without Rastro and SQL + links)
        conn.execute(Path("/layer/energia/reader.sql").read_text())
        # Lab's source drill-down uses its existing raw-source reader, including historical years.
        conn.execute(Path("/layer/energia_lab/reader.sql").read_text())

        for tipo in ("detectado", "declarado"):
            total = sum(1 for p in ubicados if p[1] == tipo)
            dentro = sum(1 for p in ubicados if p[1] == tipo and p[5])
            print(f"  venteos {tipo}s: {total}, dentro de una concesión: {dentro}")
        for table in ("empresa", "empresa_nombre", "empresa_lei", "produccion_pozo", "concesion", "participacion",
                      "operador_pozo", "venteo", "gasoducto", "concesion_gasoducto", "venteo_entorno", "estudio",
                      "concesion_revisar", "operador_area_mes", "cambio_operadora", "inicio_pozo", "fractura_pozo",
                      "fractura_registro", "gas_mes", "trayectoria_pozo", "enriquecimiento"):
            n = conn.execute(f"SELECT count(*) FROM energia.{table}").fetchone()[0]
            print(f"  energia.{table:<16}{n:>8} filas")
        for regla, n in conn.execute("SELECT regla, count(*) FROM energia.operador_pozo GROUP BY 1 ORDER BY 2 DESC"):
            print(f"  operador del pozo, {regla}: {n}")


if __name__ == "__main__":
    main()
