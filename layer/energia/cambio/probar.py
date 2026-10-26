"""Change demo for the oil and gas domain: runs the saved evaluation queries again
and says which ones still give the same result, without Rastro (SQL) and with Rastro.

With --guardar <paso>, saves the result to resultado.json (in this folder), which the app shows.
It also checks that 2025 oil is still around 46.6 million m³ (if the
unit changes, Rastro warns).

    docker compose run --rm layer-eval python /layer/energia/cambio/probar.py [--guardar <paso>]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from answer import run_sparql, try_query  # noqa: E402

HERE = Path(__file__).parent
ANSWERS = HERE.parent / "respuestas"
RESULT = HERE / "resultado.json"
NAMES = {"B": "Sin Rastro (SQL)", "C": "Con Rastro"}
LABELS = {"✅": "igual", "🟡": "distinto, sin avisar", "❌": "con error", "—": "sin query"}
NATIONAL_OIL = 46.6e6  # 2025 oil production is around 46.6 million m³ (about 800,000 barrels per day)


def same(a, b):
    if isinstance(a, list) or isinstance(b, list):
        return set(a or []) == set(b or [])
    return a is not None and b is not None and abs(a - b) <= 1e-6 * max(1, abs(b))


def short(value):
    if isinstance(value, list):
        return f"{len(value)} nombres" if value else "ninguno"
    if value is None:
        return "nada"
    return f"{value:,.0f}".replace(",", ".")


def check(entry, key, kind):
    ok = [a for a in entry["attempts"] if a["error"] is None]
    if not ok:
        return None
    result = try_query(key, ok[-1]["query"], kind, "energia")
    if result["answer"] is None and result["attempt"]["error"]:
        return "❌ error"
    if same(result["answer"], entry["answer"]):
        return "✅ igual"
    return f"🟡 {short(result['answer'])}, era {short(entry['answer'])}"


def control():
    """Unit check: is 2025 oil production still around 46.6 million m³?"""
    try:
        values = run_sparql("PREFIX energia: <https://w3id.org/rastro/energia#> "
                            "SELECT (SUM(?o) AS ?t) WHERE { ?p energia:oil ?o }", "energia")
    except Exception as e:  # noqa: BLE001 - Rastro being down is also a demo result
        return f"Control de unidades: Rastro no responde ({str(e).splitlines()[0][:120]})"
    total = float(values[0]) if values and values[0] is not None else 0
    shown = f"{total / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(total - NATIONAL_OIL) / NATIONAL_OIL > 0.2:
        return (f"🟡 Control de unidades: el petróleo de 2025 suma {shown} millones de m³, y la "
                "producción nacional ronda los 46,6: ¿cambió la unidad?")
    return f"✅ Control de unidades: el petróleo de 2025 suma {shown} millones de m³, como la producción nacional."


def validate_step(step, cells, control_text):
    """Broken stages are expected; baseline and repaired stages must actually pass."""
    if not cells:
        raise RuntimeError("No saved queries executed")
    paths = ("B", "C") if step in {"antes", "despues"} else ("C",)
    if step in {"antes", "despues", "renombrar-arreglado", "valores-arreglado"}:
        if any(not row.get(path, "").startswith("✅") for row in cells.values() for path in paths):
            raise RuntimeError(f"{step}: saved answers were not preserved")
        if not control_text.startswith("✅"):
            raise RuntimeError(f"{step}: unit control failed")


def main():
    cells, totals = {}, {k: {} for k in NAMES}
    for path in sorted(ANSWERS.glob("e*-0-B.json")):
        qid = path.name.split("-")[0]
        cells[qid] = {}
        for k in NAMES:
            entry = json.loads((ANSWERS / f"{qid}-0-{k}.json").read_text())
            kind = "lista" if isinstance(entry["answer"], list) else "número"
            cells[qid][k] = check(entry, k, kind) or "—"
            status = cells[qid][k].split(" ")[0]
            totals[k][status] = totals[k].get(status, 0) + 1
        print(f"{qid:5}" + "".join(f"{cells[qid][k]:40}" for k in NAMES))
    print()
    for k, name in NAMES.items():
        print(f"{name:18} " + " · ".join(f"{v} {LABELS[s]}" for s, v in sorted(totals[k].items())))
    check_text = control()
    print("\n" + check_text)
    if "--guardar" in sys.argv:
        step = sys.argv[sys.argv.index("--guardar") + 1]
        saved = json.loads(RESULT.read_text()) if RESULT.exists() else {}
        saved[step] = {"cells": cells, "totals": totals, "vocabulary": check_text}
        RESULT.write_text(json.dumps(saved, ensure_ascii=False, indent=1))
        validate_step(step, cells, check_text)


if __name__ == "__main__":
    main()
