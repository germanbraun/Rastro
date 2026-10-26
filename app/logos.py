"""Company icons beside names: retained official assets first, remote favicons as fallback.

app/sitios.yaml maps normalized company names to websites. Retained assets and their
source receipts live under app/company-icons; unknown icons remain blank.
"""

import base64
import re
import unicodedata
from pathlib import Path

import requests
import streamlit as st
import yaml

FORMS = (r"\b(THE|INC|INCORPORATED|LLC|L L C|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|LP|LLP|PLC"
         r"|SA|SAU|SRL|SL|AG|SE|GMBH|NV|BV|HOLDINGS?|GROUP)\b")
# Columns that name a company (the query variables, in the three domains)
COMPANY_COLUMNS = {"group", "supplier", "finalParent", "company", "operator", "sponsor", "sponsorName",
                   "empresa", "operadora", "grupo", "proveedor", "previous", "new", "partner"}
ICON = "https://www.google.com/s2/favicons?sz=64&domain="
ICON_ALT = "https://icons.duckduckgo.com/ip3/{}.ico"
LOCAL_ICONS = Path(__file__).with_name('company-icons')


def icon(domain):
    """Prefer a retained official icon so the demo also works offline."""
    if re.fullmatch(r'[a-zA-Z0-9.-]+', domain):
        for ext, mime in [('png', 'image/png'), ('svg', 'image/svg+xml'), ('ico', 'image/x-icon'),
                          ('jpg', 'image/jpeg'), ('gif', 'image/gif')]:
            path = LOCAL_ICONS / f'{domain}.{ext}'
            if path.is_file():
                return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()
    return remote_icon(domain)


def normalize(name):
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().upper()
    text = re.sub(r"[^A-Z0-9 ]", " ", text.replace("&", " AND "))
    return " ".join(re.sub(FORMS, " ", text).split())


@st.cache_data
def _sites(mtime):
    return yaml.safe_load(Path("/app/sitios.yaml").read_text()) or {}


@st.cache_data(show_spinner=False, persist="disk")   # on disk: icons are not fetched again on restart
def remote_icon(domain):
    """The favicon as an embedded image (data URI), or None if it could not be fetched. If Google does not
    have it, DuckDuckGo's icon service is tried."""
    for url in (ICON + domain, ICON_ALT.format(domain)):
        try:
            r = requests.get(url, timeout=5)
        except requests.RequestException:
            continue
        kind = r.headers.get("content-type", "").split(";")[0]
        if r.status_code == 200 and kind.startswith("image/"):   # without a favicon, the services return 404
            return f"data:{kind};base64," + base64.b64encode(r.content).decode()
    return None


def site(name):
    """The company's website; if missing, that of the group whose name is the start of its own
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
    """Adds, before each company column, a column with its favicon. Returns the table and
    the column configuration for st.dataframe."""
    config = {}
    for i, var in reversed(list(enumerate(columns))):
        if var not in COMPANY_COLUMNS:
            continue
        header = table.columns[i]
        icons = [(icon(s) if (s := site(v)) else None) or "" for v in table[header]]
        if not any(icons):
            continue
        logo = f" {header}"   # a different header per column, almost invisible
        table.insert(i, logo, icons)
        config[logo] = st.column_config.ImageColumn(" ", width="small")
    return table, config
