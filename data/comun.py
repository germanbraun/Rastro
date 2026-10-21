"""Lo que comparten los cargadores de datos.gob.ar (petróleo y gas, y Rastro Lab): descargar con caché y
reintentos, pedir un recurso al portal (CKAN) y cargar una tabla con COPY dejando su registro en
rastro_meta.load_run."""

import hashlib
from datetime import date
from pathlib import Path

import requests

CKAN = "http://datos.energia.gob.ar/api/3/action/resource_show?id="

http = requests.Session()
http.headers["User-Agent"] = "RastroMVP/0.1"


def descargar(carpeta: Path, nombre, url, verify=True, intentos=4):
    """Baja url a carpeta/nombre, una sola vez: si el archivo ya está, no se vuelve a pedir."""
    f = carpeta / nombre
    for intento in range(intentos):
        if f.exists():
            break
        print(f"  descargando {nombre}")
        try:
            with http.get(url, timeout=900, stream=True, verify=verify) as r:
                r.raise_for_status()
                tmp = f.with_suffix(".tmp")
                with tmp.open("wb") as out:
                    for chunk in r.iter_content(1 << 20):
                        out.write(chunk)
                tmp.rename(f)
        except requests.RequestException as e:   # el servidor corta descargas largas: se reintenta
            print(f"  falló ({e.__class__.__name__}), intento {intento + 1} de {intentos}")
    if not f.exists():
        raise RuntimeError(f"No se pudo descargar {nombre}")
    return f


def ckan(carpeta: Path, recurso, nombre):
    """Un recurso del portal datos.energia.gob.ar, por su identificador."""
    url = http.get(CKAN + recurso, timeout=60).json()["result"]["url"]
    return descargar(carpeta, nombre, url)


def huella(archivo: Path):
    """La huella SHA-256 de un archivo: si la fuente publica otra versión, cambia."""
    h = hashlib.sha256()
    with archivo.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def copiar(conn, tabla, filas, fuente, version, ancho=30, archivo: Path = None):
    """Carga filas en tabla con COPY y registra la carga en rastro_meta.load_run. Con archivo, registra también su
    nombre, su huella y el día en que se descargó, para saber qué versión de la fuente se cargó."""
    conn.execute("ALTER TABLE rastro_meta.load_run ADD COLUMN IF NOT EXISTS archivo text, "
                 "ADD COLUMN IF NOT EXISTS sha256 text, ADD COLUMN IF NOT EXISTS descargado date")
    n = 0
    with conn.cursor().copy(f"COPY {tabla} FROM STDIN") as cp:
        for fila in filas:
            cp.write_row(fila)
            n += 1
    datos = (archivo.name, huella(archivo), date.fromtimestamp(archivo.stat().st_mtime)) if archivo else (None, None, None)
    conn.execute("INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count, archivo, sha256, descargado) "
                 "VALUES (%s, %s, %s, %s, %s, %s, %s)", (fuente, version, tabla, n, *datos))
    print(f"  {tabla:<{ancho}}{n:>9} filas")
