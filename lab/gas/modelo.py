"""Rastro Lab, paso 1: el mismo modelo de gas con variables de las tablas crudas (A) y de Rastro (B).

Predice el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta y explica cada predicción.
El modelo es una regresión lineal: la predicción es el gas de un pozo promedio más el aporte de cada
variable, en millones de m³, exacto y sin técnicas aparte. La operadora y la concesión entran como
categorías (un coeficiente por empresa y por concesión, aprendido con los pozos de entrenamiento).
Lo que cambia entre A y B es de dónde salen las variables y qué dicen: columnas en A, conceptos con
fuente, regla y evidencia en B.

La app lo usa desde la pestaña «Rastro Lab» de petróleo y gas (app/lab.py). Desde la raíz del repo,
con Postgres y Ontop de energía arriba:
    python3 lab/gas/modelo.py             # números y la explicación de un pozo
    python3 lab/gas/modelo.py <idpozo>    # la explicación de otro pozo
    python3 lab/gas/modelo.py --12-meses  # validación: el gas de los primeros 12 meses, otro corte por fecha
"""
import numpy as np
import pandas as pd

PRUEBA = pd.Timestamp("2025-01-01")   # entrena con pozos de 2023 y 2024, prueba con los de 2025


def sql_gas(desde=1, meses=6):
    """Lo que se predice, calculado con SQL sobre las tablas crudas (para A): el gas de los meses desde+1 a
    desde+meses de cada pozo, en millones de m³, sumando sus formaciones, desde su primer mes con petróleo o gas.
    Por defecto, los meses 2 a 7 (el primero suele ser parcial). Solo pozos con todos esos meses.
    Rastro tiene lo mismo en energia:gasMonths2to7 y energia:gasFirst12Months (para B)."""
    return f"""
WITH todo AS (SELECT idpozo, make_date(anio, mes, 1) AS f, prod_gas, prod_pet FROM capitulo4.produccion
              UNION ALL SELECT idpozo, make_date(anio, mes, 1), prod_gas, prod_pet FROM capitulo4.produccion_historica),
m AS (SELECT idpozo, f, sum(coalesce(prod_gas, 0)) AS gas, sum(coalesce(prod_pet, 0)) AS pet FROM todo GROUP BY 1, 2),
i AS (SELECT idpozo, min(f) FILTER (WHERE gas > 0 OR pet > 0) AS inicio FROM m GROUP BY 1)
SELECT i.idpozo, sum(m.gas) / 1000.0 AS gas
FROM i JOIN m ON m.idpozo = i.idpozo AND m.f >= i.inicio + interval '{desde} month'
                                     AND m.f < i.inicio + interval '{desde + meses} months'
GROUP BY 1 HAVING count(*) = {meses}"""


