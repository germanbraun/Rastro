"""Demo de cambio del dominio de petróleo y gas: vuelve a ejecutar las queries guardadas de
la evaluación y dice cuáles siguen dando lo mismo, sin Rastro (SQL) y con Rastro.

Con --guardar <paso>, guarda el resultado en resultado.json (en esta carpeta), que muestra la app.
Además controla que el petróleo de 2025 siga rondando los 46,6 millones de m³ (si cambia la
unidad, Rastro avisa).

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
NATIONAL_OIL = 46.6e6  # la producción de petróleo de 2025 ronda 46,6 millones de m³ (unos 800.000 barriles por día)


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
    """Control de unidades: ¿la producción de petróleo de 2025 sigue rondando los 46,6 millones de m³?"""
    try:
        values = run_sparql("PREFIX energia: <https://w3id.org/rastro/energia#> "
                            "SELECT (SUM(?o) AS ?t) WHERE { ?p energia:oil ?o }", "energia")
    except Exception as e:  # noqa: BLE001 - Rastro caído también es un resultado de la demo
        return f"Control de unidades: Rastro no responde ({str(e).splitlines()[0][:120]})"
    total = float(values[0]) if values and values[0] is not None else 0
    shown = f"{total / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(total - NATIONAL_OIL) / NATIONAL_OIL > 0.2:
        return (f"🟡 Control de unidades: el petróleo de 2025 suma {shown} millones de m³, y la "
                "producción nacional ronda los 46,6: ¿cambió la unidad?")
    return f"✅ Control de unidades: el petróleo de 2025 suma {shown} millones de m³, como la producción nacional."


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


if __name__ == "__main__":
    main()
