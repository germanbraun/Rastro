"""Score the linker's rules on the holdout against the blind annotation, before and after the five fixes.

Run from the checkout root: python3 -I docs/experiments/research-affiliations/holdout/compare.py
Each mention's reference is its string's annotated organizations. A mention agrees when the linker's identified set
equals it; precision and recall are over (mention, organization) pairs. Strings that were also in the original
sample (the one the fixes were tuned on) are reported apart: the fair number is on the new ones. Writes
resultados.json and prints the mentions that differ.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def score(found, reference, mentions, keep):
    pairs_found = {(m, o) for m in mentions if keep(m) for o in found.get(m, set())}
    pairs_ref = {(m, o) for m in mentions if keep(m) for o in reference[m]}
    hit = len(pairs_found & pairs_ref)
    chosen = [m for m in mentions if keep(m)]
    return {"mentions": len(chosen),
            "agree": sum(found.get(m, set()) == reference[m] for m in chosen),
            "links_found": len(pairs_found), "links_reference": len(pairs_ref), "correct": hit,
            "precision": round(hit / len(pairs_found), 3) if pairs_found else None,
            "recall": round(hit / len(pairs_ref), 3) if pairs_ref else None}


def main():
    notes = {r["string_id"]: r for r in csv.DictReader((HERE / "annotations.csv").open())}
    strings = {r["text"]: r["string_id"] for r in csv.DictReader((HERE / "strings.csv").open())}
    seen = {r["text"] for r in csv.DictReader((HERE.parent / "blind-review/strings.csv").open())}
    mentions, text = [], {}
    for r in csv.DictReader((HERE / "mentions.csv").open()):
        m = (r["doi"], r["author_position"], r["affiliation_position"])
        mentions.append(m)
        text[m] = r["text"]
    missing = [s for s in strings.values() if s not in notes]
    if missing:
        raise SystemExit(f"Strings without annotation: {missing[:5]}")
    reference = {m: set(notes[strings[text[m]]]["organizations"].split()) for m in mentions}
    out, differ = {}, {}
    for version in ("before", "after"):
        found, doubtful = defaultdict(set), defaultdict(set)
        for r in csv.DictReader((HERE / f"links-{version}.csv").open()):
            m = (r["doi"], r["author_position"], r["affiliation_position"])
            (found if r["status"] == "identified" else doubtful)[m].add(r["organization"])
        out[version] = {"all": score(found, reference, mentions, lambda m: True),
                        "new_strings": score(found, reference, mentions, lambda m: text[m] not in seen),
                        "doubtful_candidates": sum(len(v) for v in doubtful.values()),
                        "doubtful_in_reference": sum(len(v & reference[m]) for m, v in doubtful.items())}
        differ[version] = {strings[text[m]]: {"text": text[m], "rastro": sorted(found.get(m, set())),
                                              "reference": sorted(reference[m])}
                           for m in mentions if found.get(m, set()) != reference[m]}
    out["strings"] = {"total": len(strings), "also_in_original_sample": len(set(strings) & seen)}
    out["ambiguous_strings"] = sorted(s for s, r in notes.items() if r["ambiguous"].strip().lower() == "yes")
    (HERE / "resultados.json").write_text(json.dumps(out, indent=1) + "\n")
    (HERE / "differences.json").write_text(json.dumps(differ, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    for sid, d in sorted(differ["after"].items()):
        print(sid, d["rastro"], "vs", d["reference"], "|", d["text"][:150])


if __name__ == "__main__":
    main()
