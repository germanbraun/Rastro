"""One status mark for every link, and contrast cards whose numbers are read, not typed."""
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
sys.path.insert(0, str(APP))
import enlaces  # noqa: E402


@pytest.mark.parametrize("rule, evidence, expected", [
    ("corrección revisada", "Revisado por un asistente de IA, a confirmar por una persona.", "ia"),
    ("corrección revisada", "", "ia"),
    ("corrección revisada con documento", "Corrección revisada: ... Documento: Acuerdo Marco ...", "persona"),
    ("texto de socios del mapa", "YPF S.A.: 50 %", "regla"),
    ("rige la declaración jurada", "Declara la producción de 12/2025: CGC ENERGIA SAU.", "regla"),
    ("mismo nombre normalizado", None, "regla"),
])
def test_status(rule, evidence, expected):
    assert enlaces.status(rule, evidence) == expected


def cards():
    for path in sorted((APP / "dominios").glob("*.yaml")):
        for item in (yaml.safe_load(path.read_text()) or {}).get("preguntas", []):
            if isinstance(item, dict) and item.get("antes_despues", {}).get("valores"):
                yield path, item["id"], item["antes_despues"]


@pytest.mark.parametrize("path, qid, card", list(cards()), ids=lambda x: x if isinstance(x, str) else None)
def test_live_contrast_has_no_typed_numbers(path, qid, card):
    """A card that reads its numbers names them in braces: no figure is typed in its texts (dates aside)."""
    english = yaml.safe_load(path.with_name(path.stem + ".en.yaml").read_text()) if path.with_name(
        path.stem + ".en.yaml").exists() else {}
    translated = next((q.get("antes_despues", {}) for q in english.get("preguntas", []) if q.get("id") == qid), {})
    for texts in (card, translated):
        for part in ("sin", "con", "impacto"):
            text = texts.get(part)
            text = " ".join(text.values()) if isinstance(text, dict) else (text or "")
            text = re.sub(r"\{\w+\}|\b(19|20)\d\d\b|m³", "", text)
            assert not re.search(r"\d", text), f"{qid} {part}: a typed number in «{text}»"
