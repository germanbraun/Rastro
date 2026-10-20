"""Rastro Lab, paso 1: el mismo modelo de gas con variables de las tablas crudas (A) y de Rastro (B).

Predice el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta y explica cada predicción.
El modelo es una regresión lineal: la predicción es el gas de un pozo promedio más el aporte de cada
variable, en millones de m³, exacto y sin técnicas aparte. La operadora y la concesión entran como
categorías (un coeficiente por empresa y por concesión, aprendido con los pozos de entrenamiento).
Lo que cambia entre A y B es de dónde salen las variables y qué dicen: columnas en A, conceptos con
fuente, regla y evidencia en B.

La app lo usa desde la pestaña «Rastro Lab» de petróleo y gas (app/lab.py). Desde la raíz del repo,
con Postgres y Ontop de energía arriba:
    python3 lab/gas/modelo.py            # números y la explicación de un pozo
    python3 lab/gas/modelo.py <idpozo>   # la explicación de otro pozo
"""
import numpy as np
import pandas as pd

PRUEBA = pd.Timestamp("2025-01-01")   # entrena con pozos de 2023 y 2024, prueba con los de 2025

# Lo que se predice (igual para A y B): el gas de los meses 2 a 7, en millones de m³
SQL_GAS = """
WITH m AS (
  SELECT idpozo, make_date(anio, mes, 1) AS f, sum(prod_gas) AS gas
  FROM (SELECT * FROM capitulo4.produccion UNION ALL SELECT * FROM capitulo4.produccion_historica) t
  WHERE formacion = 'vaca muerta' GROUP BY 1, 2
), i AS (SELECT idpozo, min(f) FILTER (WHERE gas > 0) AS inicio FROM m GROUP BY 1)
SELECT i.idpozo, sum(m.gas) / 1000.0 AS gas_2_7
FROM i JOIN m ON m.idpozo = i.idpozo AND m.f >= i.inicio + interval '1 month' AND m.f < i.inicio + interval '7 months'
WHERE i.inicio + interval '6 months' <= date '2025-12-01'
GROUP BY 1 HAVING count(*) = 6"""

# A: lo que armaría un analista con SQL sobre las tablas tal como vienen
SQL_A = """
WITH todo AS (SELECT * FROM capitulo4.produccion UNION ALL SELECT * FROM capitulo4.produccion_historica),
p AS (SELECT idpozo, min(make_date(anio, mes, 1)) AS primera,
             min(make_date(anio, mes, 1)) FILTER (WHERE prod_gas > 0 OR prod_pet > 0) AS inicio FROM todo GROUP BY 1)
SELECT DISTINCT ON (t.idpozo) t.idpozo, p.inicio, trim(t.empresa) AS empresa, t.idareapermisoconcesion AS area,
       c.participacion
FROM todo t JOIN p ON p.idpozo = t.idpozo AND make_date(t.anio, t.mes, 1) = p.inicio
LEFT JOIN sig_energia.concesion c ON c.id_concesion = t.idareapermisoconcesion
WHERE p.inicio > date '2023-01-01' AND p.primera > date '2023-01-01'
  AND t.formacion = 'vaca muerta' AND t.sub_tipo_recurso = 'SHALE' AND t.tipopozo = 'Gasífero'
ORDER BY t.idpozo, t.prod_gas DESC NULLS LAST"""

# B: lo mismo, leído de Rastro, con la regla y la evidencia de cada dato
SPARQL_B = """PREFIX energia: <https://w3id.org/rastro/energia#>
SELECT ?well ?inicio ?grupo ?nombre ?reglaNombre ?evidencia ?area ?areaNombre ?pct ?reglaSocio ?textoSocio
WHERE {
  ?s a energia:WellStart ; energia:aboutWell ?well ; energia:startMonth ?inicio ; energia:company ?c ;
     energia:declaredName ?nombre ; energia:sourceText ?evidencia ; energia:inConcession ?conc ;
     energia:startFormation "vaca muerta" ; energia:startResource "SHALE" ; energia:startWellType "Gasífero" .
  ?c energia:name ?grupo .
  ?conc energia:concessionId ?area .
  OPTIONAL { ?conc energia:name ?areaNombre }
  OPTIONAL { ?cn a energia:CompanyName ; energia:nameInSource ?nombre ; energia:rule ?reglaNombre }
  OPTIONAL { ?st a energia:Stake ; energia:inConcession ?conc ; energia:partner ?c ; energia:percent ?pct ;
                 energia:rule ?reglaSocio ; energia:sourceText ?textoSocio }
}"""

# Las mismas ideas de variables en A y B; cambia de dónde salen.
# La distancia al gasoducto no entra: es una por concesión y, con la concesión en el modelo, solo la repite
# (salía al revés: estar a 0,3 km restaba gas). Vuelve en la prueba de áreas nuevas, donde sí agrega.
VARIABLES = {
    "A": {"categorias": ["empresa", "area"], "numeros": ["porcentaje"]},
    "B": {"categorias": ["grupo", "area"], "numeros": ["pct"]},
}


