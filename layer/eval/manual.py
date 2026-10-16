"""Responder la evaluación sin API: a mano, con claude.ai o con otro asistente.

    prompt <q> <A|B|C>    imprime el prompt exacto (el mismo que usa run.py)
    set <q> A             guarda la respuesta de A (JSON {"answer": ...} por stdin)
    try <q> <B|C>         ejecuta una query (por stdin), guarda el intento y muestra
                          el resultado o el error; si falló, imprime el mensaje para
                          devolverle al LLM
    reset <q> <A|B|C>     borra la respuesta guardada

Ejemplo:
    docker compose run --rm -T layer-eval python /layer/eval/manual.py prompt q01 C
"""

import json
import os
import sys
from pathlib import Path

import psycopg
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from answer import MAX_ATTEMPTS, output_schema, retry_message, system_prompt, try_query  # noqa: E402

HERE = Path(__file__).parent
RESULTS = HERE / "results.json"


def load():
    questions = {q["id"]: q for q in yaml.safe_load((HERE / "questions.yaml").read_text())["questions"]}
    saved = json.loads(RESULTS.read_text()) if RESULTS.exists() else {"questions": {}}
    return questions, saved


def grant_reader():
    """Los cargadores recrean sus esquemas: se vuelven a dar los permisos de solo lectura."""
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        conn.execute((HERE.parent / "reader.sql").read_text())


def main():
    command, qid, approach = sys.argv[1], sys.argv[2], sys.argv[3]
    grant_reader()
    questions, saved = load()
    q = questions[qid]
    entry = saved["questions"].setdefault(qid, {"question": q["question"]})

    if command == "prompt":
        print(f"<sistema>\n{system_prompt(approach)}\n</sistema>\n")
        print(f"<pregunta>\n{q['question']}\n</pregunta>\n")
        print("Respondé solo con un objeto JSON que cumpla este esquema, sin texto alrededor:")
        print(json.dumps(output_schema(approach, q["kind"]), ensure_ascii=False))
        return

    if command == "set":
        entry[approach] = {"answer": json.loads(sys.stdin.read())["answer"], "attempts": []}
    elif command == "try":
        result = try_query(approach, sys.stdin.read().strip(), q["kind"])
        record = entry.setdefault(approach, {"answer": None, "attempts": []})
        record["attempts"].append(result["attempt"])
        error = result["attempt"]["error"]
        if error is None:
            record["answer"] = result["answer"]
            shown = result["answer"][:20] if isinstance(result["answer"], list) else result["answer"]
            print(f"OK: {shown}")
        elif len(record["attempts"]) >= MAX_ATTEMPTS:
            print(f"ERROR (último intento, sin respuesta):\n{error}")
        else:
            print(f"ERROR (intento {len(record['attempts'])} de {MAX_ATTEMPTS}). Mensaje para el LLM:\n"
                  + retry_message(error))
    elif command == "reset":
        entry.pop(approach, None)
    RESULTS.write_text(json.dumps(saved, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
