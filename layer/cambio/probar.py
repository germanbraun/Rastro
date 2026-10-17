"""Demo de cambio: vuelve a ejecutar las 20 queries guardadas y dice cuáles siguen igual.

Compara cada respuesta con la guardada en layer/eval/results.json, para el SQL directo,
el SQL con las tablas de enlaces y Rastro. No escribe nada.

    docker compose run --rm layer-eval python /layer/cambio/probar.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from answer import run_sparql, try_query  # noqa: E402

SAVED = json.loads((Path(__file__).parent.parent / "eval" / "results.json").read_text())["questions"]

# Los estados que documenta la ontología (:status), tal como los publica ClinicalTrials.gov
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


def main():
    names = {"B": "SQL directo", "D": "SQL + enlaces", "C": "Rastro"}
    print(f"{'':5}" + "".join(f"{n:22}" for n in names.values()) + "Pregunta")
    totals = {k: {} for k in names}
    for qid, entry in SAVED.items():
        kind = "lista" if isinstance(entry["reference"], list) else "número"
        cells = {}
        for key in names:
            cells[key] = check(entry, key, kind) or "—"
            status = cells[key].split(" ")[0]
            totals[key][status] = totals[key].get(status, 0) + 1
        print(f"{qid:5}" + "".join(f"{cells[k]:22}" for k in names) + entry["question"][:50])

    print()
    for key, name in names.items():
        labels = {"✅": "igual", "🟡": "distinto, sin avisar", "❌": "con error", "—": "sin query"}
        print(f"{name:14} " + " · ".join(f"{v} {labels[k]}" for k, v in sorted(totals[key].items())))

    # Control del vocabulario: ¿hay estados que la ontología no documenta?
    try:
        values = run_sparql("PREFIX : <https://w3id.org/rastro/ontology#> "
                            "SELECT DISTINCT ?s WHERE { ?t :status ?s }")
    except Exception as e:  # noqa: BLE001 - Rastro caído también es un resultado de la demo
        print(f"\nControl de vocabulario: Rastro no responde ({str(e).splitlines()[0][:120]})")
        return
    unknown = sorted(set(values) - ESTADOS)
    if unknown:
        print(f"\n🟡 Control de vocabulario: {len(unknown)} estados que la ontología no documenta: "
              + ", ".join(unknown[:6]))
    else:
        print("\n✅ Control de vocabulario: todos los estados son los que documenta la ontología.")


if __name__ == "__main__":
    main()