def porcentaje_del_mapa(texto, empresa):
    """El porcentaje de la empresa en el texto de socios del mapa, buscando su nombre tal cual."""
    for parte in str(texto).split("<br>"):
        if ":" in parte and parte.split(":")[0].strip().rstrip(".").upper() == empresa.rstrip(".").upper():
            return float(parte.split(":")[1].replace("%", "").strip())
    return np.nan


def preparar(gas, a, b):
    """Los mismos pozos en A y B, con su gas medido, ordenados por fecha de inicio."""
    a = a.copy()
    a["porcentaje"] = [porcentaje_del_mapa(t, e) for t, e in zip(a.participacion, a.empresa)]
    b = b.copy()
    b["idpozo"] = b.well.str.rsplit("/", n=1).str[-1]
    b = b.drop_duplicates("idpozo")
    b["pct"] = pd.to_numeric(b.pct)
    for df in (a, b, gas):
        df["idpozo"] = df.idpozo.astype(str)
    for df in (a, b):
        df["inicio"] = pd.to_datetime(df.inicio)
    gas = gas.assign(gas_2_7=pd.to_numeric(gas.gas_2_7))
    pozos = set(a.idpozo) & set(b.idpozo) & set(gas.idpozo)
    a = a[a.idpozo.isin(pozos)].merge(gas, on="idpozo").sort_values(["inicio", "idpozo"]).reset_index(drop=True)
    b = b[b.idpozo.isin(pozos)].merge(gas, on="idpozo").sort_values(["inicio", "idpozo"]).reset_index(drop=True)
    return a, b


def entrenar(df, categorias, numeros, alpha=1.0):
    """Regresión lineal con un poco de regularización (ridge). Devuelve la predicción, el aporte de cada
    variable (en millones de m³, respecto del pozo promedio de entrenamiento), el error y el R² en la prueba."""
    entreno = (df.inicio < PRUEBA).values
    x = pd.get_dummies(df[categorias].astype(str), prefix_sep="=", dtype=float)
    n = df[numeros].astype(float)
    n = n.fillna(n[entreno].median())       # lo que falta, con la mediana del entrenamiento
    x = pd.concat([x, n], axis=1)
    media_x, media_y = x[entreno].mean(), df.gas_2_7[entreno].mean()
    xc = (x[entreno] - media_x).values
    coef = np.linalg.solve(xc.T @ xc + alpha * np.eye(xc.shape[1]), xc.T @ (df.gas_2_7[entreno].values - media_y))
    aportes = (x - media_x) * coef
    pred = media_y + aportes.sum(axis=1).values
    # el aporte de una categoría es la suma de sus columnas («empresa=…»)
    por_variable = pd.DataFrame({c: aportes.filter(regex=f"^{c}=").sum(axis=1) for c in categorias})
    for c in numeros:
        por_variable[c] = aportes[c]
    y, p = df.gas_2_7[~entreno], pred[~entreno]
    return {"pred": pred, "aportes": por_variable, "base": media_y, "error": float(np.abs(p - y).mean()),
            "r2": float(1 - ((p - y) ** 2).sum() / ((y - y.mean()) ** 2).sum()), "relleno": n[entreno].median()}


def modelos(a, b):
    return {k: entrenar(df, **VARIABLES[k]) for k, df in (("A", a), ("B", b))}


def referencias(a):
    """El error de las referencias sin modelo, en los pozos de prueba."""
    prueba = a.inicio >= PRUEBA
    mediana = a[~prueba].gas_2_7.median()
    de_la_empresa = a[~prueba].groupby("empresa").gas_2_7.median().reindex(a[prueba].empresa).fillna(mediana).values
    y = a[prueba].gas_2_7
    return {"todos": float(np.abs(mediana - y).mean()), "operadora": float(np.abs(de_la_empresa - y).mean()),
            "entreno": int((~prueba).sum()), "prueba": int(prueba.sum())}


def marca(regla):
    """Rastro marca los datos que no salen tal cual de la fuente."""
    if not isinstance(regla, str) or "revisad" not in regla:
        return ""
    return "dato corregido con documento" if "documento" in regla else "unión revisada por IA, a confirmar por una persona"


def dudosos(b):
    """Cuántas predicciones de prueba se apoyan en un dato que no sale tal cual de la fuente."""
    prueba = b[b.inicio >= PRUEBA]
    return int(((prueba.reglaNombre.map(marca) != "") | (prueba.reglaSocio.map(marca) != "")).sum()), len(prueba)


def explicacion_a(r, a, pozo):
    """Sin Rastro: columna, valor y aporte."""
    i = a.index[a.idpozo == pozo][0]
    filas = []
    for c in VARIABLES["A"]["categorias"] + VARIABLES["A"]["numeros"]:
        v = a.loc[i, c]
        valor = f"vacío (se usa {r['A']['relleno'][c]:g})" if isinstance(v, float) and np.isnan(v) else f"{v:g}" if isinstance(v, float) else str(v)
        filas.append({"columna": c, "valor": valor, "aporte": float(r["A"]["aportes"].loc[i, c])})
    return {"pred": float(r["A"]["pred"][i]), "filas": filas}


