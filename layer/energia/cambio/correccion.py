"""One correction, every result: measures what changes when the corrected stake of Aguada Pichana Este
(linking/energia/participaciones-revisadas.csv) is removed or put back, in Rastro Layer and in Rastro Lab.

Run by correccion.sh (in this folder), which removes the correction, rebuilds Rastro, measures and puts it back.
    python3 layer/energia/cambio/correccion.py <paso>     # paso: con | sin
    python3 layer/energia/cambio/correccion.py verificar  # exact expectations; fails on any miss or error
Saves to correccion.json (in this folder), which the app shows.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lab" / "gas"))
import modelo  # noqa: E402
from modelo import sparql_local as sparql, sql_local as sql  # noqa: E402

HERE = Path(__file__).parent
RESULT = HERE / "correccion.json"
ANSWERS = ROOT / "layer" / "energia" / "respuestas"


def compose(*args):
    return subprocess.run(["docker", "compose", "-f", str(ROOT / "infra" / "docker-compose.yml"), *args],
                          capture_output=True, text=True, check=True).stdout


def main(paso):
    # Rastro Layer: the saved answers of the stake question, run again
    compose("run", "--rm", "-T", "layer-eval", "python", "/layer/evaluar.py", "energia", "rerun")
    layer = {k: json.loads((ANSWERS / f"e01-0-{k}.json").read_text())["answer"] for k in ("B", "D", "C")}
    total = sparql("""PREFIX energia: <https://w3id.org/rastro/energia#>
        SELECT ?pct WHERE { ?s a energia:Stake ; energia:inConcession/energia:concessionId "APE" ;
                                energia:partner/energia:name "TOTAL AUSTRAL S.A." ; energia:percent ?pct }""").pct.iloc[0]
    # The business answer the correction moves most: Total's gas in Aguada Pichana Este, by its share (as cq1 computes it)
    total_gas = sparql("""PREFIX energia: <https://w3id.org/rastro/energia#>
        SELECT (SUM(?gas * ?pct / 100) AS ?share) WHERE {
          ?c energia:concessionId "APE" .
          ?p a energia:WellProduction ; energia:inConcession ?c ; energia:gas ?gas .
          ?s a energia:Stake ; energia:inConcession ?c ; energia:partner/energia:name "TOTAL AUSTRAL S.A." ;
             energia:percent ?pct }""").share.iloc[0]
    # Rastro Lab: the input and the prediction of the 2025 Aguada Pichana Este wells
    a, b = modelo.preparar(sql(modelo.SQL_GAS), sql(modelo.SQL_A), sparql(modelo.SPARQL_B))
    r = modelo.modelos(a, b)
    ape = b[(b.area == "APE") & (b.inicio >= modelo.PRUEBA)]
    pozo = ape.idpozo.iloc[0]
    ia, ib = a.index[a.idpozo == pozo][0], b.index[b.idpozo == pozo][0]
    resultado = {
        "layer_C": layer["C"], "layer_D": layer["D"], "layer_B": layer["B"], "rastro_total": float(total),
        "total_ape_gas": float(total_gas),
        "lab_pozo": pozo, "lab_B_pct": float(b.loc[ib, "pct"]), "lab_A_pct": float(a.loc[ia, "porcentaje"]),
        "lab_B_pred": float(r["B"]["pred"][ib]), "lab_A_pred": float(r["A"]["pred"][ia]),
        "lab_B_marca": modelo.marca(b.loc[ib, "reglaSocio"]), "lab_pozos_ape": len(ape),
    }
    saved = json.loads(RESULT.read_text()) if RESULT.exists() else {}
    saved[paso] = resultado
    if paso == "con":   # the document's value, read while the reviewed CSV still has it (verificar runs without it)
        saved["documento"] = documented_percent()
    # Without Rastro, the same value is read from the map text in every query and in the model code
    saved["lugares_sin_rastro"] = sum("participacion" in p.read_text() for p in ANSWERS.glob("*-B.json")) + 1
    RESULT.write_text(json.dumps(saved, ensure_ascii=False, indent=1))
    print(paso, json.dumps(resultado, ensure_ascii=False))


def documented_percent():
    """The corrected stake as the reviewed CSV declares it (the document's value, not Rastro's)."""
    import csv
    with (ROOT / "linking/energia/participaciones-revisadas.csv").open(encoding="utf-8") as source:
        return next(float(r["porcentaje"]) for r in csv.DictReader(source)
                    if r["concesion"] == "AGUADA PICHANA ESTE" and r["empresa"] == "TOTAL AUSTRAL S.A.")


def check(saved, documented):
    """Exact expectations of the correction, declared before measuring: it reaches Rastro (C), the links (D) and
    Rastro Lab's input and prediction; it does not reach SQL over the sources (B) or the model on raw tables (A).
    Returns the failures; a missing or non-numeric measurement is a failure, never a pass."""
    failures = []
    numbers = ("layer_C", "layer_D", "layer_B", "rastro_total", "total_ape_gas", "lab_B_pct", "lab_A_pct", "lab_B_pred", "lab_A_pred")
    for paso in ("con", "sin"):
        run = saved.get(paso) or {}
        failures += [f"{paso}.{k}: missing or not a number" for k in numbers
                     if not isinstance(run.get(k), (int, float)) or run[k] != run[k]]
    if failures:
        return failures
    con, sin = saved["con"], saved["sin"]
    expect = [
        (con["rastro_total"] == documented, "with the correction, Rastro's stake is the document's"),
        (sin["rastro_total"] == sin["lab_A_pct"] != documented, "without it, Rastro's stake is the map's"),
        (con["layer_C"] != sin["layer_C"] and con["layer_D"] != sin["layer_D"], "the answer changes with and via links"),
        (con["layer_B"] == sin["layer_B"], "SQL over the sources as they come does not change"),
        (abs(con["total_ape_gas"] / sin["total_ape_gas"] - documented / sin["rastro_total"]) < 1e-6,
         "Total's gas in the concession follows its share"),
        (con["lab_B_pct"] == documented and sin["lab_B_pct"] == sin["lab_A_pct"], "Lab's input follows Rastro"),
        (con["lab_A_pct"] == sin["lab_A_pct"] and con["lab_A_pred"] == sin["lab_A_pred"], "the raw-table model does not"),
        (con["lab_B_pred"] != sin["lab_B_pred"], "Lab's prediction changes"),
        (con["lab_B_marca"] == "dato corregido con documento" and sin["lab_B_marca"] == "", "the correction is marked"),
        (con["lab_pozo"] == sin["lab_pozo"] and con["lab_pozos_ape"] == sin["lab_pozos_ape"], "the same well is compared"),
    ]
    return [f"expected: {what}" for ok, what in expect if not ok]


if __name__ == "__main__":
    if sys.argv[1] == "verificar":
        saved = json.loads(RESULT.read_text())
        problems = check(saved, saved.get("documento") or documented_percent())
        print("\n".join(problems) or "correction behaved as expected")
        sys.exit(1 if problems else 0)
    main(sys.argv[1])
