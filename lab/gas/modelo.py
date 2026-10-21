"""Rastro Lab: el mismo modelo de gas con variables de las tablas crudas (A) y de Rastro (B).

Predice el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta y explica cada predicción.
El modelo es una regresión lineal: la predicción es el gas de un pozo promedio más el aporte de cada
variable, en millones de m³, exacto y sin técnicas aparte. La operadora y la concesión entran como
categorías (un coeficiente por empresa y por concesión, aprendido con los pozos de entrenamiento);
la fractura (rama horizontal, etapas, arena, agua y presión), como números. Pozos desde 2018 si se cargaron
los años anteriores del Capítulo IV (data/lab-gas/).
Lo que cambia entre A y B es de dónde salen las variables y qué dicen: columnas en A, conceptos con
fuente, regla y evidencia en B.

La app lo usa desde la pestaña «Rastro Lab» de petróleo y gas (app/lab.py). Desde la raíz del repo,
con Postgres y Ontop de energía arriba:
    python3 lab/gas/modelo.py             # números y la explicación de un pozo
    python3 lab/gas/modelo.py <idpozo>    # la explicación de otro pozo
    python3 lab/gas/modelo.py --12-meses  # validación: el gas de los primeros 12 meses, otro corte por fecha
    python3 lab/gas/modelo.py --como-trabajo-publicado   # validación con el diseño de un trabajo con las mismas fuentes
    python3 lab/gas/modelo.py --publicar  # guarda la corrida, su entrada y sus predicciones en Rastro (energia:Prediction)
    python3 lab/gas/modelo.py --comparar [<corrida> <corrida>]   # qué cambió entre dos corridas (por defecto, las dos últimas)
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]

PRUEBA = pd.Timestamp("2025-01-01")   # entrena con los pozos que empezaron antes de 2025, prueba con los de 2025
# Solo los pozos que alguna vez declararon shale gas de Vaca Muerta: el resto no hace falta y hace lento todo
POZOS_GAS = "formacion = 'vaca muerta' AND sub_tipo_recurso = 'SHALE' AND tipopozo = 'Gasífero'"
# Las tres tablas del Capítulo IV: 2025, 2023 y 2024, y 2018 a 2022 (vacía si no se cargó)
TODO = """(SELECT * FROM capitulo4.produccion
          UNION ALL SELECT * FROM capitulo4.produccion_historica
          UNION ALL SELECT * FROM capitulo4_anterior.produccion)"""


def sql_gas(desde=1, meses=6):
    """Lo que se predice, calculado con SQL sobre las tablas crudas (para A): el gas de los meses desde+1 a
    desde+meses de cada pozo, en millones de m³, sumando sus formaciones, desde su primer mes con petróleo o gas.
    Por defecto, los meses 2 a 7 (el primero suele ser parcial). Solo pozos con todos esos meses.
    Rastro tiene lo mismo en energia:gasMonths2to7 y energia:gasFirst12Months (para B)."""
    return f"""
WITH todo AS (
  SELECT idpozo, make_date(anio, mes, 1) AS f, prod_gas, prod_pet FROM {TODO} t
  WHERE idpozo IN (SELECT idpozo FROM {TODO} v WHERE {POZOS_GAS})),
m AS (SELECT idpozo, f, sum(coalesce(prod_gas, 0)) AS gas, sum(coalesce(prod_pet, 0)) AS pet FROM todo GROUP BY 1, 2),
i AS (SELECT idpozo, min(f) FILTER (WHERE gas > 0 OR pet > 0) AS inicio FROM m GROUP BY 1)
SELECT i.idpozo, sum(m.gas) / 1000.0 AS gas
FROM i JOIN m ON m.idpozo = i.idpozo AND m.f >= i.inicio + interval '{desde} month'
                                     AND m.f < i.inicio + interval '{desde + meses} months'
GROUP BY 1 HAVING count(*) = {meses}"""


SQL_GAS = sql_gas()

# A: lo que armaría un analista con SQL sobre las tablas tal como vienen
SQL_A = f"""
WITH todo AS (   -- las declaraciones juradas de 2018 a 2025, solo de los pozos de shale gas de Vaca Muerta
  SELECT * FROM {TODO} t
  WHERE idpozo IN (SELECT idpozo FROM {TODO} v WHERE {POZOS_GAS})),
desde AS (SELECT min(make_date(anio, mes, 1)) AS mes FROM todo),
p AS (SELECT idpozo, min(make_date(anio, mes, 1)) AS primera,
             min(make_date(anio, mes, 1)) FILTER (WHERE prod_gas > 0 OR prod_pet > 0) AS inicio FROM todo GROUP BY 1),
