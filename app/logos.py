"""El favicon de cada empresa junto a su nombre, en las tablas de respuestas de los tres dominios.

app/sitios.yaml (lo arma layer/sitios.py) dice el sitio web de cada empresa por su nombre
normalizado. La app pide cada ícono una vez al servicio público de favicons de Google y lo guarda
en memoria (la tabla no puede dibujar imágenes de otro sitio). Sin internet, la columna queda vacía.
"""

import base64
import re
import unicodedata
from pathlib import Path

import requests
import streamlit as st
import yaml

FORMS = r"\b(THE|INC|INCORPORATED|LLC|L L C|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|LP|LLP|PLC|SA|SAU|SRL|SL|AG|SE|GMBH|NV|BV|HOLDINGS?|GROUP)\b"
# Columnas que nombran una empresa (las variables de las consultas, en los tres dominios)
COMPANY_COLUMNS = {"group", "supplier", "finalParent", "company", "operator", "sponsor", "sponsorName",
                   "empresa", "operadora", "grupo", "proveedor", "previous", "new", "partner"}
ICON = "https://www.google.com/s2/favicons?sz=64&domain="
ICON_ALT = "https://icons.duckduckgo.com/ip3/{}.ico"


def normalize(name):
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().upper()
    text = re.sub(r"[^A-Z0-9 ]", " ", text.replace("&", " AND "))
    return " ".join(re.sub(FORMS, " ", text).split())


@st.cache_data
def _sites(mtime):
    return yaml.safe_load(Path("/app/sitios.yaml").read_text()) or {}


@st.cache_data(show_spinner=False, persist="disk")   # en disco: los íconos no se piden de nuevo al reiniciar
def icon(domain):
    """El favicon como imagen incrustada (data URI), o None si no se pudo traer. Si Google no lo
    tiene, se prueba el servicio de íconos de DuckDuckGo."""
    for url in (ICON + domain, ICON_ALT.format(domain)):
        try:
            r = requests.get(url, timeout=5)
        except requests.RequestException:
            continue
        kind = r.headers.get("content-type", "").split(";")[0]
        if r.status_code == 200 and kind.startswith("image/"):   # sin favicon, los servicios responden 404
            return f"data:{kind};base64," + base64.b64encode(r.content).decode()
    return None


def site(name):
    """El sitio de la empresa; si no está, el del grupo cuyo nombre es el comienzo del suyo
    («BAE SYSTEMS LAND AND ARMAMENTS» → «BAE SYSTEMS»)."""
    p = Path("/app/sitios.yaml")
    if not p.exists():
        return None
    sites, words = _sites(p.stat().st_mtime), normalize(name).split()
    for k in range(len(words), 0, -1):
        key = " ".join(words[:k])
        if key in sites and (k == len(words) or len(key) >= 4):
            return sites[key]
    return None


def with_logos(table, columns):
    """Agrega, antes de cada columna de empresa, una columna con su favicon. Devuelve la tabla y
    la configuración de columnas para st.dataframe."""
    config = {}
    for i, var in reversed(list(enumerate(columns))):
        if var not in COMPANY_COLUMNS:
            continue
        header = table.columns[i]
        icons = [(icon(s) if (s := site(v)) else None) or "" for v in table[header]]
        if not any(icons):
            continue
        logo = f" {header}"   # un encabezado distinto por columna, casi invisible
        table.insert(i, logo, icons)
        config[logo] = st.column_config.ImageColumn(" ", width="small")
    return table, config
