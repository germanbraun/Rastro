"""The oil and gas correction checker passes the recorded run and fails a broken copy, a measurement error, or a
change that reached the raw-table paths."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("correccion_energia", ROOT / "layer/energia/cambio/correccion.py")
correccion = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(correccion)
SAVED = json.loads((ROOT / "layer/energia/cambio/correccion.json").read_text())


def test_recorded_run_behaved_as_expected():
    assert correccion.check(SAVED, correccion.documented_percent()) == []


@pytest.mark.parametrize("paso,key,value,message", [
    ("con", "layer_B", 1.0, "SQL over the sources"),
    ("sin", "layer_C", SAVED["con"]["layer_C"], "the answer changes"),
    ("con", "lab_B_marca", "", "marked"),
    ("con", "rastro_total", 27.27, "document's"),
    ("sin", "lab_A_pred", None, "missing or not a number"),
])
def test_broken_fixture_fails(paso, key, value, message):
    broken = copy.deepcopy(SAVED)
    broken[paso][key] = value
    assert any(message in failure for failure in correccion.check(broken, correccion.documented_percent()))
