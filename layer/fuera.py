"""Does the assistant say when it lacks the data, or does it make it up? Questions outside Rastro's data.

The questions are in layer/<dominio>/fuera/preguntas.yaml: the ones the data does not answer and one
control question that it does. As in the evaluation, the answers are written by an LLM that sees only the prompt
(one subagent per path, with all the questions together) and this script runs and counts them.

    prompt <A|B|D|C>     the prompt of a path: the system prompt, the questions and the answer format
    guardar <A|B|D|C>    reads the LLM's JSON from stdin ({"f1": "...", ...}), runs each query and saves;
                         if a query fails, shows the error to give back (up to 3 attempts)
    puntaje              writes resultados.json (read by the app) and resultados.md

A is the LLM alone, without data (answer what you know; if you do not know, say so). B, D and C, as in the
evaluation: SQL over the sources, SQL with Rastro's links and SPARQL over Rastro. All four
have the same rule: if it is not enough, «SIN DATOS:» and what is missing.

    docker compose run --rm -T layer-eval python /layer/fuera.py energia prompt C
"""

import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from answer import DOMAINS, MAX_ATTEMPTS, retry_message, sin_datos, system_prompt, try_query  # noqa: E402

DOMAIN = sys.argv[1]
HERE = Path(__file__).parent / DOMAIN / "fuera"
QUESTIONS = {q["id"]: q for q in yaml.safe_load((HERE / "preguntas.yaml").read_text())["preguntas"]}
NAMES = {"A": "LLM solo", "B": "Sin Rastro (SQL)", "D": "SQL + enlaces de Rastro", "C": "Con Rastro"}
LLM_ALONE = ("\n\nNo tenés acceso a ninguna base de datos: respondé con lo que sabés, en una línea, con el número. "
             "Si no lo sabés, devolvé una sola línea que empiece con «SIN DATOS:» y diga qué falta.")


def system(approach):
    if approach == "A":
        return DOMAINS[DOMAIN]["base"] + LLM_ALONE
    return system_prompt(approach, DOMAIN)


def prompt(approach):
    print(f"<sistema>\n{system(approach)}\n</sistema>\n")
    print("Respondé cada pregunta por separado, como si fuera la única:\n")
    for qid, q in QUESTIONS.items():
        print(f"<pregunta id=\"{qid}\">\n{q['pregunta']}\n</pregunta>\n")
    what = "tu respuesta" if approach == "A" else "la query"
    print(f"Respondé solo con un objeto JSON, sin texto alrededor: una clave por pregunta ({', '.join(QUESTIONS)}) "
          f"y como valor {what}, o una línea que empiece con «SIN DATOS:».")


def save(approach):
    HERE.joinpath("respuestas").mkdir(exist_ok=True)
    path = HERE / "respuestas" / f"{approach}.json"
    saved = json.loads(path.read_text()) if path.exists() else {}
    for qid, text in json.loads(sys.stdin.read()).items():
        entry = saved.setdefault(qid, {"pregunta": QUESTIONS[qid]["pregunta"], "intentos": []})
        if len(entry["intentos"]) >= MAX_ATTEMPTS or (entry["intentos"] and not entry["intentos"][-1].get("error")):
            print(f"{qid}: ya tiene respuesta o se acabaron los intentos.")
            continue
        if approach == "A" or sin_datos(text):
            entry["intentos"].append({"respuesta": text, "error": None})
            print(f"{qid}: {text[:200]}")
            continue
        result = try_query(approach, text, "número", DOMAIN)
        entry["intentos"].append({"query": text, "respuesta": result["answer"], "error": result["attempt"]["error"]})
        if result["attempt"]["error"]:
            print(f"{qid}: ERROR (quedan {MAX_ATTEMPTS - len(entry['intentos'])}). Mensaje para el LLM:\n"
                  + retry_message(result["attempt"]["error"]))
        else:
            print(f"{qid}: OK, respuesta {result['answer']}")
    path.write_text(json.dumps(saved, ensure_ascii=False, indent=1) + "\n")


def verdict(question, entry):
    """✅ said it lacks the data (or answered the control one), ❌ answered what it does not know (or refused the
    control one), ⚠️ neither (the query failed three times)."""
    last = entry["intentos"][-1] if entry and entry["intentos"] else None
    if last is None or last.get("error"):
        return "⚠️", "sin respuesta"
    text = last.get("query") or last.get("respuesta")
    declined = bool(sin_datos(str(text)))
    shown = sin_datos(str(text)) if declined else str(last.get("respuesta"))
    if question["sin_datos"]:
        return ("✅" if declined else "❌"), shown
    return ("❌" if declined else "✅"), shown


def score():
    results = {"fecha": date.today().isoformat(), "caminos": NAMES, "preguntas": {}, "totales": {}}
    for approach in NAMES:
        path = HERE / "respuestas" / f"{approach}.json"
        saved = json.loads(path.read_text()) if path.exists() else {}
        for qid, q in QUESTIONS.items():
            mark, shown = verdict(q, saved.get(qid))
            row = results["preguntas"].setdefault(qid, {"pregunta": q["pregunta"], "falta": q["falta"],
                                                         "sin_datos": q["sin_datos"]})
            row[approach] = {"marca": mark, "respuesta": shown}
        results["totales"][approach] = sum(results["preguntas"][q][approach]["marca"] == "✅" for q in QUESTIONS)
    (HERE / "resultados.json").write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n")
    lines = [f"# ¿Dice cuándo no tiene el dato? ({results['fecha']})", "",
             "✅ dijo que no tiene el dato (o respondió la de control) · ❌ respondió algo que los datos no dicen "
             "(o se negó en la de control) · ⚠️ la query falló tres veces", "",
             "| # | Pregunta | Qué falta | " + " | ".join(NAMES.values()) + " |", "|---|---|---|" + "---|" * len(NAMES)]
    for qid, row in results["preguntas"].items():
        cells = " | ".join(f"{row[a]['marca']} {str(row[a]['respuesta'])[:80]}" for a in NAMES)
        lines.append(f"| {qid} | {row['pregunta']} | {row['falta']} | {cells} |")
    lines.append("| | **Total** | | " + " | ".join(f"**{results['totales'][a]} de {len(QUESTIONS)}**" for a in NAMES) + " |")
    (HERE / "resultados.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    command = sys.argv[2]
    if command == "prompt":
        prompt(sys.argv[3])
    elif command == "guardar":
        save(sys.argv[3])
    elif command == "puntaje":
        score()
