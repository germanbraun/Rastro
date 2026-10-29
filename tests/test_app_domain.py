"""Render an unlisted domain through the existing app template in both views."""
import sys
from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "layer"))


@pytest.mark.parametrize("technical", [False, True])
def test_new_domain_renders_without_python_domain_lists(tmp_path, technical):
    (tmp_path / "ontology/queries").mkdir(parents=True)
    (tmp_path / "ontology/schema.ttl").write_text('''@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://example.org/library> a owl:Ontology .
<https://example.org/library#Book> a owl:Class; rdfs:label "Libro" .''')
    query = tmp_path / "ontology/queries/cq1.rq"
    query.write_text("# Libros publicados\nSELECT (2 AS ?answer) WHERE {}")
    cfg = {"domain": "library", "resumen": "Catálogo de prueba", "preguntas": [
        {"id": "q1", "simple": "¿Cuántos libros hay?", "tecnica": "Contar registros publicados",
         "query": str(query), "columnas": {"answer": "Libros"}}]}
    (tmp_path / "app.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True))
    registry = {"term_sources": {}, "link_sources": {}, "namespace": "https://example.org/library#", "ontology": "ontology/schema.ttl",
                "method": {"app": "app.yaml", "mapping": "mapping.ttl", "queries": "ontology/queries",
                           "ontop": {"port": 8090}}}
    # Only the transport and unrelated FAQ assets are stubbed. The actual render, ontology, console and config lookup run.
    script = f'''
from pathlib import Path
import streamlit as st
import dominio
from unittest.mock import patch
registry = {registry!r}
with patch.dict(dominio.answer.DOMAINS, {{"library": registry}}), \\
     patch.object(dominio.answer, "ROOT", Path({str(tmp_path)!r})), \\
     patch.object(dominio.common, "warm_up", lambda: None), \\
     patch.object(dominio.common, "sources", lambda domain: {{}}), \\
     patch.object(dominio.common, "llm_status", lambda: (False, "Sin LLM")), \\
     patch.object(dominio.common, "ayuda", lambda key: None), \\
     patch.object(dominio.faq, "show_faq", lambda *args: st.caption("Preguntas frecuentes")), \\
     patch.object(dominio.common, "run", lambda query, domain: (["answer"], [[2]])):
    dominio.render({str(tmp_path / "app.yaml")!r}, {technical!r})
'''
    app = AppTest.from_string(script).run(timeout=15)
    assert not app.exception, [error.message for error in app.exception]
    sections = next(radio for radio in app.radio if radio.key == "library_tab_open")   # the tabs (screen.show_sections)
    assert "Preguntar" in sections.options
    if technical:
        assert "Bajo el capó" in sections.options
    else:
        answer_button = next(button for button in app.button if button.label == "Responder")
        answer_button.click().run()
        assert not app.exception, [error.message for error in app.exception]
        assert len(app.dataframe) > 0


def test_pending_lifecycle_questions_are_not_exposed(tmp_path, monkeypatch):
    import dominio
    monkeypatch.setattr(dominio.answer, "ROOT", tmp_path)
    monkeypatch.setitem(dominio.answer.DOMAINS, "library", {"method": {"lifecycle": "state.json"}})
    assert dominio.validated_questions({"domain": "library", "preguntas": [{"id": "q1"}]}) == []


def test_change_check_in_english_keeps_its_numbers(monkeypatch):
    """Each domain declares the checks its change test records (avisos_cambio), with an English text."""
    import dominio
    import idioma

    def warnings(domain):
        es, en = (yaml.safe_load((ROOT / f"app/dominios/{domain}{ext}").read_text()) for ext in (".yaml", ".en.yaml"))
        return idioma.overlay(es, en)["avisos_cambio"]
    recorded = ("🟡 Control de unidades: el petróleo de 2025 suma 293,2 millones de m³, y la "
                "producción nacional ronda los 46,6: ¿cambió la unidad?")
    monkeypatch.setattr(idioma, "lang", lambda: "en")
    assert dominio.check_text(recorded, warnings("energia")) == (
        "2025 oil adds up to 293.2 million m³, and national production is around 46.6: did the unit change?")
    assert "US$10,000," in dominio.check_text("🟡 Control del recorte: hay contratos de US$10.000, y el recorte dice",
                                              warnings("proveedores"))
    assert dominio.check_text("🟡 Otro control: algo", warnings("energia")) == "algo"
    monkeypatch.setattr(idioma, "lang", lambda: "es")
    assert dominio.check_text(recorded, warnings("energia")) == recorded.split(": ", 1)[1]
    monkeypatch.setattr(idioma, "lang", lambda: "en")
    assert dominio.check_text("🟡 Control de vocabulario: 2 estados que la ontología no documenta: A, B",
                              warnings("oncologia")) == "2 statuses the ontology does not document: A, B"


def test_no_name_in_the_screen_code_hides_one_of_its_modules():
    """The modules call each other as module.name: a variable with a module's name (a tab called trust_view, say)
    would hide that module inside its function."""
    import ast
    package = ROOT / "app/dominio"
    modules = {p.stem for p in package.glob("*.py")} - {"__init__"}
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text())
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        names |= {a.arg for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.Lambda)) for a in n.args.args}
        assert not names & modules, f"{path.name}: {names & modules}"
