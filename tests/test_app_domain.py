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
     patch.object(dominio, "warm_up", lambda: None), \\
     patch.object(dominio, "sources", lambda domain: {{}}), \\
     patch.object(dominio, "llm_status", lambda: (False, "Sin LLM")), \\
     patch.object(dominio, "ayuda", lambda key: None), \\
     patch.object(dominio, "show_faq", lambda *args: st.caption("Preguntas frecuentes")), \\
     patch.object(dominio, "run", lambda query, domain: (["answer"], [[2]])):
    dominio.render({str(tmp_path / "app.yaml")!r}, {technical!r})
'''
    app = AppTest.from_string(script).run(timeout=15)
    assert not app.exception, [error.message for error in app.exception]
    assert any("Preguntar" in tab.label for tab in app.tabs)
    if technical:
        assert any("Bajo el capó" in tab.label for tab in app.tabs)
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
