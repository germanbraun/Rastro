"""A previously unknown vocabulary must use the same ontology and quality machinery."""
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ontology"))
sys.path.insert(0, str(ROOT / "layer"))
import calidad
import lifecycle

SPEC = importlib.util.spec_from_file_location("ontology_check", ROOT / "ontology/check.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


@pytest.fixture
def unknown_quality(tmp_path):
    rules = tmp_path / "rules.ttl"
    rules.write_text('''@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix library: <urn:library:> .
library:Pages a sh:NodeShape; sh:targetClass library:Book;
  sh:property [ sh:path library:pages; sh:minCount 1; sh:minInclusive 1 ] .
''')
    examples = tmp_path / "examples.yaml"
    examples.write_text(yaml.safe_dump({"Pages": {"bueno": 'library:a a library:Book; library:pages 10 .',
                                                "malo": 'library:a a library:Book; library:pages -1 .'}}))
    data = tmp_path / "data.yaml"
    data.write_text("- CONSTRUCT {?s ?p ?o} WHERE {?s ?p ?o}\n")
    return calidad.QualityConfig("library", rules, examples, data, tmp_path / "result.json", "http://unused",
                                 "urn:library:", "library")


def test_unknown_domain_quality_uses_its_own_prefixes_and_finds_defect(unknown_quality):
    assert calidad.check_examples(unknown_quality) == 1
    data = Graph().parse(data='@prefix l: <urn:library:> . l:a a l:Book; l:pages -1 .', format="turtle")
    result = calidad.evaluate(unknown_quality, data, {"urn:library:a": {"urn:prediction:one"}})
    assert result["domain"] == "library"
    assert result["status"] == "defects_detected"
    assert result["reglas"][0]["por_severidad"] == {"Violation": 1, "Warning": 0, "Info": 0}
    assert result["reglas"][0]["predicciones_afectadas"] == ["urn:prediction:one"]
    assert result["reglas"][0]["revisados"] == 1


def test_warning_only_findings_ask_for_review_not_defects(unknown_quality):
    rules = unknown_quality.rules.read_text().replace("library:Pages a sh:NodeShape;",
                                                      "library:Pages a sh:NodeShape; sh:severity sh:Warning;")
    unknown_quality.rules.write_text(rules.replace("sh:minInclusive 1 ]", "sh:minInclusive 1; sh:severity sh:Warning ]"))
    data = Graph().parse(data='@prefix l: <urn:library:> . l:a a l:Book; l:pages -1 .', format="turtle")
    result = calidad.evaluate(unknown_quality, data)
    assert result["status"] == "review_findings"
    assert result["por_severidad"] == {"Violation": 0, "Warning": 1, "Info": 0}
    assert result["reglas"][0]["ejemplos"][0]["severidad"] == "Warning"


def test_zero_target_quality_is_pending_not_success(unknown_quality):
    result = calidad.evaluate(unknown_quality, Graph())
    assert result["status"] == "coverage_pending"


def test_quality_example_that_never_targets_data_cannot_pass(unknown_quality):
    unknown_quality.examples.write_text(yaml.safe_dump({"Pages": {"bueno": 'library:a library:pages 10 .',
                                                                 "malo": 'library:a a library:Book .'}}))
    with pytest.raises(ValueError, match="no target"):
        calidad.check_examples(unknown_quality)


def test_shared_property_domains_are_checked_from_explicit_mapping_classes():
    ontology = Graph().parse(data='''@prefix l: <urn:library:> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> . l:name rdfs:domain l:Book .''', format="turtle")
    mapping = Graph().parse(data='''@prefix rr: <http://www.w3.org/ns/r2rml#> . @prefix l: <urn:library:> .
l:Books rr:subjectMap [rr:class l:Book]; rr:predicateObjectMap [rr:predicate l:name].
l:Authors rr:subjectMap [rr:class l:Author]; rr:predicateObjectMap [rr:predicateMap [rr:constant l:name]].
''', format="turtle")
    assert len(checker.shared_domain_errors(ontology, mapping)) == 1
    ontology.remove((None, checker.RDFS.domain, None))
    assert checker.shared_domain_errors(ontology, mapping) == []


@pytest.fixture
def requirement(tmp_path):
    (tmp_path / "ontology/queries").mkdir(parents=True)
    (tmp_path / "ontology/schema.ttl").write_text('''@prefix owl: <http://www.w3.org/2002/07/owl#> .
<https://example.org/library> a owl:Ontology .''')
    (tmp_path / "mapping.ttl").write_text("")
    (tmp_path / "sources.json").write_text('{"edition": "1"}')
    (tmp_path / "proposal.yaml").write_text(yaml.safe_dump({"question": "How many published book records?",
        "definitions": "A record is a row in the published catalogue", "scope": "synthetic test fixture",
        "answer_type": "number", "verification_plan": "Count original source rows independently"}))
    cfg = {"ontology": "ontology/schema.ttl", "method": {"lifecycle": "state.json", "mapping": "mapping.ttl",
          "queries": "ontology/queries", "source_manifest": "sources.json"}}
    return tmp_path, cfg


def test_lifecycle_refuses_implementation_without_approval_and_binds_the_decision(requirement):
    root, cfg = requirement
    lifecycle.transition("propose", cfg, "q1", "proposal.yaml", root)
    query = root / "ontology/queries/cq1.rq"
    query.write_text("SELECT (1 AS ?answer) WHERE {}")
    with pytest.raises(ValueError, match="approved definitions"):
        lifecycle.transition("implement", cfg, "q1", "ontology/queries/cq1.rq", root)
    review = {"actor": "human", "decision": "approved", "reviewer": "synthetic test reviewer",
              "reviewed_on": "2026-10-22", "proposal_sha256": lifecycle.digest(root / "proposal.yaml")}
    (root / "approval.yaml").write_text(yaml.safe_dump(review))
    assert lifecycle.transition("approve", cfg, "q1", "approval.yaml", root) == "approved"
    assert lifecycle.transition("implement", cfg, "q1", "ontology/queries/cq1.rq", root) == "implemented"
    (root / "sources.json").write_text('{"edition": "2"}')
    assert lifecycle.transition("status", cfg, "q1", root=root) == "approved"
    (root / "proposal.yaml").write_text("changed definitions")
    assert lifecycle.transition("status", cfg, "q1", root=root) == "proposed"


def test_failed_live_validation_cannot_promote_a_requirement(requirement, monkeypatch):
    root, cfg = requirement
    lifecycle.transition("propose", cfg, "q1", "proposal.yaml", root)
    (root / "approval.yaml").write_text(yaml.safe_dump({"actor": "human", "decision": "approved",
        "reviewer": "synthetic test reviewer", "reviewed_on": "2026-10-22",
        "proposal_sha256": lifecycle.digest(root / "proposal.yaml")}))
    lifecycle.transition("approve", cfg, "q1", "approval.yaml", root)
    (root / "ontology/queries/cq1.rq").write_text("SELECT (1 AS ?answer) WHERE {}")
    lifecycle.transition("implement", cfg, "q1", "ontology/queries/cq1.rq", root)
    (root / "expectations.yaml").write_text("{}")

    def fail(*args, **kwargs):
        raise ValueError("Live query failed")

    monkeypatch.setattr(lifecycle, "verify_queries", fail)
    with pytest.raises(ValueError, match="Live query failed"):
        lifecycle.transition("validate", cfg, "q1", "expectations.yaml", root)
    assert lifecycle.transition("status", cfg, "q1", root=root) == "implemented"


def test_registry_driven_quality_and_ontology_discover_an_unlisted_domain(unknown_quality, tmp_path):
    (tmp_path / "layer").mkdir()
    registry = {"library": {"ontology": "schema.ttl", "namespace": "urn:library:", "ontop": "http://localhost:8099/sparql",
        "method": {"mapping": "mapping.ttl", "queries": "queries", "quality": {
            "rules": "rules.ttl", "examples": "examples.yaml", "data": "data.yaml", "result": "result.json",
            "prefix": "library"}}}}
    (tmp_path / "layer/dominios.yaml").write_text(yaml.safe_dump(registry))
    loaded = calidad.QualityConfig.load("library", tmp_path)
    assert loaded.rules == unknown_quality.rules
    assert loaded.endpoint == "http://localhost:8099/sparql"
    assert calidad.check_examples(loaded) == 1
    assert checker.registered_targets(tmp_path) == [
        (tmp_path / "schema.ttl", tmp_path / "mapping.ttl", tmp_path / "queries")]


def test_lifecycle_validation_executes_http_and_invalidates_stale_expectations(requirement):
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs

    root, cfg = requirement
    lifecycle.transition("propose", cfg, "q1", "proposal.yaml", root)
    (root / "approval.yaml").write_text(yaml.safe_dump({"actor": "human", "decision": "approved",
        "reviewer": "synthetic test reviewer", "reviewed_on": "2026-10-22",
        "proposal_sha256": lifecycle.digest(root / "proposal.yaml")}))
    lifecycle.transition("approve", cfg, "q1", "approval.yaml", root)
    query = root / "ontology/queries/cq1.rq"
    query.write_text("SELECT (1 AS ?answer) WHERE {}")
    lifecycle.transition("implement", cfg, "q1", "ontology/queries/cq1.rq", root)
    expectations = {"cq1.rq": {"query_sha256": lifecycle.digest(query), "columns": ["answer"],
                               "number": {"column": "answer", "value": 1}}}
    (root / "expectations.yaml").write_text(yaml.safe_dump(expectations))
    requests_seen = []

    class Endpoint(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"])).decode()
            sparql = parse_qs(body)["query"][0]
            requests_seen.append(sparql)
            result = Graph().query(sparql).serialize(format="csv")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.end_headers()
            self.wfile.write(result)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Endpoint)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    cfg["method"]["ontop"] = {"port": server.server_port}
    try:
        assert lifecycle.transition("validate", cfg, "q1", "expectations.yaml", root) == "validated"
        assert requests_seen == [query.read_text()]
        assert lifecycle.validation_errors(cfg, root) == []
        data = json.loads((root / "state.json").read_text())
        assert len(data["events"]) == 4
        (root / "expectations.yaml").write_text("changed expected answer")
        assert lifecycle.transition("status", cfg, "q1", root=root) == "implemented"
        assert lifecycle.validation_errors(cfg, root)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_experiment_runner_preserves_failed_status_and_runs_independent_checks(tmp_path):
    from experiment import run_checks
    output = tmp_path / "report"
    results = run_checks([("failure", [sys.executable, "-c", "print('failed check'); raise SystemExit(9)"]),
                          ("independent", [sys.executable, "-c", "print('passed check')"])], tmp_path, output)
    assert [row["exit_code"] for row in results] == [9, 0]
    assert [row["status"] for row in results] == ["failed", "passed"]
    assert "failed check" in (output / "failure.log").read_text()
    assert all(row["seconds"] >= 0 for row in results)


def test_energy_shared_properties_do_not_create_unrelated_classes():
    from owlrl import DeductiveClosure, RDFS_Semantics
    from rdflib import Namespace, RDF, Literal
    energy = Namespace("https://w3id.org/rastro/energia#")
    graph = Graph().parse(ROOT / "ontology/energia/energia.ttl")
    graph.add((energy.exampleStudy, RDF.type, energy.EnvironmentalStudy))
    graph.add((energy.exampleStudy, energy.date, Literal("2026-01-01")))
    graph.add((energy.exampleSurroundings, RDF.type, energy.SurroundingsLink))
    graph.add((energy.exampleSurroundings, energy.aboutVenting, energy.exampleVenting))
    graph.add((energy.exampleConcession, RDF.type, energy.VentingWithoutReports))
    DeductiveClosure(RDFS_Semantics).expand(graph)
    assert (energy.exampleStudy, RDF.type, energy.Venting) not in graph
    assert (energy.exampleSurroundings, RDF.type, energy.LocationLink) not in graph
    assert (energy.exampleConcession, RDF.type, energy.ConcessionToReview) in graph
