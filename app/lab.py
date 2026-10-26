"""Oil and gas «Rastro Lab» tab: the same gas model, with and without Rastro, and the explanation of
each prediction side by side. The model is in lab/gas/modelo.py; here the data is only loaded and shown.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

import answer
from lab_walkthrough import GROUPS, compare_run, value_status
from dominio import ayuda, data_version, md, tabla

sys.path.insert(0, "/lab/gas")
import modelo  # noqa: E402

num = modelo.num


aporte = modelo.signo


def sparql_df(query):
    columns, rows = answer.run_sparql_table(query, "energia")
    return pd.DataFrame(rows, columns=columns)


@st.cache_data(persist="disk", show_spinner="Entrenando el modelo dos veces…")
def _datos(version, model_version):
    import psycopg
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        def sql(query):
            cur = conn.execute(query)
            return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
        gas, a = sql(modelo.SQL_GAS), sql(modelo.SQL_A)
    a, b = modelo.preparar(gas, a, sparql_df(modelo.SPARQL_B))
    ctx = modelo.contexto(sparql_df(modelo.SPARQL_SOCIOS), sparql_df(modelo.SPARQL_CAMBIOS))
    r = modelo.modelos(a, b)
    return a, b, ctx, r, modelo.referencias(a), modelo.dudosos(b), modelo.aprendido(r, b, ctx), modelo.peso_por_concepto(r, b), \
        modelo.al_arrancar(r, b), modelo.entrada(a, b), \
        rango_y_dentro(r, b)


def rango_y_dentro(r, b):
    desde_hasta = modelo.rango(b, **modelo.VARIABLES["B"])
    return desde_hasta, modelo.dentro_del_rango(r["B"], b, desde_hasta)


def datos():
    """The data and the two models. They are saved to disk and rebuilt if the data or the mappings change."""
    return _datos(data_version("energia", modelo.SQL_GAS + modelo.SQL_A), modelo.version())   # Lab also reads raw tables directly


def show_lab(tech, pozo=None):
    st.markdown("#### ¿Cuánto gas va a dar un pozo nuevo?")
    st.markdown(
        "Un modelo predice el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta. "
        "Es **el mismo modelo, entrenado dos veces**: una con las tablas tal como vienen y otra con Rastro. "
        "Rastro no lo hace más preciso: hace que **cada predicción se explique en conceptos de negocio, "
        "con los hechos que la respaldan, y que se pueda comprobar**.")
    (a, b, ctx, r, ref, (n_dudosos, n_prueba), tabla_aprendido, pesos, version, (entrada_a, entrada_b, origen),
     _rango) = datos()

    c1, c2, c3 = st.columns(3)
    c1.metric("Error sin Rastro", f"{num(r['A']['error'])} M m³", help=ayuda("lab_error"))
    c2.metric("Error con Rastro", f"{num(r['B']['error'])} M m³", help=ayuda("lab_error"))
    c3.metric("Con un dato corregido", f"{n_dudosos} de {n_prueba}", help=ayuda("lab_dudosos"))
    st.caption(f"Entrenado con {ref['entreno']} pozos que empezaron de {a.inicio.min():%Y} a 2024; probado con {ref['prueba']} de 2025. "
               f"Error medio por pozo, en millones de m³. Sin modelo, usar la mediana de cada concesión da "
               f"{num(ref['concesion'])}, y la de cada operadora, {num(ref['operadora'])}.")

    with st.expander("Lo que entra al modelo", expanded=False):
        st.markdown(f"Los mismos {len(entrada_b)} pozos y las mismas ideas de variables, de dos formas. "
                    "Sin Rastro, las columnas de las tablas tal como vienen; con Rastro, conceptos del diccionario, "
                    "cada uno con su fuente.")
        sin_tab, con_tab = st.tabs(["Sin Rastro", "Con Rastro"])
        with sin_tab:
            tabla(entrada_a, key="lab_entrada_a")
            st.caption("El porcentaje sale de buscar el nombre de la empresa en el texto de socios del mapa: si el nombre "
                       "no coincide, queda vacío; si el mapa está mal, nada lo dice.")
        with con_tab:
            tabla(entrada_b, key="lab_entrada_b")
            st.markdown("**De dónde sale cada columna:**")
            tabla(origen, key="lab_origen")

    with st.expander("Qué aprendió el modelo", expanded=False):
        st.markdown(md(
            f"El modelo explica el {round(100 * r['B']['r2'])} % de la diferencia entre los pozos de 2025; la mediana de "
            f"cada concesión, sola, el {round(100 * ref['r2_concesion'])} %. Casi todo lo que sabe es dónde está el pozo: "
            "la fractura y la profundidad agregan poco, y eso también es una conclusión. "
            "Pesa dos cosas, en millones de m³ por pozo, en promedio: "
            + "; ".join(f"**{k.lower()}**, {num(v)}" for k, v in pesos.items()) + ". "
            "La operadora y los socios no se pueden separar de la concesión: Rastro muestra que dentro de una "
            "concesión son siempre los mismos."))
        tabla(tabla_aprendido, key="lab_aprendido")
        st.caption("Operadora y socios, de Rastro (con sus correcciones). Efecto: cuánto suma o resta, en millones de m³, "
                   "estar en esa concesión, respecto de un pozo promedio.")

    with st.expander("Cuando la fuente cambia", expanded=False):
        v = version
        st.markdown(md(
            f"Los datos de fractura llegan tarde: de los {v['con_fractura']} pozos de 2025 que los tienen, en **{v['tarde']}** se "
            f"cargaron después de que el pozo empezó a producir (a la mitad, {num(v['meses_mediana'], 0)} meses o más). "
            f"Si la predicción se hace cuando el pozo arranca, esos pozos todavía no tenían fractura: **su predicción cambia "
            f"{num(v['cambio_medio'])} millones de m³ en promedio** (hasta {num(v['cambio_max'])}) cuando la fractura llega.\n\n"
            "Sin Rastro, el número cambia y nada dice por qué. Con Rastro, cada predicción dice qué datos usó y cuándo se "
            "cargó cada uno (en «¿De dónde sale?» de la fractura), y marca los que llegaron después de que el pozo arrancó."))
        impacto = Path("/layer/energia/cambio/impacto.json")
        if impacto.exists():
            i = json.loads(impacto.read_text())
            pozos = ", ".join(e["pozo"] for e in i["esperado"])
            cambio = i["cambiaron"][0] if i["cambiaron"] else None
            st.markdown(md(
                f"**Rastro sabe qué cambia.** Si la fuente corrige la fractura informada n.º {i['registro']}, Rastro dice de "
                f"antemano qué predicciones dependen de ella (pozo {pozos}), recorriendo de qué registros sale cada una. "
                "Se probó: se corrigió el registro, se rehízo todo y cambiaron exactamente esas"
                + (f" (de {num(cambio['antes'])} a {num(cambio['despues'])} millones de m³)" if cambio else "")
                + ", ninguna otra. Sin Rastro, para saberlo hay que rehacer todas y comparar."))

    show_well(key="lab_pozo", pozo=pozo)

    with st.expander("Las predicciones, en Rastro", expanded=False):
        show_published(tech)

    with st.expander("¿Cómo se calcula?"):
        st.markdown(md(
            "Es una regresión lineal: la predicción es el gas de un pozo promedio más el aporte de cada variable, "
            "en millones de m³. Las dos versiones usan las mismas ideas de variables (operadora, concesión, "
            "participación y fractura); cambia de dónde salen. Sin Rastro: la empresa como se declara, el código de la concesión y "
            "el porcentaje del texto de socios del mapa. Con Rastro: la operadora unida entre fuentes, la concesión y la "
            "participación corregida, cada una con su regla y su evidencia. La operadora es la del primer mes del pozo, "
            "no la de hoy: usar la de hoy sería usar el futuro. La fractura (rama horizontal, etapas, arena, agua y "
            "presión) es la informada hasta el mes en que arrancó el pozo. El gas que se predice también sale de Rastro "
            "(el gas de los meses 2 a 7 de cada pozo), y coincide con el que calcula el SQL.\n\n"
            "Ojo: la explicación dice cómo llegó el modelo a su número, no la causa física. Que un factor sume no "
            "prueba que produzca más gas; es lo que el modelo aprendió de los pozos anteriores."))
        if tech:
            st.markdown("**Sin Rastro (SQL sobre las tablas tal como vienen):** la consulta que arma la entrada del modelo A. "
                        "Cada cruce está en la consulta: el mes en que arrancó cada pozo, la empresa como se declaró, el texto "
                        "de socios del mapa (el porcentaje se busca después por nombre) y la fractura sumada de la tabla cruda.")
            st.code(modelo.SQL_A.strip(), language="sql")
            st.markdown("**Con Rastro (SPARQL):** la misma entrada, pedida en conceptos del diccionario. Los cruces y las reglas "
                        "están definidos una vez en Rastro; la consulta trae además la regla y la evidencia de cada dato.")
            st.code(modelo.SPARQL_B.strip(), language="sparql")
            st.caption("Código del modelo: lab/gas/modelo.py.")


def registros(pozo):
    """The source records of a well's prediction, read from Rastro (question 13): the reported fracturings
    and the gas months, each one with its identifier or its month."""
    from dominio import run
    query = (Path("/ontology/energia/queries") / "cq13.rq").read_text().replace('"166133"', f'"{pozo}"')
    columns, rows = run(query, "energia")
    return pd.DataFrame(rows, columns=columns)


ETIQUETAS = {"grupo": ("Operadora", ""), "area": ("Concesión", ""), "pct": ("Participación de la operadora", "%"),
             "profundidad": ("Profundidad vertical", "m"),
             **{k: (v[0][0].upper() + v[0][1:], v[1]) for k, v in modelo.FRACTURA.items()}}


def variable_label(variable):
    label, unit = ETIQUETAS[variable]
    return f"{label} ({unit})" if unit else label


def walkthrough_config():
    from dominio import load_config
    return load_config("/app/dominios/energia.yaml")["ejemplo_lab"]


def select_well(config, key="energia_lab_selected_well"):
    """One selection drives the walkthrough and the existing prediction comparison."""
    b = datos()[1]
    test = b[b.inicio >= modelo.PRUEBA]
    options = test.idpozo.astype(str).tolist()
    example = str(modelo.pozo_ejemplo(b))
    labels = {str(row.idpozo): f"{row.idpozo} · {modelo.concesion(row.areaNombre if isinstance(row.areaNombre, str) else row.area)}"
              for row in test.itertuples()}
    return st.selectbox(config["ui"]["well_selector"], options,
                        index=options.index(example), format_func=labels.get, key=key)


@st.cache_data(ttl=15, show_spinner=False)
def published_snapshot():
    """Read a single run and its complete persisted input snapshot without writing to the database."""
    import psycopg
    user = answer.DOMAINS["energia_lab"]["readers"]["B"]
    with psycopg.connect(host="postgres", port=5432, dbname=os.environ["PG_DB"],
                         user=user, password=user,
                         options="-c default_transaction_read_only=on") as conn:
        def frame(sql, params=None):
            cursor = conn.execute(sql, params)
            return pd.DataFrame(cursor.fetchall(), columns=[column.name for column in cursor.description])
        runs = frame("SELECT id, version, fecha FROM lab_gas.corrida WHERE vigente ORDER BY fecha DESC LIMIT 1")
        if runs.empty:
            return None
        run = runs.iloc[0].to_dict()
        return {"run": run,
                "inputs": frame("SELECT * FROM lab_gas.entrada WHERE corrida = %s", (run["id"],)),
                "predictions": frame("SELECT * FROM lab_gas.prediccion WHERE corrida = %s", (run["id"],)),
                "contributions": frame("SELECT * FROM lab_gas.aporte WHERE corrida = %s", (run["id"],))}


def show_run_status(pozo, config):
    _, b, _, r, *_ = datos()
    ui = config["ui"]
    snapshot = published_snapshot()
    result = compare_run(b, r["B"], pozo, snapshot, modelo.version())
    if snapshot is None:
        result["run_id"] = ""
        st.info(ui["run_missing"])
        return result
    run = snapshot["run"]
    result["run_id"] = run["id"]
    st.caption(ui["run_identity"].format(run=run["id"], date=run["fecha"],
                                         published=run["version"], current=modelo.version()))
    failed = [ui["checks"][name] for name, passed in result["checks"].items() if not passed]
    if failed:
        st.warning(ui["run_different"].format(checks=", ".join(failed)))
    else:
        st.success(ui["run_matched"])
    st.caption(ui["run_scope"])
    return result


def _selected_row(pozo):
    a, b, *_ = datos()
    if pozo is None:
        pozo = modelo.pozo_ejemplo(b)
    row = b[b.idpozo.astype(str) == str(pozo)].iloc[0]
    raw = a[a.idpozo.astype(str) == str(pozo)].iloc[0]
    return row, raw


def input_rows(pozo, config):
    row, raw = _selected_row(pozo)
    r = datos()[3]["B"]
    ui = config["ui"]
    records = []
    for item in config["inputs"]:
        variable = item["variable"]
        original = row[variable]
        effective = r["relleno"][variable] if pd.isna(original) else original
        def display(value):
            return ui["not_reported"] if pd.isna(value) else str(value)
        records.append({ui["columns"]["variable"]: variable_label(variable),
                        ui["columns"]["field"]: item["field"],
                        ui["columns"]["raw"]: display(raw[item["raw"]]),
                        ui["columns"]["concept"]: item["concept"],
                        ui["columns"]["model"]: variable,
                        ui["columns"]["original"]: display(original),
                        ui["columns"]["effective"]: display(effective),
                        ui["columns"]["status"]: " · ".join(ui["statuses"][flag]
                                                                  for flag in value_status(row, variable))})
    return records


def show_input_row(pozo, config, tech=False):
    ui = config["ui"]
    row, _ = _selected_row(pozo)
    st.markdown(ui["input_title"].format(well=row.idpozo))
    st.caption(ui["input_scope"])
    tabla(pd.DataFrame(input_rows(pozo, config)), key="lab_selected_inputs")
    st.caption(ui["availability_scope"])
    st.caption(ui["target"].format(date=f"{row.inicio:%m/%Y}", gas=num(row.gas)))


def current_evidence(pozo, group=None):
    """Read current entity URIs and their actual source records, independently of published results."""
    row, _ = _selected_row(pozo)
    keys = {"location": ["s", "st"], "fracture": ["fr"], "depth": ["tr"]}.get(group, ["s", "fr", "st", "tr"])
    uris = [str(row[key]) for key in keys if pd.notna(row[key]) and str(row[key]).startswith("https://w3id.org/rastro/energia/")]
    if not uris:
        return pd.DataFrame(columns=["dato", "regla", "evidencia", "origen", "identificador", "mes", "cargado"])
    from urllib.parse import quote
    values = " ".join("<" + quote(uri, safe=":/%#-._~") + ">" for uri in uris)
    return sparql_df("""PREFIX energia: <https://w3id.org/rastro/energia#>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT ?dato ?regla ?evidencia ?origen ?identificador ?mes ?cargado WHERE {
  { VALUES ?dato { """ + values + """ } }
  UNION {
    VALUES ?contexto { """ + values + """ }
    ?contexto energia:declaredName ?nombre ; energia:company ?empresa .
    ?dato a energia:CompanyName ; energia:nameInSource ?nombre ; energia:company ?empresa .
  }
  ?dato energia:rule ?regla ; energia:sourceText ?evidencia ; prov:wasDerivedFrom ?origen .
  OPTIONAL { ?origen energia:reportId ?identificador }
  OPTIONAL { ?origen energia:productionMonth ?mes }
  OPTIONAL { ?origen energia:loadedOn ?fechaOrigen }
  OPTIONAL { ?dato energia:loadedOn ?fechaDato }
  BIND(COALESCE(?fechaDato, ?fechaOrigen) AS ?cargado)
} ORDER BY ?dato ?origen""")


def show_source_evidence(pozo, variable, config, key="lab_variable", tech=False):
    from dominio import sql_table
    ui = config["ui"]
    item = next(item for item in config["inputs"] if item["variable"] == variable)
    source = config["sources"][item["source"]]
    columns, rows = sql_table(source["sql"], "energia_lab", approach="B", params=(str(pozo),))
    st.markdown(ui["source_title"].format(variable=variable_label(variable)))
    st.caption(source["note"])
    tabla(pd.DataFrame(rows, columns=columns), key=f"{key}_{pozo}_{variable}_raw")
    if tech:
        st.code(source["sql"], language="sql")
    group = next(name for name, variables in GROUPS.items() if variable in variables)
    tabla(current_evidence(pozo, group).rename(columns=ui["evidence_columns"]), key=f"{key}_{pozo}_{variable}_evidence")


def show_calculation(pozo=None, config=None, tech=False):
    """Explore actual contributions and source records for the shared selected well."""
    config = config or walkthrough_config()
    ui = config["ui"]
    _, b, _, r, *_ = datos()
    row, _ = _selected_row(pozo)
    pozo = row.idpozo
    base, detail = modelo.detalle(b, **modelo.VARIABLES["B"], pozo=pozo)
    pred = float(r["B"]["pred"][b.index.get_loc(row.name)])
    summary = [{ui["summary_part"]: ui["base"], ui["summary_amount"]: round(base, 3)}]
    summary += [{ui["summary_part"]: ui["groups"][group], ui["summary_amount"]:
                 round(sum(item["aporte"] for item in detail if item["variable"] in variables), 3)}
                for group, variables in GROUPS.items()]
    summary.append({ui["summary_part"]: ui["prediction"], ui["summary_amount"]: round(pred, 3)})
    st.markdown(ui["calculation_title"].format(well=pozo))
    tabla(pd.DataFrame(summary), key="lab_grouped_calculation")
    group = st.selectbox(ui["group_selector"], list(GROUPS), format_func=ui["groups"].get, key="lab_explore_group")
    selected = [item for item in detail if item["variable"] in GROUPS[group]]
    table = []
    for item in selected:
        variable = item["variable"]
        original = row[variable]
        table.append({ui["columns"]["variable"]: variable_label(variable),
                      ui["columns"]["original"]: ui["not_reported"] if pd.isna(original) else str(original),
                      ui["columns"]["effective"]: str(item["valor"]),
                      ui["training_mean"]: ui["category"] if item["promedio"] is None else num(item["promedio"], 3),
                      ui["coefficient"]: ui["category"] if item["coeficiente"] is None else f"{item['coeficiente']:.6g}",
                      ui["contribution"]: round(item["aporte"], 6),
                      ui["columns"]["status"]: " · ".join(ui["statuses"][flag] for flag in value_status(row, variable))})
    tabla(pd.DataFrame(table), key="lab_variable_calculation")
    variable = st.selectbox(ui["variable_selector"], GROUPS[group], format_func=variable_label,
                            key=f"lab_explore_variable_{group}")
    with st.container(border=True):
        st.markdown(f"**{ui['source_expander']}**")
        show_source_evidence(pozo, variable, config, tech=tech)
    st.caption(ui["formula_scope"])



def show_well(key, pozo=None):
    """A 2025 well: the prediction without Rastro and with Rastro, side by side. With a well, no selector (for the demo)."""
    a, b, ctx, r, *_, (desde_hasta, dentro) = datos()
    prueba = b[b.inicio >= modelo.PRUEBA]
    etiquetas = {f"{modelo.concesion(x.areaNombre if isinstance(x.areaNombre, str) else x.area)} · {modelo.nombre(x.grupo)} · "
                 f"empezó en {x.inicio:%m/%Y} · pozo {x.idpozo}": x.idpozo for x in prueba.itertuples()}
    ejemplo = modelo.pozo_ejemplo(b)
    inicial = next((i for i, p in enumerate(etiquetas.values()) if p == ejemplo), 0)
    if pozo is None:
        pozo = etiquetas[st.selectbox("Pozo de 2025", list(etiquetas), index=inicial, key=key, help=ayuda("lab_pozo"))]
    ea, eb = modelo.explicacion_a(r, a, pozo), modelo.explicacion_b(r, b, ctx, pozo)
    origen = registros(pozo)
    meses = origen[origen.registro.str.startswith("Gas")].fecha.sort_values()
    fracturas = origen[origen.registro.str.startswith("Fractura")]
    st.markdown(f"Dio **{num(eb['real'])} millones de m³** en sus meses 2 a 7"
                + (f" (declaraciones juradas de {meses.iloc[0][5:7]}/{meses.iloc[0][:4]} a {meses.iloc[-1][5:7]}/{meses.iloc[-1][:4]})"
                   if len(meses) else "") + ".")

    sin, con = st.columns(2, gap="large")
    with sin:
        st.markdown("##### Sin Rastro")
        st.metric("Predicción", f"{num(ea['pred'])} M m³")
        st.caption(f"Un pozo promedio da {num(r['A']['base'])}; cada columna suma o resta:")
        for f in ea["filas"]:
            izq, der = st.columns([4, 1])
            izq.markdown(f"`{f['columna']} = {f['valor']}`")
            der.markdown(f"**{aporte(f['aporte'])}**")
        st.caption("Tres números para un mismo efecto: las tres columnas cambian juntas, pero nada en las tablas lo "
                   "dice. Y si un dato está mal (como el porcentaje del mapa), nada lo marca.")
    with con:
        st.markdown("##### Con Rastro")
        st.metric("Predicción", f"{num(eb['pred'])} M m³")
        st.caption(f"Rango: de {num(max(eb['pred'] + desde_hasta[0], 0))} a {num(eb['pred'] + desde_hasta[1])} millones de m³. "
                   f"En {round(100 * dentro)} de cada 100 pozos de prueba, el gas real cayó dentro de su rango.")
        st.markdown(eb["resumen"])
        for x in eb["factores"]:
            st.markdown(f"**{x['factor']}: {aporte(x['aporte'])}.** {x['por_que']}")
            if x["nota"]:
                st.caption(x["nota"])
        st.markdown("**Lo que respalda la predicción:**")
        for h in eb["hechos"]:
            st.markdown(f"**{h['hecho']}:** {h['valor']}" + (f"  \n:orange[● {h['marca']}]" if h["marca"] else ""))
            with st.popover("¿De dónde sale?"):
                st.markdown(f"**Regla:** {h['regla']}.  \n**Evidencia:** {h['evidencia']}"
                            + (f"  \n**Nombre:** {h['nombre']}" if h.get("nombre") else "")
                            + f"  \n**Fuentes:** {h['fuentes']}.")
                if h["hecho"] == "Fractura" and len(fracturas):
                    st.markdown("**Registros de origen:** " + "; ".join(
                        f"fractura informada n.º {x.cual}, del {x.fecha[8:10]}/{x.fecha[5:7]}/{x.fecha[:4]}, cargada el "
                        f"{x.cargado[8:10]}/{x.cargado[5:7]}/{x.cargado[:4]}" for x in fracturas.itertuples()) + ".")



def show_published(tech):
    """The last run published in Rastro and two questions about its predictions, live."""
    from dominio import run
    columns, rows = run("""PREFIX energia: <https://w3id.org/rastro/energia#>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT ?version ?fecha (COUNT(?p) AS ?predicciones) WHERE {
  ?c a energia:ModelRun ; energia:current true ; energia:modelVersion ?version ; prov:startedAtTime ?fecha .
  ?p prov:wasGeneratedBy ?c } GROUP BY ?version ?fecha""", "energia")
    if not rows:
        st.info("Todavía no hay una corrida publicada: `python3 lab/gas/modelo.py --publicar`.")
        return
    version_modelo, fecha, n = rows[0]
    st.markdown(md(
        f"Cada predicción queda en Rastro como un dato más: con su rango, el aporte de cada factor, la corrida que la "
        f"hizo (versión {version_modelo}, del {str(fecha)[:10]}, {n} predicciones) y los datos de Rastro que usó. Así se le "
        "puede preguntar a Rastro por las predicciones, con una consulta o en palabras en «Preguntar → Mi propia pregunta»."))
    for archivo, titulo in (("cq11", "¿Qué predicciones de 2025 se apoyan en un dato corregido?"),
                            ("cq12", "¿Qué pozos de 2025 se esperan con más gas, y qué los explica?")):
        query = (Path("/ontology/energia/queries") / f"{archivo}.rq").read_text()
        columns, rows = run(query, "energia")
        st.markdown(f"**{titulo}**")
        titulos = {"pozo": "Pozo", "concesion": "Concesión", "gasEsperado": "Gas esperado (M m³)", "dato": "Dato corregido",
                   "regla": "Regla", "desde": "Desde", "hasta": "Hasta", "concesionYOperadora": "Concesión con su operadora",
                   "fractura": "Cómo se fracturó", "profundidad": "Su profundidad"}
        tabla(pd.DataFrame(rows, columns=columns).rename(columns=titulos), key=f"lab_{archivo}")
        if tech:
            st.code(query.strip(), language="sparql")
