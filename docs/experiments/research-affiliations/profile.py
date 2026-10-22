"""Offline inspection only: profile the captured Crossref cohort and ROR release, without loading a domain.

Run from the checkout root, after fetch.py: python3 -I docs/experiments/research-affiliations/profile.py
Inputs stay in ignored data/raw/research-affiliations/; a missing input is an error. No network, database, mapping or
model queries. The probe below is a heuristic measure of join difficulty: its hits are not links, and several hits
can be false candidates rather than several organizations actually named.
"""

import hashlib
import json
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

RAW = Path("data/raw/research-affiliations")
OUT = Path("docs/experiments/research-affiliations/source-profile.json")
ARTIFACTS = {
    "crossref-2025-argentina.json": "https://api.crossref.org/works (query and pages in crossref-ledger.json)",
    "crossref-ledger.json": "written by fetch.py",
    "ror-v2.15.zip": "https://zenodo.org/api/records/23500708/files/v2.15-2026-10-20-ror-data.zip/content",
    "crossref-retrieve-metadata.html": "https://www.crossref.org/documentation/retrieve-metadata/",
    "ror-data-dump-doc.html": "https://ror.readme.io/docs/data-dump",
}
EMAIL_OR_URL = re.compile(r"\S+@\S+|https?://\S+|www\.\S+")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def norm(text):
    """Lowercase, strip accents and punctuation, collapse spaces: only for grouping and the heuristic probe."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()


def argentina_text(s):
    """A string mentioning Argentina: a candidate, not a verified Argentine affiliation."""
    return "argentin" in norm(s)


def share(part, whole):
    return round(100 * part / whole, 2) if whole else None


def main():
    missing = [n for n in ARTIFACTS if not (RAW / n).exists()]
    if missing:
        raise SystemExit(f"Missing inputs in {RAW}: {', '.join(missing)}. Run fetch.py first.")
    ledger = json.loads((RAW / "crossref-ledger.json").read_text())
    profile = {"status": "inspection_only_not_approved",
               "ror_release": {"record": "https://zenodo.org/records/23500708", "doi": "10.5281/zenodo.23500708",
                               "version": "v2.15", "date": "2026-10-20", "md5": "5522990688eb1b94811a8145e131b41e"},
               "crossref_ledger": {k: ledger[k] for k in ("query", "reported_total", "items", "termination", "sha256")}
               | {"requests": len(ledger["pages"]), "first_request": ledger["pages"][0]["requested"],
                  "last_request": ledger["pages"][-1]["requested"]},
               "artifacts": [{"path": str(RAW / n), "source": u, "bytes": (RAW / n).stat().st_size,
                              "sha256": sha256(RAW / n)} for n, u in ARTIFACTS.items()]}

    # --- Crossref cohort ---
    works = json.loads((RAW / "crossref-2025-argentina.json").read_text())["items"]
    dois = Counter(w["DOI"].lower() for w in works)
    authors = [a for w in works for a in w.get("author", [])]
    entries = [aff for a in authors for aff in a.get("affiliation", [])]

    def text(aff):
        return (aff.get("name") or "").strip()

    def has_ror(aff):
        return any(i.get("id-type") == "ROR" for i in aff.get("id", []))

    ar_entries = [aff for aff in entries if argentina_text(text(aff))]
    by_string = defaultdict(list)
    for aff in ar_entries:
        by_string[text(aff)].append(has_ror(aff))
    profile["crossref"] = {
        "works": len(works), "duplicate_dois": sum(c - 1 for c in dois.values() if c > 1),
        "works_with_argentina_text": sum(any(argentina_text(text(f)) for a in w.get("author", [])
                                             for f in a.get("affiliation", [])) for w in works),
        "authors": len(authors),
        "authors_with_nonblank_affiliation_text": sum(1 for a in authors if any(text(f) for f in a.get("affiliation", []))),
        "affiliation_entries": len(entries),
        "affiliation_entries_with_nonblank_text": sum(1 for f in entries if text(f)),
        "affiliation_entries_with_ror": sum(1 for f in entries if has_ror(f)),
        "argentina_text_entries": len(ar_entries),
        "argentina_text_entries_with_ror": sum(1 for f in ar_entries if has_ror(f)),
        "argentina_text_distinct_raw_strings": len(by_string),
        "argentina_text_distinct_raw_strings_with_ror_in_every_occurrence": sum(1 for v in by_string.values() if all(v)),
        "argentina_text_distinct_raw_strings_with_ror_in_some_occurrences_only": sum(1 for v in by_string.values()
                                                                                   if any(v) and not all(v)),
        "argentina_text_distinct_normalized_strings": len({norm(s) for s in by_string}),
        "publishers_top": Counter(w.get("publisher", "") for w in works).most_common(8),
        "most_frequent_argentina_text_normalized": Counter(norm(text(f)) for f in ar_entries).most_common(15),
    }
    c = profile["crossref"]
    profile["gates"] = {
        "authors_with_nonblank_text_pct": share(c["authors_with_nonblank_affiliation_text"], c["authors"]),
        "argentina_text_entries_with_ror_pct": share(c["argentina_text_entries_with_ror"], c["argentina_text_entries"]),
        "argentina_text_raw_strings_with_ror_in_every_occurrence_pct":
            share(c["argentina_text_distinct_raw_strings_with_ror_in_every_occurrence"], c["argentina_text_distinct_raw_strings"]),
        "note": "cohort selected by a Crossref query on affiliation text, so it has affiliations by construction",
    }

    # --- ROR ---
    with zipfile.ZipFile(RAW / "ror-v2.15.zip") as z:
        records = json.loads(z.read(next(n for n in z.namelist() if n.endswith(".json"))))
    orgs = [r for r in records if any(loc.get("geonames_details", {}).get("country_code") == "AR"
                                      for loc in r.get("locations", []))]
    profile["ror"] = {
        "records": len(records), "argentine_orgs": len(orgs),
        "status": dict(Counter(o.get("status") for o in orgs)),
        "types": dict(Counter(t for o in orgs for t in o.get("types", []))),
        "name_types": dict(Counter(t for o in orgs for n in o.get("names", []) for t in n.get("types", []))),
        "relationship_types": dict(Counter(r.get("type") for o in orgs for r in o.get("relationships", []))),
        "orgs_with_parent": sum(1 for o in orgs if any(r.get("type") == "parent" for r in o.get("relationships", []))),
    }

    # --- Heuristic probe over distinct raw Argentina-text strings (e-mails and URLs removed first) ---
    names, acronyms = defaultdict(set), defaultdict(set)
    for o in orgs:
        for n in o.get("names", []):
            (acronyms if "acronym" in n.get("types", []) else names)[norm(n["value"])].add(o["id"])
    colliding = {a: len(ids) for a, ids in acronyms.items() if len(ids) > 1}
    display = {o["id"]: next((n["value"] for n in o["names"] if "ror_display" in n.get("types", [])), o["id"]) for o in orgs}
    long_names = [(k, v) for k, v in names.items() if len(k) >= 12]
    outcome, examples = Counter(), defaultdict(list)
    for s in sorted(by_string):
        k = norm(EMAIL_OR_URL.sub(" ", s))
        exact = names.get(k, set()) | acronyms.get(k, set())
        if exact:
            kind = "whole_string_equals_one_name" if len(exact) == 1 else "whole_string_equals_names_of_several_orgs"
            hits = exact
        else:
            tokens = set(k.split())
            hits = {i for name, ids in long_names if f" {name} " in f" {k} " for i in ids}
            hits |= {i for a, ids in acronyms.items() if a in tokens for i in ids}
            kind = ("no_heuristic_hit" if not hits else
                    "one_heuristic_hit" if len(hits) == 1 else "several_heuristic_hits")
        outcome[kind] += 1
        if len(examples[kind]) < 6:
            examples[kind].append({"string": s, "hits": sorted(display[i] for i in hits)[:6]})
    profile["heuristic_probe"] = {
        "unit": "distinct raw Argentina-text strings", "strings": len(by_string), "outcome": dict(outcome),
        "acronyms_shared_by_several_orgs": colliding, "examples": dict(examples),
        "note": "probe behaviour, not the true number of ambiguous or unmatched affiliations; hits are not links",
    }
    OUT.write_text(json.dumps(profile, ensure_ascii=False, indent=1) + "\n")
    print(f"Wrote {OUT}; inspection only, no links approved.")


if __name__ == "__main__":
    main()
