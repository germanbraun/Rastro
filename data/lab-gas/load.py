"""Loads the data that only Rastro Lab uses (Vaca Muerta gas), without touching what Rastro Layer uses:

1. Capítulo IV, years 2018 to 2022: the sworn production statements by well and month, to have more
   new wells with their gas (in capitulo4_anterior.produccion; Layer stays with 2023 to 2025).
2. Well fracturing data (Adjunto IV): length of the horizontal section, stages, sand, water and pressure of
   each fracturing, by well (in fractura.fractura). It is a new source.
3. Vaca Muerta well trajectories: vertical depth, section length and drilling dates, by well
   (in trayectoria.trayectoria). Another new source.

Downloads to data/raw/lab-gas/ (with cache) and loads with COPY. Each table is recorded in rastro_meta.load_run.
Run with: docker compose run --rm lab-gas-loader
"""

import csv
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun import ckan, copiar  # noqa: E402

CACHE = Path("/data/raw/lab-gas")
PRODUCCION = {2018: "333fd72a-9b83-4bc1-bc94-0f5940b52331", 2019: "8bc0d61c-0408-43d4-a7bc-7178fcb5d37e",
              2020: "c4a4a6a0-e75a-4e12-ae5c-54d53a70348c", 2021: "465be754-a372-4c31-b855-81dc5fe3309f",
              2022: "876b3746-85e2-4039-adeb-b1354436159f"}
FRACTURA = "2280ad92-6ed3-403e-a095-50139863ab0d"   # «Datos de fractura de pozos de hidrocarburos (Adjunto IV)»
TRAYECTORIAS = "94741ac7-4f46-4efe-b112-d3f82a4ef7c5"   # «Trayectorias de Pozo Vaca Muerta»
TRAYECTORIA_COLS = ["sigla", "idpo", "profundidad_final_total_mt", "profundidad_vertical_mt", "profundidad_sidetrack_mt",
                    "largo_rama_horizontal_mt", "unidad_intervalo_navegacion", "detalle_unidad_intervalo_navegacion",
                    "pnl_md", "pnl_tvd", "termini", "termfin", "drilini", "drilfin", "tipopozo"]

PRODUCCION_COLS = ["anio", "mes", "idpozo", "idempresa", "empresa", "prod_pet", "prod_gas", "formacion",
                   "idareapermisoconcesion", "areapermisoconcesion", "areayacimiento", "cuenca", "provincia",
                   "tipo_de_recurso", "sub_tipo_recurso", "tipoestado", "tipopozo"]
FRACTURA_COLS = ["id_base_fractura_adjiv", "idpozo", "sigla", "cuenca", "areapermisoconcesion", "yacimiento",
                 "formacion_productiva", "tipo_reservorio", "subtipo_reservorio", "longitud_rama_horizontal_m",
                 "cantidad_fracturas", "tipo_terminacion", "arena_bombeada_nacional_tn", "arena_bombeada_importada_tn",
                 "agua_inyectada_m3", "co2_inyectado_m3", "presion_maxima_psi", "potencia_equipos_fractura_hp",
                 "fecha_inicio_fractura", "fecha_fin_fractura", "fecha_data", "empresa_informante"]

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    produccion = {anio: ckan(CACHE, rid, f"produccion-{anio}.csv") for anio, rid in PRODUCCION.items()}
    fractura = ckan(CACHE, FRACTURA, "fractura.csv")
    trayectorias = ckan(CACHE, TRAYECTORIAS, "trayectorias-vm.csv")
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        conn.execute("""
            INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
              ('fractura', 'Datos de fractura de pozos (Adjunto IV, Secretaría de Energía)',
               'http://datos.energia.gob.ar/dataset/datos-de-fractura-de-pozos-adjunto-iv', 'CC-BY 4.0', 'fractura'),
              ('trayectorias', 'Trayectorias de pozo de Vaca Muerta (Secretaría de Energía)',
               'http://datos.energia.gob.ar/dataset/trayectoria-de-pozos', 'CC-BY 4.0', 'trayectoria')
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name""")
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        conn.execute("TRUNCATE capitulo4_anterior.produccion, fractura.fractura, trayectoria.trayectoria")

        def copy(table, rows, source, version, archivo=None):
            copiar(conn, table, rows, source, version, ancho=34, archivo=archivo)

        for anio, f in produccion.items():
            with f.open(encoding="utf-8-sig", newline="") as fh:
                copy("capitulo4_anterior.produccion",
                     ([r[c] or None for c in PRODUCCION_COLS] for r in csv.DictReader(fh) if r["anio"] == str(anio)),
                     "capitulo4", f"producción {anio}", archivo=f)
        with fractura.open(encoding="utf-8-sig", newline="") as fh:
            copy("fractura.fractura", ([(r[c] or "").strip() or None for c in FRACTURA_COLS] for r in csv.DictReader(fh)),
                 "fractura", "Adjunto IV, actualización diaria", archivo=fractura)
        with trayectorias.open(encoding="utf-8-sig", newline="") as fh:
            copy("trayectoria.trayectoria", ([(r[c] or "").strip() or None for c in TRAYECTORIA_COLS] for r in csv.DictReader(fh)),
                 "trayectorias", "Trayectorias de Pozo Vaca Muerta", archivo=trayectorias)
        conn.execute("CREATE INDEX IF NOT EXISTS produccion_anterior_pozo ON capitulo4_anterior.produccion (idpozo)")


if __name__ == "__main__":
    main()
