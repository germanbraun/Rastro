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
import enlaces
import idioma
from .lab_walkthrough import GROUPS, compare_run, value_status
from dominio import ayuda, data_version, md, tabla

sys.path.insert(0, "/lab/gas")
import modelo  # noqa: E402

def num(value, dec=1):
    """A number in the interface's format; in Spanish, the same as modelo.num."""
    return idioma.number(value, dec)


def aporte(value):
    """A contribution with its sign: «+3,9» or «−4,9» (modelo.signo, in the interface's format)."""
    return ("+" if value >= 0 else "−") + num(abs(value))


def sparql_df(query):
    columns, rows = answer.run_sparql_table(query, "energia")
    return pd.DataFrame(rows, columns=columns)


@st.cache_data(persist="disk", show_spinner=False)
def _datos(version, model_version):
    return calcular()


def calcular():
    """The data and the two models, without the cache (docs/slides reads its numbers through app/contraste.py)."""
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
    with st.spinner(idioma.t("lab.datos.spinner")):   # Lab also reads raw tables directly
        return _datos(data_version("energia", modelo.SQL_GAS + modelo.SQL_A), modelo.version())


def show_lab(tech, pozo=None, note=""):
    """The tab: what Lab is, its three numbers, one well without and with Rastro, and when the source changes. The
    inputs, what the model learned and the published run are technical detail. note is show_run_status's line."""
    st.markdown(idioma.t("lab.show_lab.title"))
    st.markdown(idioma.t("lab.show_lab.intro"))
    (a, b, ctx, r, ref, (n_dudosos, n_prueba), tabla_aprendido, pesos, version, (entrada_a, entrada_b, origen),
     _rango) = datos()

    c1, c2, c3 = st.columns(3)
    c1.metric(idioma.t("lab.show_lab.error_without"), f"{num(r['A']['error'])} M m³", help=ayuda("lab_error"))
    c2.metric(idioma.t("lab.show_lab.error_with"), f"{num(r['B']['error'])} M m³", help=ayuda("lab_error"))
    c3.metric(idioma.t("lab.show_lab.corrected"), idioma.t("lab.show_lab.corrected_value", n=n_dudosos, total=n_prueba),
              help=ayuda("lab_dudosos"))
    st.caption(idioma.t("lab.show_lab.trained", train=ref["entreno"], start=f"{a.inicio.min():%Y}", test=ref["prueba"],
                        concession=num(ref["concesion"]), operator=num(ref["operadora"])))

    show_well(key="lab_pozo", pozo=pozo)
    if note and not tech:
        st.caption(note)

    with st.expander(idioma.t("lab.show_lab.change_title"), expanded=False):
        v = version
        st.markdown(md(idioma.t("lab.show_lab.change_text", with_fracturing=v["con_fractura"], late=v["tarde"],
                                months=num(v["meses_mediana"], 0), mean_change=num(v["cambio_medio"]),
                                max_change=num(v["cambio_max"]))))
        impacto = Path("/layer/energia/cambio/impacto.json")
        if impacto.exists():
            i = json.loads(impacto.read_text())
            pozos = ", ".join(e["pozo"] for e in i["esperado"])
            cambio = i["cambiaron"][0] if i["cambiaron"] else None
            change = (idioma.t("lab.show_lab.impact_change", before=num(cambio["antes"]), after=num(cambio["despues"]))
                      if cambio else "")
            st.markdown(md(idioma.t("lab.show_lab.impact_text", record=i["registro"], wells=pozos, change=change)))

    if not tech:
        return
    entrada_a, entrada_b, origen, tabla_aprendido, pesos = model_tables(entrada_a, entrada_b, origen, tabla_aprendido, pesos)
    with st.expander(idioma.t("lab.show_lab.inputs_title"), expanded=False):
        st.markdown(idioma.t("lab.show_lab.inputs_text", n=len(entrada_b)))
        sin_tab, con_tab = st.tabs([idioma.t("lab.show_lab.without_rastro"), idioma.t("lab.show_lab.with_rastro")])
        with sin_tab:
            tabla(entrada_a, key="lab_entrada_a")
            st.caption(idioma.t("lab.show_lab.inputs_raw_note"))
        with con_tab:
            tabla(entrada_b, key="lab_entrada_b")
            st.markdown(idioma.t("lab.show_lab.inputs_origin"))
            tabla(origen, key="lab_origen")

    with st.expander(idioma.t("lab.show_lab.learned_title"), expanded=False):
        weights = "; ".join(f"**{k.lower()}**, {num(v)}" for k, v in pesos.items())   # concept names come from modelo
        st.markdown(md(idioma.t("lab.show_lab.learned_text", r2=round(100 * r["B"]["r2"]),
                                r2_concession=round(100 * ref["r2_concesion"]), weights=weights)))
        tabla(tabla_aprendido, key="lab_aprendido")
        st.caption(idioma.t("lab.show_lab.learned_note"))

    with st.expander(idioma.t("lab.show_lab.published_title"), expanded=False):
        show_published(tech)


