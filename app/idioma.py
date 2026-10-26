"""The interface language: Spanish by default, English on request.

Visible texts live in YAML. Texts used by the code are in app/textos/*.yaml, one entry per key with «es» and «en».
A domain's configuration, the help texts and the FAQ get an English overlay next to them (<name>.en.yaml) holding
only the texts, laid over the Spanish file. Anything not translated yet falls back to Spanish. Data from the sources
(names, evidence, rules) is shown as it comes.
"""
from pathlib import Path

import streamlit as st
import yaml

LANGUAGES = {"es": "Español", "en": "English"}
APP = Path(__file__).parent
TEXTS = APP / "textos"


def lang():
    return st.session_state.get("lang", "es")


def init():
    """The language, set once per session before anything is drawn: «?lang=en» in the address opens it in English."""
    if "lang" not in st.session_state:
        asked = st.query_params.get("lang")
        st.session_state["lang"] = asked if asked in LANGUAGES else "es"


def selector():
    """The switch in the sidebar."""
    init()
    st.radio(t("app.language"), list(LANGUAGES), format_func=LANGUAGES.get, key="lang", horizontal=True)


@st.cache_data
def _texts(stamp):
    merged = {}
    for path in sorted(TEXTS.glob("*.yaml")):
        merged.update(yaml.safe_load(path.read_text()) or {})
    return merged


def t(key, **values):
    """A code text in the current language; a key missing in the files is a bug and fails loudly."""
    entry = _texts(tuple(p.stat().st_mtime for p in sorted(TEXTS.glob("*.yaml"))))[key]
    text = entry.get(lang()) or entry["es"]
    return text.format(**values) if values else text


def overlay(base, extra):
    """Lay the English texts over the Spanish structure: dictionaries by key, lists of items with an «id» by id,
    other lists by position. Keys the Spanish file does not have are ignored, so the structure stays in one place."""
    if isinstance(base, dict) and isinstance(extra, dict):
        return {key: overlay(value, extra[key]) if key in extra else value for key, value in base.items()}
    if isinstance(base, list) and isinstance(extra, list):
        if base and all(isinstance(item, dict) and "id" in item for item in base + extra):
            by_id = {item["id"]: item for item in extra}
            return [overlay(item, by_id[item["id"]]) if item["id"] in by_id else item for item in base]
        return [overlay(b, e) for b, e in zip(base, extra)] + base[len(extra):]
    return base if extra is None else extra


def number(value, decimals=0):
    """A number in the interface's format: 12.345,6 in Spanish, 12,345.6 in English."""
    return format_number(value, decimals, lang())


def format_number(value, decimals, language):
    text = f"{float(value):,.{decimals}f}"
    return text if language == "en" else text.replace(",", "X").replace(".", ",").replace("X", ".")


def millions(value, unit="m3", language=None, decimals=None):
    """A volume in millions of m³, the one unit of the business view: «m3» values are in m³, «miles_m3» in
    thousands of m³ (gas as the sources declare it). Two decimals under 10, one above; three when it is tiny. A
    column passes the decimals of its largest value (column_decimals), so all its numbers line up."""
    v = float(value) / (1e6 if unit == "m3" else 1e3)
    return format_number(v, decimals_for(v) if decimals is None else decimals, language or lang())


def decimals_for(v):
    return 1 if abs(v) >= 10 else 2 if abs(v) >= 0.1 or v == 0 else 3


def column_decimals(values, unit="m3"):
    """The decimals for a whole column of volumes: those of its largest value."""
    scale = 1e6 if unit == "m3" else 1e3
    numbers = [abs(float(v)) / scale for v in values if v not in (None, "")]
    return decimals_for(max(numbers)) if numbers else 1


def english_path(path):
    path = Path(path)
    return path.with_name(path.stem + ".en.yaml")


@st.cache_data
def _localized(path, stamp, language):
    data = yaml.safe_load(Path(path).read_text())
    english = english_path(path)
    if language == "en" and english.exists():
        data = overlay(data, yaml.safe_load(english.read_text()) or {})
    return data


def localized(path):
    """A YAML file of visible texts, with its English overlay when the interface is in English."""
    english = english_path(path)
    stamp = (Path(path).stat().st_mtime, english.stat().st_mtime if english.exists() else 0)
    return _localized(str(path), stamp, lang())
