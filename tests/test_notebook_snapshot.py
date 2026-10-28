"""The Rastro Lab notebook (lab/notebooks/rastro-lab.ipynb) reads a saved copy of the model's inputs. If modelo.py
changes, its version changes and the copy must be saved again (python3 lab/gas/snapshot.py, after --publicar):
otherwise the notebook stops at its first check."""
import hashlib
import json
from pathlib import Path

import modelo

DATA = Path(__file__).resolve().parents[1] / "lab" / "notebooks" / "datos"


def test_the_snapshot_is_from_this_model():
    manifest = json.loads((DATA / "manifest.json").read_text())
    assert manifest["model_version"] == modelo.version(), "modelo.py changed: run lab/gas/snapshot.py again"


def test_every_saved_file_matches_its_fingerprint():
    manifest = json.loads((DATA / "manifest.json").read_text())
    for name, spec in manifest["files"].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == spec["sha256"], name


def test_the_notebook_has_no_local_paths_and_runs_on_the_standard_kernel():
    notebook = json.loads((DATA.parent / "rastro-lab.ipynb").read_text())
    assert notebook["metadata"]["kernelspec"]["name"] == "python3"
    assert "/Users/" not in json.dumps(notebook) and "/home/" not in json.dumps(notebook)
