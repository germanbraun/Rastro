"""Evalúa las tres formas de responder (A: LLM solo, B: LLM + SQL, C: LLM + Rastro).

1. Calcula la respuesta correcta de cada pregunta con su SPARQL de referencia.
2. Genera las respuestas que falten en results.json, con la Claude API
   (ANTHROPIC_API_KEY) o con Ollama (RASTRO_PROVIDER=ollama). Sin ninguno, se pueden
   generar a mano o con otro asistente usando manual.py.
3. Puntúa todo y escribe results.md.

Las respuestas quedan guardadas en results.json, que se versiona: en otra máquina,
sin API key, el script solo puntúa lo guardado. Para regenerar un enfoque:
    docker compose run --rm layer-eval python /layer/eval/run.py --fresh B
Si cambiaron los datos (nuevos enlaces o una carga nueva), --rerun vuelve a ejecutar
las queries que ya escribió el LLM, sin pedirle nada nuevo.

Se corre con: docker compose run --rm layer-eval
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import psycopg
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HERE = Path(__file__).parent
RESULTS = HERE / "results.json"
TOLERANCE = 0.05    # números: correcto si está a menos del 5 % de la referencia
MIN_F1 = 0.8        # listas: correcto si coincide en al menos un 80 % (F1)
NAMES = {"A": "LLM solo", "B": "LLM + SQL crudo", "C": "LLM + Rastro"}


def admin():
    return psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                           f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")


def normalize(values, items, conn):
    """Lleva una lista de nombres a un conjunto comparable.

    Los fármacos se comparan por familia de ChEMBL, usando sus sinónimos: así
    "T-DM1", "ado-trastuzumab emtansine" y "TRASTUZUMAB EMTANSINE" son lo mismo.
    """
    out = set()
    for v in values or []:
        key = " ".join(str(v).lower().split())
        if items == "fármacos":
            row = conn.execute("SELECT family FROM linking.drug_name WHERE name = linking.norm_aact(%s)",
                               (v,)).fetchone()
            key = row[0] if row else key
        out.add(key)
    return out


def score(question, reference, answer, conn):
    if answer is None:
        return False
    if question["kind"] == "número":
        if reference == 0:
            return answer == 0
        return abs(answer - reference) / abs(reference) <= TOLERANCE
    ref = normalize(reference, question["items"], conn)
    got = normalize(answer, question["items"], conn)
    hits = len(ref & got)
    if not ref or not got or not hits:
        return not ref and not got
    precision, recall = hits / len(got), hits / len(ref)
    return 2 * precision * recall / (precision + recall) >= MIN_F1


def short(value):
    if value is None:
        return "sin respuesta"
    if isinstance(value, list):
        text = ", ".join(value[:4]) + (f" y {len(value) - 4} más" if len(value) > 4 else "")
        return text or "lista vacía"
    return f"{value:,.0f}" if value >= 10 else f"{value:.1f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", nargs="*", default=[], help="enfoques a regenerar: A, B, C")
    parser.add_argument("--rerun", action="store_true", help="re-ejecutar las queries guardadas de B y C")
    args = parser.parse_args()

    spec = yaml.safe_load((HERE / "questions.yaml").read_text())
    saved = json.loads(RESULTS.read_text()) if RESULTS.exists() else {"questions": {}}

    with admin() as conn:
        conn.execute((HERE.parent / "reader.sql").read_text())

    from answer import APPROACHES, MODEL, PROVIDER, run_sparql, to_answer, try_query  # noqa: E402

    can_generate = PROVIDER == "ollama" or bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not can_generate:
        print("Sin ANTHROPIC_API_KEY ni Ollama: solo se puntúan las respuestas guardadas.\n")

    for q in spec["questions"]:
        entry = saved["questions"].setdefault(q["id"], {})
        entry["question"] = q["question"]
        entry["reference"] = to_answer(run_sparql(spec["prefixes"] + q["reference"]), q["kind"])
        if args.rerun:
            for key in ("B", "C"):
                ok = [a for a in entry.get(key, {}).get("attempts", []) if a["error"] is None]
                if ok:
                    start = time.time()
                    entry[key]["answer"] = try_query(key, ok[-1]["query"], q["kind"])["answer"]
                    entry[key]["seconds"] = round(time.time() - start, 2)
        for key, approach in APPROACHES.items():
            if key in entry and key not in args.fresh:
                continue
            if not can_generate:
                continue
            print(f"{q['id']} {NAMES[key]}...", flush=True)
            try:
                entry[key] = approach(q["question"], q["kind"])
            except Exception as e:  # noqa: BLE001 - se registra y se sigue con la próxima
                entry[key] = {"answer": None, "attempts": [], "error": str(e)[:500]}
            saved["model"], saved["date"] = f"{MODEL} ({PROVIDER})", date.today().isoformat()
            RESULTS.write_text(json.dumps(saved, ensure_ascii=False, indent=1))
    RESULTS.write_text(json.dumps(saved, ensure_ascii=False, indent=1))

    # Puntaje
    totals = {k: 0 for k in NAMES}
    lines = []
    with admin() as conn:
        for q in spec["questions"]:
            entry = saved["questions"][q["id"]]
            cells = []
            for key in NAMES:
                if key not in entry:
                    cells.append("—")
                    continue
                ok = score(q, entry["reference"], entry[key]["answer"], conn)
                totals[key] += ok
                cells.append(("✅ " if ok else "❌ ") + short(entry[key]["answer"]))
            lines.append(f"| {q['id']} | {q['question']} | {short(entry['reference'])} | " + " | ".join(cells) + " |")

    n = len(spec["questions"])
    summary = " · ".join(f"{NAMES[k]}: **{totals[k]} de {n}**" for k in NAMES)
    report = [
        "# Resultados: ¿cuántas preguntas responde bien un LLM?", "",
        f"Modelo: `{saved.get('model', '—')}` · Fecha: {saved.get('date', '—')}", "",
        summary, "",
        "- **LLM solo:** responde con lo que sabe, sin acceso a datos.",
        "- **LLM + SQL crudo:** escribe SQL sobre las tablas de las fuentes tal como se cargaron.",
        "- **LLM + Rastro:** escribe SPARQL sobre la ontología de Rastro.", "",
        f"Correcto: números a menos del {TOLERANCE:.0%} de la referencia; listas con al menos "
        f"{MIN_F1:.0%} de coincidencia (F1). Las queries generadas están en `results.json`.", "",
        "| # | Pregunta | Referencia | " + " | ".join(NAMES.values()) + " |",
        "|---|---|---|---|---|---|",
        *lines,
    ]
    (HERE / "results.md").write_text("\n".join(report) + "\n")
    print(summary.replace("**", ""))


if __name__ == "__main__":
    main()
