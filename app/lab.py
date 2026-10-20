"""Pestaña «Rastro Lab» de petróleo y gas: el mismo modelo de gas, con y sin Rastro, y la explicación de
cada predicción lado a lado. El modelo está en lab/gas/modelo.py; acá solo se cargan los datos y se muestra.
"""
import os
import sys

import pandas as pd
import streamlit as st

import answer
from dominio import ayuda, data_version, md

sys.path.insert(0, "/lab/gas")
import modelo  # noqa: E402


def num(v, dec=1):
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def aporte(v):
    return ("+" if v >= 0 else "−") + num(abs(v))


@st.cache_data(persist="disk", show_spinner="Entrenando el modelo dos veces…")
def _datos(version):
    import psycopg
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        def sql(query):
            cur = conn.execute(query)
            return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
        gas, a = sql(modelo.SQL_GAS), sql(modelo.SQL_A)
    columns, rows = answer.run_sparql_table(modelo.SPARQL_B, "energia")
    a, b = modelo.preparar(gas, a, pd.DataFrame(rows, columns=columns))
    return a, b, modelo.modelos(a, b), modelo.referencias(a), modelo.dudosos(b)


def datos():
    """Los datos y los dos modelos. Se guardan en disco y se rehacen si cambian los datos o los mapeos."""
    return _datos(data_version("energia"))


def show_lab(tech):
    st.markdown("#### ¿Cuánto gas va a dar un pozo nuevo?")
    st.markdown(
        "Un modelo predice el gas de los primeros meses (del 2 al 7) de un pozo nuevo de shale gas de Vaca Muerta. "
        "Es **el mismo modelo, entrenado dos veces**: una con las tablas tal como vienen y otra con Rastro. "
        "Rastro no lo hace más preciso: hace que **cada predicción se explique en conceptos de negocio, "
        "cada uno con su fuente, y que se pueda comprobar**.")
    a, b, r, ref, (n_dudosos, n_prueba) = datos()

    c1, c2, c3 = st.columns(3)
    c1.metric("Error sin Rastro", f"{num(r['A']['error'])} M m³", help=ayuda("lab_error"))
    c2.metric("Error con Rastro", f"{num(r['B']['error'])} M m³", help=ayuda("lab_error"))
    c3.metric("Con un dato corregido", f"{n_dudosos} de {n_prueba}", help=ayuda("lab_dudosos"))
    st.caption(f"Entrenado con {ref['entreno']} pozos que empezaron en 2023 y 2024; probado con {ref['prueba']} de 2025. "
               f"Error medio en millones de m³ por pozo; usar la mediana de cada operadora da {num(ref['operadora'])}. "
               "Sin Rastro no se puede saber qué predicciones dependen de un dato corregido.")

    prueba = b[b.inicio >= modelo.PRUEBA]
    etiquetas = {f"{(x.areaNombre if isinstance(x.areaNombre, str) else x.area).title()} · {x.grupo.title()} · "
                 f"empezó en {x.inicio:%m/%Y} · pozo {x.idpozo}": x.idpozo for x in prueba.itertuples()}
    inicial = next((i for i, p in enumerate(etiquetas.values()) if p == "166271"), 0)
    pozo = etiquetas[st.selectbox("Pozo de 2025", list(etiquetas), index=inicial, key="lab_pozo", help=ayuda("lab_pozo"))]
    ea, eb = modelo.explicacion_a(r, a, pozo), modelo.explicacion_b(r, b, pozo)
    st.markdown(f"Dio **{num(eb['real'])} millones de m³** en sus meses 2 a 7. "
                f"Un pozo promedio da {num(r['B']['base'])}; cada variable suma o resta a partir de ahí.")

    sin, con = st.columns(2, gap="large")
    with sin:
        st.markdown("##### Sin Rastro")
        st.metric("Predicción", f"{num(ea['pred'])} M m³")
        for f in ea["filas"]:
            izq, der = st.columns([4, 1])
            izq.markdown(f"`{f['columna']} = {f['valor']}`")
            der.markdown(f"**{aporte(f['aporte'])}**")
        st.caption("Columnas y códigos de las tablas. Para saber de dónde sale cada valor hay que leer el SQL; "
                   "si un dato está mal (como un porcentaje del mapa), nada lo dice.")
    with con:
        st.markdown("##### Con Rastro")
        st.metric("Predicción", f"{num(eb['pred'])} M m³")
        for f in eb["filas"]:
            izq, der = st.columns([4, 1])
            valor = f["valor"].title() if f["concepto"] == "Operadora" else f["valor"]
            izq.markdown(f"**{f['concepto']}:** {valor}" +(f"  \n:orange[● {f['marca']}]" if f["marca"] else ""))
            der.markdown(f"**{aporte(f['aporte'])}**")
            with st.popover("¿Por qué?"):
                st.markdown(f"**Regla:** {f['regla']}.  \n**Evidencia:** {f['evidencia']}"
                            + (f"  \n**Nombre:** {f['nombre']}" if f.get("nombre") else "")
                            + f"  \n**Fuentes:** {f['fuentes']}.")
        st.markdown("**Por concepto:** " + "; ".join(f"{k.lower()} {aporte(v)}" for k, v in eb["grupos"].items()) + ".")

    with st.expander("¿Cómo se calcula?"):
        st.markdown(md(
            "Es una regresión lineal: la predicción es el gas de un pozo promedio más el aporte de cada variable, "
            "en millones de m³. La operadora y la concesión cuentan como categorías (un valor por empresa y por "
            "concesión, aprendido con los pozos de 2023 y 2024). Las dos versiones usan las mismas ideas de variables; "
            "cambia de dónde salen. Sin Rastro: la empresa como se declara, el código de la concesión y el porcentaje "
            "del texto de socios del mapa. Con Rastro: la operadora unida entre fuentes, la concesión y la participación "
            "corregida, cada una con su regla y su evidencia. La operadora es la del primer mes del pozo, no la de hoy: "
            "usar la de hoy sería usar el futuro."))
        if tech:
            st.markdown("**Sin Rastro (SQL sobre las tablas tal como vienen):**")
            st.code(modelo.SQL_A.strip(), language="sql")
            st.markdown("**Con Rastro (SPARQL):**")
            st.code(modelo.SPARQL_B.strip(), language="sparql")
            st.caption("Código del modelo: lab/gas/modelo.py.")
