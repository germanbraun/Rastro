"""Carga las dos fuentes de la Secretaría de Energía para el dominio de petróleo y gas.

Capítulo IV (datos.energia.gob.ar, CC-BY 4.0): la producción declarada de 2025, pozo por pozo y
mes por mes, y el padrón de pozos con su ubicación. Se usa 2025 porque es el último año completo:
el archivo de 2026 todavía no trae a todas las operadoras.

Servicio de mapas (WFS de sig.energia.gob.ar): las concesiones de explotación con su contorno,
operadora y socios; los puntos de venteo declarados; y los posibles venteos detectados por
satélite. El certificado del servidor viene sin la cadena completa, así que se descarga sin
verificarlo: son datos públicos de solo lectura.

Cada descarga se guarda en data/raw/energia/ y no se vuelve a pedir.

Se corre con: docker compose run --rm energia-loader
"""

import csv
import html
import json
import os
import re
from pathlib import Path

import psycopg
import requests
import urllib3

CACHE = Path("/data/raw/energia")
CKAN = "http://datos.energia.gob.ar/api/3/action/resource_show?id="
PRODUCCION_2025 = "d774b5d7-0756-48fe-88f2-8729b57b22da"
PADRON_POZOS = "cb5c0f04-7835-45cd-b982-3e25ca7d7751"
WFS = "https://sig.energia.gob.ar/mapserv?map=/etc/mapserver/mapase.map"
PAGE = 10_000

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
http = requests.Session()
http.headers["User-Agent"] = "RastroMVP/0.1"

PRODUCCION_COLS = ["anio", "mes", "idpozo", "idempresa", "empresa", "prod_pet", "prod_gas", "formacion",
                   "idareapermisoconcesion", "areapermisoconcesion", "areayacimiento", "cuenca", "provincia",
                   "tipo_de_recurso", "sub_tipo_recurso", "tipoestado"]
POZO_COLS = ["idpozo", "sigla", "empresa", "cod_area", "area", "yacimiento", "formacion", "cuenca", "provincia",
             "tipo_recurso", "sub_tipo_recurso", "tipoestado"]


def download(name, url, verify=True, tries=4):
    f = CACHE / name
    for attempt in range(tries):
        if f.exists():
            break
        print(f"  descargando {name}")
        try:
            with http.get(url, timeout=900, stream=True, verify=verify) as r:
                r.raise_for_status()
                tmp = f.with_suffix(".tmp")
                with tmp.open("wb") as out:
                    for chunk in r.iter_content(1 << 20):
                        out.write(chunk)
                tmp.rename(f)
        except requests.RequestException as e:   # el servidor corta descargas largas: se reintenta
            print(f"  falló ({e.__class__.__name__}), intento {attempt + 1} de {tries}")
    if not f.exists():
        raise RuntimeError(f"No se pudo descargar {name}")
    return f


def ckan(resource_id, name):
    url = http.get(CKAN + resource_id, timeout=60).json()["result"]["url"]
    return download(name, url)


def wfs_features(layer):
    """Todas las entidades de una capa del WFS, en páginas de PAGE, como texto GML de cada una."""
    feats, start = [], 0
    while True:
        f = download(f"{layer}-{start}.gml", f"{WFS}&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
                     f"&TYPENAMES=ms:{layer}&COUNT={PAGE}&STARTINDEX={start}", verify=False)
        page = re.findall(rf"<ms:{layer} .*?</ms:{layer}>", f.read_text(errors="ignore"), re.S)
        feats += page
        if len(page) < PAGE:
            return feats
        start += PAGE


def prop(feat, key):
    m = re.search(rf"<ms:{key}(?: [^>]*)?>(.*?)</ms:{key}>", feat, re.S)
    if not m:
        return None
    value = re.sub(r"<[^>]+>", "", m.group(1)) if "timePosition" in m.group(1) else m.group(1)
    return html.unescape(value).strip() or None


def point(feat):
    lat, lon = map(float, re.search(r"<gml:pos[^>]*>([^<]+)</gml:pos>", feat).group(1).split()[:2])
    return lon, lat  # el WFS 2.0 da EPSG:4326 como «latitud longitud»


def ring(feat):
    """El contorno exterior más largo, como [[lon, lat], ...]."""
    rings = re.findall(r"<gml:exterior>.*?<gml:posList[^>]*>([^<]+)</gml:posList>", feat, re.S)
    best = max(rings, key=len).split()
    return json.dumps([[float(best[i + 1]), float(best[i])] for i in range(0, len(best) - 1, 2)])


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")

    produccion = ckan(PRODUCCION_2025, "produccion-2025.csv")
    padron = ckan(PADRON_POZOS, "pozos.csv")
    concesiones = [(prop(f, "id_concesion"), prop(f, "areapermisoconcesion"), prop(f, "empresa_informante"),
                    prop(f, "empresa_operadora"), prop(f, "participacion"), prop(f, "estadodearea"),
                    prop(f, "observaciones"), ring(f))
                   for f in wfs_features("planosbase_concesiones_explotacion")]
    declarados = [(f.split('"', 2)[1], prop(f, "nombre"), prop(f, "tipo"), prop(f, "procedencia"),
                   prop(f, "nombre_procedencia"), prop(f, "empresa_informante"), prop(f, "empresa_operadora_area"),
                   *point(f)) for f in wfs_features("planosbase_puntos_venteo_declarados")]
    detectados = [(f.split('"', 2)[1], prop(f, "fecha"), prop(f, "provincia"), prop(f, "satelite"), *point(f))
                  for f in wfs_features("sensoresremotos_venteos_detectados")]

    with psycopg.connect(conninfo) as conn:
        conn.execute("""
            INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
              ('capitulo4', 'Producción por pozo, Capítulo IV (Secretaría de Energía)',
               'http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo', 'CC-BY 4.0', 'capitulo4'),
              ('sig_energia', 'Mapas de la Secretaría de Energía (WFS)',
               'https://sig.energia.gob.ar/wfsenergia', 'Datos públicos (Secretaría de Energía)', 'sig_energia')
            ON CONFLICT (id) DO NOTHING""")
        conn.execute(Path(__file__).with_name("schema.sql").read_text())

        def copy(table, rows, source, version):
            n = 0
            with conn.cursor().copy(f"COPY {table} FROM STDIN") as cp:
                for row in rows:
                    cp.write_row(row)
                    n += 1
            conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                         "VALUES (%s, %s, %s, %s)", (source, version, table, n))
            print(f"  {table:<30}{n:>9} filas")

        with produccion.open(encoding="utf-8-sig", newline="") as fh:
            copy("capitulo4.produccion",
                 ([r[c] or None for c in PRODUCCION_COLS] for r in csv.DictReader(fh) if r["anio"] == "2025"),
                 "capitulo4", "producción 2025")

        def pozos(fh):
            for r in csv.DictReader(fh):
                try:
                    lon, lat = json.loads(r["geojson"])["coordinates"][:2]
                except (ValueError, KeyError, TypeError):
                    lon = lat = None
                yield [(r[c] or "").strip() or None for c in POZO_COLS] + [lon, lat]
        with padron.open(encoding="utf-8-sig", newline="") as fh:
            copy("capitulo4.pozo", pozos(fh), "capitulo4", "padrón de pozos")

        copy("sig_energia.concesion", concesiones, "sig_energia", "WFS")
        copy("sig_energia.venteo_declarado", declarados, "sig_energia", "WFS")
        copy("sig_energia.venteo_detectado", detectados, "sig_energia", "WFS")


if __name__ == "__main__":
    main()