fr AS (   -- la fractura de cada pozo, de la tabla tal como viene: las fracturas hasta el mes en que arrancó
  SELECT x.idpozo, max(longitud_rama_horizontal_m) AS longitud_rama_horizontal_m, sum(cantidad_fracturas) AS cantidad_fracturas,
         sum(coalesce(arena_bombeada_nacional_tn, 0) + coalesce(arena_bombeada_importada_tn, 0)) AS arena_tn,
         sum(agua_inyectada_m3) AS agua_inyectada_m3, max(presion_maxima_psi) AS presion_maxima_psi
  FROM fractura.fractura x JOIN p ON p.idpozo = x.idpozo
  WHERE x.fecha_inicio_fractura < p.inicio + interval '1 month' GROUP BY 1),
tr AS (   -- la trayectoria de cada pozo: la de rama más larga entre las perforadas antes de que arrancara
  SELECT DISTINCT ON (y.idpo) y.idpo AS idpozo, y.profundidad_vertical_mt
  FROM trayectoria.trayectoria y JOIN p ON p.idpozo = y.idpo
  WHERE y.profundidad_vertical_mt > 0 AND (y.drilfin IS NULL OR y.drilfin < p.inicio + interval '1 month')
  ORDER BY y.idpo, y.largo_rama_horizontal_mt DESC NULLS LAST)
SELECT DISTINCT ON (t.idpozo) t.idpozo, p.inicio, trim(t.empresa) AS empresa, t.idareapermisoconcesion AS area,
       c.participacion, fr.longitud_rama_horizontal_m, fr.cantidad_fracturas, fr.arena_tn, fr.agua_inyectada_m3,
       fr.presion_maxima_psi, tr.profundidad_vertical_mt
FROM todo t JOIN p ON p.idpozo = t.idpozo AND make_date(t.anio, t.mes, 1) = p.inicio
LEFT JOIN sig_energia.concesion c ON c.id_concesion = t.idareapermisoconcesion
LEFT JOIN fr ON fr.idpozo = t.idpozo
LEFT JOIN tr ON tr.idpozo = t.idpozo
WHERE p.inicio > (SELECT mes FROM desde) AND p.primera > (SELECT mes FROM desde)
  AND t.formacion = 'vaca muerta' AND t.sub_tipo_recurso = 'SHALE' AND t.tipopozo = 'Gasífero'
ORDER BY t.idpozo, t.prod_gas DESC NULLS LAST"""

# B: lo mismo, leído de Rastro, con la regla y la evidencia de cada dato
SPARQL_B = """PREFIX energia: <https://w3id.org/rastro/energia#>
SELECT ?well ?s ?st ?fr ?inicio ?grupo ?nombre ?reglaNombre ?evidencia ?area ?areaNombre ?pct ?reglaSocio ?textoSocio ?gas27 ?gas12
       ?rama ?etapas ?arena ?agua ?presion ?fracEvidencia ?fracNombre ?fracRegla ?fracEmpresa ?fracCargada
       ?tr ?profundidad ?trEvidencia
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
  OPTIONAL { ?tr a energia:WellTrajectory ; energia:aboutWell ?well ; energia:verticalDepthM ?profundidad ;
                 energia:sourceText ?trEvidencia }
  OPTIONAL { ?fr a energia:Fracturing ; energia:aboutWell ?well ; energia:lateralLengthM ?rama ; energia:fracStages ?etapas ;
                 energia:proppantTonnes ?arena ; energia:waterM3 ?agua ; energia:maxPressurePsi ?presion ;
                 energia:sourceText ?fracEvidencia ; energia:declaredName ?fracNombre ; energia:company/energia:name ?fracEmpresa ;
                 energia:loadedOn ?fracCargada .
             OPTIONAL { ?fcn a energia:CompanyName ; energia:nameInSource ?fracNombre ; energia:rule ?fracRegla } }
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
FRACTURA_A = ["longitud_rama_horizontal_m", "cantidad_fracturas", "arena_tn", "agua_inyectada_m3", "presion_maxima_psi"]
FRACTURA_B = ["rama", "etapas", "arena", "agua", "presion"]
PROFUNDIDAD_A, PROFUNDIDAD_B = ["profundidad_vertical_mt"], ["profundidad"]   # de las trayectorias de pozo
VARIABLES = {
    "A": {"categorias": ["empresa", "area"], "numeros": ["porcentaje"] + FRACTURA_A + PROFUNDIDAD_A},
    "B": {"categorias": ["grupo", "area"], "numeros": ["pct"] + FRACTURA_B + PROFUNDIDAD_B},
}
# Cómo se lee cada variable de fractura de Rastro: concepto, unidad y cuántos decimales
FRACTURA = {"rama": ("largo de la rama horizontal", "m", 0), "etapas": ("etapas de fractura", "", 0),
            "arena": ("arena bombeada", "t", 0), "agua": ("agua inyectada", "m³", 0),
            "presion": ("presión máxima", "psi", 0)}


# --- Para correr en la máquina (consola, pruebas de cambio, prueba a ciegas); la app usa sus propias conexiones ---

def sql_local(query):
    """Una consulta a Postgres por docker compose, como tabla."""
    import io
    import subprocess
    out = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", os.environ.get("PG_USER", "rastro"),
                          "--csv", "-c", query], capture_output=True, text=True, check=True, cwd=RAIZ).stdout
    return pd.read_csv(io.StringIO(out), dtype={"idpozo": str})


