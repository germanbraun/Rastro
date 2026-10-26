"""Impact of a change in the source: Rastro says in advance which predictions depend on a source
record, and it is checked that they are exactly the ones that change when the source corrects it.

Run by impacto.sh (in this folder), which corrects the reported fracturing in the database, rebuilds Rastro, publishes a
run, compares and puts it back as it was.
    python3 layer/energia/cambio/impacto.py antes|despues|restaurado
Saves to impacto.json (in this folder), which the app shows.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lab" / "gas"))
import modelo  # noqa: E402

HERE = Path(__file__).parent
RESULT = HERE / "impacto.json"
REGISTRO = "4703"     # a reported fracturing of a 2025 well (166133)
CORRECCION = 12       # the source corrects the stages: from 18 to 30


def preguntar_a_rastro():
    """Question 14: which predictions of the current run used this record."""
    query = (ROOT / "ontology/energia/queries/cq14.rq").read_text().replace('"4703"', f'"{REGISTRO}"')
    return modelo.sparql_local(query).astype({"pozo": str})


def publicar():
    a, b = modelo.preparar(modelo.sql_local(modelo.SQL_GAS), modelo.sql_local(modelo.SQL_A), modelo.sparql_local(modelo.SPARQL_B))
    r = modelo.modelos(a, b)
    desde_hasta = modelo.rango(b, **modelo.VARIABLES["B"])
    return modelo.publicar(r, b, desde_hasta, modelo.dentro_del_rango(r["B"], b, desde_hasta))


def main(paso):
    guardado = json.loads(RESULT.read_text()) if RESULT.exists() else {}
    if paso == "antes":
        corrida = publicar()   # the baseline run, with the data as it is
        esperado = preguntar_a_rastro()
        guardado = {"registro": REGISTRO, "correccion": f"etapas +{CORRECCION}", "corrida_antes": corrida,
                    "esperado": esperado.to_dict("records")}
    elif paso == "despues":
        corrida = publicar()
        c = modelo.comparar(guardado["corrida_antes"], corrida)
        cambios = c["cambios"].astype({"idpozo": str})
        esperados = {e["pozo"] for e in guardado["esperado"]}
        guardado.update(corrida_despues=corrida, cambiaron=cambios.to_dict("records"),
                        coincide=set(cambios.idpozo) == esperados)
    elif paso == "restaurado":
        corrida = publicar()
        guardado.update(corrida_restaurada=corrida,
                        restaurado_igual=len(modelo.comparar(guardado["corrida_antes"], corrida)["cambios"]) == 0)
    RESULT.write_text(json.dumps(guardado, ensure_ascii=False, indent=1, default=str))
    print(paso, json.dumps({k: v for k, v in guardado.items() if k != "esperado"}, ensure_ascii=False, default=str)[:600])

    if paso == "despues" and not guardado["coincide"]:
        raise RuntimeError("Changed predictions differ from the announced impact")
    if paso == "restaurado" and not guardado["restaurado_igual"]:
        raise RuntimeError("Restored predictions differ from the baseline")


if __name__ == "__main__":
    main(sys.argv[1])
