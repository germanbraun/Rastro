"""Check the three measurements of the alias correction against the approved expectations; write correccion.json.

Called by correccion.sh with the seconds of the source change and of the rebuild. The expectations come from the
approved plan (change-test-proposal.md), computed from the source texts before running. Every expectation is exact:
numbers by their change, lists by the items added and removed, cq1 by each affected affiliation and its coverage.
Any measurement error or failed expectation is listed in «failures» and the script exits nonzero.
"""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
GARRAHAN = "https://ror.org/051mda743"
AFFECTED = ["10.1002/epd2.70126/4/0", "10.1002/epd2.70126/5/0"]
EXPECTED = {"e1": 0, "e2": [], "e3": 1, "e4": [], "e5": -2}   # D and C: number change, or list items added


def change(before, after):
    if isinstance(before, list) and isinstance(after, list):
        return {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after))}
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return after - before
    return None


def check_runs(before, after):
    runs, failures = {}, []
    for run in sorted(set(before["answers"]) | set(after["answers"])):
        qid, _, approach = run.split("-")
        b, a = before["answers"].get(run), after["answers"].get(run)
        errors = [m["error"] for m in (b, a) if m is None or m.get("error")] if b and a else ["missing measurement"]
        moved = change(b["answer"], a["answer"]) if b and a else None
        ok = None
        if approach in "DC":
            want = EXPECTED[qid]
            ok = not errors and (moved == {"added": want, "removed": []} if isinstance(want, list) else moved == want)
            if not ok:
                failures.append(f"{run}: expected change {want}, got {moved}" + (f", errors {errors}" if errors else ""))
        elif errors:
            failures.append(f"{run}: measurement error {errors}")
        runs[run] = {"before": b and b["answer"], "after_rebuild": a and a["answer"], "change": moved,
                     "expected_change": EXPECTED[qid] if approach in "DC" else None, "as_expected": ok, "errors": errors}
    return runs, failures


def check_queries(before, after):
    b, a, failures = before["queries"], after["queries"], []
    expectations = [
        ("cq1 rows unchanged", b["cq1"]["rows"] == a["cq1"]["rows"]),
        ("cq1 covers the same mentions", b["cq1"]["mentions"] == a["cq1"]["mentions"]),
        ("cq1: both affected affiliations had no organization before",
         all(b["cq1"]["by_mention"].get(k) == [""] for k in AFFECTED)),
        ("cq1: both affected affiliations show Garrahan, and only Garrahan, after",
         all(a["cq1"]["by_mention"].get(k) == [GARRAHAN] for k in AFFECTED)),
        ("cq2: Garrahan from 0 to 1 publication", (b["cq2"]["garrahan"], a["cq2"]["garrahan"]) == (0, 1)),
        ("cq2: one more organization", a["cq2"]["rows"] - b["cq2"]["rows"] == 1),
        ("cq3: two fewer candidates", b["cq3"]["rows"] - a["cq3"]["rows"] == 2),
        ("cq3: the affected affiliations leave the list", (b["cq3"]["affected"], a["cq3"]["affected"]) == (2, 0)),
    ]
    failures += [name for name, ok in expectations if not ok]
    return {name: ok for name, ok in expectations}, failures


def main(source_seconds, rebuild_seconds):
    load = lambda step: json.loads((HERE / f"medicion-{step}.json").read_text())   # noqa: E731
    before, source, after = load("antes"), load("fuente"), load("despues")
    runs, run_failures = check_runs(before, after)
    queries, query_failures = check_queries(before, after)
    source_changed = sorted(r for r in before["answers"] if source["answers"][r]["answer"] != before["answers"][r]["answer"])
    failures = run_failures + query_failures
    result = {
        "fecha": date.today().isoformat(),
        "correction": f"ROR alias «Hospital de Pediatría Prof. Dr. Juan P. Garrahan» for {GARRAHAN}",
        "edits": {"B": "0 saved queries edited", "D": "0 saved queries edited; linker rerun",
                  "C": "0 saved queries edited, 0 mapping lines; linker rerun and Ontop restart"},
        "elapsed_seconds": {"source_change": source_seconds, "rebuild_links_and_ontop": rebuild_seconds,
                            "note": "machine time of each step, not active work"},
        "answers_changed_by_the_source_change_alone": source_changed,
        "queries": {"before": before["queries"], "after_source_change": source["queries"], "after_rebuild": after["queries"],
                    "expectations": queries},
        "runs": runs,
        "summary": {a: {"behaved_as_expected": sum(1 for k, r in runs.items() if k.endswith(a) and r["as_expected"]),
                        "runs": sum(1 for k in runs if k.endswith(a))} for a in "DC"},
        "failures": failures,
        "passed": not failures,
    }
    (HERE / "correccion.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"passed": not failures, "failures": failures, "summary": result["summary"]}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
