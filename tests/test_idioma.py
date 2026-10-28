"""The English interface stays in step with the Spanish one: overlays only fill existing keys, keep placeholders,
and every text key used in the code exists with its Spanish."""
import re
import string
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
sys.path.insert(0, str(APP))
import idioma  # noqa: E402

OVERLAYS = sorted(APP.rglob("*.en.yaml"))


def placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name} if isinstance(text, str) else set()


def walk(spanish, english, path="$"):
    """Yield problems where the English overlay does not fit the Spanish structure."""
    if isinstance(english, dict) and isinstance(spanish, str) and set(english) == {"term", "text"}:
        return   # a glossary entry that translates its term too (dominio.glossary)
    if isinstance(english, dict):
        if not isinstance(spanish, dict):
            yield f"{path}: English has a dictionary where Spanish has {type(spanish).__name__}"
            return
        for key, value in english.items():
            if key not in spanish:
                yield f"{path}.{key}: not in the Spanish file"
            else:
                yield from walk(spanish[key], value, f"{path}.{key}")
    elif isinstance(english, list):
        if not isinstance(spanish, list):
            yield f"{path}: English has a list where Spanish has {type(spanish).__name__}"
            return
        if spanish and all(isinstance(i, dict) and "id" in i for i in spanish + english):
            by_id = {item["id"]: item for item in spanish}
            for item in english:
                if item["id"] not in by_id:
                    yield f"{path}[{item['id']}]: id not in the Spanish file"
                else:
                    yield from walk(by_id[item["id"]], item, f"{path}[{item['id']}]")
        else:
            if len(english) > len(spanish):
                yield f"{path}: English list is longer than the Spanish one"
            for i, (s, e) in enumerate(zip(spanish, english)):
                yield from walk(s, e, f"{path}[{i}]")
    elif english is not None and placeholders(english) != placeholders(spanish):
        yield f"{path}: placeholders {sorted(placeholders(english))} differ from Spanish {sorted(placeholders(spanish))}"


@pytest.mark.parametrize("english", OVERLAYS, ids=lambda p: str(p.relative_to(ROOT)))
def test_overlay_fits_the_spanish_file(english):
    spanish = english.with_name(english.name.replace(".en.yaml", ".yaml"))
    problems = list(walk(yaml.safe_load(spanish.read_text()), yaml.safe_load(english.read_text())))
    assert not problems, "\n".join(problems[:20])


def test_overlay_merges_by_key_by_id_and_by_position():
    base = {"a": "uno", "keep": 1, "items": [{"id": "x", "t": "equis"}, {"id": "y", "t": "ye"}], "plain": ["p", "q"]}
    extra = {"a": "one", "items": [{"id": "y", "t": "why"}], "plain": ["P"], "extra": "ignored"}
    assert idioma.overlay(base, extra) == {"a": "one", "keep": 1, "plain": ["P", "q"],
                                           "items": [{"id": "x", "t": "equis"}, {"id": "y", "t": "why"}]}


def test_every_text_key_has_spanish_and_matching_placeholders():
    texts = {}
    for path in sorted((APP / "textos").glob("*.yaml")):
        texts.update(yaml.safe_load(path.read_text()) or {})
    used = set()
    for source in APP.glob("*.py"):
        used |= set(re.findall(r'\bt\(\s*["\']([a-z_][\w.]*)["\']', source.read_text()))
    assert used <= set(texts), f"keys used in code but missing: {sorted(used - set(texts))}"
    for key, entry in texts.items():
        assert entry.get("es"), f"{key}: no Spanish"
        if entry.get("en"):
            assert placeholders(entry["en"]) == placeholders(entry["es"]), f"{key}: placeholders differ"


def test_a_volume_column_shares_its_decimals():
    column = [15_850_377, 3_994_269, 41_000]   # m³: 15,9 sets one decimal for the whole column
    decimals = idioma.column_decimals(column, 1e6)
    assert [idioma.scaled(v, 1e6, "es", decimals) for v in column] == ["15,9", "4,0", "0,0"]
    assert idioma.scaled(12_301_226, 1e3, "en") == "12,301.2"
    assert idioma.column_decimals([None, ""], 1e6) == 1