def model_tables(entrada_a, entrada_b, origen, aprendido, pesos):
    """The model's tables with their headers in the interface's language (modelo writes them in Spanish); the
    values from the sources and the raw column names stay as they come."""
    use = idioma.t("lab.tables.use")
    entrada_a = entrada_a.assign(uso=entrada_a.uso.map(use))
    entrada_b = entrada_b.set_axis(idioma.t("lab.tables.inputs_columns"), axis=1)
    entrada_b[entrada_b.columns[-1]] = entrada_b[entrada_b.columns[-1]].map(use)
    origen = pd.DataFrame(dict(zip(idioma.t("lab.tables.origin_columns"),
                                   (entrada_b.columns[:-1], idioma.t("lab.tables.origin_concepts"),
                                    idioma.t("lab.tables.origin_sources")))))
    aprendido = aprendido.set_axis(idioma.t("lab.tables.learned_columns"), axis=1)
    pesos = dict(zip(idioma.t("lab.tables.concepts"), pesos.values()))
    return entrada_a, entrada_b, origen, aprendido, pesos


def show_how(tech):
    """«¿Cómo se calcula?», last in the tab; the queries only in the technical view."""
    with st.expander(idioma.t("lab.show_lab.how_title")):
        st.markdown(md(idioma.t("lab.show_lab.how_text")))
        if tech:
            st.markdown(idioma.t("lab.show_lab.how_sql"))
            st.code(modelo.SQL_A.strip(), language="sql")
            st.markdown(idioma.t("lab.show_lab.how_sparql"))
            st.code(modelo.SPARQL_B.strip(), language="sparql")
            st.caption(idioma.t("lab.show_lab.how_code"))


def registros(pozo):
    """The source records of a well's prediction, read from Rastro (question 13): the reported fracturings
    and the gas months, each one with its identifier or its month."""
    from dominio.common import run
    query = (Path("/ontology/energia/queries") / "cq13.rq").read_text().replace('"166133"', f'"{pozo}"')
    columns, rows = run(query, "energia")
    return pd.DataFrame(rows, columns=columns)


UNITS = {"grupo": "", "area": "", "pct": "%", "profundidad": "m", **modelo.FRACTURA}


# The model writes these marks (modelo.marca); the app shows them with the same status mark as every link
MODEL_MARKS = {"marca_ia": "ia", "marca_documento": "persona"}


def mark(text):
    """A fact's mark: a link's review status with the app's one mark, any other note after an orange dot."""
    for model_text, key in MODEL_MARKS.items():
        text = text.replace(modelo.texto(model_text, idioma.lang()), enlaces.label(key))
    return text if text[:1] in "🟠✅" else f"● {text}"


def flags_text(row, variable, ui):
    """A model input's status: observed, imputed or late, and the link mark when its name join waits for a person."""
    return " · ".join(enlaces.label("ia") if flag == "pending" else ui["statuses"][flag]
                      for flag in value_status(row, variable))


def variable_label(variable):
    """A model variable in words; the fracturing labels are modelo's «fractura_<variable>» texts, capitalized."""
    label, unit = idioma.t(f"lab.variable_label.{variable}"), UNITS[variable]
    return f"{label} ({unit})" if unit else label


def walkthrough_config():
    from dominio.common import load_config
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


