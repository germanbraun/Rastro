"""Draw a second holdout: 100 more works from the same approved capture, none of the original sample or of the first
holdout, to test the two linking fixes found on the first holdout (glued footnote number, longer institute name).

Run from the checkout root: python3 -I docs/experiments/research-affiliations/holdout-2/draw.py
Same eligibility as draw.py (at least one affiliation mentioning Argentina); both earlier samples' DOIs are removed,
the rest sorted and 100 drawn with random.Random(SEED).sample. The seed was fixed before drawing. Writes the DOI list
and every distinct affiliation string with its mentions (committed), so the blind reviewers need nothing else.
"""

import csv
import hashlib
import json
import random
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
CAPTURE = Path("data/raw/research-affiliations/crossref-2025-argentina.json")
CAPTURE_SHA256 = "9d328bbe41ad3ba27092cf08532a70007e38f5ec4aca4cb389d7c8ed6428e526"
SEED, SIZE = 20261028, 100


def argentina_text(s):
    return "argentin" in unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def main():
    raw = CAPTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CAPTURE_SHA256:
        raise SystemExit("The capture is not the approved one; do not draw from another snapshot.")
    works = {w["DOI"].lower(): w for w in json.loads(raw)["items"]}
    seen = set((HERE.parent / "sample-dois.txt").read_text().split()) | set((HERE.parent / "holdout/dois.txt").read_text().split())
    eligible = sorted(d for d, w in works.items() if d not in seen
                      and any(argentina_text(f.get("name", "")) for a in w.get("author", []) for f in a.get("affiliation", [])))
    chosen = sorted(random.Random(SEED).sample(eligible, SIZE))
    (HERE / "dois.txt").write_text("\n".join(chosen) + "\n")
    mentions = [(d, i, j, (f.get("name") or "").strip(),
                 next((x["id"] for x in f.get("id", []) if x.get("id-type") == "ROR"), ""))
                for d in chosen for i, a in enumerate(works[d].get("author", []))
                for j, f in enumerate(a.get("affiliation", []))]
    mentions = [m for m in mentions if m[3]]
    with (HERE / "mentions.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["doi", "author_position", "affiliation_position", "text", "ror_id"])
        w.writerows(mentions)
    counts = {}
    for m in mentions:
        counts[m[3]] = counts.get(m[3], 0) + 1
    with (HERE / "strings.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["string_id", "review", "mentions", "text"])
        for n, text in enumerate(sorted(counts), 1):
            w.writerow([f"k{n:03d}", "full" if argentina_text(text) else "screen", counts[text], text])
    print(f"eligible {len(eligible)}, works {len(chosen)}, mentions {len(mentions)}, strings {len(counts)}, "
          f"with «argentin» {sum(argentina_text(t) for t in counts)}", file=sys.stderr)


if __name__ == "__main__":
    main()