def sparql_local(query):
    """Una consulta al Ontop de petróleo y gas en esta máquina, como tabla."""
    import io
    import urllib.parse
    import urllib.request
    url = f"http://localhost:{os.environ.get('ONTOP_ENERGIA_PORT', '8082')}/sparql"
    pedido = urllib.request.Request(url, urllib.parse.urlencode({"query": query}).encode(), {"Accept": "text/csv"})
    return pd.read_csv(io.StringIO(urllib.request.urlopen(pedido, timeout=300).read().decode()))


def sql_ejecutar(script):
    """Ejecuta un script SQL en Postgres por docker compose (todo o nada)."""
    import subprocess
    subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", os.environ.get("PG_USER", "rastro"), "-q",
                    "-v", "ON_ERROR_STOP=1", "-1", "-f", "-"], input=script, text=True, check=True, cwd=RAIZ)


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
    for c in ["pct"] + FRACTURA_B + PROFUNDIDAD_B:
        b[c] = pd.to_numeric(b[c])
    for c in FRACTURA_A + PROFUNDIDAD_A:
        a[c] = pd.to_numeric(a[c])
    b["gas"] = pd.to_numeric(b[objetivo])
    b = b[b.gas.notna()]
    for df in (a, b, gas):
        df["idpozo"] = df.idpozo.astype(str)
    for df in (a, b):
        df["inicio"] = pd.to_datetime(df.inicio)
    b["fracCargada"] = pd.to_datetime(b.fracCargada)
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