def explicacion_b(r, b, pozo):
    """Con Rastro: concepto, valor, aporte, marca y el porqué (regla, evidencia y fuentes)."""
    i = b.index[b.idpozo == pozo][0]
    f, ap = b.loc[i], r["B"]["aportes"].loc[i]
    area = f.areaNombre if isinstance(f.areaNombre, str) else f.area
    filas = [
        {"concepto": "Operadora", "valor": f.grupo, "aporte": float(ap.grupo), "marca": marca(f.reglaNombre),
         "regla": "rige la declaración jurada del primer mes", "evidencia": f.evidencia,
         "nombre": f"Declarado como «{f.nombre}»; unido a {f.grupo} por: {f.reglaNombre}.",
         "fuentes": "Capítulo IV de la Secretaría de Energía (declaraciones juradas)"},
        {"concepto": "Concesión", "valor": area.title(), "aporte": float(ap.area), "marca": "",
         "regla": "el mismo código de concesión en las dos fuentes",
         "evidencia": f"Código {f.area} en la declaración jurada del primer mes y en el mapa de concesiones.",
         "fuentes": "Capítulo IV y mapa de concesiones de la Secretaría de Energía"},
        {"concepto": "Participación de la operadora", "valor": f"{f.pct:g} %" if pd.notna(f.pct) else "sin dato",
         "aporte": float(ap.pct), "marca": marca(f.reglaSocio), "regla": f.reglaSocio, "evidencia": f.textoSocio,
         "fuentes": "Mapa de concesiones de la Secretaría de Energía (texto de socios)"
                    + (", corregido con un documento" if "documento" in str(f.reglaSocio) else "")},
    ]
    grupos = {"La empresa (operadora y participación)": float(ap.grupo + ap.pct), "La ubicación (concesión)": float(ap.area)}
    return {"pred": float(r["B"]["pred"][i]), "filas": filas, "grupos": grupos,
            "real": float(f.gas_2_7), "inicio": f.inicio, "area": area.title(), "operadora": f.grupo}


if __name__ == "__main__":
    import io
    import subprocess
    import sys
    import urllib.parse
    import urllib.request

    def sql(query):
        out = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "rastro", "--csv", "-c", query],
                             capture_output=True, text=True, check=True).stdout
        return pd.read_csv(io.StringIO(out), dtype={"idpozo": str})

    def sparql(query):
        data = urllib.parse.urlencode({"query": query}).encode()
        req = urllib.request.Request("http://localhost:8082/sparql", data, {"Accept": "text/csv"})
        return pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=300).read().decode()))

    a, b = preparar(sql(SQL_GAS), sql(SQL_A), sparql(SPARQL_B))
    r, ref = modelos(a, b), referencias(a)
    print(f"Pozos de shale gas nuevos de Vaca Muerta con sus meses 2 a 7: {len(a)} "
          f"({ref['entreno']} para entrenar, de 2023 y 2024; {ref['prueba']} para probar, de 2025)")
    print(f"Referencias, error medio en millones de m³: la mediana de todos {ref['todos']:.1f}; "
          f"la mediana de la operadora {ref['operadora']:.1f}")
    for k in "AB":
        print(f"Modelo {k}: error medio {r[k]['error']:.1f} millones de m³, R² {r[k]['r2']:.2f}")
    print("Predicciones de prueba con un dato que no sale tal cual de la fuente: %d de %d" % dudosos(b))

    pozo = sys.argv[1] if len(sys.argv) > 1 else b[(b.inicio >= PRUEBA) & (b.area == "APE")].idpozo.iloc[0]
    ea, eb = explicacion_a(r, a, pozo), explicacion_b(r, b, pozo)
    print(f"\nPozo {pozo}, {eb['area']}: empezó en {eb['inicio']:%m/%Y} y dio {eb['real']:.1f} millones de m³ en los meses 2 a 7.")
    print(f"Un pozo promedio da {r['A']['base']:.1f}. A predice {ea['pred']:.1f}; B predice {eb['pred']:.1f}.")
    print("\nSin Rastro (A), en millones de m³:")
    for f in ea["filas"]:
        print(f"  {f['columna']} = {f['valor']}: {f['aporte']:+.1f}")
    print("\nCon Rastro (B), en millones de m³:")
    for f in eb["filas"]:
        print(f"  {f['concepto']}: {f['valor']}: {f['aporte']:+.1f}" + (f" · {f['marca'].upper()}" if f["marca"] else ""))
        print(f"    ¿Por qué? Regla: {f['regla']}. Evidencia: {f['evidencia']} {f.get('nombre', '')} Fuentes: {f['fuentes']}.")
    print("\nAgrupado por concepto: " + "; ".join(f"{k} {v:+.1f}" for k, v in eb["grupos"].items()) + ".")