def show_run_status(pozo, config, tech=True):
    """Whether the published run is the one computed now. The technical view shows it in full; the business view
    shows nothing here and keeps, in result["note"], one line to show under the well when they differ."""
    _, b, _, r, *_ = datos()
    ui = config["ui"]
    snapshot = published_snapshot()
    result = compare_run(b, r["B"], pozo, snapshot, modelo.version())
    if snapshot is None:
        result.update(run_id="", note=ui["run_missing"])
        if tech:
            st.info(ui["run_missing"])
        return result
    run = snapshot["run"]
    failed = [ui["checks"][name] for name, passed in result["checks"].items() if not passed]
    result.update(run_id=run["id"], note=ui["run_different"].format(checks=", ".join(failed)) if failed else "")
    if tech:
        st.caption(ui["run_identity"].format(run=run["id"], date=run["fecha"],
                                             published=run["version"], current=modelo.version()))
        if failed:
            st.warning(result["note"])
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
                        ui["columns"]["status"]: flags_text(row, variable, ui)})
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
    from dominio.common import sql_table
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
                      ui["columns"]["status"]: flags_text(row, variable, ui)})
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
    etiquetas = {idioma.t("lab.show_well.option",
                          concession=modelo.concesion(x.areaNombre if isinstance(x.areaNombre, str) else x.area),
                          operator=modelo.nombre(x.grupo), start=f"{x.inicio:%m/%Y}", well=x.idpozo): x.idpozo
                 for x in prueba.itertuples()}
    ejemplo = modelo.pozo_ejemplo(b)
    inicial = next((i for i, p in enumerate(etiquetas.values()) if p == ejemplo), 0)
    if pozo is None:
        pozo = etiquetas[st.selectbox(idioma.t("lab.show_well.selector"), list(etiquetas), index=inicial, key=key, help=ayuda("lab_pozo"))]
    ea, eb = modelo.explicacion_a(r, a, pozo, lang=idioma.lang()), modelo.explicacion_b(r, b, ctx, pozo, lang=idioma.lang())
    origen = registros(pozo)
    meses = origen[origen.registro.str.startswith("Gas")].fecha.sort_values()
    fracturas = origen[origen.registro.str.startswith("Fractura")]
    months = (idioma.t("lab.show_well.months", first=f"{meses.iloc[0][5:7]}/{meses.iloc[0][:4]}",
                       last=f"{meses.iloc[-1][5:7]}/{meses.iloc[-1][:4]}") if len(meses) else "")
    st.markdown(idioma.t("lab.show_well.actual", gas=num(eb["real"]), months=months))

    sin, con = st.columns(2, gap="large")
    with sin:
        st.markdown(idioma.t("lab.show_well.without_title"))
        st.metric(idioma.t("lab.show_well.prediction"), f"{num(ea['pred'])} M m³")
        st.caption(idioma.t("lab.show_well.base", base=num(r["A"]["base"])))
        for f in ea["filas"]:
            izq, der = st.columns([4, 1])
            izq.markdown(f"`{f['columna']} = {f['valor']}`")
            der.markdown(f"**{aporte(f['aporte'])}**")
        st.caption(idioma.t("lab.show_well.without_note"))
    with con:
        st.markdown(idioma.t("lab.show_well.with_title"))
        st.metric(idioma.t("lab.show_well.prediction"), f"{num(eb['pred'])} M m³")
        st.caption(idioma.t("lab.show_well.range", low=num(max(eb["pred"] + desde_hasta[0], 0)),
                            high=num(eb["pred"] + desde_hasta[1]), inside=round(100 * dentro)))
        st.markdown(eb["resumen"])
        for x in eb["factores"]:
            st.markdown(f"**{x['factor']}: {aporte(x['aporte'])}.** {x['por_que']}")
            if x["nota"]:
                st.caption(x["nota"])
        st.markdown(idioma.t("lab.show_well.facts"))
        for h in eb["hechos"]:
            st.markdown(f"**{h['hecho']}:** {h['valor']}" + (f"  \n:orange[{mark(h['marca'])}]" if h["marca"] else ""))
            with st.popover(idioma.t("lab.show_well.where_from")):
                st.markdown(idioma.t("lab.show_well.rule_evidence", rule=h["regla"], evidence=h["evidencia"])
                            + (idioma.t("lab.show_well.name", name=h["nombre"]) if h.get("nombre") else "")
                            + idioma.t("lab.show_well.sources", sources=h["fuentes"]))
                if h["id"] == "fractura" and len(fracturas):
                    st.markdown(idioma.t("lab.show_well.origin_records", records="; ".join(
                        idioma.t("lab.show_well.origin_record", id=x.cual,
                                 date=f"{x.fecha[8:10]}/{x.fecha[5:7]}/{x.fecha[:4]}",
                                 loaded=f"{x.cargado[8:10]}/{x.cargado[5:7]}/{x.cargado[:4]}")
                        for x in fracturas.itertuples())))



def show_published(tech):
    """The last run published in Rastro and two questions about its predictions, live."""
    from dominio.common import run
    columns, rows = run("""PREFIX energia: <https://w3id.org/rastro/energia#>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT ?version ?fecha (COUNT(?p) AS ?predicciones) WHERE {
  ?c a energia:ModelRun ; energia:current true ; energia:modelVersion ?version ; prov:startedAtTime ?fecha .
  ?p prov:wasGeneratedBy ?c } GROUP BY ?version ?fecha""", "energia")
    if not rows:
        st.info(idioma.t("lab.show_published.missing"))
        return
    version_modelo, fecha, n = rows[0]
    st.markdown(md(idioma.t("lab.show_published.intro", version=version_modelo, date=str(fecha)[:10], n=n)))
    titulos = {name: idioma.t(f"lab.show_published.column_{name}") for name in
               ("pozo", "concesion", "gasEsperado", "dato", "regla", "desde", "hasta", "concesionYOperadora",
                "fractura", "profundidad")}
    for archivo in ("cq11", "cq12"):
        query = (Path("/ontology/energia/queries") / f"{archivo}.rq").read_text()
        columns, rows = run(query, "energia")
        st.markdown(idioma.t(f"lab.show_published.{archivo}"))
        tabla(pd.DataFrame(rows, columns=columns).rename(columns=titulos), key=f"lab_{archivo}")
        if tech:
            st.code(query.strip(), language="sparql")
