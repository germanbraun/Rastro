"""Composition test: 5 questions that combine 3 or 4 concepts, for SQL + links (D)
and Rastro (C). Same prompt, retries and score as the evaluation.

    prompt <q> <D|C>    prints the prompt
    try <q> <D|C>       runs a query (from stdin), saves the attempt and shows the result
    puntaje             compares each answer with the reference

    docker compose run --rm -T layer-eval python /layer/composicion/manual.py prompt m1 C
"""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))

from answer import MAX_ATTEMPTS, output_schema, retry_message, run_sparql, system_prompt, to_answer, try_query  # noqa: E402

HERE = Path(__file__).parent
ANSWERS = HERE / "respuestas"
SPEC = yaml.safe_load((HERE / "preguntas.yaml").read_text())
QUESTIONS = {q["id"]: q for q in SPEC["questions"]}
NAMES = {"D": "SQL + enlaces", "C": "Rastro"}


def prompt(qid, approach):
    q = QUESTIONS[qid]
    print(f"<sistema>\n{system_prompt(approach)}\n</sistema>\n")
    print(f"<pregunta>\n{q['question']}\n</pregunta>\n")
    print("Respondé solo con un objeto JSON que cumpla este esquema, sin texto alrededor:")
    print(json.dumps(output_schema(approach, q["kind"]), ensure_ascii=False))


def attempt(qid, approach):
    path = ANSWERS / f"{qid}-{approach}.json"
    entry = json.loads(path.read_text()) if path.exists() else {"question": QUESTIONS[qid]["question"], "attempts": []}
    if len(entry["attempts"]) >= MAX_ATTEMPTS:
        print(f"Ya hay {MAX_ATTEMPTS} intentos para esta pregunta: no se aceptan más.")
        return
    result = try_query(approach, sys.stdin.read().strip(), QUESTIONS[qid]["kind"])
    entry["attempts"].append(result["attempt"])
    entry["answer"] = result["answer"]
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=1))
    if result["attempt"]["error"]:
        print("ERROR. Mensaje para el LLM:\n" + retry_message(result["attempt"]["error"]))
    else:
        print(f"OK. Respuesta: {json.dumps(result['answer'], ensure_ascii=False)[:500]}")


def score_all():
    from run import admin, score
    totals = {k: 0 for k in NAMES}
    with admin() as conn:
        for qid, q in QUESTIONS.items():
            reference = to_answer(run_sparql(SPEC["prefixes"] + q["reference"]), q["kind"])
            cells = []
            for k in NAMES:
                path = ANSWERS / f"{qid}-{k}.json"
                entry = json.loads(path.read_text()) if path.exists() else {"attempts": []}
                ok = bool(score(q, reference, entry.get("answer"), conn))
                totals[k] += ok
                cells.append(f"{'✅' if ok else '❌'} {entry.get('answer')} ({len(entry['attempts'])} int.)")
            print(f"{qid}  ref {reference}  ·  " + "  ·  ".join(cells))
    print("\n" + " · ".join(f"{NAMES[k]}: {v} de {len(QUESTIONS)}" for k, v in totals.items()))


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "prompt":
        prompt(sys.argv[2], sys.argv[3])
    elif command == "try":
        attempt(sys.argv[2], sys.argv[3])
    elif command == "puntaje":
        score_all()
