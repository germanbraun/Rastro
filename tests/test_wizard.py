"""The wizard's sketch (app/wizard.py) as a buyer sees it: no internal names in its texts, and a typed question
matched to an approved one only when they share a word. The screens read the demo's files at their container paths,
so they are walked in a real browser, not here."""
import sys
from pathlib import Path

import pytest
import yaml

pytest.importorskip("streamlit")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "layer"))
import wizard  # noqa: E402

INTERNAL = ("inspect-sources", "add-source", "install.sh", "docs/", "infra/", "Agent SDK", "skill")


def visible_texts():
    """Every text the sketch shows: its steps in both languages and the wizard.* and its start-page texts."""
    for name in ("wizard.yaml", "wizard.en.yaml"):
        for step in yaml.safe_load((ROOT / "app" / name).read_text())["pasos"]:
            yield from (v for k, v in step.items() if k != "id")
    texts = yaml.safe_load((ROOT / "app/textos/inicio.yaml").read_text())
    for key, value in texts.items():
        if key.startswith(("wizard.", "inicio.wizard")):
            yield from (value.values() if isinstance(value, dict) else [value])


@pytest.mark.parametrize("word", INTERNAL)
def test_the_sketch_names_no_internal_piece(word):
    found = [t for t in visible_texts() if word.lower() in t.lower()]
    assert not found, found


APPROVED = [{"simple": "¿Cuánto petróleo le corresponde a cada empresa?", "tecnica": "participación por concesión"},
            {"simple": "¿Qué concesiones hay que revisar por venteos?", "tecnica": "venteos y gasoductos"}]


def test_a_question_is_matched_only_when_it_shares_a_word():
    assert wizard.closest("¿Cuánto petróleo produjo YPF?", APPROVED) is APPROVED[0]
    assert wizard.closest("venteos cerca de gasoductos", APPROVED) is APPROVED[1]
    assert wizard.closest("¿Quién ganó el partido?", APPROVED) is None
    assert wizard.closest("¿Cuánto cuesta un café?", APPROVED) is None   # a question word alone is not a match
    assert wizard.closest("algo", []) is None
