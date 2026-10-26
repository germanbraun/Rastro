"""One correction, every result: measures what changes when the corrected stake of Aguada Pichana Este
(linking/energia/participaciones-revisadas.csv) is removed or put back, in Rastro Layer and in Rastro Lab.

Run by correccion.sh (in this folder), which removes the correction, rebuilds Rastro, measures and puts it back.
    python3 layer/energia/cambio/correccion.py <paso>     # paso: con | sin
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
    # Rastro Lab: the input and the prediction of the 2025 Aguada Pichana Este wells
    a, b = modelo.preparar(sql(modelo.SQL_GAS), sql(modelo.SQL_A), sparql(modelo.SPARQL_B))
    r = modelo.modelos(a, b)
    ape = b[(b.area == "APE") & (b.inicio >= modelo.PRUEBA)]
    pozo = ape.idpozo.iloc[0]
    ia, ib = a.index[a.idpozo == pozo][0], b.index[b.idpozo == pozo][0]
    resultado = {
        "layer_C": layer["C"], "layer_D": layer["D"], "layer_B": layer["B"], "rastro_total": float(total),
        "lab_pozo": pozo, "lab_B_pct": float(b.loc[ib, "pct"]), "lab_A_pct": float(a.loc[ia, "porcentaje"]),
        "lab_B_pred": float(r["B"]["pred"][ib]), "lab_A_pred": float(r["A"]["pred"][ia]),
        "lab_B_marca": modelo.marca(b.loc[ib, "reglaSocio"]), "lab_pozos_ape": len(ape),
    }
    saved = json.loads(RESULT.read_text()) if RESULT.exists() else {}
    saved[paso] = resultado
    # Without Rastro, the same value is read from the map text in every query and in the model code
    saved["lugares_sin_rastro"] = sum("participacion" in p.read_text() for p in ANSWERS.glob("*-B.json")) + 1
    RESULT.write_text(json.dumps(saved, ensure_ascii=False, indent=1))
    print(paso, json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
