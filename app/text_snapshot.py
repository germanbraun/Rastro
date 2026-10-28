"""Capture every text the app shows for a domain, in one language, to compare languages and catch regressions.

Run inside the app service: python /app/text_snapshot.py <domain> <es|en> <out.json>. Renders the business and
technical views with Streamlit's AppTest (every tab runs) and lists each element's visible text.
"""
import json
import sys

from streamlit.testing.v1 import AppTest

KINDS = ["title", "header", "subheader", "markdown", "caption", "info", "warning", "success", "error", "metric",
         "button", "toggle", "radio", "selectbox", "expander", "tabs", "text_input", "text_area"]


def texts(app):
    found = []
    for kind in KINDS:
        for element in getattr(app, kind, []):
            for attribute in ("value", "label", "options", "help"):
                value = getattr(element, attribute, None)
                if isinstance(value, str) and value.strip():
                    found.append(f"{kind}.{attribute}: {value}")
                elif isinstance(value, (list, tuple)):
                    found.extend(f"{kind}.{attribute}: {v}" for v in value if isinstance(v, str))
    for frame in app.dataframe:
        found.append("dataframe.columns: " + " | ".join(map(str, frame.value.columns)))
    return found


def main(domain, lang, out):
    config = f"/app/dominios/{domain}.yaml"
    result = {}
    for tech in (False, True):
        script = (f"import sys\nsys.path.insert(0, '/layer')\nimport streamlit as st\n"
                  f"st.session_state.setdefault('lang', {lang!r})\n"
                  f"import dominio\ndominio.render({config!r}, {tech!r})")
        app = AppTest.from_string(script).run(timeout=600)
        result["technical" if tech else "business"] = {"exceptions": [e.message for e in app.exception],
                                                       "texts": texts(app)}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print({view: (len(v["texts"]), len(v["exceptions"])) for view, v in result.items()})


if __name__ == "__main__":
    main(*sys.argv[1:4])
