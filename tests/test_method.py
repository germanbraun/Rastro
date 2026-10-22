"""Method gates must reject false success, wrong targets and stale publication evidence."""
import importlib.util
import json
from pathlib import Path

import pytest
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("method", ROOT / "layer/method.py")
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def test_real_registry_and_lab_target():
    registry = yaml.safe_load((ROOT / "layer/dominios.yaml").read_text())
    assert method.registry_errors(registry) == []
    assert registry["energia_lab"]["method"]["evaluation"]["run"].endswith("energia_lab")
    registry["energia_lab"]["method"]["evaluation"] = registry["energia"]["method"]["evaluation"]
    assert any("different question set" in e for e in method.registry_errors(registry))


def test_csv_empty_is_valid_only_when_expected():
    assert method.check_csv("answer\n", {"columns": ["answer"], "rows": 0}) == 0
    with pytest.raises(ValueError, match="min_rows"):
        method.check_csv("answer\n", {"columns": ["answer"], "min_rows": 1})


@pytest.mark.parametrize("body,spec", [
    ("<html>error</html>", {"columns": ["answer"], "min_rows": 1}),
    ("answer\n1,2\n", {"columns": ["answer"], "rows": 1}),
    ("answer\nNaN\n", {"columns": ["answer"], "number": {"column": "answer", "value": 1}}),
    ("answer\n1\n", {"columns": ["answer"]}),
    ("answer\na\na\n", {"columns": ["answer"], "values": [["a"]]}),
])
def test_csv_rejects_error_bodies_malformed_rows_and_wrong_answers(body, spec):
    with pytest.raises(ValueError):
        method.check_csv(body, spec)


def test_numeric_tolerance_is_explicit():
    spec = {"columns": ["answer"], "number": {"column": "answer", "value": 100, "relative_tolerance": .05}}
    assert method.check_csv("answer\n104\n", spec) == 1
    with pytest.raises(ValueError):
        method.check_csv("answer\n106\n", spec)


def test_query_gate_rejects_http_failure_and_stale_checks(tmp_path):
    query = tmp_path / "cq1.rq"
    query.write_text("SELECT ?answer WHERE {}")
    cfg = {"method": {"queries": ".", "ontop": {"port": 8082}}}
    expectations = {"cq1.rq": {"query_sha256": method.digest(query), "columns": ["answer"], "rows": 0}}

    def post(*args, **kwargs):
        response = requests.Response()
        response.status_code = 500
        response._content = b"answer\nerror\n"
        response.headers["Content-Type"] = "text/csv"
        return response

    with pytest.raises(requests.HTTPError):
        method.verify_queries(cfg, expectations, tmp_path, post)
    query.write_text("SELECT ?answer WHERE { ?answer ?p ?o }")
    with pytest.raises(ValueError, match="stale"):
        method.verify_queries(cfg, expectations, tmp_path, post)
    with pytest.raises(ValueError, match="exactly"):
        method.verify_queries(cfg, {}, tmp_path, post)


def evidence_fixture(root):
    folder = root / "layer/example"
    folder.mkdir(parents=True)
    (folder / "eval").mkdir()
    questions = folder / "eval/questions.yaml"
    questions.write_text("questions:\n- id: q1\n- id: q2\n")
    result = folder / "resultados.json"
    result.write_text(json.dumps({"questions": {qid: {"reference": [], "B": {}, "D": {}, "C": {}}
                                               for qid in ("q1", "q2")}}))
    evidence = root / "independent.txt"
    evidence.write_text("Synthetic test fixture: independent source calculation")
    artifact = {"path": "independent.txt", "sha256": method.digest(evidence)}
    approved = {"source": "test source", "source_version": "test version", "checked_answer": [],
                "reviewer": "test reviewer", "reviewed_on": "2026-10-22", "independent": True,
                "status": "approved", "artifact": artifact["path"], "sha256": artifact["sha256"],
                "adjudication": "all approaches agree"}
    manifest = {"questions_sha256": method.digest(questions),
                "run": {"model": "test", "model_version": "1", "source_versions": ["1"],
                        "prompt_artifacts": [artifact], "attempt_artifacts": [artifact],
                        "result_artifact": {"path": "layer/example/resultados.json", "sha256": method.digest(result)}},
                "references": {"q1": approved, "q2": approved.copy()}}
    path = folder / "reference-evidence.yaml"
    path.write_text(yaml.safe_dump(manifest))
    return {"method": {"evaluation": {"folder": "layer/example", "harness": "current"}}}, path, manifest


def test_publication_requires_agreement_case_review_and_unchanged_artifacts(tmp_path):
    cfg, path, manifest = evidence_fixture(tmp_path)
    assert method.publication_errors(cfg, tmp_path) == []
    del manifest["references"]["q2"]
    path.write_text(yaml.safe_dump(manifest))
    assert any("every question" in e for e in method.publication_errors(cfg, tmp_path))
    cfg, path, manifest = evidence_fixture_again(tmp_path)
    (tmp_path / "layer/example/resultados.json").write_text("changed score")
    assert any("scored result" in e for e in method.publication_errors(cfg, tmp_path))


def evidence_fixture_again(root):
    import shutil
    shutil.rmtree(root / "layer")
    return evidence_fixture(root)


def test_publication_does_not_accept_provisional_review(tmp_path):
    cfg, path, manifest = evidence_fixture(tmp_path)
    manifest["references"]["q1"]["status"] = "pending"
    path.write_text(yaml.safe_dump(manifest))
    assert any("review is pending" in e for e in method.publication_errors(cfg, tmp_path))


def test_unmeasured_experiment_cannot_close():
    errors = method.experiment_errors({"domain": "example", "steps": {}, "interventions": [],
                                       "errors_caught": [], "method_changes": []})
    assert any("agent_hours" in e for e in errors)
    assert any("method_commit" in e for e in errors)
    assert any("result" in e for e in errors)


def test_publication_rejects_a_reviewed_answer_that_does_not_match_scoring(tmp_path):
    cfg, path, manifest = evidence_fixture(tmp_path)
    manifest["references"]["q1"]["checked_answer"] = ["different"]
    path.write_text(yaml.safe_dump(manifest))
    assert any("differs from the scored reference" in e for e in method.publication_errors(cfg, tmp_path))
