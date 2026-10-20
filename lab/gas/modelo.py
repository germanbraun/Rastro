"""Rastro Lab, paso 1: el mismo modelo de gas con variables de las tablas crudas (A) y de Rastro (B).

Predice el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta y explica cada predicción.
El modelo es una regresión lineal: la predicción es el gas de un pozo promedio más el aporte de cada
variable, en millones de m³, exacto y sin técnicas aparte. La operadora y la concesión entran como
categorías (un coeficiente por empresa y por concesión, aprendido con los pozos de entrenamiento).
Lo que cambia entre A y B es de dónde salen las variables y qué dicen: columnas en A, conceptos con
fuente, regla y evidencia en B.

Correr desde la raíz del repo, con Postgres y Ontop de energía arriba:
    python3 lab/gas/modelo.py            # números y la explicación de un pozo
    python3 lab/gas/modelo.py <idpozo>   # la explicación de otro pozo
"""
import io
import subprocess
import sys
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

ONTOP = "http://localhost:8082/sparql"
POZO = sys.argv[1] if len(sys.argv) > 1 else None


def sql(query):
    out = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "rastro", "--csv", "-c", query],
                         capture_output=True, text=True, check=True).stdout
    return pd.read_csv(io.StringIO(out))


def sparql(query):
    data = urllib.parse.urlencode({"query": "PREFIX energia: <https://w3id.org/rastro/energia#>\n" + query}).encode()
    req = urllib.request.Request(ONTOP, data, {"Accept": "text/csv"})
    return pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=300).read().decode()))


# --- Lo que se predice (igual para A y B): gas de los meses 2 a 7, en millones de m³ ---------------
gas = sql("""
WITH m AS (
  SELECT idpozo, make_date(anio, mes, 1) AS f, sum(prod_gas) AS gas
  FROM (SELECT * FROM capitulo4.produccion UNION ALL SELECT * FROM capitulo4.produccion_historica) t
  WHERE formacion = 'vaca muerta' GROUP BY 1, 2
), i AS (SELECT idpozo, min(f) FILTER (WHERE gas > 0) AS inicio FROM m GROUP BY 1)
SELECT i.idpozo, sum(m.gas) / 1000.0 AS gas_2_7
FROM i JOIN m ON m.idpozo = i.idpozo AND m.f >= i.inicio + interval '1 month' AND m.f < i.inicio + interval '7 months'
WHERE i.inicio + interval '6 months' <= date '2025-12-01'
GROUP BY 1 HAVING count(*) = 6""")

# --- A: lo que armaría un analista con SQL sobre las tablas tal como vienen ------------------------
a = sql("""
WITH todo AS (SELECT * FROM capitulo4.produccion UNION ALL SELECT * FROM capitulo4.produccion_historica),
p AS (SELECT idpozo, min(make_date(anio, mes, 1)) AS primera,
             min(make_date(anio, mes, 1)) FILTER (WHERE prod_gas > 0 OR prod_pet > 0) AS inicio FROM todo GROUP BY 1)
SELECT DISTINCT ON (t.idpozo) t.idpozo, p.inicio, trim(t.empresa) AS empresa, t.idareapermisoconcesion AS area,
       t.tipopozo, c.participacion
FROM todo t JOIN p ON p.idpozo = t.idpozo AND make_date(t.anio, t.mes, 1) = p.inicio
LEFT JOIN sig_energia.concesion c ON c.id_concesion = t.idareapermisoconcesion
WHERE p.inicio > date '2023-01-01' AND p.primera > date '2023-01-01'
  AND t.formacion = 'vaca muerta' AND t.sub_tipo_recurso = 'SHALE' AND t.tipopozo = 'Gasífero'
ORDER BY t.idpozo, t.prod_gas DESC NULLS LAST""")


def porcentaje_del_mapa(texto, empresa):
    """El porcentaje de la empresa en el texto de socios del mapa, buscando su nombre tal cual."""
    for parte in str(texto).split("<br>"):
        if ":" in parte and parte.split(":")[0].strip().rstrip(".").upper() == empresa.rstrip(".").upper():
            return float(parte.split(":")[1].replace("%", "").strip())
    return np.nan


a["porcentaje"] = [porcentaje_del_mapa(t, e) for t, e in zip(a.participacion, a.empresa)]

# --- B: lo mismo, leído de Rastro -----------------------------------------------------------------
b = sparql("""
SELECT ?well ?inicio ?grupo ?nombre ?reglaNombre ?evidencia ?area ?areaNombre ?pct ?reglaSocio ?textoSocio ?gasoducto ?km
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
  OPTIONAL { ?pl a energia:PipelineLink ; energia:aboutConcession ?conc ; energia:pipeline ?gasoducto ; energia:distanceKm ?km }
}""")
b["idpozo"] = b.well.str.rsplit("/", n=1).str[-1]
b = b.drop_duplicates("idpozo")
b["inicio"] = pd.to_datetime(b.inicio)
a["inicio"] = pd.to_datetime(a.inicio)

# Los mismos pozos en A y B, con su gas medido
for df in (a, b, gas):
    df["idpozo"] = df.idpozo.astype(str)
pozos = sorted(set(a.idpozo) & set(b.idpozo) & set(gas.idpozo))
a = a[a.idpozo.isin(pozos)].merge(gas, on="idpozo").sort_values("inicio").reset_index(drop=True)
b = b[b.idpozo.isin(pozos)].merge(gas, on="idpozo").sort_values("inicio").reset_index(drop=True)


