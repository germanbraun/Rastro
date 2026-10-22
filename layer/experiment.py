"""Run a domain's method gates and retain measured execution evidence.

python layer/experiment.py <domain> --expectations FILE [--measure] [--publish]
This runs technical checks, not a claim of generalization or a substitute for human review.
"""
import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from method import ROOT, registry_errors


def commands(domain, cfg, expectations, measure=False, publish=False):
    method = cfg["method"]
    python = sys.executable
    checks = [
        ("registry", [python, "layer/method.py", "registry", domain]),
        ("ontology", [python, "ontology/check.py", cfg["ontology"]]),
    ]
    if method.get("quality"):
        checks += [("quality_examples", [python, "ontology/calidad.py", domain, "--examples-only"]),
                   ("quality_data", shlex.split(method["quality"]["run"]))]
    checks.append(("query_assertions", [python, "layer/method.py", "verify", domain, "--expectations", str(expectations)]))
    if method.get("app") and method.get("app_mode") != "legacy":
        checks.append(("app_views", ["docker", "compose", "run", "--rm", "--no-deps", "-T", "app",
                                     "python", "/app/check_domain.py", domain]))
    if measure:
        evaluation = method.get("evaluation")
        if not evaluation:
            raise ValueError("Measurement requested but evaluation is not built")
        run = shlex.split(evaluation["run"])
        if evaluation["harness"] == "legacy":
            checks.append(("evaluation", run + ["python", "/layer/eval/run.py", "--rerun"]))
        else:
            checks.extend(("evaluation_" + command, run + [command]) for command in ("rerun", "puntaje"))
    if publish:
        checks.append(("publication", [python, "layer/method.py", "publication", domain]))
    return checks


def run_checks(checks, cwd, output):
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name, command in checks:
        start = time.perf_counter()
        with (output / f"{name}.log").open("w") as log:
            try:
                result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
                code = result.returncode
            except (subprocess.TimeoutExpired, OSError) as error:
                log.write(f"{type(error).__name__}: {error}\n")
                code = 124 if isinstance(error, subprocess.TimeoutExpired) else 127
        results.append({"check": name, "command": command, "seconds": time.perf_counter() - start,
                        "exit_code": code, "status": "passed" if code == 0 else "failed",
                        "artifact": f"{name}.log"})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain")
    parser.add_argument("--expectations", required=True, type=Path)
    parser.add_argument("--measure", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    registry = yaml.safe_load((ROOT / "layer/dominios.yaml").read_text())
    cfg = registry[args.domain]
    errors = registry_errors({args.domain: cfg})
    if errors:
        raise ValueError("\n".join(errors))
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = ROOT / "data/cache/experiments" / args.domain / run
    checks = commands(args.domain, cfg, args.expectations.resolve(), args.measure, args.publish)
    results = run_checks(checks, ROOT, output)
    files = [ROOT / "docs/method.md", ROOT / "docs/method-contracts.md", *list((ROOT / ".claude/skills").rglob("*.md")),
             ROOT / "layer/method.py", ROOT / "layer/lifecycle.py", ROOT / "ontology/check.py", ROOT / "ontology/calidad.py",
             ROOT / "layer/experiment.py", ROOT / "app/dominio.py", ROOT / "app/check_domain.py",
             ROOT / "layer/dominios.yaml", ROOT / "infra/docker-compose.yml", ROOT / "requirements-dev.txt",
             ROOT / "infra/loaders/requirements.txt"]
    report = {"domain": args.domain, "run": run, "method_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "method_files": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
        "checks": results, "status": "passed" if all(row["exit_code"] == 0 for row in results) else "failed",
        "business_approval": "not_established_by_this_runner", "independent_review": "not_established_by_this_runner",
        "generalization": "not_established_by_a_technical_run"}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Technical checks: {report['status']}; evidence: {output / 'report.json'}")
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
