"""Structural checks of the afiliaciones competency queries, derived from the pinned source records, not from Rastro.

layer/method.py verify only asserts row counts. These checks assert the properties the approved definitions promise:
- cq1 returns exactly the mention keys of the 100 selected works (none missing, none invented), with their source text;
- cq2 counts each organization once, with 1 to 100 distinct publications, and only organizations cq1 identifies;
- cq3 rows belong to selected mentions, and it returns the candidate established independently: «Instituto Sabato»
  appears in a selected affiliation and no ROR v2.15 record has that word in a name or a relationship label.
They are technical checks, not accuracy: the blind reviewer's reference decides that. Writes structural-checks.json.

Run on the machine (Ontop afiliaciones on localhost:8083): python3 docs/experiments/research-affiliations/structural-checks.py
"""

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
RAW = ROOT / "data/raw/research-affiliations"
QUERIES = ROOT / "ontology/afiliaciones/queries"
SAMPLE_SHA256 = "707ec8cc38e325d9edada4b4e375146208e86a527e28e06a5f12e77e2c402e76"
ROR_MD5 = "5522990688eb1b94811a8145e131b41e"


def fingerprint(path, algorithm):
    h = hashlib.new(algorithm)
    h.update(path.read_bytes())
    return h.hexdigest()


def source_mentions():
    path = RAW / "sample-100.json"
    if fingerprint(path, "sha256") != SAMPLE_SHA256:
        raise SystemExit("sample-100.json is not the approved snapshot")
    return {(w["DOI"].lower(), str(i), str(j)): f.get("name")
            for w in json.loads(path.read_text())
            for i, a in enumerate(w.get("author", []))
            for j, f in enumerate(a.get("affiliation", []))}


def ror_mentions(word):
    path = RAW / "ror-v2.15.zip"
    if fingerprint(path, "md5") != ROR_MD5:
        raise SystemExit("ror-v2.15.zip is not the approved release")
    with zipfile.ZipFile(path) as z:
        records = json.loads(z.read(next(n for n in z.namelist() if n.endswith(".json"))))
    return [r["id"] for r in records
            if any(word in (n.get("value") or "").lower() for n in r.get("names", []))
            or any(word in (x.get("label") or "").lower() for x in r.get("relationships", []))]


def run(name):
    query = QUERIES / name
    response = requests.post("http://localhost:8083/sparql", data={"query": query.read_text()},
                             headers={"Accept": "text/csv"}, timeout=120)
    response.raise_for_status()
    return fingerprint(query, "sha256"), list(csv.DictReader(io.StringIO(response.text)))


def main():
    mentions = source_mentions()
    results, failures = {}, []

    def check(label, ok, detail):
        results[label] = {"passed": bool(ok), "detail": detail}
        if not ok:
            failures.append(label)

    sha1, cq1 = run("cq1.rq")
    keys = {(r["doi"], r["authorPosition"], r["affiliationPosition"]) for r in cq1}
    check("cq1 covers exactly the source mention keys", keys == set(mentions),
          f"{len(set(mentions))} source keys; {len(keys)} in cq1; missing {len(set(mentions) - keys)}, "
          f"extra {len(keys - set(mentions))}")
    wrong_text = [k for k in keys & set(mentions)
                  if any(r["affiliation"] != mentions[k] for r in cq1
                         if (r["doi"], r["authorPosition"], r["affiliationPosition"]) == k)]
    check("cq1 shows each mention's source text", not wrong_text, f"{len(wrong_text)} keys with another text")

    sha2, cq2 = run("cq2.rq")
    organizations = [r["organization"] for r in cq2]
    counts = [int(r["publications"]) for r in cq2]
    identified = {r["organization"] for r in cq1 if r["organization"]}
    check("cq2 counts each organization once", len(organizations) == len(set(organizations)),
          f"{len(organizations)} rows, {len(set(organizations))} organizations")
    check("cq2 counts 1 to 100 publications per organization", all(1 <= n <= 100 for n in counts),
          f"range {min(counts)}-{max(counts)}")
    check("cq2 counts only organizations cq1 identifies", set(organizations) <= identified,
          f"{len(set(organizations) - identified)} not in cq1")

    sha3, cq3 = run("cq3.rq")
    outside = [r for r in cq3 if (r["doi"], r["authorPosition"], r["affiliationPosition"]) not in mentions]
    check("cq3 rows belong to selected mentions", not outside, f"{len(outside)} outside")
    check("cq3 rows carry evidence", all(r["evidence"].strip() for r in cq3), f"{len(cq3)} rows")
    in_source = [k for k, text in mentions.items() if "sabato" in (text or "").lower()]
    in_ror = ror_mentions("sabato")
    returned = [r for r in cq3 if "sabato" in r["candidate"].lower()]
    check("cq3 returns the independently established candidate (Instituto Sabato)",
          in_source and not in_ror and returned,
          f"{len(in_source)} selected mentions name it; {len(in_ror)} ROR records name it; {len(returned)} cq3 rows")

    receipt = {"queries": {"cq1.rq": sha1, "cq2.rq": sha2, "cq3.rq": sha3},
               "sources": {"sample-100.json sha256": SAMPLE_SHA256, "ror-v2.15.zip md5": ROR_MD5},
               "checks": results, "passed": not failures}
    (HERE / "structural-checks.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    for label, r in results.items():
        print(f"{'ok  ' if r['passed'] else 'FAIL'} {label}: {r['detail']}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
