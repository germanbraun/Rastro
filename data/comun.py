"""What the datos.gob.ar loaders share (oil and gas, and Rastro Lab): download with cache and
retries, request a resource from the portal (CKAN) and load a table with COPY, recording it in
rastro_meta.load_run."""

import hashlib
from datetime import date
from pathlib import Path

import requests

CKAN = "http://datos.energia.gob.ar/api/3/action/resource_show?id="

http = requests.Session()
http.headers["User-Agent"] = "RastroMVP/0.1"


def descargar(carpeta: Path, nombre, url, verify=True, intentos=4):
    """Downloads url to carpeta/nombre, only once: if the file is already there, it is not requested again."""
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
        except requests.RequestException as e:   # the server cuts long downloads: retry
            print(f"  falló ({e.__class__.__name__}), intento {intento + 1} de {intentos}")
    if not f.exists():
        raise RuntimeError(f"No se pudo descargar {nombre}")
    return f


def ckan(carpeta: Path, recurso, nombre):
    """A resource of the datos.energia.gob.ar portal, by its identifier."""
    url = http.get(CKAN + recurso, timeout=60).json()["result"]["url"]
    return descargar(carpeta, nombre, url)


def huella(archivo: Path):
    """The SHA-256 fingerprint of a file: if the source publishes another version, it changes."""
    h = hashlib.sha256()
    with archivo.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def copiar(conn, tabla, filas, fuente, version, ancho=30, archivo: Path = None):
    """Loads filas into tabla with COPY and records the load in rastro_meta.load_run. With archivo, it also records its
    name, its fingerprint and the day it was downloaded, to know which version of the source was loaded."""
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
