"""Pestaña «Rastro Lab» de petróleo y gas: el mismo modelo de gas, con y sin Rastro, y la explicación de
cada predicción lado a lado. El modelo está en lab/gas/modelo.py; acá solo se cargan los datos y se muestra.
"""
import os
import sys

import pandas as pd
import streamlit as st

import answer
from dominio import ayuda, data_version, md, tabla

sys.path.insert(0, "/lab/gas")
import modelo  # noqa: E402

num = modelo.num


def aporte(v):
    return ("+" if v >= 0 else "−") + num(abs(v))


def sparql_df(query):
    columns, rows = answer.run_sparql_table(query, "energia")
    return pd.DataFrame(rows, columns=columns)


@st.cache_data(persist="disk", show_spinner="Entrenando el modelo dos veces…")
def _datos(version):
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
        modelo.al_arrancar(r, b), modelo.entrada(a, b)


def datos():
    """Los datos y los dos modelos. Se guardan en disco y se rehacen si cambian los datos o los mapeos."""
    return _datos(data_version("energia"))


def show_lab(tech):
    st.markdown("#### ¿Cuánto gas va a dar un pozo nuevo?")
    st.markdown(
        "Un modelo predice el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta. "
        "Es **el mismo modelo, entrenado dos veces**: una con las tablas tal como vienen y otra con Rastro. "
        "Rastro no lo hace más preciso: hace que **cada predicción se explique en conceptos de negocio, "
        "con los hechos que la respaldan, y que se pueda comprobar**.")
    a, b, ctx, r, ref, (n_dudosos, n_prueba), tabla_aprendido, pesos, version, (entrada_a, entrada_b, origen) = datos()

    c1, c2, c3 = st.columns(3)
    c1.metric("Error sin Rastro", f"{num(r['A']['error'])} M m³", help=ayuda("lab_error"))
    c2.metric("Error con Rastro", f"{num(r['B']['error'])} M m³", help=ayuda("lab_error"))
    c3.metric("Con un dato corregido", f"{n_dudosos} de {n_prueba}", help=ayuda("lab_dudosos"))
    st.caption(f"Entrenado con {ref['entreno']} pozos que empezaron de {a.inicio.min():%Y} a 2024; probado con {ref['prueba']} de 2025. "
               f"Error medio por pozo, en millones de m³; usar la mediana de cada operadora da {num(ref['operadora'])}.")

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
            f"El modelo explica el {round(100 * r['B']['r2'])} % de la diferencia entre los pozos de 2025. "
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

    show_well(key="lab_pozo")

    with st.expander("¿Cómo se calcula?"):
        st.markdown(md(
            "Es una regresión lineal: la predicción es el gas de un pozo promedio más el aporte de cada variable, "
            "en millones de m³. Las dos versiones usan las mismas ideas de variables (operadora, concesión, "
            "participación y fractura); cambia de dónde salen. Sin Rastro: la empresa como se declara, el código de la concesión y "
            "el porcentaje del texto de socios del mapa. Con Rastro: la operadora unida entre fuentes, la concesión y la "
            "participación corregida, cada una con su regla y su evidencia. La operadora es la del primer mes del pozo, "
            "no la de hoy: usar la de hoy sería usar el futuro. La fractura (rama horizontal, etapas, arena, agua y "
            "presión) es la informada hasta el mes en que arrancó el pozo. El gas que se predice también sale de Rastro "
            "(el gas de los meses 2 a 7 de cada pozo), y coincide con el que calcula el SQL."))
        if tech:
            st.markdown("**Sin Rastro (SQL sobre las tablas tal como vienen):**")
            st.code(modelo.SQL_A.strip(), language="sql")
            st.markdown("**Con Rastro (SPARQL):**")
            st.code(modelo.SPARQL_B.strip(), language="sparql")
            st.caption("Código del modelo: lab/gas/modelo.py.")


def show_well(key, pozo=None):
    """Un pozo de 2025: la predicción sin Rastro y con Rastro, lado a lado. Con pozo, sin selector (para la demo)."""
    a, b, ctx, r, *_ = datos()
    prueba = b[b.inicio >= modelo.PRUEBA]
    etiquetas = {f"{modelo.concesion(x.areaNombre if isinstance(x.areaNombre, str) else x.area)} · {modelo.nombre(x.grupo)} · "
                 f"empezó en {x.inicio:%m/%Y} · pozo {x.idpozo}": x.idpozo for x in prueba.itertuples()}
    ejemplo = modelo.pozo_ejemplo(b)
    inicial = next((i for i, p in enumerate(etiquetas.values()) if p == ejemplo), 0)
    if pozo is None:
        pozo = etiquetas[st.selectbox("Pozo de 2025", list(etiquetas), index=inicial, key=key, help=ayuda("lab_pozo"))]
    ea, eb = modelo.explicacion_a(r, a, pozo), modelo.explicacion_b(r, b, ctx, pozo)
    st.markdown(f"Dio **{num(eb['real'])} millones de m³** en sus meses 2 a 7.")

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
