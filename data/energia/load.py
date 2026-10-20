"""Carga las dos fuentes de la Secretaría de Energía para el dominio de petróleo y gas.

Capítulo IV (datos.energia.gob.ar, CC-BY 4.0): la producción declarada de 2025, pozo por pozo y
mes por mes, y el padrón de pozos con su ubicación. Se usa 2025 porque es el último año completo:
el archivo de 2026 todavía no trae a todas las operadoras. Aparte, 2023 y 2024, en su propia tabla,
solo para ver quién operó cada concesión a lo largo del tiempo (por ejemplo, las áreas maduras
que YPF vendió).

Servicio de mapas (WFS de sig.energia.gob.ar): las concesiones de explotación con su contorno,
operadora y socios; los puntos de venteo declarados; y los posibles venteos detectados por
satélite. El certificado del servidor viene sin la cadena completa, así que se descarga sin
verificarlo: son datos públicos de solo lectura.

Del mismo WFS salen también los gasoductos de transporte de ENARGAS. Del WFS del Instituto
Geográfico Nacional (listado en IDERA), las localidades y las áreas protegidas. De GLEIF, el
identificador global (LEI) de las empresas que más producen, buscado por nombre en Argentina. Y
el listado de estudios ambientales que presentan las empresas, con sus observaciones.

Cada descarga se guarda en data/raw/energia/ y no se vuelve a pedir.

Se corre con: docker compose run --rm energia-loader
"""

import csv
import html
import json
import os
import re
import time
from pathlib import Path

import psycopg
import requests
import urllib3

CACHE = Path("/data/raw/energia")
CKAN = "http://datos.energia.gob.ar/api/3/action/resource_show?id="
PRODUCCION_2025 = "d774b5d7-0756-48fe-88f2-8729b57b22da"
PRODUCCION_ANTERIOR = {2023: "231c39b3-e81e-4398-af8d-b115807f2c25",   # los archivos completos, no los de
                       2024: "43a09dce-1742-44d0-bc13-f193deaab563"}   # «DDJJ abiertas y cerradas»
PADRON_POZOS = "cb5c0f04-7835-45cd-b982-3e25ca7d7751"
ESTUDIOS_AMBIENTALES = "7b8583fe-8994-4efa-9fbf-79c4a3f2f467"   # «Actividad ambiental de petróleo y gas»
WFS = "https://sig.energia.gob.ar/mapserv?map=/etc/mapserver/mapase.map"
PAGE = 10_000
IGN = "https://wms.ign.gob.ar/geoserver/ows?service=wfs&version=2.0.0&request=GetFeature&outputFormat=application/json"
GLEIF = "https://api.gleif.org/api/v1/lei-records"
GLEIF_TOP = 40   # las empresas que más producen o más participación tienen

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
http = requests.Session()
http.headers["User-Agent"] = "RastroMVP/0.1"

PRODUCCION_COLS = ["anio", "mes", "idpozo", "idempresa", "empresa", "prod_pet", "prod_gas", "formacion",
                   "idareapermisoconcesion", "areapermisoconcesion", "areayacimiento", "cuenca", "provincia",
                   "tipo_de_recurso", "sub_tipo_recurso", "tipoestado", "tipopozo"]
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


def lines(feat):
    """Todos los tramos de una línea, como [[[lon, lat], ...], ...]."""
    out = []
    for pl in re.findall(r"<gml:posList[^>]*>([^<]+)</gml:posList>", feat):
        v = pl.split()
        out.append([[float(v[i + 1]), float(v[i])] for i in range(0, len(v) - 1, 2)])
    return json.dumps(out)


def ign(layer):
    f = download(f"ign-{layer}.json", f"{IGN}&typeNames=ign:{layer}")
    return json.loads(f.read_text())["features"]


def exteriors(geometry):
    polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    return json.dumps([[[round(x, 6), round(y, 6)] for x, y, *_ in poly[0]] for poly in polys])


