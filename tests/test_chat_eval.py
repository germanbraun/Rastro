"""How layer/chat_eval.py decides a chat turn is right: a number said within 5 % in any scale, the names of a list,
and «no data» where the data has no answer."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))
import answer  # noqa: E402,F401 - imported first, so loading chat_eval does not change its provider for other tests


def load(monkeypatch):
    monkeypatch.setenv("RASTRO_PROVIDER", "files")   # chat_eval sets these on import; restored after the test
    monkeypatch.setenv("RASTRO_FILES", "/tmp")
    monkeypatch.setattr(sys, "argv", ["chat_eval.py", "energia"])
    spec = importlib.util.spec_from_file_location("chat_eval", ROOT / "layer/chat_eval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_number_in_any_scale(monkeypatch):
    m = load(monkeypatch)
    assert m.says_number("unos 12,6 millones de m³", 12570093.35)
    assert m.says_number("5.246.629 miles de m³", 5246629.44)
    assert not m.says_number("2,57 millones en Loma Campana y 2,1 en La Amarga Chica", 12570093.35)


def test_names_and_no_data(monkeypatch):
    m = load(monkeypatch)
    assert m.says_names("Fue TOTAL AUSTRAL S.A., con 12,3 millones", ["TOTAL AUSTRAL S.A."])
    assert not m.says_names("Fue YPF", ["TOTAL AUSTRAL S.A."])
    assert m.score({"kind": "sin_datos"}, {"sin_datos": "no hay precios"}, "") == (True, "sin datos")
    assert m.score({"kind": "sin_datos"}, {"query": "SELECT", "rows": [["1"]], "answer": "1"}, "")[0] is False
