"""The affiliations references come from the blind annotation only: a complete annotation gives the five answers, an
incomplete or invalid one is refused."""
import csv
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/experiments/research-affiliations/blind-review"


@pytest.fixture
def reviewed(tmp_path):
    for name in ("strings.csv", "ror-argentina.csv", "mentions.csv", "reference.py"):
        shutil.copy(FOLDER / name, tmp_path / name)
    spec = importlib.util.spec_from_file_location("reference", tmp_path / "reference.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE, module.OUT = tmp_path, tmp_path / "referencias.json"
    strings = list(csv.DictReader((tmp_path / "strings.csv").open(encoding="utf-8")))
    conicet = next(s for s in strings if s["review"] == "full" and "CONICET" in s["text"])
    other = next(s for s in strings if s["review"] == "full" and s is not conicet)

    def write(rows):
        with (tmp_path / "annotations.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["string_id", "review", "screen", "organizations", "other_references", "evidence", "ambiguous", "note"])
            w.writerows(rows)

    rows = [[s["string_id"], s["review"], "no" if s["review"] == "screen" else "",
             module.CONICET if s is conicet else "", "", "", "", "" if s is conicet else "ninguna"] for s in strings]
    return module, write, rows, conicet, other


def test_complete_annotation_gives_the_answers(reviewed):
    module, write, rows, conicet, other = reviewed
    write(rows)
    module.main()
    out = json.loads(module.OUT.read_text())
    mentions = [m for m in csv.DictReader((module.HERE / "mentions.csv").open(encoding="utf-8"))
                if m["text"] == conicet["text"]]
    argentina = [m for m in csv.DictReader((module.HERE / "mentions.csv").open(encoding="utf-8"))
                 if "argentin" in module.norm(m["text"])]
    assert out["answers"]["e1"] == len({m["doi"] for m in mentions})
    assert out["answers"]["e3"] == 1
    assert out["answers"]["e5"] == len(argentina) - len(mentions)
    assert "falta que una persona" in out["nota"]


def test_incomplete_or_invalid_annotation_is_refused(reviewed):
    module, write, rows, conicet, other = reviewed
    skipped = [r if r[0] != other["string_id"] else [r[0], r[1], "", "", "", "", "", ""] for r in rows]
    write(skipped)
    with pytest.raises(SystemExit, match="no «ninguna»"):
        module.main()
    foreign = [r if r[0] != conicet["string_id"] else [*r[:3], "https://ror.org/not-argentine", *r[4:]] for r in rows]
    write(foreign)
    with pytest.raises(SystemExit, match="not an Argentine ROR organization"):
        module.main()
