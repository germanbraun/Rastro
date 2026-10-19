"""Demo de cambio: vuelve a ejecutar las 20 queries guardadas y dice cuáles siguen igual.

Compara cada respuesta con la guardada en layer/eval/results.json, para el SQL directo,
el SQL con las tablas de enlaces y Rastro. Con --guardar <paso>, además guarda el resultado
en layer/cambio/resultado.json, que muestra la app.

    docker compose run --rm layer-eval python /layer/cambio/probar.py [--guardar <paso>]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from answer import run_sparql, try_query  # noqa: E402

SAVED = json.loads((Path(__file__).parent.parent / "eval" / "results.json").read_text())["questions"]
RESULT = Path(__file__).parent / "resultado.json"
NAMES = {"B": "SQL directo", "D": "SQL + enlaces", "C": "Rastro"}
LABELS = {"✅": "igual", "🟡": "distinto, sin avisar", "❌": "con error", "—": "sin query"}

# Los estados que documenta la ontología (oncologia:status), tal como los publica ClinicalTrials.gov
ESTADOS = {"COMPLETED", "UNKNOWN", "RECRUITING", "TERMINATED", "ACTIVE_NOT_RECRUITING",
           "NOT_YET_RECRUITING", "WITHDRAWN", "ENROLLING_BY_INVITATION", "SUSPENDED",
           "NO_LONGER_AVAILABLE", "AVAILABLE", "APPROVED_FOR_MARKETING", "TEMPORARILY_NOT_AVAILABLE"}


def same(a, b):
    if isinstance(a, list) or isinstance(b, list):
        return set(a or []) == set(b or [])
    return a is not None and b is not None and abs(a - b) <= 1e-6 * max(1, abs(b))


def check(entry, key, kind):
    ok = [a for a in entry[key]["attempts"] if a["error"] is None]
    if not ok:
        return None
    result = try_query(key, ok[-1]["query"], kind)
    if result["answer"] is None and result["attempt"]["error"]:
        return "❌ error"
    if same(result["answer"], entry[key]["answer"]):
        return "✅ igual"
    return f"🟡 {short(result['answer'])}, era {short(entry[key]['answer'])}"


def short(value):
    if isinstance(value, list):
        return f"{len(value)} nombres" if value else "ninguno"
    if value is None:
        return "nada"
    if value == int(value):
        return f"{value:,.0f}".replace(",", ".")
    return f"{value:.1f}"


def vocabulary():
    """Control del vocabulario: ¿hay estados que la ontología no documenta?"""
    try:
        values = run_sparql("PREFIX oncologia: <https://w3id.org/rastro/oncologia#> "
                            "SELECT DISTINCT ?s WHERE { ?t oncologia:status ?s }")
    except Exception as e:  # noqa: BLE001 - Rastro caído también es un resultado de la demo
        return f"Control de vocabulario: Rastro no responde ({str(e).splitlines()[0][:120]})"
    unknown = sorted(set(values) - ESTADOS)
    if unknown:
        return (f"🟡 Control de vocabulario: {len(unknown)} estados que la ontología no documenta: "
                + ", ".join(unknown[:6]))
    return "✅ Control de vocabulario: todos los estados son los que documenta la ontología."


def main():
    cells, totals = {}, {k: {} for k in NAMES}
    print(f"{'':5}" + "".join(f"{n:22}" for n in NAMES.values()) + "Pregunta")
    for qid, entry in SAVED.items():
        kind = "lista" if isinstance(entry["reference"], list) else "número"
        cells[qid] = {k: check(entry, k, kind) or "—" for k in NAMES}
        for k, cell in cells[qid].items():
            status = cell.split(" ")[0]
            totals[k][status] = totals[k].get(status, 0) + 1
        print(f"{qid:5}" + "".join(f"{cells[qid][k]:22}" for k in NAMES) + entry["question"][:50])

    print()
    for k, name in NAMES.items():
        print(f"{name:14} " + " · ".join(f"{v} {LABELS[s]}" for s, v in sorted(totals[k].items())))
    vocab = vocabulary()
    print("\n" + vocab)

    if "--guardar" in sys.argv:
        step = sys.argv[sys.argv.index("--guardar") + 1]
        saved = json.loads(RESULT.read_text()) if RESULT.exists() else {}
        saved[step] = {"cells": cells, "totals": totals, "vocabulary": vocab}
        RESULT.write_text(json.dumps(saved, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
