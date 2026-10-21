"""Arma la prueba a ciegas de las explicaciones de Rastro Lab: 10 pozos de 2025, cada uno con su explicación
sin Rastro y con Rastro, mezcladas y sin decir cuál es cuál. Una persona del sector que no armó Rastro responde
tres preguntas por explicación. La clave (qué explicación es de qué modelo) queda en un archivo aparte.

    python3 lab/gas/a_ciegas.py   # escribe docs/lab-explicaciones-a-ciegas.md y lab/gas/a-ciegas-clave.json
"""
import json
import random
from pathlib import Path

import modelo
from modelo import signo, sparql_local as sparql, sql_local as sql

ROOT = Path(__file__).resolve().parents[2]

N = 10


def texto_a(ea, r):
    filas = "\n".join(f"- `{f['columna']} = {f['valor']}`: {signo(f['aporte'])}" for f in ea["filas"])
    return (f"Predicción: **{modelo.num(ea['pred'])} millones de m³**. Un pozo promedio da {modelo.num(r['A']['base'])}; "
            f"cada columna suma o resta (en millones de m³):\n\n{filas}")


def texto_b(eb):
    factores = "\n".join(f"- **{x['factor']}: {signo(x['aporte'])}.** {x['por_que']}" for x in eb["factores"])
    hechos = "\n".join(f"- **{h['hecho']}:** {h['valor']}" + (f" ({h['marca']})" if h["marca"] else "")
                       + f". Regla: {h['regla']}. Evidencia: {str(h['evidencia']).rstrip('.')}. Fuente: {h['fuentes']}."
                       for h in eb["hechos"])
    return f"{eb['resumen']}\n\n{factores}\n\nLo que respalda la predicción:\n\n{hechos}"


def main():
    a, b = modelo.preparar(sql(modelo.SQL_GAS), sql(modelo.SQL_A), sparql(modelo.SPARQL_B))
    ctx = modelo.contexto(sparql(modelo.SPARQL_SOCIOS), sparql(modelo.SPARQL_CAMBIOS))
    r = modelo.modelos(a, b)
    azar = random.Random(42)
    pozos = azar.sample(sorted(b[(b.inicio >= modelo.PRUEBA) & b.rama.notna()].idpozo), N)
    items = []
    for p in pozos:
        items.append({"pozo": p, "modelo": "sin Rastro", "texto": texto_a(modelo.explicacion_a(r, a, p), r)})
        items.append({"pozo": p, "modelo": "con Rastro", "texto": texto_b(modelo.explicacion_b(r, b, ctx, p))})
    azar.shuffle(items)
    partes = ["""# Prueba a ciegas: ¿se entienden estas explicaciones?

Un modelo predice cuánto gas va a dar un pozo nuevo de shale gas de Vaca Muerta en sus meses 2 a 7 (en millones de
m³). Abajo hay 20 explicaciones de predicciones, de 10 pozos de 2025. Para cada una, responda las tres preguntas
del 1 (nada) al 5 (totalmente). No hace falta saber cómo funciona el modelo.

1. **¿La entiende?** ¿Sabe por qué el modelo predice ese número?
2. **¿Puede comprobar los datos?** ¿Sabe de dónde sale cada dato y podría verificarlo?
3. **¿La defendería ante un cliente?**

Responda sin consultar a quien armó la prueba. Tiempo estimado: 30 minutos.
"""]
    for n, it in enumerate(items, 1):
        partes.append(f"\n## Explicación {n}\n\n{it['texto']}\n\n"
                      "| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |\n|---|---|---|\n|  |  |  |\n")
    (ROOT / "docs" / "lab-explicaciones-a-ciegas.md").write_text("".join(partes))
    clave = [{"explicacion": n, "pozo": it["pozo"], "modelo": it["modelo"]} for n, it in enumerate(items, 1)]
    (ROOT / "lab" / "gas" / "a-ciegas-clave.json").write_text(json.dumps(clave, ensure_ascii=False, indent=1))
    print(f"{len(items)} explicaciones de {N} pozos: docs/lab-explicaciones-a-ciegas.md (clave en lab/gas/a-ciegas-clave.json)")


if __name__ == "__main__":
    main()
