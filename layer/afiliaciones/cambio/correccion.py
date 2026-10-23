"""Compare the three measurements of the alias correction with the approved expectations; write correccion.json.

Called by correccion.sh with the seconds of the source change and of the rebuild. Expectations come from the approved
plan (change-test-proposal.md), computed from the source texts before running, not from this result.
"""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
EXPECTED = {"e1": 0, "e2": 0, "e3": 1, "e4": 0, "e5": -2}   # change of the answer, for D and C
EXPECTED_QUERIES = {"cq1": "the two affiliations show Garrahan", "cq2": "Garrahan with 1 publication",
                    "cq3": "the two affiliations leave the list (125 -> 123)"}


def load(step):
    return json.loads((HERE / f"medicion-{step}.json").read_text())


def change(before, after):
    if isinstance(before, list) or isinstance(after, list):
        return {"added": sorted(set(after or []) - set(before or [])), "removed": sorted(set(before or []) - set(after or []))}
    return None if before is None or after is None else after - before


def main(source_seconds, rebuild_seconds):
    before, source, after = load("antes"), load("fuente"), load("despues")
    runs = {}
    for run, b in before["answers"].items():
        qid, _, approach = run.split("-")
        moved = change(b["answer"], after["answers"][run]["answer"])
        if isinstance(moved, dict):
            delta = len(moved["added"]) - len(moved["removed"])
        else:
            delta = moved
        expected = EXPECTED[qid] if approach in "DC" else None
        runs[run] = {"before": b["answer"], "after_source_change": source["answers"][run]["answer"],
                     "after_rebuild": after["answers"][run]["answer"], "change": moved,
                     "expected_change": expected, "as_expected": None if expected is None else delta == expected,
                     "errors": [m["answers"][run]["error"] for m in (before, source, after) if m["answers"][run]["error"]]}
    q = {"before": before["queries"], "after_source_change": source["queries"], "after_rebuild": after["queries"]}
    queries_ok = (after["queries"]["cq1"]["affected"] == ["https://ror.org/051mda743"]
                  and after["queries"]["cq2"]["garrahan"] == 1 and before["queries"]["cq2"]["garrahan"] == 0
                  and before["queries"]["cq3"]["rows"] - after["queries"]["cq3"]["rows"] == 2)
    result = {
        "fecha": date.today().isoformat(),
        "correction": "ROR alias «Hospital de Pediatría Prof. Dr. Juan P. Garrahan» for https://ror.org/051mda743",
        "edits": {"B": "0 saved queries edited", "D": "0 saved queries edited; linker rerun",
                  "C": "0 saved queries edited, 0 mapping lines; linker rerun and Ontop restart"},
        "seconds": {"source_change": source_seconds, "rebuild_links_and_ontop": rebuild_seconds},
        "expected_queries": EXPECTED_QUERIES, "queries": q, "queries_as_expected": queries_ok,
        "runs": runs,
        "summary": {a: {"as_expected": sum(1 for k, r in runs.items() if k.endswith(a) and r["as_expected"]),
                        "runs": sum(1 for k in runs if k.endswith(a))} for a in "DC"},
    }
    (HERE / "correccion.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"queries_as_expected": queries_ok, "summary": result["summary"],
                      "B": {k: r["change"] for k, r in runs.items() if k.endswith("B") and r["change"] not in (0, None, {"added": [], "removed": []})}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