SQL_GAS = sql_gas()

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
SELECT ?well ?inicio ?grupo ?nombre ?reglaNombre ?evidencia ?area ?areaNombre ?pct ?reglaSocio ?textoSocio ?gas27 ?gas12
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
  OPTIONAL { ?s energia:gasMonths2to7 ?gas27 }
  OPTIONAL { ?s energia:gasFirst12Months ?gas12 }
}"""

# El contexto que Rastro da de cada concesión: sus socios y sus cambios de operadora
SPARQL_SOCIOS = """PREFIX energia: <https://w3id.org/rastro/energia#>
SELECT ?area ?socio ?pct ?regla WHERE {
  ?st a energia:Stake ; energia:inConcession/energia:concessionId ?area ; energia:partner/energia:name ?socio ;
      energia:percent ?pct ; energia:rule ?regla .
}"""
SPARQL_CAMBIOS = """PREFIX energia: <https://w3id.org/rastro/energia#>
SELECT ?area (COUNT(?x) AS ?cambios) WHERE {
  ?x a energia:OperatorChange ; energia:inConcession/energia:concessionId ?area .
} GROUP BY ?area"""

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


def preparar(gas, a, b, objetivo="gas27"):
    """Los mismos pozos en A y B, ordenados por fecha de inicio. A lleva el gas calculado con SQL; B, el que
    da Rastro (objetivo: gas27 o gas12). Son el mismo número, calculado por los dos caminos."""
    a = a.copy()
    a["porcentaje"] = [porcentaje_del_mapa(t, e) for t, e in zip(a.participacion, a.empresa)]
    b = b.copy()
    b["idpozo"] = b.well.str.rsplit("/", n=1).str[-1]
    b = b.drop_duplicates("idpozo")
    b["pct"] = pd.to_numeric(b.pct)
    b["gas"] = pd.to_numeric(b[objetivo])
    b = b[b.gas.notna()]
    for df in (a, b, gas):
        df["idpozo"] = df.idpozo.astype(str)
    for df in (a, b):
        df["inicio"] = pd.to_datetime(df.inicio)
    gas = gas.assign(gas=pd.to_numeric(gas.gas))
    pozos = set(a.idpozo) & set(b.idpozo) & set(gas.idpozo)
    a = a[a.idpozo.isin(pozos)].merge(gas, on="idpozo").sort_values(["inicio", "idpozo"]).reset_index(drop=True)
    b = b[b.idpozo.isin(pozos)].sort_values(["inicio", "idpozo"]).reset_index(drop=True)
    return a, b


def contexto(socios, cambios):
    """Por concesión, lo que dice Rastro: sus socios (con porcentaje y regla) y sus cambios de operadora."""
    socios = socios.assign(pct=pd.to_numeric(socios.pct)).sort_values(["area", "pct"], ascending=[True, False])
    return {"socios": {k: g.to_dict("records") for k, g in socios.groupby("area")},
            "cambios": dict(zip(cambios.area, pd.to_numeric(cambios.cambios)))}


def entrenar(df, categorias, numeros, prueba=PRUEBA, alpha=1.0):
    """Regresión lineal con un poco de regularización (ridge). Devuelve la predicción, el aporte de cada
    variable (en millones de m³, respecto del pozo promedio de entrenamiento), el error y el R² en la prueba,
    y lo que vio el modelo de cada categoría al entrenar (cuántos pozos y su mediana), que explica su aporte."""
    entreno = (df.inicio < prueba).values
    x = pd.get_dummies(df[categorias].astype(str), prefix_sep="=", dtype=float)
    n = df[numeros].astype(float)
    n = n.fillna(n[entreno].median())       # lo que falta, con la mediana del entrenamiento
    x = pd.concat([x, n], axis=1)
    media_x, media_y = x[entreno].mean(), df.gas[entreno].mean()
    xc = (x[entreno] - media_x).values
    coef = np.linalg.solve(xc.T @ xc + alpha * np.eye(xc.shape[1]), xc.T @ (df.gas[entreno].values - media_y))
    aportes = (x - media_x) * coef
    pred = media_y + aportes.sum(axis=1).values
    # el aporte de una categoría es la suma de sus columnas («empresa=…»)
    por_variable = pd.DataFrame({c: aportes.filter(regex=f"^{c}=").sum(axis=1) for c in categorias})
    for c in numeros:
        por_variable[c] = aportes[c]
    visto = {c: df[entreno].groupby(c).gas.agg(["count", "median"]) for c in categorias}
    y, p = df.gas[~entreno], pred[~entreno]
    return {"pred": pred, "aportes": por_variable, "base": media_y, "error": float(np.abs(p - y).mean()),
            "r2": float(1 - ((p - y) ** 2).sum() / ((y - y.mean()) ** 2).sum()), "relleno": n[entreno].median(),
            "visto": visto, "mediana": float(df.gas[entreno].median()),
            "coef": dict(zip(x.columns, coef)), "desvio": n[entreno].std()}


def modelos(a, b, prueba=PRUEBA):
    return {k: entrenar(df, prueba=prueba, **VARIABLES[k]) for k, df in (("A", a), ("B", b))}


def r2(p, y):
    return float(1 - ((p - y) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def referencias(a, prueba=PRUEBA):
    """El error (y el R²) de las referencias sin modelo, en los pozos de prueba."""
    p = a.inicio >= prueba
    mediana = a[~p].gas.median()
    y = a[p].gas
    def de(c):
        return a[~p].groupby(c).gas.median().reindex(a[p][c]).fillna(mediana).values
    return {"todos": float(np.abs(mediana - y).mean()), "operadora": float(np.abs(de("empresa") - y).mean()),
            "r2_operadora": r2(de("empresa"), y), "r2_concesion": r2(de("area"), y),
            "entreno": int((~p).sum()), "prueba": int(p.sum())}


def num(v, dec=1):
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def nombre(empresa):
    """El nombre de una empresa para leer: «YPF S.A.», no «YPF S.A.» en mayúsculas ni «Ypf S.A.»."""
    siglas = {"Ypf": "YPF", "S.A.": "S.A.", "S.A": "S.A.", "Sl": "SL", "Sau": "SAU", "S.R.L.": "S.R.L.", "Pbbpolisur": "PBBPolisur"}
    return " ".join(siglas.get(w, siglas.get(w.upper(), w)) for w in str(empresa).title().split())


def marca(regla):
    """Rastro marca los datos que no salen tal cual de la fuente."""
    if not isinstance(regla, str) or "revisad" not in regla:
        return ""
    return "dato corregido con documento" if "documento" in regla else "unión revisada por IA, a confirmar por una persona"


def dudosos(b, prueba=PRUEBA):
    """Cuántas predicciones de prueba se apoyan en un dato que no sale tal cual de la fuente."""
    p = b[b.inicio >= prueba]
    return int(((p.reglaNombre.map(marca) != "") | (p.reglaSocio.map(marca) != "")).sum()), len(p)


def explicacion_a(r, a, pozo):
    """Sin Rastro: lo que da una herramienta estándar con las tablas crudas, columna por columna."""
    i = a.index[a.idpozo == pozo][0]
    m, filas = r["A"], []
    for c in VARIABLES["A"]["categorias"] + VARIABLES["A"]["numeros"]:
        v = a.loc[i, c]
        valor = f"vacío (se usa {m['relleno'][c]:g})" if isinstance(v, float) and np.isnan(v) else f"{v:g}" if isinstance(v, float) else str(v)
        filas.append({"columna": c, "valor": valor, "aporte": float(m["aportes"].loc[i, c])})
    return {"pred": float(m["pred"][i]), "filas": filas}


def socios_texto(lista):
    return ", ".join(f"{nombre(s['socio'])} {num(s['pct'], 1).rstrip('0').rstrip(',')} %" for s in lista)


def aprendido(r, b, ctx, prueba=PRUEBA):
    """Lo que aprendió el modelo, por concesión, con lo que dice Rastro de cada una. Con estos datos, la
    operadora y los socios no cambian dentro de una concesión: el modelo aprende un efecto por concesión."""
    m, entreno = r["B"], b.inicio < prueba
    efecto = m["aportes"].sum(axis=1)
    filas = []
    for area, g in b[entreno].groupby("area"):
        concesion = g.areaNombre.dropna().iloc[0].title() if g.areaNombre.notna().any() else area
        filas.append({"Concesión": concesion, "Operadora": ", ".join(sorted(g.grupo.map(nombre).unique())),
                      "Socios (Rastro)": socios_texto(ctx["socios"].get(area, [])),
                      "Pozos de 2023 y 2024": len(g), "Mediana de su gas": round(float(g.gas.median()), 1),
                      "Efecto en la predicción": round(float(efecto[g.index].mean()), 1)})
    return pd.DataFrame(filas).sort_values("Efecto en la predicción", ascending=False)


def explicacion_b(r, b, ctx, pozo, prueba=PRUEBA):
    """Con Rastro: un solo factor, «la concesión y su operadora», con lo que aprendió el modelo de ellas, y los
    hechos de Rastro que lo respaldan, cada uno con su regla y su evidencia. «marca» dice si un dato no sale tal
    cual de la fuente."""
    i = b.index[b.idpozo == pozo][0]
    f, m = b.loc[i], r["B"]
    entreno = b[b.inicio < prueba]
    area = (f.areaNombre if isinstance(f.areaNombre, str) else f.area).title()
    operadora = nombre(f.grupo)
    efecto = float(m["aportes"].loc[i].sum())
    misma = entreno[entreno.area == f.area]
    if len(misma):
        ops = sorted(misma.grupo.map(nombre).unique())
        por_que = (f"Los {len(misma)} pozos de {area} en 2023 y 2024 ({'todos de ' + ops[0] if len(ops) == 1 else ', '.join(ops)}) "
                   f"dieron una mediana de {num(misma.gas.median())} millones de m³, "
                   f"{'más' if misma.gas.median() > m['mediana'] else 'menos'} que la de todos los pozos ({num(m['mediana'])}).")
    else:
        otra = entreno[entreno.grupo == f.grupo]
        por_que = (f"El modelo no vio pozos de {area}. Usa lo que vio de {operadora} en otras concesiones: "
                   f"{len(otra)} pozos, mediana {num(otra.gas.median())} millones de m³." if len(otra)
                   else f"El modelo no vio pozos de {area} ni de {operadora}: usa el pozo promedio.")
    cambios = int(ctx["cambios"].get(f.area, 0))
    socios = ctx["socios"].get(f.area, [])
    juntas = (f"El modelo no puede separar la concesión de su operadora ni de sus socios, y Rastro muestra por qué: "
              f"{area} {'no cambió de operadora' if cambios == 0 else f'cambió {cambios} vez de operadora'} entre 2023 y 2025, "
              f"y todos sus pozos comparten los mismos socios.")
    hechos = [
        {"hecho": "Operadora", "valor": operadora, "marca": marca(f.reglaNombre),
         "regla": "rige quien declara el pozo en su primer mes", "evidencia": f.evidencia,
         "nombre": None if marca(f.reglaNombre) == "" else f"Declarado como «{f.nombre}»; unido a {operadora} por: {f.reglaNombre}.",
         "fuentes": "Capítulo IV de la Secretaría de Energía (declaraciones juradas)"},
        {"hecho": "Socios", "valor": socios_texto(socios) or "sin dato", "marca": marca(f.reglaSocio),
         "regla": f.reglaSocio, "evidencia": f.textoSocio,
         "fuentes": "Mapa de concesiones de la Secretaría de Energía (texto de socios)"
                    + (", corregido con un documento" if "documento" in str(f.reglaSocio) else "")},
        {"hecho": "Cambios de operadora, 2023 a 2025", "valor": str(cambios), "marca": "",
         "regla": "otra empresa declara la mayor parte de la producción de la concesión al menos 3 meses seguidos",
         "evidencia": f"Rastro no encontró cambios en {area}." if cambios == 0 else f"Rastro encontró {cambios}.",
         "fuentes": "Capítulo IV, mes a mes"},
    ]
    resumen = (f"Se esperan {num(float(m['pred'][i]))} millones de m³: un pozo promedio da {num(m['base'])}, "
               f"y estar en {area} con {operadora} {'suma' if efecto >= 0 else 'resta'} {num(abs(efecto))}.")
    return {"pred": float(m["pred"][i]), "efecto": efecto, "por_que": por_que, "juntas": juntas, "hechos": hechos,
            "resumen": resumen, "real": float(f.gas), "evidencia_gas": f.evidencia, "inicio": f.inicio,
            "area": area, "operadora": operadora}


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

    ctx = contexto(sparql(SPARQL_SOCIOS), sparql(SPARQL_CAMBIOS))
    if "--12-meses" in sys.argv:
        # Validación con el mismo objetivo que otros trabajos: el gas de los primeros 12 meses. Solo los pozos
        # que empezaron hasta enero de 2025 tienen 12 meses; se entrena hasta junio de 2024 y se prueba con el resto.
        corte = pd.Timestamp("2024-07-01")
        a, b = preparar(sql(sql_gas(desde=0, meses=12)), sql(SQL_A), sparql(SPARQL_B), objetivo="gas12")
        r, ref = modelos(a, b, corte), referencias(a, corte)
        print(f"Gas de los primeros 12 meses: {len(a)} pozos ({ref['entreno']} hasta junio de 2024 para entrenar, "
              f"{ref['prueba']} después para probar). Mediana: {a.gas.median():.1f} millones de m³.")
        print(f"R² de la mediana de la concesión {ref['r2_concesion']:.2f}; de la mediana de la operadora {ref['r2_operadora']:.2f}")
        for k in "AB":
            print(f"Modelo {k}: error medio {r[k]['error']:.1f} millones de m³, R² {r[k]['r2']:.2f}")
        sys.exit()

    a, b = preparar(sql(SQL_GAS), sql(SQL_A), sparql(SPARQL_B))
    print("El gas de A (SQL) y el de B (Rastro) coinciden en todos los pozos:",
          bool(np.allclose(a.set_index("idpozo").gas.loc[b.idpozo].values, b.gas.values, atol=0.01)))
    r, ref = modelos(a, b), referencias(a)
    print(f"Pozos de shale gas nuevos de Vaca Muerta con sus meses 2 a 7: {len(a)} "
          f"({ref['entreno']} para entrenar, de 2023 y 2024; {ref['prueba']} para probar, de 2025)")
    print(f"Referencias, error medio en millones de m³: la mediana de todos {ref['todos']:.1f}; "
          f"la mediana de la operadora {ref['operadora']:.1f} (R² {ref['r2_operadora']:.2f}); "
          f"R² de la mediana de la concesión {ref['r2_concesion']:.2f}")
    for k in "AB":
        print(f"Modelo {k}: error medio {r[k]['error']:.1f} millones de m³, R² {r[k]['r2']:.2f}")
    print("Predicciones de prueba con un dato que no sale tal cual de la fuente: %d de %d" % dudosos(b))
    print("\nLo que aprendió el modelo, por concesión:")
    print(aprendido(r, b, ctx).to_string(index=False))

    pozo = sys.argv[1] if len(sys.argv) > 1 else "166271"
    ea, eb = explicacion_a(r, a, pozo), explicacion_b(r, b, ctx, pozo)
    print(f"\nPozo {pozo}, {eb['area']}: empezó en {eb['inicio']:%m/%Y} y dio {eb['real']:.1f} millones de m³.")
    print("\nSin Rastro (A):")
    for f in ea["filas"]:
        print(f"  {f['columna']} = {f['valor']}: {f['aporte']:+.1f}")
    print(f"\nCon Rastro (B): {eb['resumen']}")
    print(f"  Por qué: {eb['por_que']}")
    print(f"  {eb['juntas']}")
    for h in eb["hechos"]:
        print(f"  {h['hecho']}: {h['valor']}" + (f" · {h['marca'].upper()}" if h["marca"] else "") + f" (regla: {h['regla']})")
