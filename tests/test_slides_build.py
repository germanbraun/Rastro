"""The deck builder: a deck's own speaker notes, English number formats, the shared deck's export, and the English
executive deck saying the same numbers as the Spanish one."""
import importlib.util
import json
import re
from pathlib import Path

SLIDES = Path(__file__).resolve().parents[1] / "docs/slides"
SPEC = importlib.util.spec_from_file_location("build", SLIDES / "build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


def test_english_swaps_the_separators():
    numbers = {"d": {"c": {"big": "3.600", "small": "21,4", "pct": "100 %"}}}
    build.NUMBERS["test"] = numbers["d"]
    found = [build.number(re.match(r"\{\{([\w.]+)\}\}", f"{{{{test.c.{k}}}}}"), "en") for k in ("big", "small", "pct")]
    assert found == ["3,600", "21.4", "100%"]
    assert build.number(re.match(r"\{\{([\w.]+)\}\}", "{{test.c.small}}")) == "21,4"


def test_a_deck_replaces_a_shared_slides_notes():
    meta = json.loads((SLIDES / "mazos/ejecutivo.json").read_text())
    text = build.slide("e-integracion", 4, meta)
    assert text.count("<aside>") == 1 and "Qué decir" in text and "{{" not in text
    assert "Qué decir" not in build.slide("e-integracion", 4)   # the main deck keeps its own notes


def test_export_fills_numbers_and_pages(tmp_path):
    build.export("ejecutivo", tmp_path)
    order = json.loads((SLIDES / "mazos/ejecutivo.json").read_text())["order"]
    for page, name in enumerate(order, 1):
        text = (tmp_path / "project/slides" / f"{name}.html").read_text()
        assert "{{" not in text and text.startswith(f'<section id="{name}"')
        if 'bottom:64px' in text:
            assert f"<p>{page}</p></div>" in text


def test_english_executive_deck_shows_the_same_numbers():
    def placeholders(name):
        body = re.sub(r"<aside>.*?</aside>", "", (SLIDES / "slides" / f"{name}.html").read_text(), flags=re.S)
        return sorted(re.findall(r"\{\{([\w.]+)\}\}", body))
    es = json.loads((SLIDES / "mazos/ejecutivo.json").read_text())["order"]
    en = json.loads((SLIDES / "mazos/ejecutivo-en.json").read_text())["order"]
    assert len(es) == len(en)
    for a, b in zip(es, en):
        assert placeholders(a) == placeholders(b), (a, b)
