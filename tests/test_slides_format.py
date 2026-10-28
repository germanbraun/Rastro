"""Every slide of a deck can be published to the shared deck as it is: one <section> with inline styles only (the
shared deck's format drops <style> blocks, classes and margins), and every measured number a placeholder that the
build fills from docs/slides/numeros/."""
import json
import re
from pathlib import Path

import pytest

SLIDES = Path(__file__).resolve().parents[1] / "docs/slides"
IN_A_DECK = sorted({name for deck in (SLIDES / "mazos").glob("*.json") for name in json.loads(deck.read_text())["order"]})


@pytest.mark.parametrize("name", IN_A_DECK)
def test_slide_uses_inline_styles_only(name):
    text = (SLIDES / "slides" / f"{name}.html").read_text().strip()
    assert text.startswith(f'<section id="{name}"') and text.endswith("</section>") and text.count("<section") == 1
    for forbidden in ("<style", "class=", "margin"):
        assert forbidden not in text, f"{name}: {forbidden}"


def test_every_placeholder_has_its_number():
    numbers = {path.stem: json.loads(path.read_text()) for path in (SLIDES / "numeros").glob("*.json")}
    for name in IN_A_DECK:
        for key in re.findall(r"\{\{([\w.]+)\}\}", (SLIDES / "slides" / f"{name}.html").read_text()):
            domain, card, value = key.split(".")
            assert value in numbers[domain][card], f"{name}: {key}"
