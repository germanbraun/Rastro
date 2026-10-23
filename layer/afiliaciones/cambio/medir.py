"""Measure every saved evaluation query and the three competency queries, without writing any saved answer.

Run in the layer-eval service: python /layer/afiliaciones/cambio/medir.py <step>. Writes medicion-<step>.json next to it.
"""
import json
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, "/layer")
from answer import run_sparql_table, try_query  # noqa: E402

import yaml  # noqa: E402

HERE = Path(__file__).parent
DOMAIN = "afiliaciones"
GARRAHAN = "https://ror.org/051mda743"
AFFECTED = [("10.1002/epd2.70126", "4", "0"), ("10.1002/epd2.70126", "5", "0")]


def grant_readers():
    """The linker recreates the afiliaciones schema, which drops the read-only users' grants: give them again."""
    with psycopg.connect(host="postgres", port=5432, dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
                         password=os.environ["PG_PASSWORD"]) as conn:
        conn.execute((HERE.parent / "reader.sql").read_text())


def main(step):
    grant_readers()
    kinds = {q["id"]: q["kind"] for q in yaml.safe_load((HERE.parent / "eval/questions.yaml").read_text())["questions"]}
    answers = {}
    for path in sorted((HERE.parent / "respuestas").glob("*.json")):
        qid, _, approach = path.stem.split("-")
        ok = [a for a in json.loads(path.read_text())["attempts"] if a["error"] is None]
        result = try_query(approach, ok[-1]["query"], kinds[qid], DOMAIN)
        answers[path.stem] = {"answer": result["answer"], "error": result["attempt"]["error"]}
    queries = {}
    for name in ("cq1", "cq2", "cq3"):
        columns, rows = run_sparql_table(Path(f"/ontology/afiliaciones/queries/{name}.rq").read_text(), DOMAIN)
        records = [dict(zip(columns, r)) for r in rows]
        queries[name] = {"rows": len(records)}
        if name == "cq1":
            queries[name]["affected"] = sorted({(r["organization"] or "") for r in records
                                                if (r["doi"], str(r["authorPosition"]), str(r["affiliationPosition"])) in AFFECTED})
        if name == "cq2":
            queries[name]["garrahan"] = next((int(float(r["publications"])) for r in records if r["organization"] == GARRAHAN), 0)
        if name == "cq3":
            queries[name]["affected"] = sum((r["doi"], str(r["authorPosition"]), str(r["affiliationPosition"])) in AFFECTED
                                            for r in records)
    (HERE / f"medicion-{step}.json").write_text(json.dumps({"answers": answers, "queries": queries}, ensure_ascii=False, indent=1))
    print(step, {k: v for k, v in queries.items()})


if __name__ == "__main__":
    main(sys.argv[1])