PRUEBA = pd.Timestamp("2025-01-01")   # entrena con pozos de 2023 y 2024, prueba con los de 2025
# Las mismas ideas de variables en A y B; cambia de dónde salen
VARIABLES = {
    "A": {"categorias": ["empresa", "area"], "numeros": ["porcentaje"]},
    "B": {"categorias": ["grupo", "area"], "numeros": ["pct"]},
}
# La distancia al gasoducto no entra: es una por concesión y, con la concesión en el modelo, solo la repite
# (salía al revés: estar a 0,3 km restaba gas). Vuelve en la prueba de áreas nuevas, donde sí agrega.


def entrenar(df, categorias, numeros):
    """Regresión lineal con un poco de regularización. Devuelve la predicción, el aporte de cada variable
    (en millones de m³, respecto del pozo promedio de entrenamiento), el error y el R² en la prueba."""
    entreno = df.inicio < PRUEBA
    x = pd.get_dummies(df[categorias].astype(str), prefix_sep="=", dtype=float)
    n = df[numeros].astype(float)
    n = n.fillna(n[entreno].median())       # lo que falta, con la mediana del entrenamiento
    x = pd.concat([x, n], axis=1)
    modelo = Ridge(alpha=1.0).fit(x[entreno], df.gas_2_7[entreno])
    pred = modelo.predict(x)
    aportes = (x - x[entreno].mean()) * modelo.coef_
    base = pred[entreno].mean()
    # el aporte de una categoría es la suma de sus columnas («empresa=…»)
    por_variable = pd.DataFrame({c: aportes.filter(regex=f"^{c}=").sum(axis=1) for c in categorias})
    for c in numeros:
        por_variable[c] = aportes[c]
    y, p = df.gas_2_7[~entreno], pred[~entreno]
    return {"pred": pred, "aportes": por_variable, "base": base, "error": np.abs(p - y).mean(),
            "r2": 1 - ((p - y) ** 2).sum() / ((y - y.mean()) ** 2).sum(), "relleno": n[entreno].median()}


r = {k: entrenar(df, **VARIABLES[k]) for k, df in (("A", a), ("B", b))}
prueba = a.inicio >= PRUEBA
mediana = a[~prueba].gas_2_7.median()
de_la_empresa = a[~prueba].groupby("empresa").gas_2_7.median().reindex(a[prueba].empresa).fillna(mediana).values
print(f"Pozos de shale gas nuevos de Vaca Muerta con sus meses 2 a 7: {len(a)} "
      f"({(~prueba).sum()} para entrenar, de 2023 y 2024; {prueba.sum()} para probar, de 2025)")
print(f"Referencias, error medio en millones de m³: la mediana de todos {np.abs(mediana - a[prueba].gas_2_7).mean():.1f}; "
      f"la mediana de la operadora {np.abs(de_la_empresa - a[prueba].gas_2_7).mean():.1f}")
for k in "AB":
    print(f"Modelo {k}: error medio {r[k]['error']:.1f} millones de m³, R² {r[k]['r2']:.2f}")

# --- La explicación de un pozo, lado a lado --------------------------------------------------------
pozo = POZO or b[(b.inicio >= PRUEBA) & (b.area == "APE")].idpozo.iloc[0]
ia, ib = a.index[a.idpozo == pozo][0], b.index[b.idpozo == pozo][0]
fa, fb = a.loc[ia], b.loc[ib]


def mm(v):
    return f"{v:+.1f}"


def corregido(regla):
    """Rastro marca los datos que no salen tal cual de la fuente."""
    if not isinstance(regla, str) or "revisad" not in regla:
        return ""
    return " · DATO CORREGIDO CON DOCUMENTO" if "documento" in regla else " · UNIÓN REVISADA POR IA, a confirmar por una persona"


print(f"\nPozo {pozo}, {fb.areaNombre}: empezó en {fb.inicio:%m/%Y} y dio {fb.gas_2_7:.1f} millones de m³ en los meses 2 a 7.")
print(f"Un pozo promedio da {r['A']['base']:.1f}. A predice {r['A']['pred'][ia]:.1f}; B predice {r['B']['pred'][ib]:.1f}.")

print("\nSin Rastro (A), en millones de m³:")
for c in VARIABLES["A"]["categorias"] + VARIABLES["A"]["numeros"]:
    v = fa[c] if not (isinstance(fa[c], float) and np.isnan(fa[c])) else f"(vacío, se usa {r['A']['relleno'][c]:.1f})"
    print(f"  {c} = {v}: {mm(r['A']['aportes'].loc[ia, c])}")

ap = r["B"]["aportes"].loc[ib]
print("\nCon Rastro (B), en millones de m³:")
print(f"  Operadora: {fb.grupo}: {mm(ap.grupo)}{corregido(fb.reglaNombre)}")
print(f"    ¿Por qué? {fb.evidencia} Regla: rige la declaración jurada del primer mes. "
      f"Nombre declarado «{fb.nombre}», unido por: {fb.reglaNombre}. Fuente: Capítulo IV, Secretaría de Energía.")
print(f"  Concesión: {fb.areaNombre}: {mm(ap.area)}")
print(f"    ¿Por qué? Código {fb.area} en la declaración jurada y en el mapa de concesiones. Fuentes: Capítulo IV y mapa de la Secretaría de Energía.")
print(f"  Participación de la operadora: {fb.pct:.1f} %: {mm(ap.pct)}{corregido(fb.reglaSocio)}")
print(f"    ¿Por qué? Regla: {fb.reglaSocio}. Evidencia: {fb.textoSocio}")
print(f"\nAgrupado por concepto: la ubicación {mm(ap.area)}; la empresa (operadora y su participación) {mm(ap.grupo + ap.pct)}.")
