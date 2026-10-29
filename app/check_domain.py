"""Exercise a configured domain's example queries and both real app views.

Run inside the app service: python /app/check_domain.py <domain>.
No transport stubs are used; live services and validated questions are prerequisites.
"""
import argparse
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))
import answer
import dominio


def check(domain):
    cfg = answer.DOMAINS[domain]
    config_path = ROOT / cfg["method"]["app"]
    app_config = dominio.load_config(config_path)
    questions = dominio.validated_questions(app_config)
    if not questions or len(questions) != len(app_config["preguntas"]):
        raise ValueError("Every app question must have a current validation receipt")
    for question in questions:
        columns, rows = dominio.run(Path(question["query"]).read_text(), domain)
        if not columns:
            raise ValueError(f"{question['id']}: example query returned no result schema")
        print(f"{question['id']}: {len(rows)} data rows (answer assertions are a separate gate)")
    for tech in (False, True):
        app = AppTest.from_string(f"import dominio\ndominio.render({str(config_path)!r}, {tech!r})").run(timeout=300)
        if app.exception:
            raise RuntimeError("\n".join(error.message for error in app.exception))
        # Only the open section is drawn (screen.show_sections), so each one is opened in turn
        sections = next(radio for radio in app.radio if radio.key == f"{app_config['domain']}_tab_open")
        expected = "Bajo el capó" if tech else "Preguntar"
        if expected not in sections.options:
            raise ValueError(f"Required app view did not render: {expected}")
        # The section names screen.render uses; the radio shows each one's label
        names = [n for n in ("demo", "ask", "trust", "model", "example", "method", "faq", "hood")
                 if sections.format_func(n) in sections.options]
        for name in names:
            app.radio(key=sections.key).set_value(name).run(timeout=300)
            if app.exception:
                raise RuntimeError(f"{name}: " + "\n".join(error.message for error in app.exception))
        if len(names) != len(sections.options):
            raise ValueError(f"Sections not opened: {sections.options}")
        print(f"{'technical' if tech else 'business'} view: passed, {len(names)} sections opened")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain")
    check(parser.parse_args().domain)
