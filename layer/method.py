"""Executable gates for the Rastro method. Run from the repository root.

registry [domain], verify domain --expectations FILE, publication domain,
experiment domain --init|--lint|--check|--start STEP|--stop STEP --work TEXT|--append KIND --field KEY=VALUE...
The experiment log is written by these commands, never by hand. Missing evidence is pending, never a pass.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import shlex
import subprocess
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(path, root=ROOT):
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {path}")
    return resolved


def registry_errors(registry, root=ROOT):
    errors = []
    for domain, cfg in registry.items():
        method = cfg.get("method", {})
        ontop = method.get("ontop")
        if ontop:
            port = ontop.get("port")
            if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
                errors.append(f"{domain}: invalid Ontop port")
            compose = yaml.safe_load((root / "infra/docker-compose.yml").read_text())
            if ontop.get("service") not in compose.get("services", {}):
                errors.append(f"{domain}: missing Ontop compose service")
        for key in ("questions", "queries", "mapping", "app"):
            if key in method and not local(method[key], root).exists():
                errors.append(f"{domain}: missing method.{key}: {method[key]}")
        for key in ("ontology", "sparql_notes", "sql_notes", "links_notes"):
            if key in cfg and not local(cfg[key], root).is_file():
                errors.append(f"{domain}: missing {key}: {cfg[key]}")
        evaluation = method.get("evaluation")
        if evaluation:
            harness = evaluation.get("harness")
            folder = local(evaluation["folder"], root)
            if harness not in {"current", "legacy"}:
                errors.append(f"{domain}: declare evaluation.harness (current or legacy)")
            elif harness == "current":
                if not (folder / "eval/questions.yaml").is_file():
                    errors.append(f"{domain}: evaluation questions missing")
                command = shlex.split(evaluation["run"])
                if len(command) < 2 or command[-2:] != ["/layer/evaluar.py", domain]:
                    errors.append(f"{domain}: evaluation command targets a different question set")
                if folder != root / "layer" / domain:
                    errors.append(f"{domain}: current harness requires layer/{domain}")
            elif not (folder / "questions.yaml").is_file():
                errors.append(f"{domain}: legacy questions missing")
        quality = method.get("quality")
        if quality:
            for key in ("rules", "examples", "data", "result", "run"):
                if not quality.get(key):
                    errors.append(f"{domain}: quality.{key} is required")
        for key, path in method.get("quality", {}).items():
            if key in {"rules", "examples", "data", "predictions"} and not local(path, root).is_file():
                errors.append(f"{domain}: missing quality.{key}: {path}")
    return errors


EVIDENCE = {"invariant": "technical", "independent": "independent"}   # what an entry's expectations rest on


def check_csv(text, spec, root=ROOT):
    """Validate CSV shape and explicit assertions, including deliberately empty answers. «keys» compares the rows'
    key columns with a list derived from the sources: the same set, without repeats unless «repeats: true» (a key
    with several answer rows); «bounds» holds every row."""
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("Missing or duplicate CSV headers")
    columns = spec.get("columns")
    if not columns or reader.fieldnames != columns:
        raise ValueError(f"Expected columns {columns}, got {reader.fieldnames}")
    rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError("Malformed CSV rows")
    assertions = set(spec) & {"rows", "min_rows", "max_rows", "values", "number", "keys", "bounds"}
    if not assertions:
        raise ValueError("At least one explicit answer assertion is required")
    for key, ok in (("rows", len(rows) == spec.get("rows")),
                    ("min_rows", len(rows) >= spec.get("min_rows", 0)),
                    ("max_rows", len(rows) <= spec.get("max_rows", len(rows)))):
        if key in spec and not ok:
            raise ValueError(f"{key} assertion failed: got {len(rows)} rows")
    if "values" in spec:
        actual = sorted(tuple(row[c] for c in columns) for row in rows)
        expected = sorted(tuple(str(v) for v in row) for row in spec["values"])
        if actual != expected:
            raise ValueError("Answer values differ (including duplicate counts)")
    if "keys" in spec:
        key_columns = spec["keys"]["columns"]
        actual = [tuple(row[c] for c in key_columns) for row in rows]
        with local(spec["keys"]["file"], root).open(encoding="utf-8") as source:
            expected = {tuple(row[c] for c in key_columns) for row in csv.DictReader(source)}
        if len(actual) != len(set(actual)) and not spec["keys"].get("repeats"):
            raise ValueError("keys assertion failed: repeated keys")
        if set(actual) != expected:
            raise ValueError(f"keys assertion failed: {len(expected - set(actual))} missing, "
                             f"{len(set(actual) - expected)} unexpected")
    for column, limits in spec.get("bounds", {}).items():
        for row in rows:
            value = float(row[column]) if row[column] != "" else math.nan
            if not math.isfinite(value) or not (limits.get("min", -math.inf) <= value <= limits.get("max", math.inf)):
                raise ValueError(f"bounds assertion failed: {column}={row[column]!r}")
    if "number" in spec:
        number = spec["number"]
        if len(rows) != 1:
            raise ValueError("Numeric assertion requires exactly one row")
        value = float(rows[0][number["column"]])
        if not math.isfinite(value) or not math.isclose(value, float(number["value"]),
                                                       rel_tol=number.get("relative_tolerance", 0),
                                                       abs_tol=number.get("absolute_tolerance", 0)):
            raise ValueError("Numeric answer differs")
    return len(rows)


def verify_queries(cfg, expectations, root=ROOT, post=requests.post):
    folder = local(cfg["method"]["queries"], root)
    queries = {p.name: p for p in folder.glob("cq*.rq")}
    if not queries or set(expectations) != set(queries):
        raise ValueError("Expectations must cover exactly every competency query")
    port = cfg["method"]["ontop"]["port"]
    for name, query in sorted(queries.items()):
        spec = expectations[name]
        if spec.get("query_sha256") != digest(query):
            raise ValueError(f"{name}: missing or stale query fingerprint")
        if spec.get("evidence") not in EVIDENCE:
            raise ValueError(f"{name}: declare evidence: invariant (technical checks) or independent (references)")
        response = post(f"http://localhost:{port}/sparql", data={"query": query.read_text()},
                        headers={"Accept": "text/csv"}, timeout=60)
        response.raise_for_status()
        if response.headers.get("Content-Type", "").split(";")[0].strip().lower() != "text/csv":
            raise ValueError(f"{name}: endpoint did not return CSV")
        count = check_csv(response.text, spec, root)
        print(f"{name}: passed ({count} data rows; {EVIDENCE[spec['evidence']]} validation)")


def publication_errors(cfg, root=ROOT):
    """Evidence gates publication, not exploratory scoring. Never invent human approval."""
    evaluation = cfg["method"]["evaluation"]
    folder = local(evaluation["folder"], root)
    questions = folder / ("eval/questions.yaml" if evaluation["harness"] == "current" else "questions.yaml")
    manifest = folder / "reference-evidence.yaml"
    if not manifest.exists():
        return [f"Pending independent reference evidence: {manifest.relative_to(root)}"]
    data = yaml.safe_load(manifest.read_text()) or {}
    errors = []
    if data.get("questions_sha256") != digest(questions):
        errors.append("Reference evidence is stale: questions fingerprint differs")
    for key in ("model", "model_version", "prompt_artifacts", "attempt_artifacts", "source_versions"):
        if not data.get("run", {}).get(key):
            errors.append(f"Missing run.{key}")
    artifact = data.get("run", {}).get("result_artifact", {})
    expected_result = folder / ("resultados.json" if evaluation["harness"] == "current" else "results.json")
    if (not artifact.get("path") or local(artifact["path"], root) != expected_result
            or not expected_result.is_file() or digest(expected_result) != artifact.get("sha256")):
        errors.append("Missing or changed scored result artifact")
    for key in ("prompt_artifacts", "attempt_artifacts"):
        for artifact in data.get("run", {}).get(key, []):
            if not isinstance(artifact, dict) or not artifact.get("path"):
                errors.append(f"Invalid run.{key} artifact")
            elif not local(artifact["path"], root).is_file() or digest(local(artifact["path"], root)) != artifact.get("sha256"):
                errors.append(f"Missing or changed {key} artifact: {artifact['path']}")
    qids = {q["id"] for q in yaml.safe_load(questions.read_text())["questions"]}
    try:
        scored = json.loads(expected_result.read_text()).get("questions", {}) if expected_result.is_file() else {}
    except (json.JSONDecodeError, AttributeError):
        errors.append("Invalid scored result JSON")
        scored = {}
    if set(scored) != qids:
        errors.append("Scored results must cover exactly the current question set")
    lifecycle = cfg["method"].get("lifecycle")
    if lifecycle:
        from lifecycle import question_status, read_state
        state = read_state(cfg, root)
        for qid in qids:
            entry = state["questions"].get(qid)
            if entry is None or question_status(entry, cfg, root) != "validated":
                errors.append(f"{qid}: lifecycle validation is pending or stale")
    evidence = data.get("references", {})
    # Two roles: the business owner approves requirements, the reference reviewer provides evidence. One person
    # cannot stand in for the other.
    owners = set()
    if lifecycle:
        for entry in state["questions"].values():
            approval = local(entry["approval"]["path"], root) if entry.get("approval") else None
            if approval and approval.is_file():
                owners.add((yaml.safe_load(approval.read_text()) or {}).get("reviewer"))
    for qid, item in evidence.items():
        if item.get("reviewer") and item["reviewer"] in owners:
            errors.append(f"{qid}: the reference reviewer is the business owner who approved the requirements")
    if set(evidence) != qids:
        errors.append("Independent evidence must cover every question, including agreement cases")
    for qid in qids:
        item = evidence.get(qid, {})
        result = scored.get(qid, {})
        if any(path not in result for path in ("B", "D", "C")):
            errors.append(f"{qid}: missing B/D/C results")
        expected, actual = item.get("checked_answer"), result.get("reference")
        if isinstance(expected, list) and isinstance(actual, list):
            matches = sorted(json.dumps(v, sort_keys=True) for v in expected) == sorted(
                json.dumps(v, sort_keys=True) for v in actual)
        else:
            matches = expected == actual and expected is not None
        if not matches:
            errors.append(f"{qid}: independently checked answer differs from the scored reference")
        for key in ("source", "source_version", "checked_answer", "reviewer", "reviewed_on", "adjudication"):
            if key not in item or item[key] is None or item[key] == "":
                errors.append(f"{qid}: missing {key}")
        if item.get("independent") is not True or item.get("status") != "approved":
            errors.append(f"{qid}: independent human review is pending")
        artifact = item.get("artifact")
        if not artifact or not local(artifact, root).is_file() or digest(local(artifact, root)) != item.get("sha256"):
            errors.append(f"{qid}: missing or changed reference artifact")
    return errors


def experiment_errors(data):
    errors = []
    for key in ("domain", "sources", "question_author", "started_on", "ended_on", "method_commit"):
        if not data.get(key):
            errors.append(f"Missing experiment {key}")
    for step in ("initialize", "questions", "sources", "mapping", "links", "quality", "evaluate", "show", "maintain"):
        entry = data.get("steps", {}).get(step, {})
        if entry.get("status") not in {"completed", "not_applicable"} or not entry.get("evidence"):
            errors.append(f"{step}: outcome and evidence (or reason not applicable) required")
        for key in ("agent_hours", "human_hours"):
            value = entry.get(key)
            if isinstance(value, bool) or not isinstance(value, (float, int)) or value < 0:
                errors.append(f"{step}: measured {key} required")
    required = {"interventions": ("step", "decision", "reason", "kind", "minutes"),
                "errors_caught": ("step", "check", "failure_kind", "fix"),
                "method_changes": ("change", "scope", "reason")}
    for key, fields in required.items():
        entries = data.get(key)
        if not isinstance(entries, list):
            errors.append(f"Record {key}; use [] explicitly if none occurred")
            continue
        for entry in entries:
            if not isinstance(entry, dict) or any(field not in entry or entry[field] is None for field in fields):
                errors.append(f"Incomplete {key} entry; required: {fields}")
    if not data.get("result"):
        errors.append("Missing experiment result")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["registry", "verify", "publication", "experiment"])
    parser.add_argument("domain", nargs="?")
    parser.add_argument("--expectations", type=Path)
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--check", action="store_true", help="closing gate: complete, and the log lints")
    parser.add_argument("--lint", action="store_true", help="the log's structure, at any time")
    parser.add_argument("--start", metavar="STEP", help="open a session in a step")
    parser.add_argument("--stop", metavar="STEP", help="close the open session of a step")
    parser.add_argument("--work", default="", help="what the closing session did")
    parser.add_argument("--status", help="with --stop: the step's new status")
    parser.add_argument("--evidence", action="append", default=[], help="with --stop: an evidence line to add")
    parser.add_argument("--at", help="ISO time instead of now (say «approximate» in --work)")
    parser.add_argument("--append", choices=["intervention", "error", "method-change"])
    parser.add_argument("--field", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    registry = yaml.safe_load((ROOT / "layer/dominios.yaml").read_text())
    if args.domain and args.domain not in registry:
        parser.error("Unknown domain; initialize its registry entry first")
    selected = {args.domain: registry[args.domain]} if args.domain else registry
    errors = registry_errors(selected)
    if errors:
        raise ValueError("\n".join(errors))
    if args.command == "registry":
        print("Registry passed")
        return
    if not args.domain:
        parser.error("This command requires a domain")
    cfg = registry[args.domain]
    if args.command == "verify":
        if args.expectations is None:
            parser.error("--expectations is required; unreviewed answers are not verification")
        verify_queries(cfg, yaml.safe_load(args.expectations.read_text()))
    elif args.command == "publication":
        errors = publication_errors(cfg)
    else:
        path = ROOT / "docs/experiments" / f"{args.domain}.yaml"
        if args.init:
            path.parent.mkdir(exist_ok=True)
            data = {"domain": args.domain, "method_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "sources": [], "question_author": None, "started_on": None, "ended_on": None,
                "steps": {}, "interventions": [], "errors_caught": [], "method_changes": [], "result": None}
            with path.open("x") as out:
                yaml.safe_dump(data, out, sort_keys=False)
            print(f"Created pending log: {path}")
            return
        import experiment_log
        data = experiment_log.load(path)   # refuses duplicate keys
        if args.start or args.stop or args.append:
            if args.start:
                experiment_log.start(data, args.start, args.at)
            if args.stop:
                experiment_log.stop(data, args.stop, args.work, args.at, args.status, args.evidence)
            if args.append:
                fields = dict(item.split("=", 1) for item in args.field)
                if "minutes" in fields:
                    fields["minutes"] = None if fields["minutes"] in ("", "null") else float(fields["minutes"])
                experiment_log.append(data, args.append, fields)
            errors = experiment_log.lint_errors(data)
            if errors:
                raise ValueError("\n".join(errors))
            experiment_log.save(path, data)
            print(f"Recorded in {path.relative_to(ROOT)}")
            return
        errors = experiment_log.lint_errors(data, closing=args.check)
        if args.check:
            errors += experiment_errors(data)
            from lifecycle import validation_errors
            errors.extend(validation_errors(cfg, ROOT))
    if errors:
        raise ValueError("\n".join(errors))
    print(f"{args.command}: passed")


if __name__ == "__main__":
    main()
