"""The reference review packet: the form's answers are read as the question's kind, the adjudications are found by
question, only the tables a query reads are listed, and nothing is recorded while a question is pending."""
import csv
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The script reads the registry through layer/answer.py and the database through psycopg; neither is needed here, so
# both are stand-ins while it loads, and the real modules (if other tests loaded them) are put back.
STAND_INS = {"psycopg": types.ModuleType("psycopg"),
             "answer": types.SimpleNamespace(DOMAINS={"demo": {"method": {"evaluation": {"folder": "layer/demo"}}}})}
saved = {name: sys.modules.get(name) for name in STAND_INS}
sys.modules.update(STAND_INS)
try:
    SPEC = importlib.util.spec_from_file_location("review_packet", ROOT / "layer/review_packet.py")
    packet = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(packet)
finally:
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name)
        else:
            sys.modules[name] = module


def test_answers_by_kind():
    assert packet.parse("12570093.35", "número") == 12570093.35
    assert packet.parse(" YPF S.A.; TECPETROL S.A. ;", "lista") == ["YPF S.A.", "TECPETROL S.A."]
    assert not packet.differs(12570100.0, 12570093.35)
    assert packet.differs(15700.0, 15809.0)
    assert not packet.differs(["ypf s.a."], ["YPF S.A."])


def test_adjudications_by_question(tmp_path):
    path = tmp_path / "adjudicacion.md"
    path.write_text("| Pregunta | Diferencia | Qué se encontró | Resultado |\n|---|---|---|---|\n"
                    "| e05 (gasoductos) | 33 vs 29 | Error de Rastro | Referencia: 33 |\n"
                    "| e02, forma 2 | 6.263 | Otra lectura | Respuesta distinta |\n")
    rows = packet.adjudications(path)
    assert set(rows) == {"e05", "e02"} and rows["e05"][0][3] == "Referencia: 33"


def test_only_the_tables_a_query_reads():
    known = {"capitulo4.produccion": (("Capítulo IV", "http://x"), "2025", None, "2026-10-20"),
             "sig_energia.concesion": (("Mapas", "http://y"), "WFS", "abcdef0123456789", "2026-10-20")}
    used = packet.tables_in("select * from capitulo4.produccion p join otro.tabla t on p.x = t.x", known)
    assert used == ["capitulo4.produccion"]
    lines = packet.source_lines(["capitulo4.produccion", "sig_energia.concesion"], known)
    assert len(lines) == 2 and "sha256 abcdef012345" in lines[1]


def test_nothing_recorded_while_pending(tmp_path, monkeypatch):
    (tmp_path / "eval").mkdir()
    (tmp_path / "revision").mkdir()
    (tmp_path / "eval" / "questions.yaml").write_text(
        "questions:\n  - {id: e01, kind: número}\n  - {id: e02, kind: lista}\n")
    with (tmp_path / "revision" / "formulario.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, packet.FORM_COLUMNS)
        writer.writeheader()
        writer.writerow({"pregunta": "e01", "respuesta_rastro": "1", "respuesta_revisada": "1",
                         "fuentes_y_version": "x", "como_lo_verifique": "y", "revisor": "", "fecha": "2026-10-29",
                         "estado": "revisada"})
    monkeypatch.setattr(packet, "folder", lambda domain: tmp_path)
    assert packet.record("demo") == 1
    assert not (tmp_path / "eval" / "referencias.json").exists()
    assert not (tmp_path / "reference-evidence.yaml").exists()
