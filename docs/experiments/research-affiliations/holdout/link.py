"""Run the linker's rules on the holdout, without touching Rastro: the mentions go to a temporary table and the
linker's link() reads it instead of crossref.affiliation. Corrections are not applied (none exist for these mentions):
this measures the rules alone. Doubtful candidates are reported apart; they would wait for a review.

Run from the checkout root with the stack up (Postgres on localhost:5434, the ROR tables loaded):
    python docs/experiments/research-affiliations/holdout/link.py [<link.py>] > <output.csv>
The default is the current linking/afiliaciones/link.py; pass another version to compare.
"""

import csv
import importlib.util
import os
import sys
from pathlib import Path

import psycopg

HERE = Path(__file__).parent


class Holdout:
    """A connection whose crossref.affiliation is the holdout's temporary table."""
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, *args):
        return self.conn.execute(query.replace("crossref.affiliation", "pg_temp.holdout_affiliation"), *args)


def env():
    values = dict(line.split("=", 1) for line in Path(".env").read_text().splitlines() if "=" in line and not line.startswith("#"))
    return {k: os.environ.get(k, v) for k, v in values.items()}


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("linking/afiliaciones/link.py")
    spec = importlib.util.spec_from_file_location("linker", path)
    linker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(linker)
    e = env()
    with psycopg.connect(host="localhost", port=int(e.get("PG_PORT", 5434)), dbname=e["PG_DB"], user=e["PG_USER"],
                         password=e["PG_PASSWORD"]) as conn:
        conn.execute("CREATE TEMP TABLE holdout_affiliation (doi text, author_position int, affiliation_position int, "
                     "name text, ror_id text)")
        with conn.cursor().copy("COPY holdout_affiliation FROM STDIN") as cp:
            for r in csv.DictReader((HERE / "mentions.csv").open()):
                cp.write_row([r["doi"], int(r["author_position"]), int(r["affiliation_position"]), r["text"],
                              r["ror_id"] or None])
        identified, doubtful = linker.link(Holdout(conn))
    w = csv.writer(sys.stdout)
    w.writerow(["doi", "author_position", "affiliation_position", "organization", "status", "rule"])
    for (doi, ap, fp, org), (rule, _) in sorted(identified.items()):
        w.writerow([doi, ap, fp, org, "identified", rule.split(":")[0]])
    for (doi, ap, fp, org), reason in sorted(doubtful.items()):
        w.writerow([doi, ap, fp, org, "doubtful", reason[:60]])


if __name__ == "__main__":
    main()
