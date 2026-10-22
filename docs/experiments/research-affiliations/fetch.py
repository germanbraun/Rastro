"""Capture the inspection snapshot: the Crossref cohort with a request ledger, and the exact ROR release.

Run from the checkout root: python3 -I docs/experiments/research-affiliations/fetch.py
Writes to ignored data/raw/research-affiliations/. Crossref is a live API: every run is a new snapshot, recorded in
its ledger (query, reported total, each page's cursor, size, time and hash). It cannot restore an earlier capture.
"""

import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAW = Path("data/raw/research-affiliations")
CONTACT = "germanbraun@gmail.com"
HEADERS = {"User-Agent": f"Rastro-inspection/0.2 (mailto:{CONTACT})"}
CROSSREF = "https://api.crossref.org/works"
QUERY = {"query.affiliation": "Argentina",
         "filter": "from-pub-date:2025-01-01,until-pub-date:2025-12-31,type:journal-article",
         "select": "DOI,author,container-title,publisher,issued,member,ISSN",
         "rows": "1000", "mailto": CONTACT}
ROR = {"record": "https://zenodo.org/records/23500708", "doi": "10.5281/zenodo.23500708",
       "file": "https://zenodo.org/api/records/23500708/files/v2.15-2026-10-20-ror-data.zip/content",
       "md5": "5522990688eb1b94811a8145e131b41e", "path": RAW / "ror-v2.15.zip"}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=180) as r:
        return r.status, r.geturl(), r.read()


def crossref():
    pages, items, cursor = [], [], "*"
    while True:
        url = CROSSREF + "?" + urllib.parse.urlencode({**QUERY, "cursor": cursor})
        status, final, body = get(url)
        message = json.loads(body)["message"]
        pages.append({"requested": now(), "status": status, "final_url": final, "cursor": cursor,
                      "items": len(message["items"]), "total_results": message["total-results"],
                      "sha256": hashlib.sha256(body).hexdigest()})
        items += message["items"]
        if not message["items"]:
            break
        cursor = message["next-cursor"]
        time.sleep(1)
    capture = {"query": QUERY, "retrieved": pages[0]["requested"], "items": items}
    path = RAW / "crossref-2025-argentina.json"
    path.write_text(json.dumps(capture))
    ledger = {"endpoint": CROSSREF, "query": QUERY, "pages": pages, "items": len(items),
              "reported_total": pages[0]["total_results"], "termination": "empty page after the last cursor",
              "file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (RAW / "crossref-ledger.json").write_text(json.dumps(ledger, indent=1))
    print(f"Crossref: {len(items)} items of {ledger['reported_total']} reported, {len(pages)} requests")


def ror():
    if not ROR["path"].exists() or hashlib.md5(ROR["path"].read_bytes()).hexdigest() != ROR["md5"]:
        ROR["path"].write_bytes(get(ROR["file"])[2])
    md5 = hashlib.md5(ROR["path"].read_bytes()).hexdigest()
    if md5 != ROR["md5"]:
        raise SystemExit(f"ROR checksum mismatch: {md5}")
    print(f"ROR: {ROR['path']} matches Zenodo's MD5 {md5}")


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    ror()
    crossref()
