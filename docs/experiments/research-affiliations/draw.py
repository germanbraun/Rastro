"""Draw the bounded set: 100 works at random, with the seed fixed in the approval record.

Run from the checkout root: python3 -I docs/experiments/research-affiliations/draw.py
Reads the inspector's Crossref capture (checked against its approved SHA-256), keeps works with at least one
affiliation mentioning Argentina, sorts their DOIs and draws 100 with random.Random(SEED).sample. Writes the DOI list
(committed) and the selected raw records (ignored, with their fingerprint). Never redraw because a set looks hard.
"""

import hashlib
import json
import random
import unicodedata
from pathlib import Path

CAPTURE = Path("data/raw/research-affiliations/crossref-2025-argentina.json")
CAPTURE_SHA256 = "9d328bbe41ad3ba27092cf08532a70007e38f5ec4aca4cb389d7c8ed6428e526"
SEED, SIZE = 20261022, 100
DOIS = Path("docs/experiments/research-affiliations/sample-dois.txt")
SELECTED = Path("data/raw/research-affiliations/sample-100.json")
SUMMARY = Path("docs/experiments/research-affiliations/sample.json")


def argentina_text(s):
    return "argentin" in unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def main():
    raw = CAPTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CAPTURE_SHA256:
        raise SystemExit("The capture is not the approved one; do not draw from another snapshot.")
    works = {w["DOI"].lower(): w for w in json.loads(raw)["items"]}
    eligible = sorted(d for d, w in works.items()
                      if any(argentina_text(f.get("name", "")) for a in w.get("author", []) for f in a.get("affiliation", [])))
    chosen = sorted(random.Random(SEED).sample(eligible, SIZE))
    DOIS.write_text("\n".join(chosen) + "\n")
    selected = [works[d] for d in chosen]
    SELECTED.write_text(json.dumps(selected, ensure_ascii=False, sort_keys=True))
    mentions = [(w["DOI"], i, j, (f.get("name") or "").strip()) for w in selected
                for i, a in enumerate(w.get("author", [])) for j, f in enumerate(a.get("affiliation", []))]
    SUMMARY.write_text(json.dumps({
        "capture_sha256": CAPTURE_SHA256, "seed": SEED, "algorithm": "random.Random(seed).sample over sorted lowercase DOIs",
        "eligible_works": len(eligible), "selected_works": len(chosen),
        "dois_file": str(DOIS), "dois_sha256": hashlib.sha256(DOIS.read_bytes()).hexdigest(),
        "selected_records_file": str(SELECTED), "selected_records_sha256": hashlib.sha256(SELECTED.read_bytes()).hexdigest(),
        "authors": sum(len(w.get("author", [])) for w in selected),
        "affiliation_mentions": len(mentions),
        "distinct_raw_strings": len({m[3] for m in mentions if m[3]}),
        "argentina_text_mentions": sum(1 for m in mentions if argentina_text(m[3])),
        "mentions_with_ror": sum(1 for w in selected for a in w.get("author", []) for f in a.get("affiliation", [])
                                 if any(i.get("id-type") == "ROR" for i in f.get("id", []))),
        "blank_mentions": sum(1 for m in mentions if not m[3]),
        "note": "about 200 strings was an estimate, not a limit; this is the actual size",
    }, indent=1) + "\n")
    print(open(SUMMARY).read())


if __name__ == "__main__":
    main()
