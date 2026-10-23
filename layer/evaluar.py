"""Evaluación de un dominio: sin Rastro (SQL) y con Rastro (SPARQL). The results title and the optional SQL
function that normalizes company names come from the domain's method.evaluation entry in layer/dominios.yaml.

Las respuestas las escribe un LLM que solo ve el prompt (subagentes, a mano o con otro
asistente): este script le da el prompt, ejecuta cada query que propone y puntúa.

    El primer argumento es el dominio; sus archivos están en layer/<dominio>/.

    prompt <q> <n> <B|D|C> el prompt de la pregunta q; n = 0 es la pregunta de la evaluación
                           y n = 1, 2, 3 son sus otras formas (consistencia/parafrasis.yaml)
    try <q> <n> <B|D|C>    ejecuta una query (por stdin), guarda el intento y muestra el
                           resultado o el error, con el mensaje para devolverle al LLM
    rerun                  vuelve a ejecutar las queries guardadas (si cambiaron los datos), sin
                           pedirle nada nuevo al LLM
    puntaje                calcula las referencias, puntúa todo y escribe resultados.json
                           (lo lee la app) y resultados.md

B es sin Rastro: SQL sobre las tablas de las fuentes tal como se cargaron.
D es la línea de base justa: SQL sobre las mismas tablas más las tablas de Rastro
(esquema del dominio), documentadas con lo mismo que dice el diccionario.
C es con Rastro: SPARQL sobre el Ontop del dominio. Cada respuesta queda en
layer/<dominio>/respuestas/<q>-<n>-<B|D|C>.json.

    docker compose run --rm -T layer-eval python /layer/evaluar.py proveedores prompt p01 0 C
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

import psycopg
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from answer import DOMAINS, MAX_ATTEMPTS, output_schema, retry_message, run_sparql, system_prompt, to_answer, try_query  # noqa: E402

DOMAIN = sys.argv[1]
HERE = Path(__file__).parent / DOMAIN
EVALUATION = DOMAINS[DOMAIN]["method"]["evaluation"]
NORMALIZE = EVALUATION.get("normalize")   # SQL function for company names; without one, lists compare exactly
TITLE = EVALUATION["title"]
ANSWERS = HERE / "respuestas"
SPEC = yaml.safe_load((HERE / "eval" / "questions.yaml").read_text())
QUESTIONS = {q["id"]: q for q in SPEC["questions"]}
PARAPHRASES = yaml.safe_load((HERE / "consistencia" / "parafrasis.yaml").read_text()) or {}
NAMES = {"B": "Sin Rastro (SQL)", "D": "SQL + enlaces de Rastro", "C": "Con Rastro"}
TOLERANCE = 0.05    # números: correcto si está a menos del 5 % de la referencia
MIN_F1 = 0.8        # listas: correcto si coincide en al menos un 80 % (F1)


def admin():
    return psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                           f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")


def text(qid, n):
    return QUESTIONS[qid]["question"] if n == 0 else PARAPHRASES[qid][n - 1]


def prompt(qid, n, approach):
    print(f"<sistema>\n{system_prompt(approach, DOMAIN)}\n</sistema>\n")
    print(f"<pregunta>\n{text(qid, n)}\n</pregunta>\n")
    print("Respondé solo con un objeto JSON que cumpla este esquema, sin texto alrededor:")
    print(json.dumps(output_schema(approach, QUESTIONS[qid]["kind"]), ensure_ascii=False))


def attempt(qid, n, approach):
    ANSWERS.mkdir(exist_ok=True)
    path = ANSWERS / f"{qid}-{n}-{approach}.json"
    entry = json.loads(path.read_text()) if path.exists() else {"question": text(qid, n), "attempts": []}
    if len(entry["attempts"]) >= MAX_ATTEMPTS and entry.get("answer") is not None:
        print("Esta pregunta ya tiene respuesta: no se aceptan más intentos.")
        return
    if len(entry["attempts"]) >= MAX_ATTEMPTS:
        print(f"Ya hay {MAX_ATTEMPTS} intentos para esta pregunta: no se aceptan más.")
        return
    result = try_query(approach, sys.stdin.read().strip(), QUESTIONS[qid]["kind"], DOMAIN)
    entry["attempts"].append(result["attempt"])
    entry["answer"] = result["answer"]
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=1))
    if result["attempt"]["error"]:
        left = MAX_ATTEMPTS - len(entry["attempts"])
        print(f"ERROR (quedan {left} intentos). Mensaje para el LLM:\n" + retry_message(result["attempt"]["error"]))
    else:
        print(f"OK. Respuesta: {json.dumps(result['answer'], ensure_ascii=False)[:500]}")


def rerun():
    for path in sorted(ANSWERS.glob("*.json")):
        entry = json.loads(path.read_text())
        ok = [a for a in entry["attempts"] if a["error"] is None]
        if ok:
            qid, _, approach = path.stem.split("-")
            entry["answer"] = try_query(approach, ok[-1]["query"], QUESTIONS[qid]["kind"], DOMAIN)["answer"]
            path.write_text(json.dumps(entry, ensure_ascii=False, indent=1))
    print("Queries guardadas ejecutadas de nuevo.")


def normalize(values, items, conn):
    """Lleva una lista de nombres a un conjunto comparable: las empresas, por su nombre
    normalizado (la misma función que usa Rastro para enlazar)."""
    out = set()
    for v in values or []:
        if items == "empresas" and NORMALIZE:
            out.add(conn.execute(f"SELECT {NORMALIZE}(%s)", (v,)).fetchone()[0])
        else:
            out.add(" ".join(str(v).lower().split()))
    return out


def score(q, reference, answer, conn):
    if answer is None:
        return False
    if q["kind"] == "número":
        return answer == 0 if reference == 0 else abs(answer - reference) / abs(reference) <= TOLERANCE
    ref, got = normalize(reference, q["items"], conn), normalize(answer, q["items"], conn)
    hits = len(ref & got)
    if not hits:
        return not ref and not got
    precision, recall = hits / len(got), hits / len(ref)
    return 2 * precision * recall / (precision + recall) >= MIN_F1


def short(value):
    if value is None:
        return "sin respuesta"
    if isinstance(value, list):
        return ", ".join(value[:3]) + (f" y {len(value) - 3} más" if len(value) > 3 else "") or "ninguno"
    return f"{value:,.0f}".replace(",", ".")


def load(qid, n, k):
    path = ANSWERS / f"{qid}-{n}-{k}.json"
    return json.loads(path.read_text()) if path.exists() else None


def same(values):
    """¿Las respuestas son la misma? Los números, salvo redondeo (una parte en un millón)."""
    if all(isinstance(v, (int, float)) for v in values):
        return max(values) - min(values) <= 1e-6 * max(1, abs(max(values)))
    keys = {json.dumps(sorted(v), ensure_ascii=False) if isinstance(v, list) else json.dumps(v) for v in values}
    return len(keys) == 1


def score_all():
    names = {k: v for k, v in NAMES.items() if any(ANSWERS.glob(f"*-{k}.json"))}  # los que ya tienen respuestas
    results = {"date": date.today().isoformat(), "questions": {}, "totals": {}, "consistency": {}}
    with admin() as conn:
        for qid, q in QUESTIONS.items():
            reference = to_answer(run_sparql(SPEC["prefixes"] + q["reference"], DOMAIN), q["kind"])
            entry = {"question": q["question"], "kind": q["kind"], "reference": reference}
            for k in names:
                saved = load(qid, 0, k)
                if saved:
                    entry[k] = {**saved, "ok": score(q, reference, saved.get("answer"), conn)}
            results["questions"][qid] = entry
        for qid, others in PARAPHRASES.items():
            q, reference = QUESTIONS[qid], results["questions"][qid]["reference"]
            row = {"texts": [q["question"], *others]}
            for k in names:
                answers = [(load(qid, n, k) or {}).get("answer") for n in range(len(others) + 1)]
                row[k] = {"answers": answers, "ok": [score(q, reference, a, conn) for a in answers],
                          "same": same(answers)}
            results["consistency"][qid] = row
    for k in names:
        results["totals"][k] = {
            "correct": sum(e.get(k, {}).get("ok", False) for e in results["questions"].values()),
            "consistent": sum(r[k]["same"] for r in results["consistency"].values()),
            "consistent_correct": sum(sum(r[k]["ok"]) for r in results["consistency"].values()),
            "retries": sum(len(e.get(k, {}).get("attempts", [])) > 1 for e in results["questions"].values()),
        }
    (HERE / "resultados.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))

    n, m = len(QUESTIONS), len(PARAPHRASES)
    lines = [f"# Resultados: {TITLE}, sin Rastro y con Rastro", "",
             f"Fecha: {results['date']}. Respuestas escritas por subagentes de Claude Code (Claude Opus 5.5) "
             "que solo vieron el prompt. Las referencias las escribió un asistente de IA; falta que las "
             "confirme una persona.", "",
             "| | " + " | ".join(names.values()) + " |", "|---|" + "---|" * len(names),
             f"| Correctas (de {n}) | " + " | ".join(str(results["totals"][k]["correct"]) for k in names) + " |",
             f"| Misma respuesta en las 4 formas (de {m} preguntas) | "
             + " | ".join(str(results["totals"][k]["consistent"]) for k in names) + " |",
             f"| Correctas en la prueba de consistencia (de {4 * m}) | "
             + " | ".join(str(results["totals"][k]["consistent_correct"]) for k in names) + " |",
             "", "| # | Pregunta | Referencia | " + " | ".join(names.values()) + " |", "|---|---|---|" + "---|" * len(names)]
    for qid, e in results["questions"].items():
        cells = [("✅ " if e[k]["ok"] else "❌ ") + short(e[k].get("answer")) if k in e else "—" for k in names]
        lines.append(f"| {qid} | {e['question']} | {short(e['reference'])} | " + " | ".join(cells) + " |")
    lines += ["", "## Consistencia", "", "Respuestas por forma (la de la evaluación y sus 3 otras formas; "
              "en las listas, cantidad de nombres):", "", "| # | " + " | ".join(names.values()) + " |", "|---|" + "---|" * len(names)]
    for qid, r in results["consistency"].items():
        cells = [f"{'✅' if r[k]['same'] else '❌'} {sum(r[k]['ok'])}/4 correctas · "
                 + " / ".join(fmt(a) for a in r[k]["answers"]) for k in names]
        lines.append(f"| {qid} | " + " | ".join(cells) + " |")
    (HERE / "resultados.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def fmt(a):
    if a is None:
        return "—"
    if isinstance(a, list):
        return str(len(a))
    return f"{a:,.0f}".replace(",", ".")


if __name__ == "__main__":
    try:   # los cargadores recrean los esquemas: se vuelven a dar los permisos
        with admin() as c:
            c.execute((HERE / "reader.sql").read_text())
    except psycopg.Error:
        pass   # otro proceso los está dando al mismo tiempo ("tuple concurrently updated")
    command = sys.argv[2]
    if command == "prompt":
        prompt(sys.argv[3], int(sys.argv[4]), sys.argv[5])
    elif command == "try":
        attempt(sys.argv[3], int(sys.argv[4]), sys.argv[5])
    elif command == "rerun":
        rerun()
    elif command == "puntaje":
        score_all()
