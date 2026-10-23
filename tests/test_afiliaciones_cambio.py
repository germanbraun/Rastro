"""The afiliaciones correction checker fails on wrong lists, errors and broken cq1 coverage (GPT's probe, 7d515f4)."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("correccion", ROOT / "layer/afiliaciones/cambio/correccion.py")
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

ORG = ["https://ror.org/0081fs513", "https://ror.org/03cqe8w59"]
MENTIONS = {"10.1002/epd2.70126/4/0": [""], "10.1002/epd2.70126/5/0": [""]}


def measurements():
    before = {"answers": {"e1-0-C": {"answer": 63.0, "error": None}, "e2-0-C": {"answer": ORG, "error": None},
                          "e3-0-C": {"answer": 69.0, "error": None}, "e5-0-C": {"answer": 42.0, "error": None}},
              "queries": {"cq1": {"rows": 1675, "mentions": 1456, "by_mention": MENTIONS},
                          "cq2": {"rows": 69, "garrahan": 0}, "cq3": {"rows": 125, "affected": 2}}}
    after = copy.deepcopy(before)
    after["answers"]["e3-0-C"]["answer"], after["answers"]["e5-0-C"]["answer"] = 70.0, 40.0
    after["queries"] = {"cq1": {"rows": 1675, "mentions": 1456,
                                "by_mention": {k: [check.GARRAHAN] for k in MENTIONS}},
                        "cq2": {"rows": 70, "garrahan": 1}, "cq3": {"rows": 123, "affected": 0}}
    return before, after


def test_expected_change_passes():
    before, after = measurements()
    assert check.check_runs(before, after)[1] == []
    assert check.check_queries(before, after)[1] == []


def test_wrong_list_item_with_same_size_fails():
    before, after = measurements()
    after["answers"]["e2-0-C"]["answer"] = [ORG[0], "https://ror.org/wrong"]
    assert check.check_runs(before, after)[1]


def test_measurement_error_fails():
    before, after = measurements()
    after["answers"]["e1-0-C"]["error"] = "permission denied"
    assert check.check_runs(before, after)[1]


def test_broken_cq1_coverage_fails():
    before, after = measurements()
    after["queries"]["cq1"]["rows"], after["queries"]["cq1"]["mentions"] = 1, 1
    assert check.check_queries(before, after)[1]


def test_one_affected_mention_missing_fails():
    before, after = measurements()
    after["queries"]["cq1"]["by_mention"]["10.1002/epd2.70126/5/0"] = [""]
    assert check.check_queries(before, after)[1]
