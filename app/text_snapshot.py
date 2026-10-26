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


def oncology(lang):
    """Oncology has its own screen in app/app.py, reached with «Ver detalles técnicos» and the domain selector."""
    app = AppTest.from_file("/app/app.py", default_timeout=600)
    app.session_state["lang"] = lang
    app.run()
    next(t for t in app.toggle if not t.key).set_value(True).run()
    radio = next(r for r in app.radio if r.key == "domain")
    import yaml

    import idioma
    domains = yaml.safe_load(open("/app/dominios.yaml"))
    if lang == "en":   # the selector shows the English names: pick the same entry the app builds
        domains = idioma.overlay(domains, yaml.safe_load(open("/app/dominios.en.yaml")))
    entry = next(d for d in domains if d["id"] == "oncologia")
    radio.set_value(entry).run()
    return {"technical": {"exceptions": [e.message for e in app.exception], "texts": texts(app)}}


def main(domain, lang, out):
    config = f"/app/dominios/{domain}.yaml"
    result = {}
    if domain == "oncologia":
        result = oncology(lang)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        print({view: (len(v["texts"]), len(v["exceptions"])) for view, v in result.items()})
        return
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
