"""Measures «Conversar con los datos» (layer/chat.py) with the domain's conversations, without an API key.

The chat's own code runs every turn: the query step, Rastro running the query (and giving an error back), the answer
in words and the check of its numbers. Only the model call changes: RASTRO_PROVIDER=files writes each call to
layer/<domain>/chat/llamadas/<key>.txt and reads the reply from <key>.json. A fresh assistant answers each file,
seeing only that file (the evaluation's rule: one prompt per evaluator), and writes the JSON reply next to it.

    run      runs every conversation as far as the replies go; lists the calls still waiting for a reply. Run it again
             after they are answered: a follow-up's call exists only once the turn before it has its answer
    puntaje  when no call waits: the references (SPARQL over Rastro), the score and resultado.json / resultado.md

    docker compose run --rm -T layer-eval python /layer/chat_eval.py energia run|puntaje

A turn is right when its answer in words says the reference: a number within 5 % (as written, or in thousands,
millions or billions), the names of a list (80 % of them), or, where the data has no answer, that it says so (or its
query finds nothing) instead of a number.
"""
import datetime
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import yaml

HERE = Path(__file__).parent
DOMAIN = sys.argv[1] if len(sys.argv) > 1 else "energia"
FOLDER = HERE / DOMAIN / "chat"
os.environ.update(RASTRO_PROVIDER="files", RASTRO_FILES=str(FOLDER / "llamadas"))   # before answer reads them

import answer  # noqa: E402
import chat  # noqa: E402

TOLERANCE = 0.05
SCALES = (1, 1e3, 1e6, 1e9)


def conversations():
    return yaml.safe_load((FOLDER / "conversaciones.yaml").read_text())


def run_all():
    """Every conversation, turn after turn, until a call has no reply. Returns ({id: turns}, waiting keys)."""
    done, waiting = {}, []
    for c in conversations()["conversations"]:
        history = []
        for spec in c["turns"]:
            try:
                history.append(chat.turn(spec["question"], history, DOMAIN))
            except answer.Pending as pending:
                waiting.append(str(pending))
                break
        done[c["id"]] = history
    return done, waiting


def plain(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", re.sub(r"\b(s\.?a\.?u?|s\.?r\.?l)\b", " ", text)).split()


def says_number(text, reference):
    values = [chat.parse_number(w) for w in chat.NUMBER.findall(text)]
    return any(v is not None and abs(v * s - reference) <= TOLERANCE * abs(reference) for v in values for s in SCALES)


def says_names(text, names):
    words = " ".join(plain(text))
    found = [n for n in names if " ".join(plain(n)) in words]
    return len(found) >= 0.8 * len(names)


def score(spec, turn, prefixes):
    """(right, the reference as shown) for one turn."""
    if spec["kind"] == "sin_datos":
        return bool(turn.get("sin_datos") or (turn.get("query") and not turn.get("rows"))), "sin datos"
    _, rows = answer.run_sparql_table(prefixes + spec["reference"], DOMAIN)
    said = turn.get("answer") or ""
    if spec["kind"] == "número":
        reference = float(rows[0][0])
        return says_number(said, reference), reference
    names = [r[0] for r in rows]
    return says_names(said, names), names


def puntaje():
    done, waiting = run_all()
    if waiting:
        sys.exit(f"{len(waiting)} llamadas esperan respuesta: corré «run» y respondelas antes de puntuar")
    data = conversations()
    turns = []
    for c in data["conversations"]:
        for n, (spec, turn) in enumerate(zip(c["turns"], done[c["id"]])):
            right, reference = score(spec, turn, data["prefixes"])
            turns.append({"conversation": c["id"], "turn": n + 1, "question": spec["question"], "kind": spec["kind"],
                          "reference": reference, "answer": turn.get("answer"), "sin_datos": turn.get("sin_datos"),
                          "query": turn.get("query"), "attempts": len(turn.get("attempts", [])),
                          "unsupported": turn.get("unsupported", []), "right": right})
    run = yaml.safe_load((HERE / DOMAIN / "eval" / "run.yaml").read_text())
    result = {"date": datetime.date.today().isoformat(), "model": run["model"], "model_version": run["model_version"],
              "how": "RASTRO_PROVIDER=files: a fresh assistant answered each call, seeing only its file",
              "totals": {"turns": len(turns), "right": sum(t["right"] for t in turns),
                         "follow_ups": sum(t["turn"] > 1 for t in turns),
                         "follow_ups_right": sum(t["right"] for t in turns if t["turn"] > 1),
                         "with_unsupported_numbers": sum(bool(t["unsupported"]) for t in turns),
                         "retries": sum(max(t["attempts"] - 1, 0) for t in turns)},
              "turns": turns}
    (FOLDER / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (FOLDER / "resultado.md").write_text(markdown(result))
    print(markdown(result))


def markdown(result):
    t = result["totals"]
    lines = [f"# Conversar con los datos: {DOMAIN} ({result['date']}, {result['model']})", "",
             f"Correctas: **{t['right']} de {t['turns']}** (preguntas que siguen a otra: {t['follow_ups_right']} de "
             f"{t['follow_ups']}). Respuestas con un número que no está en los datos: {t['with_unsupported_numbers']}. "
             f"Consultas repetidas por un error: {t['retries']}.", "",
             "| Conv. | Pregunta | Esperado | Respuesta | ¿Bien? |", "|---|---|---|---|---|"]
    for turn in result["turns"]:
        said = turn["answer"] or f"SIN DATOS: {turn['sin_datos']}"
        flag = "✅" if turn["right"] else "❌"
        if turn["unsupported"]:
            flag += f" (sin respaldo: {', '.join(turn['unsupported'])})"
        reference = ", ".join(turn["reference"]) if isinstance(turn["reference"], list) else turn["reference"]
        lines.append(f"| {turn['conversation']}.{turn['turn']} | {turn['question']} | {reference} | "
                     f"{said.replace('|', '/').replace(chr(10), ' ')} | {flag} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    step = sys.argv[2] if len(sys.argv) > 2 else "run"
    if step == "run":
        _, waiting = run_all()
        print("\n".join(f"llamadas/{key}.txt" for key in waiting) or "Ninguna llamada espera: corré «puntaje».")
    elif step == "puntaje":
        puntaje()
    else:
        sys.exit(__doc__)
