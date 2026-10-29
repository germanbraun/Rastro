"""The interface language: Spanish by default, English on request.

Visible texts live in YAML. Texts used by the code are in app/textos/*.yaml, one entry per key with «es» and «en».
A domain's configuration, the help texts and the FAQ get an English overlay next to them (<name>.en.yaml) holding
only the texts, laid over the Spanish file. Anything not translated yet falls back to Spanish. Data from the sources
(names, evidence, rules) is shown as it comes.
"""
import time
from pathlib import Path

import streamlit as st
import yaml

LANGUAGES = {"es": "Español", "en": "English"}
DEFAULT = "en"   # the language a visit opens in (decided on 2026-10-29)
APP = Path(__file__).parent
TEXTS = APP / "textos"


def lang():
    return st.session_state.get("lang", "es")


def init():
    """The language, set once per session before anything is drawn: the app opens in English; «?lang=es» in the
    address, or the switch, shows it in Spanish. (Spanish stays the texts' base language, and lang()'s fallback outside
    a session, as the checks and scripts use it.)"""
    if "lang" not in st.session_state:
        asked = st.query_params.get("lang")
        st.session_state["lang"] = asked if asked in LANGUAGES else DEFAULT


def selector():
    """The switch in the sidebar.

    Its label is translated, so switching language makes Streamlit see a new widget and reset it to the first option.
    The language therefore lives in its own key («lang»), and the widget starts from it and writes back to it."""
    init()
    st.radio(t("app.language"), list(LANGUAGES), index=list(LANGUAGES).index(lang()), format_func=LANGUAGES.get,
             key="lang_choice", horizontal=True,
             on_change=lambda: st.session_state.update(lang=st.session_state["lang_choice"]))


_TEXTS = {"checked": 0.0, "stamp": None, "texts": {}}


def _texts():
    """All code texts, read again when a file in app/textos changes. A page draws hundreds of texts, so the files'
    dates are checked at most once a second, not on every text."""
    now = time.monotonic()
    if now - _TEXTS["checked"] > 1:
        stamp = tuple(p.stat().st_mtime for p in sorted(TEXTS.glob("*.yaml")))
        if stamp != _TEXTS["stamp"]:
            merged = {}
            for path in sorted(TEXTS.glob("*.yaml")):
                merged.update(yaml.safe_load(path.read_text()) or {})
            _TEXTS.update(stamp=stamp, texts=merged)
        _TEXTS["checked"] = now
    return _TEXTS["texts"]


def t(key, **values):
    """A code text in the current language; a key missing in the files is a bug and fails loudly."""
    entry = _texts()[key]
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


def scaled(value, scale, language=None, decimals=None):
    """A quantity in the unit the business view shows: value / scale, where each domain declares its units and their
    scale in its YAML («unidades»; oil and gas shows m³ in millions, scale 1e6). Two decimals under 10, one above;
    three when it is tiny. A column passes the decimals of its largest value (column_decimals), so all its numbers
    line up."""
    v = float(value) / scale
    return format_number(v, decimals_for(v) if decimals is None else decimals, language or lang())


def decimals_for(v):
    return 1 if abs(v) >= 10 else 2 if abs(v) >= 0.1 or v == 0 else 3


def column_decimals(values, scale):
    """The decimals for a whole column of quantities shown as value / scale: those of its largest value."""
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
