"""The experiment log is written by commands: hours come from the sessions, and the lint catches the four kinds of
hand-editing error the affiliations experiment had (duplicate key, unparseable file, early end time, stale hours)."""
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))
import experiment_log as log  # noqa: E402


def test_duplicate_keys_are_refused(tmp_path):
    path = tmp_path / "x.yaml"
    path.write_text("interventions:\n- step: a\n  reason: one\n  reason: two\n")
    with pytest.raises(yaml.YAMLError, match="duplicate keys"):
        log.load(path)


def test_start_and_stop_derive_the_hours():
    data = {}
    log.start(data, "links", "2026-10-22T10:00:00Z")
    with pytest.raises(ValueError, match="still open"):
        log.start(data, "quality", "2026-10-22T10:10:00Z")
    log.stop(data, "links", "linker and corrections", "2026-10-22T10:30:00Z")
    log.start(data, "links", "2026-10-22T11:00:00Z")
    data["steps"]["links"]["sessions"][-1]["pauses"] = [{"started_on": "2026-10-22T11:10:00Z",
                                                         "ended_on": "2026-10-22T11:20:00Z"}]
    log.stop(data, "links", "review", "2026-10-22T11:40:00Z")
    assert data["steps"]["links"]["agent_hours"] == 1.0
    assert log.lint_errors(data, closing=True) == []


def test_lint_finds_overlaps_stale_hours_and_open_sessions():
    data = {"steps": {
        "a": {"agent_hours": 0.5, "sessions": [{"started_on": "2026-10-22T10:00:00Z", "ended_on": "2026-10-22T11:00:00Z",
                                                "pauses": [], "work": "x"}]},
        "b": {"agent_hours": 0.0, "sessions": [{"started_on": "2026-10-22T10:30:00Z", "ended_on": None,
                                                "pauses": [], "work": ""}]}}}
    errors = log.lint_errors(data)
    assert any("differ from its sessions" in e for e in errors)
    assert not any("open sessions" in e for e in errors)          # one open session is the current one
    assert any("open sessions" in e for e in log.lint_errors(data, closing=True))
    data["steps"]["b"]["sessions"][0]["ended_on"] = "2026-10-22T10:45:00Z"
    data["steps"]["b"]["agent_hours"] = 0.25
    assert any("overlaps" in e for e in log.lint_errors(data))


def test_append_requires_its_fields():
    data = {}
    log.append(data, "method-change", {"change": "x", "scope": "generic", "reason": "y"})
    with pytest.raises(ValueError, match="requires"):
        log.append(data, "intervention", {"step": "a"})


def test_saving_keeps_the_affiliations_log_identical(tmp_path):
    original = ROOT / "docs/experiments/afiliaciones.yaml"
    copy = tmp_path / "log.yaml"
    log.save(copy, log.load(original))
    assert log.load(copy) == log.load(original)
    assert log.lint_errors(log.load(original)) == []