def gleif(names):
    """Los candidatos de GLEIF para cada nombre, en Argentina. Se guardan y no se vuelven a pedir."""
    rows = []
    for name in names:
        f = CACHE / "gleif" / (re.sub(r"[^A-Za-z0-9]+", "_", name)[:80] + ".json")
        if not f.exists():
            f.parent.mkdir(exist_ok=True)
            r = http.get(GLEIF, timeout=60, params={"filter[fulltext]": name, "filter[entity.legalAddress.country]": "AR",
                                                     "page[size]": 5})
            r.raise_for_status()
            f.write_text(r.text)
            time.sleep(1.05)   # GLEIF pide no pasar de 60 consultas por minuto
        for x in json.loads(f.read_text())["data"]:
            e = x["attributes"]["entity"]
            rows.append((name, x["attributes"]["lei"], e["legalName"]["name"],
                         " | ".join(o["name"] for o in e.get("otherNames") or []), e["status"],
                         e["legalAddress"]["country"]))
    return rows


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")

    produccion = ckan(PRODUCCION_2025, "produccion-2025.csv")
    anteriores = {anio: ckan(rid, f"produccion-{anio}.csv") for anio, rid in PRODUCCION_ANTERIOR.items()}
    padron = ckan(PADRON_POZOS, "pozos.csv")
    estudios = ckan(ESTUDIOS_AMBIENTALES, "estudios-ambientales.csv")
    concesiones = [(prop(f, "id_concesion"), prop(f, "areapermisoconcesion"), prop(f, "empresa_informante"),
                    prop(f, "empresa_operadora"), prop(f, "participacion"), prop(f, "estadodearea"),
                    prop(f, "observaciones"), ring(f))
                   for f in wfs_features("planosbase_concesiones_explotacion")]
    declarados = [(f.split('"', 2)[1], prop(f, "nombre"), prop(f, "tipo"), prop(f, "procedencia"),
                   prop(f, "nombre_procedencia"), prop(f, "empresa_informante"), prop(f, "empresa_operadora_area"),
                   *point(f)) for f in wfs_features("planosbase_puntos_venteo_declarados")]
    detectados = [(f.split('"', 2)[1], prop(f, "fecha"), prop(f, "provincia"), prop(f, "satelite"), *point(f))
                  for f in wfs_features("sensoresremotos_venteos_detectados")]
    gasoductos = [(f.split('"', 2)[1], prop(f, "nombregaso"), prop(f, "nombretram"), prop(f, "tipotramo"),
                   prop(f, "subtipotra"), prop(f, "licenciata"), lines(f))
                  for f in wfs_features("enargas_visor_gasoductos_transporte")]
    localidades = []
    for f in ign("localidad_bahra"):
        p = f["properties"]
        try:
            lon, lat = float(p["long_gd"]), float(p["lat_gd"])
        except (TypeError, ValueError):
            continue
        localidades.append((p["gid"], p["fna"], p["tipo_asent"], p["nom_pcia"], p["nom_depto"], lon, lat))
    areas = [(f["properties"]["gid"], f["properties"]["fna"], f["properties"]["fdc"], exteriors(f["geometry"]))
             for f in ign("area_protegida") if f.get("geometry")]

    with psycopg.connect(conninfo) as conn:
        conn.execute("""
            INSERT INTO rastro_meta.source (id, name, homepage, license, db_schema) VALUES
              ('capitulo4', 'Capítulo IV: producción y padrón de pozos (Secretaría de Energía)',
               'http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo', 'CC-BY 4.0', 'capitulo4'),
              ('sig_energia', 'Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite (WFS)',
               'https://sig.energia.gob.ar/wfsenergia', 'Datos públicos (Secretaría de Energía)', 'sig_energia'),
              ('enargas', 'Gasoductos de transporte (ENARGAS)', 'https://www.enargas.gob.ar/',
               'Datos públicos (ENARGAS, vía el WFS de la Secretaría de Energía)', 'enargas'),
              ('ign', 'Instituto Geográfico Nacional (IGN)', 'https://www.ign.gob.ar/',
               'CC-BY 4.0 (IGN)', 'ign'),
              ('gleif', 'GLEIF (LEI)', 'https://www.gleif.org/', 'CC0 1.0', 'gleif'),
              ('ambiental', 'Estudios ambientales de petróleo y gas (Secretaría de Energía)',
               'http://datos.energia.gob.ar/dataset/actividad-ambiental-petroleo-y-gas', 'CC-BY 4.0', 'ambiental')
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name""")
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
        for anio, f in anteriores.items():
            with f.open(encoding="utf-8-sig", newline="") as fh:
                copy("capitulo4.produccion_historica",
                     ([r[c] or None for c in PRODUCCION_COLS] for r in csv.DictReader(fh) if r["anio"] == str(anio)),
                     "capitulo4", f"producción {anio}")

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
        copy("enargas.gasoducto", gasoductos, "enargas", "WFS de la Secretaría de Energía")
        copy("ign.localidad", localidades, "ign", "WFS del IGN (BAHRA)")
        copy("ign.area_protegida", areas, "ign", "WFS del IGN")
        with estudios.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
            copy("ambiental.estudio",
                 ([r["id_estudio"], r["fecha_estudio"] or None, r["tipo_estudio"] or None, (r["concesion"] or "").strip() or None,
                   r["yacimiento"] or None, r["empresa"] or None, r["objeto_estudio"] or None, r["nombre_objeto"] or None,
                   (r["observaciones"] or "").strip() or None] for r in csv.DictReader(fh)),
                 "ambiental", "listado de estudios ambientales")

        # Las empresas que más producen u operan, con su nombre de las declaraciones juradas
        # Se busca sin forma societaria («YPF S.A.» → «YPF»): GLEIF busca por palabras
        names = [re.sub(r"\b(S\.?\s?A\.?\s?U?\.?|S\.?\s?R\.?\s?L\.?|S\.?\s?L\.?|SAU|LTD\.?)(\s|$)", " ", r[0]).strip(" .,")
                 for r in conn.execute(f"""
            SELECT trim(empresa) FROM capitulo4.produccion GROUP BY 1
            ORDER BY sum(prod_pet) + sum(prod_gas) DESC LIMIT {GLEIF_TOP}""")]
        copy("gleif_energia.candidato", gleif(names), "gleif", "API de GLEIF")


if __name__ == "__main__":
    main()
