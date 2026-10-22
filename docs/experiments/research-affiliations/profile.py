"""Offline inspection only: profile the downloaded Crossref cohort and ROR release, without loading a domain.

Run from the checkout root: python3 -I docs/experiments/research-affiliations/profile.py
Inputs stay in ignored data/raw/research-affiliations/. No network, database, mapping or model queries.
The candidate matches below are a naive structural probe of join difficulty, not proposed or approved links.
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
    "crossref-2025-argentina.json": "https://api.crossref.org/works (query in the file)",
    "ror-v2.15.zip": "https://zenodo.org/records/ (ROR data dump v2.15, 2026-10-20)",
    "ror-zenodo-latest.json": "https://zenodo.org/api/communities/ror-data/records?q=&sort=newest&size=3",
    "crossref-retrieve-metadata.html": "https://www.crossref.org/documentation/retrieve-metadata/",
    "crossref-rest-api.html": "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
    "ror-data-dump-doc.html": "https://ror.readme.io/docs/data-dump",
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def norm(text):
    """Lowercase, strip accents and punctuation, collapse spaces: only for the structural probe."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()


def ror_argentina():
    with zipfile.ZipFile(RAW / "ror-v2.15.zip") as z:
        name = next(n for n in z.namelist() if n.endswith(".json"))
        records = json.loads(z.read(name))
    orgs = [r for r in records if any(loc.get("geonames_details", {}).get("country_code") == "AR"
                                      for loc in r.get("locations", []))]
    return records, orgs


def main():
    profile = {"status": "inspection_only_not_approved",
               "artifacts": [{"path": str(RAW / n), "url": u, "bytes": (RAW / n).stat().st_size, "sha256": sha256(RAW / n)}
                             for n, u in ARTIFACTS.items() if (RAW / n).exists()]}

    # --- Crossref cohort ---
    cohort = json.loads((RAW / "crossref-2025-argentina.json").read_text())
    works = cohort["items"]
    dois = Counter(w["DOI"].lower() for w in works)
    authors = [a for w in works for a in w.get("author", [])]
    entries = [(w["DOI"], aff) for w in works for a in w.get("author", []) for aff in a.get("affiliation", [])]
    raw = [aff.get("name", "").strip() for _, aff in entries if aff.get("name", "").strip()]
    with_id = [aff for _, aff in entries if aff.get("id")]
    id_types = Counter(i.get("id-type") for aff in with_id for i in aff.get("id", []))
    ar = [aff.get("name", "") for _, aff in entries if "argentin" in norm(aff.get("name", ""))]
    works_with_ar = sum(any("argentin" in norm(aff.get("name", "")) for a in w.get("author", []) for aff in a.get("affiliation", []))
                        for w in works)
    ar_entries_with_ror = sum(1 for _, aff in entries if "argentin" in norm(aff.get("name", ""))
                              and any(i.get("id-type") == "ROR" for i in aff.get("id", [])))
    profile["crossref"] = {
        "query": cohort["query"], "retrieved": cohort["retrieved"],
        "works": len(works), "distinct_dois": len(dois), "duplicate_dois": sum(c - 1 for c in dois.values() if c > 1),
        "works_with_an_affiliation_mentioning_argentina": works_with_ar,
        "authors": len(authors),
        "authors_with_at_least_one_affiliation": sum(1 for a in authors if a.get("affiliation")),
        "affiliation_entries": len(entries),
        "affiliation_entries_with_raw_string": len(raw),
        "affiliation_entries_with_any_id": len(with_id),
        "affiliation_id_types": dict(id_types),
        "argentine_affiliation_entries": len(ar),
        "argentine_entries_with_ror_id": ar_entries_with_ror,
        "distinct_argentine_strings": len(set(norm(s) for s in ar)),
        "publishers_top": Counter(w.get("publisher", "") for w in works).most_common(8),
    }

    # --- ROR, Argentine organizations ---
    records, orgs = ror_argentina()
    name_types = Counter(t for o in orgs for n in o.get("names", []) for t in n.get("types", []))
    relations = Counter(r.get("type") for o in orgs for r in o.get("relationships", []))
    profile["ror"] = {
        "records": len(records), "argentine_orgs": len(orgs),
        "status": dict(Counter(o.get("status") for o in orgs)),
        "types": dict(Counter(t for o in orgs for t in o.get("types", []))),
        "name_types": dict(name_types),
        "relationship_types": dict(relations),
        "orgs_with_parent": sum(1 for o in orgs if any(r.get("type") == "parent" for r in o.get("relationships", []))),
    }

    # --- Structural join probe: normalized name equality and name containment, Argentine strings only ---
    index = defaultdict(set)
    for o in orgs:
        for n in o.get("names", []):
            index[norm(n["value"])].add(o["id"])
    display = {o["id"]: next((n["value"] for n in o["names"] if "ror_display" in n.get("types", [])), o["id"]) for o in orgs}
    long_names = [(k, v) for k, v in index.items() if len(k) >= 12]
    acronyms = {norm(n["value"]): o["id"] for o in orgs for n in o.get("names", []) if "acronym" in n.get("types", [])}
    outcome = Counter()
    examples = defaultdict(list)
    for s in sorted(set(ar)):
        k = norm(s)
        exact = index.get(k, set())
        if len(exact) == 1:
            kind = "exact_single"
        elif len(exact) > 1:
            kind = "exact_ambiguous"
        else:
            contained = {i for name, ids in long_names if f" {name} " in f" {k} " for i in ids}
            tokens = set(k.split())
            acr = {acronyms[a] for a in acronyms if a in tokens}
            hits = contained | acr
            kind = "no_candidate" if not hits else ("one_candidate_by_containment" if len(hits) == 1
                                                     else "several_candidates_by_containment")
            if hits and len(examples[kind]) < 6:
                examples[kind].append({"string": s, "candidates": sorted(display[i] for i in hits)[:6]})
        outcome[kind] += 1
        if kind in ("exact_single", "no_candidate") and len(examples[kind]) < 6:
            examples[kind].append({"string": s})
    profile["join_probe"] = {"distinct_argentine_strings": len(set(ar)), "outcome": dict(outcome),
                             "examples": dict(examples),
                             "note": "naive probe of difficulty; candidates are not links and need evidence and review"}
    top = Counter(norm(s) for s in ar).most_common(15)
    profile["crossref"]["most_frequent_argentine_strings_normalized"] = top
    OUT.write_text(json.dumps(profile, ensure_ascii=False, indent=1) + "\n")
    print(f"Wrote {OUT}; inspection only, no links approved.")


if __name__ == "__main__":
    main()
