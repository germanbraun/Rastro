"""Carga los datos que solo usa Rastro Lab (gas de Vaca Muerta), sin tocar lo que usa Rastro Layer:

1. Capítulo IV, años 2018 a 2022: las declaraciones juradas de producción por pozo y mes, para tener más
   pozos nuevos con su gas (en capitulo4_anterior.produccion; Layer sigue con 2023 a 2025).
2. Datos de fractura de pozos (Adjunto IV): largo de la rama horizontal, etapas, arena, agua y presión de
   cada fractura, por pozo (en fractura.fractura). Es una fuente nueva.

Descarga a data/raw/lab-gas/ (con caché) y carga con COPY. Cada tabla queda en rastro_meta.load_run.
Se corre con: docker compose run --rm lab-gas-loader
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
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        conn.execute("""
            INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
              ('fractura', 'Datos de fractura de pozos (Adjunto IV, Secretaría de Energía)',
               'http://datos.energia.gob.ar/dataset/datos-de-fractura-de-pozos-adjunto-iv', 'CC-BY 4.0', 'fractura')
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name""")
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        conn.execute("TRUNCATE capitulo4_anterior.produccion, fractura.fractura")

        def copy(table, rows, source, version):
            copiar(conn, table, rows, source, version, ancho=34)

        for anio, f in produccion.items():
            with f.open(encoding="utf-8-sig", newline="") as fh:
                copy("capitulo4_anterior.produccion",
                     ([r[c] or None for c in PRODUCCION_COLS] for r in csv.DictReader(fh) if r["anio"] == str(anio)),
                     "capitulo4", f"producción {anio}")
        with fractura.open(encoding="utf-8-sig", newline="") as fh:
            copy("fractura.fractura", ([(r[c] or "").strip() or None for c in FRACTURA_COLS] for r in csv.DictReader(fh)),
                 "fractura", f"descargado {fractura.stat().st_mtime:.0f}")
        conn.execute("CREATE INDEX IF NOT EXISTS produccion_anterior_pozo ON capitulo4_anterior.produccion (idpozo)")


if __name__ == "__main__":
    main()
