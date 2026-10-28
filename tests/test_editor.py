"""The checks of the SPARQL and R2RML editors in «Bajo el capó»: a syntax error points at its line, a term the
dictionary does not declare is reported, and a mapping is saved only as a whole, valid file."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "app"), str(ROOT / "layer")]

PREFIX = "PREFIX energia: <https://w3id.org/rastro/energia#>\n"


@pytest.fixture(autouse=True)
def spanish(monkeypatch):
    import idioma
    monkeypatch.setattr(idioma, "lang", lambda: "es")


def test_a_valid_query_passes():
    from dominio import editor
    assert editor.sparql_check(PREFIX + "SELECT ?w WHERE { ?w a energia:Well } LIMIT 5", "energia") == ([], [])


def test_a_syntax_error_points_at_its_line():
    from dominio import editor
    problems, _ = editor.sparql_check(PREFIX + "SELECT ?w WHERE {\n  ?w a energia:Well\n  FILTER( }", "energia")
    assert len(problems) == 1 and problems[0][0] == 4


def test_a_term_the_dictionary_lacks_is_reported():
    from dominio import editor
    problems, warnings = editor.sparql_check(PREFIX + "SELECT ?w WHERE { ?w a energia:Pozo }", "energia")
    assert not problems and "energia:Pozo" in warnings[0]


def test_the_real_mapping_passes():
    from dominio import editor
    problems, warnings, maps = editor.mapping_check((ROOT / "mappings/energia.r2rml.ttl").read_text(), "energia")
    assert problems == [] and maps > 10


def test_a_broken_mapping_is_caught():
    from dominio import editor
    text = (ROOT / "mappings/energia.r2rml.ttl").read_text()
    problems, _, _ = editor.mapping_check(text.replace(" ;\n", " \n", 1), "energia")   # a missing «;»
    assert problems and problems[0][0] > 1
    missing_subject = ("@prefix rr: <http://www.w3.org/ns/r2rml#> .\n"
                       "<#Solo> a rr:TriplesMap ; rr:logicalTable [ rr:tableName \"t\" ] .\n")
    problems, _, _ = editor.mapping_check(missing_subject, "energia")
    assert any("rr:subjectMap" in text for _, _, text in problems) and problems[0][0] == 2
    unknown = ("@prefix rr: <http://www.w3.org/ns/r2rml#> .\n@prefix energia: <https://w3id.org/rastro/energia#> .\n"
               "<#X> a rr:TriplesMap ; rr:logicalTable [ rr:tableName \"t\" ] ;\n"
               "  rr:subjectMap [ rr:template \"x/{id}\" ; rr:class energia:Pozo ] .\n")
    problems, _, _ = editor.mapping_check(unknown, "energia")
    assert any("energia:Pozo" in text for _, _, text in problems)


def test_saving_keeps_the_previous_file(tmp_path, monkeypatch):
    from dominio import editor
    mapping = tmp_path / "mappings" / "x.r2rml.ttl"
    mapping.parent.mkdir()
    mapping.write_text("old")
    monkeypatch.setattr(editor, "mapping_path", lambda domain: mapping)
    backup = editor.save_mapping("energia", "new")
    assert mapping.read_text() == "new" and backup.read_text() == "old" and backup.parent.name == ".backup"
