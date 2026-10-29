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
