"""«Uniones para confirmar» (app/dominio/review_view.py): confirming and rejecting, on a copy of a reviewed CSV."""
import datetime
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "layer"))
import enlaces  # noqa: E402
from dominio import review_view  # noqa: E402

DAY = datetime.date(2026, 10, 29)


@pytest.fixture
def corrections(tmp_path):
    path = tmp_path / "correcciones.csv"
    shutil.copy(ROOT / "linking/energia/correcciones.csv", path)
    return path


def test_every_waiting_row_is_found(corrections):
    waiting = review_view.pending([corrections])
    assert waiting and all(enlaces.status("corrección revisada", row["motivo"]) == "ia" for _, _, row in waiting)


def test_confirming_turns_the_link_confirmed_by_a_person(corrections):
    _, index, row = review_view.pending([corrections])[0]
    review_view.confirm(corrections, index, "Ana Pérez", "Boletín Oficial, 3 de mayo de 2024, p. 12", today=DAY)
    motivo = review_view.read(corrections)[1][index]["motivo"]
    assert "Confirmado por Ana Pérez el 29/10/2026, con este documento: Boletín Oficial" in motivo
    assert enlaces.AI not in motivo and enlaces.status("corrección revisada", motivo) == "persona"
    assert motivo.startswith(row["motivo"].replace(review_view.AI_SENTENCE, "").strip()[:30])   # the reason stays


def test_rejecting_moves_the_row_and_keeps_why(corrections):
    before = review_view.read(corrections)[1]
    _, index, row = review_view.pending([corrections])[0]
    review_view.reject(corrections, index, "Ana Pérez", "Son empresas distintas", today=DAY)
    assert len(review_view.read(corrections)[1]) == len(before) - 1
    fields, kept = review_view.read(corrections.with_name("correcciones-rechazadas.csv"))
    assert kept == [{**row, "rechazado_por": "Ana Pérez", "fecha": "29/10/2026", "razon": "Son empresas distintas"}]


def test_nothing_is_written_without_who_and_the_document(corrections):
    before = corrections.read_text()
    with pytest.raises(ValueError):
        review_view.confirm(corrections, 0, "Ana Pérez", " ")
    with pytest.raises(ValueError):
        review_view.reject(corrections, 0, "", "porque sí")
    assert corrections.read_text() == before


def test_the_files_are_written_as_they_were(corrections):
    fields, rows = review_view.read(corrections)
    review_view.write(corrections, fields, rows)
    assert corrections.read_text() == (ROOT / "linking/energia/correcciones.csv").read_text()


@pytest.fixture
def decisions(tmp_path):
    path = tmp_path / "correcciones.csv"
    shutil.copy(ROOT / "linking/afiliaciones/correcciones.csv", path)
    return path


def test_the_confirmation_column_format_is_reviewed(decisions):
    waiting = review_view.pending([decisions])
    assert len(waiting) == len(review_view.read(decisions)[1])   # all «pending» today
    _, index, _ = waiting[0]
    review_view.confirm(decisions, index, "Ana Pérez", "sitio web de la organización", today=DAY)
    _, rejected_index, _ = review_view.pending([decisions])[0]
    review_view.reject(decisions, rejected_index, "Ana Pérez", "La sigla es de otra institución", today=DAY)
    rows = review_view.read(decisions)[1]
    assert rows[index]["human_confirmation"] == "confirmed by Ana Pérez on 2026-10-29; evidence: sitio web de la organización"
    assert rows[rejected_index]["human_confirmation"] == "rejected by Ana Pérez on 2026-10-29; reason: La sigla es de otra institución"
    assert len(rows) == len(waiting) and len(review_view.pending([decisions])) == len(waiting) - 2   # rows stay


def test_the_records_match_the_approved_quality_rule(decisions):
    import re
    rule = (ROOT / "ontology/afiliaciones/calidad/reglas.ttl").read_text()
    pattern = re.search(r'humanConfirmation ; sh:minCount 1 ; sh:maxCount 1 ;\s*sh:pattern "(.+?)" ;', rule).group(1)
    pattern = pattern.replace("\\\\", "\\")
    review_view.confirm(decisions, 0, "Ana Pérez", "sitio web", today=DAY)
    review_view.reject(decisions, 1, "Ana Pérez", "otra institución", today=DAY)
    for row in review_view.read(decisions)[1][:3]:
        assert re.match(pattern, row["human_confirmation"]), row["human_confirmation"]


def test_the_linker_does_not_apply_a_rejected_decision(decisions, monkeypatch):
    sys.path.insert(0, str(ROOT / "linking/afiliaciones"))
    import link
    review_view.reject(decisions, 0, "Ana Pérez", "otra institución", today=DAY)
    monkeypatch.setattr(link, "HERE", decisions.parent)
    reviewed = link.corrections()
    first = review_view.read(decisions)[1][0]
    key = (first["doi"], int(first["author_position"]), int(first["affiliation_position"]), first["organization"])
    assert reviewed[key][:2] == (None, None) and reviewed[key][2].startswith("rejected by Ana Pérez")

