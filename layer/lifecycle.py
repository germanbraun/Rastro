"""Enforce requirement handoffs: propose, approve, implement, validate, status.

python layer/lifecycle.py <command> <domain> <question-id> [--artifact FILE]
Approval artifacts record a real human decision; this tool cannot authenticate the reviewer.
Changing a bound artifact invalidates the dependent state instead of silently keeping approval.
"""
import argparse
import fcntl
import hashlib
import json
import os
from datetime import date
from pathlib import Path

import yaml

from method import EVIDENCE, ROOT, digest, local, verify_queries

STATES = ("proposed", "approved", "implemented", "validated")


def bound(path, root):
    file = local(path, root)
    if not file.is_file():
        raise ValueError(f"Missing artifact: {path}")
    return {"path": str(file.relative_to(root)), "sha256": digest(file)}


def unchanged(artifact, root):
    path = local(artifact["path"], root)
    return path.is_file() and digest(path) == artifact["sha256"]


def context(cfg, root):
    method = cfg["method"]
    paths = [cfg["ontology"], method["mapping"]]
    if method.get("source_manifest"):
        paths.append(method["source_manifest"])
    return [bound(path, root) for path in paths]


def question_status(entry, cfg, root=ROOT):
    if not unchanged(entry["proposal"], root):
        return "proposed"
    state = entry["state"]
    if state == "proposed":
        return state
    if not unchanged(entry["approval"], root):
        return "proposed"
    if state == "approved":
        return state
    if not unchanged(entry["query"], root) or entry["context"] != context(cfg, root):
        return "approved"
    if state == "validated" and not expectations_unchanged(entry["validation"], root):
        return "implemented"
    return state


def expectation_entry(path, name, root):
    """A question's own entry of the expectations file, and its fingerprint: editing another query's entry does not
    invalidate this question."""
    data = yaml.safe_load(local(path, root).read_text())
    spec = data.get(name) if isinstance(data, dict) else None
    return spec, hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def expectations_unchanged(validation, root):
    if "entry" not in validation:   # receipts from before per-question binding bind the whole file
        return unchanged(validation["expectations"], root)
    path = local(validation["expectations"]["path"], root)
    return path.is_file() and expectation_entry(path, validation["entry"]["name"], root)[1] == validation["entry"]["sha256"]


def validation_level(entry):
    """«technical» (invariants) or «independent» (independent references); None if not validated or unknown."""
    return (entry.get("validation") or {}).get("level")


def state_path(cfg, root):
    path = cfg.get("method", {}).get("lifecycle")
    if not path:
        raise ValueError("Declare method.lifecycle before adopting the lifecycle; no legacy approvals are inferred")
    return local(path, root)


def read_state(cfg, root=ROOT):
    path = state_path(cfg, root)
    return json.loads(path.read_text()) if path.exists() else {"questions": {}, "events": []}


def transition(command, cfg, qid, artifact=None, root=ROOT):
    path = state_path(cfg, root)
    lock_path = root / "data/cache" / ("lifecycle-" + path.stem + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = read_state(cfg, root)
        entry = data["questions"].get(qid)
        current = question_status(entry, cfg, root) if entry else None
        if command == "status":
            if entry is None:
                raise ValueError(f"No proposed requirement: {qid}")
            return current
        if command == "propose":
            proposal = yaml.safe_load(local(artifact, root).read_text())
            for key in ("question", "definitions", "scope", "answer_type", "verification_plan"):
                if not proposal.get(key):
                    raise ValueError(f"Proposal requires {key}")
            entry = {"state": "proposed", "proposal": bound(artifact, root)}
        elif command == "approve":
            if current != "proposed" or not unchanged(entry["proposal"], root):
                raise ValueError("Approval requires a current proposed requirement; re-propose changed artifacts first")
            review = yaml.safe_load(local(artifact, root).read_text())
            if (review.get("decision") != "approved" or review.get("actor") != "human"
                    or not review.get("reviewer") or not review.get("reviewed_on")
                    or review.get("proposal_sha256") != entry["proposal"]["sha256"]):
                raise ValueError("A human approval record must bind the current proposal fingerprint")
            date.fromisoformat(str(review["reviewed_on"]))
            entry.update(state="approved", approval=bound(artifact, root))
        elif command == "implement":
            if current != "approved":
                raise ValueError("Implementation requires current approved definitions")
            query = bound(artifact, root)
            if not local(artifact, root).is_relative_to(local(cfg["method"]["queries"], root)):
                raise ValueError("Query must be inside the registered competency-query folder")
            entry.update(state="implemented", query=query, context=context(cfg, root))
        elif command == "validate":
            if current != "implemented":
                raise ValueError("Validation requires a current implementation")
            if not cfg["method"].get("source_manifest"):
                raise ValueError("Validation requires a versioned source manifest")
            # The ontology/mapping checks and every query assertion must actually execute.
            import sys
            sys.path.insert(0, str(ROOT / "ontology"))
            from check import revisar
            if not revisar(local(cfg["ontology"], root), local(cfg["method"]["mapping"], root),
                           local(cfg["method"]["queries"], root)):
                raise ValueError("Ontology/mapping check failed")
            expectations = yaml.safe_load(local(artifact, root).read_text())
            verify_queries(cfg, expectations, root)
            name = Path(entry["query"]["path"]).name
            spec, fingerprint = expectation_entry(artifact, name, root)
            entry.update(state="validated", validation={
                "expectations": bound(artifact, root), "entry": {"name": name, "sha256": fingerprint},
                "level": EVIDENCE[spec["evidence"]], "date": date.today().isoformat()})
        else:
            raise ValueError(f"Unknown transition: {command}")
        data["questions"][qid] = entry
        data["events"].append({"question": qid, "from": current, "to": entry["state"],
                               "date": date.today().isoformat(), "artifact": bound(artifact, root)})
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        os.replace(temporary, path)
        return entry["state"]


def validation_errors(cfg, root=ROOT):
    if not cfg.get("method", {}).get("lifecycle"):
        return ["A new-domain experiment requires method.lifecycle"]
    state = read_state(cfg, root)
    expected = {str(path.relative_to(root)) for path in local(cfg["method"]["queries"], root).glob("cq*.rq")}
    validated = set()
    errors = []
    for qid, entry in state["questions"].items():
        if question_status(entry, cfg, root) != "validated":
            errors.append(f"{qid}: lifecycle is not currently validated")
        else:
            validated.add(entry["query"]["path"])
    if not expected or validated != expected:
        errors.append("Validated lifecycle receipts must cover exactly the competency queries")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["propose", "approve", "implement", "validate", "status"])
    parser.add_argument("domain")
    parser.add_argument("question")
    parser.add_argument("--artifact")
    args = parser.parse_args()
    if args.command != "status" and not args.artifact:
        parser.error("--artifact is required")
    registry = yaml.safe_load((ROOT / "layer/dominios.yaml").read_text())
    print(transition(args.command, registry[args.domain], args.question, args.artifact))


if __name__ == "__main__":
    main()
