"""How layer/evaluar.py scores an answer (it makes the published numbers): numbers within 5 %, lists by F1 ≥ 0.8,
and «the same answer» across wordings. Read from the real oil and gas set, with no database: names that are not
companies compare without the normalizing SQL function."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))


def load(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["evaluar.py", "energia"])
    spec = importlib.util.spec_from_file_location("evaluar", ROOT / "layer/evaluar.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_numbers_within_five_percent(monkeypatch):
    m = load(monkeypatch)
    q = {"kind": "número"}
    assert m.score(q, 45, 47, None)          # e08 without Rastro: 4.4 % off, counts as right
    assert not m.score(q, 33, 36, None)      # e05 without Rastro: 9 % off
    assert not m.score(q, 60, 43, None) and not m.score(q, 45, None, None)
    assert m.score(q, 0, 0, None) and not m.score(q, 0, 1, None)


def test_lists_by_f1(monkeypatch):
    m = load(monkeypatch)
    q = {"kind": "lista", "items": "concesiones"}
    five = ["LOMA CAMPANA", "LA CALERA", "LA ANGOSTURA SUR I", "BAJO DEL CHOIQUE - LA INVERNADA", "LOMA LA LATA"]
    assert m.score(q, five, [v.lower() for v in five], None)            # case and spacing do not matter
    assert m.score(q, five, five[:4] + ["OTRA"], None)                  # 4 of 5 right: F1 0.8
    assert not m.score(q, five, five[:3] + ["OTRA", "MÁS"], None)       # 3 of 5: F1 0.6
    assert m.score(q, [], [], None) and not m.score(q, five, [], None)


def test_the_same_answer_across_wordings(monkeypatch):
    m = load(monkeypatch)
    assert m.same([12570093.35, 12570093.351]) and not m.same([12570093.35, 12581212.0])
    assert m.same([["B", "A"], ["A", "B"]]) and not m.same([["A"], ["A", "B"]])
