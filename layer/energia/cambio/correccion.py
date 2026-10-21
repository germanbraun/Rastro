"""Una corrección, todos los resultados: mide qué cambia cuando se saca o se pone la participación corregida
de Aguada Pichana Este (linking/energia/participaciones-revisadas.csv), en Rastro Layer y en Rastro Lab.

Lo corre correccion.sh (en esta carpeta), que saca la corrección, rearma Rastro, mide y la vuelve a poner.
    python3 layer/energia/cambio/correccion.py <paso>     # paso: con | sin
Guarda en correccion.json (en esta carpeta), que muestra la app.
"""
import io
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lab" / "gas"))
import modelo  # noqa: E402

HERE = Path(__file__).parent
RESULT = HERE / "correccion.json"
ANSWERS = ROOT / "layer" / "energia" / "respuestas"


def compose(*args):
    return subprocess.run(["docker", "compose", "-f", str(ROOT / "infra" / "docker-compose.yml"), *args],
                          capture_output=True, text=True, check=True).stdout


def sql(query):
    return pd.read_csv(io.StringIO(compose("exec", "-T", "postgres", "psql", "-U", "rastro", "--csv", "-c", query)),
                       dtype={"idpozo": str})


def sparql(query):
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request("http://localhost:8082/sparql", data, {"Accept": "text/csv"})
    return pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=300).read().decode()))


def main(paso):
    # Rastro Layer: las respuestas guardadas de la pregunta de participación, ejecutadas de nuevo
    compose("run", "--rm", "-T", "layer-eval", "python", "/layer/evaluar.py", "energia", "rerun")
    layer = {k: json.loads((ANSWERS / f"e01-0-{k}.json").read_text())["answer"] for k in ("B", "D", "C")}
    total = sparql("""PREFIX energia: <https://w3id.org/rastro/energia#>
        SELECT ?pct WHERE { ?s a energia:Stake ; energia:inConcession/energia:concessionId "APE" ;
                                energia:partner/energia:name "TOTAL AUSTRAL S.A." ; energia:percent ?pct }""").pct.iloc[0]
    # Rastro Lab: la entrada y la predicción de los pozos de Aguada Pichana Este de 2025
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
    # Sin Rastro, el mismo dato se lee del texto del mapa en cada consulta y en el código del modelo
    saved["lugares_sin_rastro"] = sum("participacion" in p.read_text() for p in ANSWERS.glob("*-B.json")) + 1
    RESULT.write_text(json.dumps(saved, ensure_ascii=False, indent=1))
    print(paso, json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