def r2(p, y):
    return float(1 - ((p - y) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def entrenar(df, categorias, numeros, prueba=PRUEBA, alpha=1.0):
    """Regresión lineal con un poco de regularización (ridge). Devuelve la predicción, el aporte de cada
    variable (en millones de m³, respecto del pozo promedio de entrenamiento), el error y el R² en la prueba."""
    entreno = (df.inicio < prueba).values
    x = pd.get_dummies(df[categorias].astype(str), prefix_sep="=", dtype=float)
    n = df[numeros].astype(float)
    n = n.fillna(n[entreno].mean())         # lo que falta, con el promedio del entrenamiento: no suma ni resta
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
    y, p = df.gas[~entreno], pred[~entreno]
    return {"pred": pred, "aportes": por_variable, "base": media_y, "error": float(np.abs(p - y).mean()),
            "r2": r2(p, y), "relleno": n[entreno].mean(), "mediana": float(df.gas[entreno].median())}


def rango(df, categorias, numeros, prueba=PRUEBA):
    """Cuánto se suele equivocar el modelo, sin mirar la prueba: se entrena con los pozos anteriores al año previo
    a la prueba, se predicen los de ese año y se toman los errores del 10 % y del 90 %. Sumados a cada predicción,
    dan un rango en el que deberían caer 8 de cada 10 pozos."""
    antes = df[df.inicio < prueba].reset_index(drop=True)
    corte = prueba - pd.DateOffset(years=1)
    r = entrenar(antes, categorias, numeros, prueba=corte)
    errores = (antes.gas - r["pred"])[(antes.inicio >= corte).values]
    return float(errores.quantile(0.1)), float(errores.quantile(0.9))


def dentro_del_rango(r, df, desde_hasta, prueba=PRUEBA):
    """Qué parte de los pozos de prueba cayó dentro de su rango."""
    p = (df.inicio >= prueba).values
    bajo, alto = r["pred"][p] + desde_hasta[0], r["pred"][p] + desde_hasta[1]
    y = df.gas[p].values
    return float(((y >= bajo) & (y <= alto)).mean())


def modelos(a, b, prueba=PRUEBA):
    return {k: entrenar(df, prueba=prueba, **VARIABLES[k]) for k, df in (("A", a), ("B", b))}


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


def concesion(texto):
    """El nombre de una concesión para leer: «Las Tacanas II», no «LAS TACANAS II» ni «Las Tacanas Ii»."""
    return " ".join(w.upper() if w.upper() in ("I", "II", "III", "IV", "V") else w for w in str(texto).title().split())


def signo(v):
    """Un aporte con su signo: «+3,9» o «−4,9»."""
    return ("+" if v >= 0 else "−") + num(abs(v))


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
        if isinstance(v, float):
            valor = f"vacío (se usa {m['relleno'][c]:g})" if np.isnan(v) else f"{v:g}"
        else:
            valor = str(v)
        filas.append({"columna": c, "valor": valor, "aporte": float(m["aportes"].loc[i, c])})
    return {"pred": float(m["pred"][i]), "filas": filas}


def socios_texto(lista):
    return ", ".join(f"{nombre(s['socio'])} {num(s['pct'], 1).rstrip('0').rstrip(',')} %" for s in lista)


UBICACION = ["grupo", "area", "pct"]   # en B, lo que no cambia dentro de una concesión


def aprendido(r, b, ctx, prueba=PRUEBA):
    """Lo que aprendió el modelo, por concesión, con lo que dice Rastro de cada una: el efecto de estar en esa
    concesión con su operadora y sus socios (sin la fractura, que es de cada pozo)."""
    m, entreno = r["B"], b.inicio < prueba
    efecto = m["aportes"][UBICACION].sum(axis=1)
    filas = []
    for area, g in b[entreno].groupby("area"):
        nombre_area = concesion(g.areaNombre.dropna().iloc[0]) if g.areaNombre.notna().any() else area
        filas.append({"Concesión": nombre_area, "Operadora": ", ".join(sorted(g.grupo.map(nombre).unique())),
                      "Socios (Rastro)": socios_texto(ctx["socios"].get(area, [])),
                      "Pozos de entrenamiento": len(g), "Mediana de su gas": round(float(g.gas.median()), 1),
                      "Efecto en la predicción": round(float(efecto[g.index].mean()), 1)})
    return pd.DataFrame(filas).sort_values("Efecto en la predicción", ascending=False)


def explicacion_b(r, b, ctx, pozo, prueba=PRUEBA):
    """Con Rastro: dos factores. La concesión con su operadora y sus socios (que no cambian dentro de una
    concesión, así que el modelo no puede separarlos) y cómo se fracturó el pozo. Para cada uno, por qué suma o
    resta y los hechos de Rastro que lo respaldan, con su regla y su evidencia. «marca» dice si un dato no sale
    tal cual de la fuente."""
    i = b.index[b.idpozo == pozo][0]
    f, m = b.loc[i], r["B"]
    entreno = b[b.inicio < prueba]
    area = concesion(f.areaNombre if isinstance(f.areaNombre, str) else f.area)
    operadora = nombre(f.grupo)
    lugar = float(m["aportes"].loc[i, UBICACION].sum())
    hondo = float(m["aportes"].loc[i, PROFUNDIDAD_B].sum())
    if pd.notna(f.profundidad):
        tipica = m["relleno"]["profundidad"]
        quienes = "hondos" if hondo * (f.profundidad - tipica) > 0 else "someros"   # el signo del aporte dice hacia dónde empuja
        por_que_hondo = (f"Está a {num(f.profundidad, 0)} m de profundidad vertical (típico: {num(tipica, 0)}), de su trayectoria; "
                         f"en el entrenamiento, los pozos más {quienes} dieron más gas.")
    else:
        por_que_hondo = "No hay trayectoria de este pozo: el modelo usa la profundidad de un pozo típico."
    fractura = float(m["aportes"].loc[i, FRACTURA_B].sum())
    misma = entreno[entreno.area == f.area]
    if len(misma):
        ops = sorted(misma.grupo.map(nombre).unique())
        quienes = "todos de " + ops[0] if len(ops) == 1 else ", ".join(ops)
        por_que_lugar = (f"Los {len(misma)} pozos de {area} que vio el modelo ({quienes}) "
                         f"dieron una mediana de {num(misma.gas.median())} millones de m³, "
                         f"{'más' if misma.gas.median() > m['mediana'] else 'menos'} que la de todos los pozos ({num(m['mediana'])}).")
    else:
        por_que_lugar = f"El modelo no vio pozos de {area}: usa lo que vio de {operadora} en otras concesiones."
    tiene = pd.notna(f.rama)
    if tiene:   # las dos variables de fractura que más mueven esta predicción, con su aporte real, contra un pozo típico
        ap = m["aportes"].loc[i, FRACTURA_B]
        orden = ap.abs().sort_values(ascending=False).index[:2]
        partes = [f"{FRACTURA[c][0]} {num(f[c], 0)} {FRACTURA[c][1]}".strip() + f" (típico: {num(m['relleno'][c], 0)}), "
                  + ("+" if ap[c] >= 0 else "−") + num(abs(ap[c])) for c in orden]
        por_que_fractura = "Pesan sobre todo: " + "; ".join(partes) + "."
        if set(orden) == {"rama", "etapas"} and ap["rama"] * ap["etapas"] < 0:
            por_que_fractura += (" Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, "
                                 f"y juntas suman {signo(ap['rama'] + ap['etapas'])}.")
    else:
        por_que_fractura = "No hay datos de fractura de este pozo: el modelo usa los de un pozo típico."
    cambios = int(ctx["cambios"].get(f.area, 0))
    una = len(misma) == 0 or misma.grupo.nunique() == 1
    juntas = ("El modelo no puede separar la concesión de su operadora ni de sus socios, y Rastro muestra por qué: "
              + (f"{area} tuvo una sola operadora en los pozos que vio el modelo" if una else f"{area} tuvo más de una operadora")
              + (", no cambió de operadora entre 2023 y 2025" if cambios == 0 else f", cambió {cambios} vez de operadora entre 2023 y 2025")
              + " y todos sus pozos comparten los mismos socios.")
    hechos = [
        {"hecho": "Operadora", "valor": operadora, "marca": marca(f.reglaNombre),
         "regla": "rige quien declara el pozo en su primer mes", "evidencia": f.evidencia,
         "nombre": None if marca(f.reglaNombre) == "" else f"Declarado como «{f.nombre}»; unido a {operadora} por: {f.reglaNombre}.",
         "fuentes": "Capítulo IV de la Secretaría de Energía (declaraciones juradas)"},
        {"hecho": "Socios", "valor": socios_texto(ctx["socios"].get(f.area, [])) or "sin dato", "marca": marca(f.reglaSocio),
         "regla": f.reglaSocio, "evidencia": f.textoSocio,
         "fuentes": "Mapa de concesiones de la Secretaría de Energía (texto de socios)"
                    + (", corregido con un documento" if "documento" in str(f.reglaSocio) else "")},
    ]
    if not isinstance(f.reglaSocio, str):   # la operadora no está entre los socios del mapa: las fuentes no coinciden
        hechos[1].update(marca=f"{operadora} no figura entre los socios del mapa", regla="texto de socios del mapa",
                         evidencia=f"Las declaraciones juradas dicen que opera {operadora}, pero el mapa no la lista entre "
                                   f"los socios de {area}. El modelo usa una participación típica.")
    if tiene:
        informa = nombre(f.fracEmpresa)
        tarde = meses_tarde(f)
        hechos.append({"hecho": "Fractura", "valor": f"{num(f.rama, 0)} m de rama, {num(f.etapas, 0)} etapas",
                       "marca": " · ".join(x for x in (marca(f.fracRegla), "la informa otra empresa" if informa != operadora else "",
                                                       f"cargada {tarde} {'mes' if tarde == 1 else 'meses'} después de que arrancó el pozo"
                                                       if tarde else "") if x),
                       "regla": "las fracturas informadas hasta el mes en que arrancó el pozo, sumadas",
                       "evidencia": f.fracEvidencia,
                       "nombre": f"Informada como «{f.fracNombre}»; Rastro la une a {informa}"
                                 + (f", que no es la operadora ({operadora})." if informa != operadora else "."),
                       "fuentes": "Datos de fractura de pozos (Adjunto IV), Secretaría de Energía"})
    if pd.notna(f.profundidad):
        hechos.append({"hecho": "Trayectoria", "valor": f"{num(f.profundidad, 0)} m de profundidad vertical", "marca": "",
                       "regla": "una por pozo: la de rama más larga entre las perforadas antes de que arrancara",
                       "evidencia": f.trEvidencia, "fuentes": "Trayectorias de pozo de Vaca Muerta, Secretaría de Energía"})
    resumen = (f"Se esperan {num(float(m['pred'][i]))} millones de m³: un pozo promedio da {num(m['base'])}; "
               f"estar en {area} con {operadora} {'suma' if lugar >= 0 else 'resta'} {num(abs(lugar))}, "
               f"cómo se fracturó {'suma' if fractura >= 0 else 'resta'} {num(abs(fractura))} "
               f"y su profundidad {'suma' if hondo >= 0 else 'resta'} {num(abs(hondo))}.")
    factores = [{"factor": f"{area}, con {operadora}", "aporte": lugar, "por_que": por_que_lugar,
                 "nota": juntas if len(misma) else ""},
                {"factor": "Cómo se fracturó", "aporte": fractura, "por_que": por_que_fractura, "nota": ""},
                {"factor": "Su profundidad", "aporte": hondo, "por_que": por_que_hondo, "nota": ""}]
    return {"pred": float(m["pred"][i]), "factores": factores, "hechos": hechos, "resumen": resumen,
            "real": float(f.gas), "inicio": f.inicio, "area": area, "operadora": operadora}


def pozo_ejemplo(b, prueba=PRUEBA):
    """El pozo que se muestra primero: uno de 2025 con datos de fractura, en Aguada Pichana Este (donde se ve la
    participación corregida) o, si no hay, uno cuya fractura llegó después de que arrancó."""
    p = b[(b.inicio >= prueba) & b.rama.notna()]
    if (p.area == "APE").any():
        return p[p.area == "APE"].idpozo.iloc[0]
    tarde = p[p.apply(meses_tarde, axis=1) > 0]
    return (tarde if len(tarde) else p).idpozo.iloc[0]


def meses_tarde(f):
    """Cuántos meses después de que arrancó el pozo se cargó su fractura en el portal (0 si estaba a tiempo)."""
    if pd.isna(f.fracCargada):
        return 0
    n = (f.fracCargada.year - f.inicio.year) * 12 + f.fracCargada.month - f.inicio.month
    return max(n, 0)


def al_arrancar(r, b, prueba=PRUEBA):
    """Qué cambia en las predicciones de prueba si se predice cuando arranca cada pozo, con la fuente de fractura
    como estaba ese mes: los pozos cuya fractura se cargó después no la tenían, y el modelo usaba un pozo típico
    (sin aporte de la fractura)."""
    p = b.index[(b.inicio >= prueba).values]
    con = b.loc[p][b.loc[p].rama.notna()]
    tarde = con.apply(meses_tarde, axis=1)
    sin = tarde[tarde > 0].index
    cambio = r["B"]["aportes"].loc[sin, FRACTURA_B].sum(axis=1).abs()
    return {"pozos": len(p), "con_fractura": len(con), "tarde": len(sin),
            "meses_mediana": float(tarde[tarde > 0].median()) if len(sin) else 0.0,
            "cambio_medio": float(cambio.mean()) if len(sin) else 0.0, "cambio_max": float(cambio.max()) if len(sin) else 0.0}


# Lo que entra al modelo con Rastro: cada columna es un concepto del diccionario, con su fuente
ENTRADA_B = [   # (columna, título, concepto de Rastro, fuente)
    ("idpozo", "Pozo", "energia:WellStart → energia:aboutWell", "Capítulo IV"),
    ("inicio", "Empezó", "energia:startMonth", "Capítulo IV"),
    ("grupo", "Operadora", "energia:company (unida entre fuentes)", "Capítulo IV y correcciones revisadas"),
    ("area", "Concesión", "energia:inConcession", "Capítulo IV y mapa de concesiones"),
    ("pct", "Participación (%)", "energia:Stake → energia:percent", "Mapa de concesiones y correcciones con documento"),
    ("rama", "Rama horizontal (m)", "energia:Fracturing → energia:lateralLengthM", "Datos de fractura"),
    ("etapas", "Etapas", "energia:fracStages", "Datos de fractura"),
    ("arena", "Arena (t)", "energia:proppantTonnes", "Datos de fractura"),
    ("agua", "Agua (m³)", "energia:waterM3", "Datos de fractura"),
    ("presion", "Presión máxima (psi)", "energia:maxPressurePsi", "Datos de fractura"),
    ("profundidad", "Profundidad vertical (m)", "energia:WellTrajectory → energia:verticalDepthM", "Trayectorias de pozo"),
    ("gas", "Gas meses 2 a 7 (M m³)", "energia:gasMonths2to7 (lo que se predice)", "Capítulo IV"),
]
ENTRADA_A = ["idpozo", "inicio", "empresa", "area", "porcentaje"] + FRACTURA_A + PROFUNDIDAD_A + ["gas"]


def entrada(a, b, prueba=PRUEBA):
    """Lo que entra al modelo, pozo por pozo: sin Rastro, las columnas de las tablas; con Rastro, los conceptos.
    La última columna dice si el pozo se usó para entrenar o para probar."""
    uso = np.where(b.inicio >= prueba, "prueba", "entrenamiento")
    sin = a[ENTRADA_A].assign(inicio=a.inicio.dt.strftime("%m/%Y"), uso=np.where(a.inicio >= prueba, "prueba", "entrenamiento"))
    con = b[[c for c, *_ in ENTRADA_B]].assign(inicio=b.inicio.dt.strftime("%m/%Y"), grupo=b.grupo.map(nombre), uso=uso,
                                                area=[concesion(n) if isinstance(n, str) else c for n, c in zip(b.areaNombre, b.area)])
    con = con.rename(columns={c: titulo for c, titulo, *_ in ENTRADA_B} | {"uso": "Uso"})
    origen = pd.DataFrame([{"Columna": titulo, "Concepto de Rastro": concepto, "Fuente": fuente}
                           for _, titulo, concepto, fuente in ENTRADA_B])
    return sin, con, origen


def version():
    """La versión del modelo: una huella del código de este archivo. Si el código cambia, cambia la versión."""
    import hashlib
    return hashlib.sha1(Path(__file__).read_bytes()).hexdigest()[:8]


def publicar(r, b, desde_hasta, dentro, prueba=PRUEBA):
    """Guarda en Rastro (esquema lab_gas) la corrida del modelo con Rastro, cada predicción con su rango y los datos
    que usó, y el aporte de cada factor. Queda como la corrida vigente. Devuelve su identificador."""
    from datetime import datetime

    def txt(v):
        return "NULL" if v is None or (isinstance(v, float) and np.isnan(v)) else "'" + str(v).replace("'", "''") + "'"

    m, ahora = r["B"], datetime.now()
    corrida = f"{ahora:%Y%m%d-%H%M%S}-{version()}"
    de_prueba = (b.inicio >= prueba).values
    predicciones, aportes, entradas = [], [], []
    for i, f in b.iterrows():
        entradas.append(f"({txt(corrida)}, {txt(f.idpozo)}, {txt(f'{f.inicio:%Y-%m-%d}')}, {txt(f.grupo)}, {txt(f.area)}, "
                        + ", ".join("NULL" if pd.isna(f[c]) else f"{float(f[c]):.3f}" for c in ["pct", *FRACTURA_B, "gas"])
                        + f", {bool(de_prueba[i])}, " + ("NULL" if pd.isna(f.profundidad) else f"{float(f.profundidad):.1f}") + ")")
        gas = float(m["pred"][i])
        predicciones.append(f"({txt(corrida)}, {txt(f.idpozo)}, {gas:.3f}, {max(gas + desde_hasta[0], 0):.3f}, "
                            f"{gas + desde_hasta[1]:.3f}, {bool(de_prueba[i])}, {txt(f.s)}, {txt(f.fr)}, {txt(f.st)}, {txt(f.tr)})")
        for factor, columnas in (("La concesión con su operadora y socios", UBICACION), ("Cómo se fracturó el pozo", FRACTURA_B),
                                 ("La profundidad del pozo", PROFUNDIDAD_B)):
            aportes.append(f"({txt(corrida)}, {txt(f.idpozo)}, {txt(factor)}, {float(m['aportes'].loc[i, columnas].sum()):.3f})")
    sql_ejecutar(f"""
UPDATE lab_gas.corrida SET vigente = false;
INSERT INTO lab_gas.corrida VALUES ({txt(corrida)}, {txt(version())}, {txt(f"{ahora:%Y-%m-%d %H:%M:%S}")}, {txt(f"{prueba:%Y-%m-%d}")},
  {int((~de_prueba).sum())}, {int(de_prueba.sum())}, {m['error']:.3f}, {m['r2']:.4f}, {dentro:.4f}, true);
INSERT INTO lab_gas.prediccion VALUES {", ".join(predicciones)};
INSERT INTO lab_gas.aporte VALUES {", ".join(aportes)};
INSERT INTO lab_gas.entrada VALUES {", ".join(entradas)};
""")
    return corrida


def comparar(antes=None, despues=None):
    """Qué cambió entre dos corridas publicadas (por defecto, las dos últimas): pozos cuya entrada o predicción es
    distinta, en qué variable y cuánto se movió la predicción."""
    # solo corridas con su entrada guardada (las primeras no la tienen)
    corridas = sql_local("SELECT id FROM lab_gas.corrida c WHERE EXISTS (SELECT 1 FROM lab_gas.entrada e "
                         "WHERE e.corrida = c.id) ORDER BY fecha DESC LIMIT 2").id.tolist()
    if len(corridas) < 2 and not (antes and despues):
        return None
    despues, antes = despues or corridas[0], antes or corridas[1]
    columnas = ["operadora", "concesion", "participacion", "rama", "etapas", "arena", "agua", "presion", "profundidad", "gas"]
    distintas = " OR ".join(f"a.{c} IS DISTINCT FROM d.{c}" for c in columnas)
    cambios = sql_local(f"""
SELECT d.idpozo, concat_ws(', ', {", ".join(f"CASE WHEN a.{c} IS DISTINCT FROM d.{c} THEN '{c}' END" for c in columnas)}) AS cambio,
       round(pa.gas, 1) AS antes, round(pd.gas, 1) AS despues, round(pd.gas - pa.gas, 1) AS diferencia
FROM lab_gas.entrada d
JOIN lab_gas.entrada a ON a.idpozo = d.idpozo AND a.corrida = '{antes}'
JOIN lab_gas.prediccion pd ON pd.corrida = d.corrida AND pd.idpozo = d.idpozo
JOIN lab_gas.prediccion pa ON pa.corrida = a.corrida AND pa.idpozo = a.idpozo
WHERE d.corrida = '{despues}' AND ({distintas} OR abs(pd.gas - pa.gas) > 0.05)
ORDER BY abs(pd.gas - pa.gas) DESC""")
    return {"antes": antes, "despues": despues, "cambios": cambios}


def peso_por_concepto(r, b, prueba=PRUEBA):
    """Qué pesa más en las predicciones de prueba: el aporte medio, sin signo, de cada concepto."""
    ap = r["B"]["aportes"][b.inicio >= prueba]
    return {"La concesión con su operadora y socios": float(ap[UBICACION].sum(axis=1).abs().mean()),
            "Cómo se fracturó el pozo": float(ap[FRACTURA_B].sum(axis=1).abs().mean()),
            "La profundidad del pozo": float(ap[PROFUNDIDAD_B].sum(axis=1).abs().mean())}


if __name__ == "__main__":
    import sys

    sql, sparql = sql_local, sparql_local
    ctx = contexto(sparql(SPARQL_SOCIOS), sparql(SPARQL_CAMBIOS))
    if "--como-trabajo-publicado" in sys.argv:
        # Validación con el diseño de un trabajo con las mismas fuentes (ver las preguntas frecuentes de la app):
        # gas de los primeros 12 meses, solo pozos con fractura, y dos formas de separar la prueba:
        # uno de cada cinco pozos en orden cronológico (como ese trabajo) y los pozos desde 2023 (hacia el futuro).
        from sklearn.ensemble import RandomForestRegressor
        a, b = preparar(sql(sql_gas(desde=0, meses=12)), sql(SQL_A), sparql(SPARQL_B), objetivo="gas12")
        con = b.rama.notna().values
        a, b = a[con].reset_index(drop=True), b[con].reset_index(drop=True)
        print(f"Pozos de shale gas de Vaca Muerta con 12 meses y fractura: {len(b)}, de {b.inicio.min():%m/%Y} a {b.inicio.max():%m/%Y}")
        for corte, prueba in (("uno de cada cinco", (np.arange(len(b)) % 5 == 4)),
                               ("desde 2023", (b.inicio >= pd.Timestamp("2023-01-01")).values)):
            orden = pd.Series(np.where(prueba, pd.Timestamp("2100-01-01"), pd.Timestamp("1900-01-01")))
            aa, bb = a.assign(inicio=orden), b.assign(inicio=orden)   # entrenar() separa por fecha: se marca la prueba
            r, ref = modelos(aa, bb, pd.Timestamp("2000-01-01")), referencias(aa, pd.Timestamp("2000-01-01"))
            x = pd.get_dummies(bb[["grupo", "area"]], dtype=float).join(bb[["pct"] + FRACTURA_B].astype(float))
            x = x.fillna(x[~prueba].median())
            bosque = RandomForestRegressor(500, min_samples_leaf=4, random_state=42).fit(x[~prueba], bb.gas[~prueba])
            print(f"  Prueba {corte} ({prueba.sum()} pozos): mediana del área R² {ref['r2_concesion']:.2f}; "
                  f"lineal A {r['A']['r2']:.2f}, lineal B {r['B']['r2']:.2f}; "
                  f"bosque aleatorio con las variables de Rastro {r2(bosque.predict(x[prueba]), bb.gas[prueba]):.2f}")
        sys.exit()
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
    if "--comparar" in sys.argv:
        c = comparar(*[x for x in sys.argv[2:] if not x.startswith("--")][:2])
        if c is None:
            print("Hacen falta dos corridas publicadas.")
        else:
            print(f"De {c['antes']} a {c['despues']}: {len(c['cambios'])} pozos con otra entrada u otra predicción.")
            print(c["cambios"].head(15).to_string(index=False))
        sys.exit()
    if "--publicar" in sys.argv:
        r = modelos(a, b)
        desde_hasta = rango(b, **VARIABLES["B"])
        corrida = publicar(r, b, desde_hasta, dentro_del_rango(r["B"], b, desde_hasta))
        print(f"Corrida {corrida} publicada en Rastro: {len(b)} predicciones (energia:Prediction), vigente.")
        sys.exit()
    print("El gas de A (SQL) y el de B (Rastro) coinciden en todos los pozos:",
          bool(np.allclose(a.set_index("idpozo").gas.loc[b.idpozo].values, b.gas.values, atol=0.01)))
    r, ref = modelos(a, b), referencias(a)
    print(f"Pozos de shale gas nuevos de Vaca Muerta con sus meses 2 a 7: {len(a)} "
          f"({ref['entreno']} para entrenar, de {a.inicio.min():%m/%Y} a 2024; {ref['prueba']} para probar, de 2025); "
          f"con fractura: {int(b.rama.notna().sum())}")
    print(f"Referencias, error medio en millones de m³: la mediana de todos {ref['todos']:.1f}; "
          f"la mediana de la operadora {ref['operadora']:.1f} (R² {ref['r2_operadora']:.2f}); "
          f"R² de la mediana de la concesión {ref['r2_concesion']:.2f}")
    for k in "AB":
        print(f"Modelo {k}: error medio {r[k]['error']:.1f} millones de m³, R² {r[k]['r2']:.2f}")
    print("Predicciones de prueba con un dato que no sale tal cual de la fuente: %d de %d" % dudosos(b))
    print("\nLo que aprendió el modelo, por concesión:")
    print(aprendido(r, b, ctx).to_string(index=False))

    pozo = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else pozo_ejemplo(b)
    ea, eb = explicacion_a(r, a, pozo), explicacion_b(r, b, ctx, pozo)
    print(f"\nPozo {pozo}, {eb['area']}: empezó en {eb['inicio']:%m/%Y} y dio {eb['real']:.1f} millones de m³.")
    print("\nSin Rastro (A):")
    for f in ea["filas"]:
        print(f"  {f['columna']} = {f['valor']}: {f['aporte']:+.1f}")
    print(f"\nCon Rastro (B): {eb['resumen']}")
    for x in eb["factores"]:
        print(f"  {x['factor']}: {x['aporte']:+.1f}. {x['por_que']} {x['nota']}")
    for h in eb["hechos"]:
        print(f"  {h['hecho']}: {h['valor']}" + (f" · {h['marca'].upper()}" if h["marca"] else "") + f" (regla: {h['regla']})")
    v = al_arrancar(r, b)
    print(f"\nCuando la fuente cambia: de {v['con_fractura']} pozos de prueba con fractura, en {v['tarde']} se cargó después de que "
          f"arrancaron (mediana {v['meses_mediana']:.0f} meses). Prediciendo al arrancar, esos pozos no la tenían: su predicción "
          f"cambia {v['cambio_medio']:.1f} millones de m³ en promedio (hasta {v['cambio_max']:.1f}).")
    print("\nPeso medio de cada concepto en las predicciones de prueba:",
          "; ".join(f"{k} {v:.1f}" for k, v in peso_por_concepto(r, b).items()))
