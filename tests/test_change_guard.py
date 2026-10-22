"""Recovery preserves actual local edits and runs even when a child fails."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("change_guard", ROOT / "layer/change_guard.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "STATE", tmp_path / "cache/state")
    monkeypatch.setattr(guard, "FILES", ["mapping", "answers"])
    guard.STATE.mkdir(parents=True)
    (tmp_path / "mapping").write_text("pre-existing user edit")
    (tmp_path / "answers").mkdir()
    (tmp_path / "answers/untracked.json").write_text("user answer")
    return tmp_path


def test_restore_preserves_edits_and_untracked_answers(sandbox):
    state = {}
    guard.save_files(state)
    (sandbox / "mapping").write_text("changed by experiment")
    (sandbox / "answers/untracked.json").unlink()
    (sandbox / "answers/generated.json").write_text("test-only answer")
    guard.restore_files(state)
    assert (sandbox / "mapping").read_text() == "pre-existing user edit"
    assert (sandbox / "answers/untracked.json").read_text() == "user answer"
    assert not (sandbox / "answers/generated.json").exists()
    guard.restore_files(state)  # Retrying restoration is idempotent.


def test_snapshot_refuses_symlinks(sandbox):
    (sandbox / "answers/link").symlink_to(sandbox / "mapping")
    with pytest.raises(ValueError, match="symlinks"):
        guard.save_files({})


def test_failed_child_still_recovers(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "STATE", tmp_path / "cache/state")
    monkeypatch.setattr(guard.sys, "argv", ["change_guard.py", "run", "cambio"])
    monkeypatch.setattr(guard.signal, "signal", lambda *args: None)
    monkeypatch.setattr(guard, "configure_database", lambda: None)
    monkeypatch.setattr(guard, "snapshot", lambda kind: {"kind": kind})
    recovered = []
    monkeypatch.setattr(guard, "recover", lambda state: recovered.append(state))

    class FailedChild:
        def __init__(self, *args, **kwargs):
            pass

        def wait(self):
            return 17

        def poll(self):
            return 17

    monkeypatch.setattr(guard.subprocess, "Popen", FailedChild)
    with pytest.raises(SystemExit) as error:
        guard.main()
    assert error.value.code == 17
    assert recovered == [{"kind": "cambio"}]


def test_rebuild_failure_retains_recovery(sandbox, monkeypatch):
    state = {"files": [], "schema": "backup"}
    monkeypatch.setattr(guard, "restore_tables", lambda state: None)

    def fail():
        raise RuntimeError("Ontop failed")

    monkeypatch.setattr(guard, "rebuild", fail)
    with pytest.raises(RuntimeError, match="Ontop failed"):
        guard.recover(state)
    assert guard.STATE.exists()


def test_change_measurement_rejects_empty_and_broken_baselines():
    spec = importlib.util.spec_from_file_location("change_measurement", ROOT / "layer/energia/cambio/probar.py")
    measurement = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measurement)
    with pytest.raises(RuntimeError, match="No saved queries"):
        measurement.validate_step("antes", {}, "✅ units")
    with pytest.raises(RuntimeError, match="not preserved"):
        measurement.validate_step("antes", {"q1": {"B": "❌ error", "C": "✅ igual"}}, "✅ units")
    measurement.validate_step("renombrar-arreglado", {"q1": {"B": "❌ error", "C": "✅ igual"}}, "✅ units")
    with pytest.raises(RuntimeError, match="unit control"):
        measurement.validate_step("valores-arreglado", {"q1": {"B": "❌ error", "C": "✅ igual"}}, "🟡 wrong units")
