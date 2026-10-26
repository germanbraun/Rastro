"""The five evaluation references, derived from the blind reviewer's annotation only (instructions.md), never from
Rastro. Checks that the annotation is complete and valid, then writes layer/afiliaciones/eval/referencias.json, which
layer/evaluar.py uses instead of the provisional SPARQL references. Run from the repo root:
python3 docs/experiments/research-affiliations/blind-review/reference.py
"""
import csv
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parents[3] / "layer/afiliaciones/eval/referencias.json"
CONICET, UBA, DOI_E2 = "https://ror.org/03cqe8w59", "https://ror.org/0081fs513", "10.1001/jamaneurol.2025.0023"


def read(name):
    return list(csv.DictReader((HERE / name).open(encoding="utf-8")))


def norm(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def check(annotations, strings, argentine):
    """Every string reviewed under the protocol: a screen row says no, yes or unsure; a full, yes or unsure row lists
    its organizations or says «ninguna» in its note; every id is an Argentine ROR organization."""
    problems = []
    if [a["string_id"] for a in annotations] != [s["string_id"] for s in strings]:
        problems.append("the annotation does not have exactly the 962 strings, in order")
    for a in annotations:
        sid, screen = a["string_id"], a["screen"].strip().lower()
        if a["review"] == "screen" and screen not in ("no", "yes", "unsure"):
            problems.append(f"{sid}: screen must be no, yes or unsure")
        full = a["review"] == "full" or screen in ("yes", "unsure")
        ids = a["organizations"].split() + a["other_references"].split()
        if full and not a["organizations"].strip() and "ninguna" not in norm(a["note"]):
            problems.append(f"{sid}: reviewed in full but no organizations and no «ninguna» in the note")
        if not full and ids:
            problems.append(f"{sid}: screened «no» but lists organizations")
        problems += [f"{sid}: {i} is not an Argentine ROR organization" for i in ids if i not in argentine]
    return problems


def main():
    strings, annotations = read("strings.csv"), read("annotations.csv")
    argentine = {o["id"] for o in read("ror-argentina.csv")}
    problems = check(annotations, strings, argentine)
    if problems:
        sys.exit("The annotation is not complete:\n" + "\n".join(problems[:40]))
    by_text = {s["text"]: next(a for a in annotations if a["string_id"] == s["string_id"]) for s in strings}
    mentions = read("mentions.csv")

    def named(mention, with_other=False):
        a = by_text[mention["text"]]
        return set(a["organizations"].split()) | (set(a["other_references"].split()) if with_other else set())

    def answers(with_other):
        return {
            "e1": len({m["doi"] for m in mentions if CONICET in named(m, with_other)}),
            "e2": sorted({o for m in mentions if m["doi"].lower() == DOI_E2 for o in named(m, with_other)}),
            "e3": len({o for m in mentions for o in named(m, with_other)}),
            "e4": sorted({m["doi"].lower() for m in mentions if UBA in named(m, with_other)}),
            "e5": sum(1 for m in mentions if "argentin" in norm(m["text"]) and not named(m, with_other)),
        }

    digest = hashlib.sha256((HERE / "annotations.csv").read_bytes()).hexdigest()
    OUT.write_text(json.dumps({
        "nota": "Referencias de una revisión a ciegas hecha por GPT (asistente de IA), sin ver Rastro; falta que una "
                "persona las confirme.",
        "annotation": {"path": "docs/experiments/research-affiliations/blind-review/annotations.csv", "sha256": digest},
        "answers": answers(False),
        "with_other_references": answers(True),   # how much the rule leaves out: forms that ROR does not have
        "ambiguous": sum(a["ambiguous"].strip().lower() == "yes" for a in annotations),
    }, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(answers(False), ensure_ascii=False))


if __name__ == "__main__":
    main()
