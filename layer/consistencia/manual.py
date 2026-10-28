"""Consistency test: answer the paraphrases without an API, with subagents or by hand.

    prompt <q> <n> <B|C>   prints the prompt (the same as the evaluation, with paraphrase n)
    try <q> <n> <B|C>      runs a query (from stdin), saves the attempt and shows the
                           result or the error
    puntaje                compares every answer with the reference of the original

Each answer is saved in respuestas/<q>-<n>-<B|C>.json.

    docker compose run --rm -T layer-eval python /layer/consistencia/manual.py prompt q01 1 C
"""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))

from answer import MAX_ATTEMPTS, output_schema, retry_message, system_prompt, try_query  # noqa: E402

HERE = Path(__file__).parent
ANSWERS = HERE / "respuestas"
PARAPHRASES = yaml.safe_load((HERE / "parafrasis.yaml").read_text())
QUESTIONS = {q["id"]: q for q in yaml.safe_load((HERE.parent / "eval" / "questions.yaml").read_text())["questions"]}
SAVED = json.loads((HERE.parent / "eval" / "results.json").read_text())["questions"]
NAMES = {"B": "SQL directo", "D": "SQL + enlaces", "C": "Rastro"}


def text(qid, n):
    return QUESTIONS[qid]["question"] if n == 0 else PARAPHRASES[qid][n - 1]


def prompt(qid, n, approach):
    kind = QUESTIONS[qid]["kind"]
    print(f"<sistema>\n{system_prompt(approach, "oncologia")}\n</sistema>\n")
    print(f"<pregunta>\n{text(qid, n)}\n</pregunta>\n")
    print("Respondé solo con un objeto JSON que cumpla este esquema, sin texto alrededor:")
    print(json.dumps(output_schema(approach, kind), ensure_ascii=False))


def attempt(qid, n, approach):
    path = ANSWERS / f"{qid}-{n}-{approach}.json"
    entry = json.loads(path.read_text()) if path.exists() else {"question": text(qid, n), "attempts": []}
    if len(entry["attempts"]) >= MAX_ATTEMPTS:
        print(f"Ya hay {MAX_ATTEMPTS} intentos para esta pregunta: no se aceptan más.")
        return
    result = try_query(approach, sys.stdin.read().strip(), QUESTIONS[qid]["kind"], "oncologia")
    entry["attempts"].append(result["attempt"])
    entry["answer"] = result["answer"]
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=1))
    if result["attempt"]["error"]:
        print("ERROR. Mensaje para el LLM:\n" + retry_message(result["attempt"]["error"]))
    else:
        print(f"OK. Respuesta: {json.dumps(result['answer'], ensure_ascii=False)[:500]}")


def score_all():
    from run import admin, score  # the same criterion as the evaluation
    rows, totals = [], {k: {"ok": 0, "n": 0, "consistent": 0} for k in NAMES}
    with admin() as conn:
        for qid, paraphrases in PARAPHRASES.items():
            q, reference = QUESTIONS[qid], SAVED[qid]["reference"]
            cells = []
            for k in NAMES:
                answers = [SAVED[qid][k]["answer"]]
                for n in range(1, len(paraphrases) + 1):
                    path = ANSWERS / f"{qid}-{n}-{k}.json"
                    answers.append(json.loads(path.read_text()).get("answer") if path.exists() else None)
                oks = [bool(score(q, reference, a, conn)) for a in answers]
                totals[k]["ok"] += sum(oks)
                totals[k]["n"] += len(oks)
                same = len({json.dumps(a, sort_keys=True) if not isinstance(a, list) else json.dumps(sorted(a)) for a in answers}) == 1
                totals[k]["consistent"] += same
                cells.append(f"{sum(oks)}/{len(oks)} correctas · " + " / ".join(fmt(a) for a in answers))
            rows.append((qid, cells))
    print(f"{'':5}" + "".join(f"{name:48}" for name in NAMES.values()))
    for qid, cells in rows:
        print(f"{qid:5}" + "".join(f"{c:48}" for c in cells))
    print()
    for k, name in NAMES.items():
        t = totals[k]
        print(f"{name:12} {t['ok']} de {t['n']} correctas · misma respuesta en las 4 versiones: "
              f"{t['consistent']} de {len(PARAPHRASES)} preguntas")


def fmt(a):
    if a is None:
        return "—"
    if isinstance(a, list):
        return f"{len(a)}"
    return f"{a:,.0f}".replace(",", ".") if a == int(a) else f"{a:.1f}"


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "prompt":
        prompt(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif command == "try":
        attempt(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif command == "puntaje":
        score_all()
