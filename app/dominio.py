"""Pantalla de un dominio a partir de su archivo de configuración (app/dominios/<dominio>.yaml).

Las mismas tres pestañas que oncología: Preguntar, Por qué confiar y Preguntas frecuentes,
con los dos modos (negocio por defecto, técnico con el interruptor). Todo lo propio del
dominio (preguntas, columnas, evidencia, tarjetas, escenarios de cambio) está en el YAML.
"""

import base64
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
import sqlparse
import streamlit as st
import yaml

import answer
import logos

PROV = "PREFIX prov: <http://www.w3.org/ns/prov#>\n"


def load_config(path):
    return _load_yaml(path, Path(path).stat().st_mtime)


def read_json(path):
    p = Path(path)
    return _load_json(path, p.stat().st_mtime) if p.exists() else {}


@st.cache_data
def _load_yaml(path, mtime):   # la fecha del archivo es parte de la clave: si cambia, se relee
    return yaml.safe_load(Path(path).read_text())


@st.cache_data
def _ayuda(mtime):
    return yaml.safe_load(Path("/app/ayuda.yaml").read_text()) or {}


def ayuda(key):
    """El texto del ícono «?» de cada parte de la app (app/ayuda.yaml)."""
    p = Path("/app/ayuda.yaml")
    return _ayuda(p.stat().st_mtime).get(key) if p.exists() else None


@st.cache_data
def _load_json(path, mtime):
    return json.loads(Path(path).read_text())


@st.cache_data
def sources(domain):
    ns = answer.DOMAINS[domain]["namespace"]
    _, rows = answer.run_sparql_table(f"""PREFIX {domain}: <{ns}>
        SELECT ?id ?name ?license WHERE {{ ?s a {domain}:DataSource ; {domain}:name ?name ; {domain}:license ?license .
          BIND (STRAFTER(STR(?s), "/source/") AS ?id) }}""", domain)
    return {r[0]: {"name": r[1], "license": r[2]} for r in rows}


@st.cache_data
def run(query, domain):
    return answer.run_sparql_table(query, domain)


def prefixed(query, domain):
    """Agrega los prefijos que la consulta usa: el del dominio siempre, el de PROV-O solo si hace falta."""
    ns = answer.DOMAINS[domain]["namespace"]
    return f"PREFIX {domain}: <{ns}>\n" + (PROV if "prov:" in query else "") + query


def md(text):
    """Texto para st.markdown: «$» es fórmula en Streamlit, y los montos dicen «US$»."""
    return str(text).replace("$", "\\$")


def money(value):
    return f"{float(value):,.0f}".replace(",", ".")


def as_table(columns, rows, cfg, tech, col_sources):
    """La respuesta como tabla: columnas con nombre de negocio y números legibles."""
    formats, names = cfg.get("formatos", {}), cfg.get("columnas", {})
    data = []
    for row in rows:
        line = []
        for c, v in zip(columns, row):
            if v is not None and formats.get(c) in ("dinero", "numero"):
                v = money(v)
            elif v is not None and formats.get(c) == "porcentaje":
                v = f"{float(v) * 100:.0f} %"
            line.append(v)
        data.append(line)
    if tech:
        labels = cfg.get("fuentes", {})
        headers = [f"{c} · {', '.join(labels.get(s, s) for s in col_sources.get(c, []))}" for c in columns]
    else:
        headers = [names.get(c, c) for c in columns]
    return pd.DataFrame(data, columns=headers)


def show_answer(cfg, tech, query, columns, rows, item=None, note=None):
    domain = cfg["domain"]
    info = sources(domain)
    labels = cfg.get("fuentes", {})
    used, col_sources = answer.column_sources(query, domain)
    if tech:
        st.markdown("**Fuentes que usó esta respuesta:** " + " · ".join(f"`{labels.get(s, s)}`" for s in used), help=ayuda("fuentes_respuesta"))
    else:
        names = [info[s]["name"] for s in used if s in info] + (["enlaces de Rastro"] if "rastro" in used else [])
        st.markdown("**Fuentes:** " + ", ".join(names), help=ayuda("fuentes_respuesta"))
    if not rows:
        st.info("La consulta no devolvió resultados.")
    else:
        table, config = logos.with_logos(as_table(columns, rows, cfg, tech, col_sources), columns)
        st.dataframe(table, hide_index=True, use_container_width=True, column_config=config)
        if item and item.get("mapa"):
            show_map(domain)
        st.caption(f"{len(rows)} fila{'s' if len(rows) != 1 else ''}."
                   + (" La evidencia está en «¿De dónde sale la respuesta?»." if item and item.get("evidencia") else ""))

    with st.expander("¿De dónde sale la respuesta?"):
        evidence = (item or {}).get("evidencia")
        if not tech:
            st.markdown("**Dónde buscó Rastro:**")
            for s in used:
                if s == "rastro":
                    st.markdown(f"- **{cfg.get('nota_rastro', 'Los enlaces de Rastro')}**")
                elif s in info:
                    st.markdown(f"- **{info[s]['name']}** · licencia: {info[s]['license']}")
            if item and item.get("ventaja"):
                st.markdown("**Qué aportó Rastro:** " + md(item["ventaja"]))
            if item and item.get("definicion"):
                st.markdown("La regla está escrita una sola vez, en el **diccionario de negocio**, y vale para "
                            "todas las preguntas que la usan.")
            if evidence:
                st.markdown(f"**{md(evidence['texto'])}**")
                ev_cols, ev_rows = run(prefixed(evidence["query"], domain), domain)
                for r in ev_rows:
                    st.markdown("- " + md(evidence["formato"].format(**dict(zip(ev_cols, r)))))
                st.caption("Cada respuesta se puede auditar: la evidencia dice qué dice cada fuente y con qué regla "
                           "se unieron.")
            st.caption("Para ver la consulta y el SQL, active «Ver detalles técnicos» en la barra lateral.")
            return
        if note:
            st.caption(note)
        st.markdown("**1. La consulta**, sobre los conceptos de Rastro (SPARQL):")
        st.code(query, language="sparql")
        st.markdown("**2. El SQL que Rastro generó y ejecutó en Postgres** (lo traduce Ontop con los mapeos):")
        sql = None
        try:
            sql = sqlparse.format(answer.ontop_sql(query, domain), reindent=True, keyword_case="upper", indent_width=2)
            st.code(sql, language="sql")
        except requests.RequestException:
            st.caption("Ontop no devolvió la traducción.")
        explain(query, sql, domain, item)
        st.markdown("**3. Las fuentes:**")
        for s in used:
            if s == "rastro":
                st.markdown(f"- 🐘 **Enlaces de Rastro**: {cfg.get('nota_rastro', '')}")
            elif s in info:
                st.markdown(f"- 🐘 **{info[s]['name']}** · licencia: {info[s]['license']}")
        if item and item.get("definicion"):
            st.markdown("**4. La regla de negocio, en la ontología.** Ningún mapeo la asigna: Ontop la deduce.")
            st.code(item["definicion"], language="turtle")
        if evidence:
            st.markdown("**4. La evidencia**, pedida al grafo"
                        + (" (cada enlace es una entidad PROV-O, con la fuente de la que se derivó):"
                           if "prov:" in evidence["query"] else ":"))
            ev_query = prefixed(evidence["query"], domain)
            st.code(ev_query, language="sparql")
            ev_cols, ev_rows = run(ev_query, domain)
            st.dataframe(pd.DataFrame(ev_rows, columns=ev_cols), hide_index=True, use_container_width=True)


def explain(query, sql, domain, item=None):
    """«Explicame la consulta»: las preguntas de ejemplo traen su explicación guardada; las propias
    se explican en vivo si hay un LLM configurado."""
    key = f"explain_{abs(hash(query))}"
    stored = (item or {}).get("explicacion")
    available, _ = llm_status()
    if st.button("💬 Explicame la consulta", key=f"{key}_boton", disabled=not stored and not available,
                 help=None if stored or available else "Para explicar preguntas propias hace falta un LLM."):
        st.session_state[key] = stored
        if not stored:
            with st.spinner("El LLM está leyendo la consulta..."):
                st.session_state[key] = answer.explain_query(query, sql, domain)
    if st.session_state.get(key):
        st.info(md(st.session_state[key]))


# La consola SPARQL de la vista técnica: dónde están las consultas de ejemplo y el puerto que se
# abre en la computadora para otras herramientas
CONSOLE = {"oncologia": ("/ontology/queries", 8080), "proveedores": ("/ontology/proveedores/queries", 8081),
           "energia": ("/ontology/energia/queries", 8082)}


# Instancias de ejemplo para «Así se ve un dato del grafo»: una por clase importante de cada dominio
INSTANCES = {
    "energia": {
        "Una concesión: Loma Campana": "https://w3id.org/rastro/energia/concession/LCAM",
        "Una empresa: YPF": "https://w3id.org/rastro/energia/company/YPF",
        "Una participación (enlace con evidencia): Chevron en Loma Campana": "https://w3id.org/rastro/energia/stake/LCAM/CHEVRON",
        "La operadora de un pozo (enlace con evidencia): pozo 107709": "https://w3id.org/rastro/energia/operatorlink/107709",
        "La producción de un pozo en 2025": "https://w3id.org/rastro/energia/production/e2d7b974a6ee583249613016f6a495a9",
        "Un posible venteo visto por satélite": "https://w3id.org/rastro/energia/venting/sensoresremotos_venteos_detectados.61105",
        "Dónde cae ese venteo (enlace con evidencia)": "https://w3id.org/rastro/energia/locationlink/sensoresremotos_venteos_detectados.61105",
    },
    "proveedores": {
        "Un grupo: Leidos": "https://w3id.org/rastro/proveedores/group/549300IUTGTP6EJP8124",
        "Un proveedor: la SAIC de hoy": "https://w3id.org/rastro/proveedores/supplier/MMLKPW9JLX64",
        "Por qué ese proveedor es de su grupo (enlace con evidencia)": "https://w3id.org/rastro/proveedores/link/group/MMLKPW9JLX64",
        "Un contrato": "https://w3id.org/rastro/proveedores/contract/CONT_AWD_HHSN261200800001E_7529_-NONE-_-NONE-",
    },
    "oncologia": {
        "Un fármaco: trastuzumab": "https://w3id.org/rastro/drug/CHEMBL1201585",
        "Un ensayo": "https://w3id.org/rastro/trial/NCT00021255",
        "Por qué un ensayo prueba un fármaco (enlace con evidencia)": "https://w3id.org/rastro/link/NCT00003440/CHEMBL1201585",
    },
}
ONTOLOGY_FILE = {"energia": "/ontology/energia/energia.ttl", "proveedores": "/ontology/proveedores/proveedores.ttl",
                 "oncologia": "/ontology/rastro.ttl"}
PROV_NS, RDF_TYPE = "http://www.w3.org/ns/prov#", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"


@st.cache_data
def labels(domain):
    """Las etiquetas en español del diccionario: término → «palabras de negocio»."""
    import rdflib
    g = rdflib.Graph().parse(ONTOLOGY_FILE[domain])
    return {str(s): str(o) for s, o in g.subject_objects(rdflib.RDFS.label)}


def short_iri(iri, domain):
    ns = answer.DOMAINS[domain]["namespace"]
    return (iri.replace(ns, f"{domain}:").replace(PROV_NS, "prov:").replace(RDF_TYPE, "a")
            .replace("https://w3id.org/rastro/", "rastro:"))


# «Diccionario, enlaces y mapeos» (vista técnica): las piezas de Rastro que usa la demo en 3 pasos.
# Los enlaces se leen en vivo de las tablas de Rastro; los mapeos, del archivo R2RML del dominio.
PIECES = {
    "energia": {
        "mapeos": "/mappings/energia.r2rml.ttl",
        "enlaces": [
            ("Paso 1 · Los socios de cada concesión, separados del texto del mapa",
             """SELECT c.nombre AS concesion, e.nombre AS socia, p.porcentaje, p.texto AS evidencia
                FROM energia.participacion p JOIN energia.concesion c USING (id_concesion) JOIN energia.empresa e USING (empresa_id)
                WHERE c.nombre IN ('LOMA CAMPANA', 'LA AMARGA CHICA', 'BANDURRIA SUR') ORDER BY 1, 3 DESC"""),
            ("Paso 1 · La misma empresa, escrita distinto en cada fuente",
             """SELECT n.fuente, n.nombre AS nombre_en_la_fuente, e.nombre AS empresa, n.regla
                FROM energia.empresa_nombre n JOIN energia.empresa e USING (empresa_id)
                WHERE e.nombre IN ('COMPAÑIA GENERAL DE COMBUSTIBLES', 'CHEVRON', 'PLUSPETROL') ORDER BY 3, 1, 2"""),
            ("Paso 2 · Quién opera cada pozo (pozos donde el padrón dice otra cosa)",
             """SELECT o.idpozo AS pozo, e.nombre AS operadora, o.empresa_padron AS segun_el_padron, o.regla, o.evidencia
                FROM energia.operador_pozo o JOIN energia.empresa e USING (empresa_id)
                WHERE o.empresa_padron IS NOT NULL AND upper(o.empresa_padron) NOT LIKE upper(left(e.nombre, 6)) || '%'
                ORDER BY o.idpozo LIMIT 6"""),
            ("Paso 3 · En qué concesión cae cada posible venteo (La Calera)",
             """SELECT v.id AS venteo, v.fecha, v.satelite, c.nombre AS concesion, v.evidencia
                FROM energia.venteo v JOIN energia.concesion c USING (id_concesion)
                WHERE v.tipo = 'detectado' AND c.nombre = 'LA CALERA' ORDER BY v.fecha DESC LIMIT 6"""),
        ],
        "mapas": [("Paso 1 · Participación, nombres de empresa y producción", ["Stake", "CompanyName", "WellProductionAmounts"]),
                  ("Paso 2 · La operadora de cada pozo", ["OperatorLink"]),
                  ("Paso 3 · El venteo y su concesión", ["DetectedVenting", "LocationLink"])],
    },
    "proveedores": {
        "mapeos": "/mappings/proveedores.r2rml.ttl",
        "enlaces": [
            ("Pasos 1 y 2 · Las empresas del grupo Leidos, con la evidencia de cada una",
             """SELECT s.name AS proveedor, sg.matrix_name AS matriz_en_usaspending, g.name AS grupo, sg.rule AS regla, sg.source_text AS evidencia
                FROM proveedores.supplier_group sg JOIN proveedores.supplier s ON s.uei = sg.supplier_uei
                JOIN proveedores.group_company g USING (group_id)
                WHERE g.name LIKE 'LEIDOS%' OR s.uei = 'MMLKPW9JLX64' ORDER BY g.name, s.name LIMIT 8"""),
        ],
        "mapas": [("Pasos 1 y 2 · Proveedor, grupo y el enlace con su evidencia", ["SupplierGroup", "GroupLink"])],
    },
    "oncologia": {
        "mapeos": "/mappings/rastro.r2rml.ttl",
        "enlaces": [
            ("Qué escribió cada ensayo y qué fármaco reconoció Rastro (trastuzumab)",
             """SELECT t.nct_id AS ensayo, t.intervention AS lo_que_escribio_el_ensayo, t.matched AS coincidio_con,
                       d.pref_name AS farmaco, t.rule AS regla
                FROM linking.trial_drug t JOIN linking.drug d ON d.chembl_id = t.parent_chembl_id
                WHERE d.pref_name = 'TRASTUZUMAB' AND lower(t.intervention) NOT LIKE '%trastuzumab%' ORDER BY t.nct_id LIMIT 8"""),
        ],
        "mapas": [("El ensayo prueba un fármaco, con su evidencia", ["TrialDrug", "DrugLink"])],
    },
}


def sql_table(query, domain):
    """Una consulta de solo lectura sobre las tablas de enlaces de Rastro."""
    import psycopg
    user = answer.DOMAINS[domain]["readers"]["D"]
    with psycopg.connect(answer.READER.format(user) % os.environ["PG_DB"]) as conn:
        cur = conn.execute(query)
        return [c.name for c in cur.description], cur.fetchall()


def mapping_blocks(path, names):
    """Los TriplesMap pedidos, tal como están en el archivo R2RML."""
    text = Path(path).read_text()
    blocks = {}
    for m in re.finditer(r"^<#(\w+)> a rr:TriplesMap ;.*?(?=^<#|\Z)", text, re.S | re.M):
        blocks[m.group(1)] = m.group(0).strip()
    return [blocks[n] for n in names if n in blocks]


def ontology_doc(domain):
    """El diccionario como documentación (al estilo de WIDOCO): clases, relaciones y atributos, con su
    etiqueta, su descripción y entre qué clases van."""
    import rdflib
    from rdflib.namespace import OWL, RDF, RDFS
    g = rdflib.Graph().parse(ONTOLOGY_FILE[domain])
    ns = answer.DOMAINS[domain]["namespace"]

    def name(x):
        return short_iri(str(x), domain) if x else ""

    def text(x, prop):
        return " ".join(str(o) for o in g.objects(x, prop))

    sections = []
    for title, kind in [("Clases", OWL.Class), ("Relaciones (entre entidades)", OWL.ObjectProperty),
                        ("Atributos (datos simples)", OWL.DatatypeProperty)]:
        rows = []
        for s in sorted(set(g.subjects(RDF.type, kind)), key=str):
            if not str(s).startswith(ns):
                continue
            row = {"Término": name(s), "En el diccionario": text(s, RDFS.label), "Descripción": text(s, RDFS.comment)}
            if kind == OWL.Class:
                row["Es un tipo de"] = ", ".join(name(o) for o in g.objects(s, RDFS.subClassOf) if isinstance(o, rdflib.URIRef))
            else:
                row["De"] = ", ".join(name(o) for o in g.objects(s, RDFS.domain))
                row["A"] = ", ".join(name(o) for o in g.objects(s, RDFS.range))
            rows.append(row)
        sections.append((title, rows))
    return sections


def show_pieces(domain, diagram=None):
    """La pestaña técnica «Diccionario, enlaces y mapeos»."""
    pieces = PIECES.get(domain, {})
    st.markdown("### El diccionario (la ontología)", help=ayuda("ontologia"))
    st.caption(f"Documentación generada del archivo de la ontología (`{ONTOLOGY_FILE[domain].replace('/ontology/', 'ontology/')}`), "
               "como la que arman herramientas de documentación de ontologías (por ejemplo, WIDOCO).")
    if diagram and Path(f"/app/{diagram}.svg").exists():
        with st.expander("El diccionario dibujado", expanded=False):
            svg = base64.b64encode(Path(f"/app/{diagram}.svg").read_bytes()).decode()
            st.markdown(f'<img src="data:image/svg+xml;base64,{svg}" style="width:100%">', unsafe_allow_html=True)
    for title, rows in ontology_doc(domain):
        with st.expander(f"{title} ({len(rows)})", expanded=title == "Clases"):
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                         column_config={"Descripción": st.column_config.TextColumn(width="large")})
    if pieces.get("enlaces"):
        st.markdown("### Entity linking: algunos enlaces que usa la demo", help=ayuda("enlaces"))
        st.caption("Registros reales de las tablas de enlaces de Rastro: qué decía cada fuente, qué decidió Rastro y con qué regla.")
        for title, query in pieces["enlaces"]:
            st.markdown(f"**{title}**")
            try:
                cols, rows = sql_table(query, domain)
                st.dataframe(pd.DataFrame(rows, columns=cols), hide_index=True, use_container_width=True)
            except Exception as e:
                st.warning(f"No se pudo leer: {str(e)[:200]}")
            with st.expander("La consulta"):
                st.code(sqlparse.format(query, reindent=True, keyword_case="upper"), language="sql")
    if pieces.get("mapas"):
        st.markdown("### Mapeos (R2RML): los que usa la demo", help=ayuda("mapeos"))
        st.caption(f"Cómo se traduce cada tabla al diccionario, tal como está en `{pieces['mapeos'].lstrip('/')}`. "
                   "Si una fuente cambia, se arregla acá.")
        for title, names in pieces["mapas"]:
            with st.expander(title):
                st.code("\n\n".join(mapping_blocks(pieces["mapeos"], names)), language="turtle")


def dot_text(text, n=24):
    text = str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return text if len(text) <= n else text[:n - 1] + "…"


def instance_graph(iri, rows, domain):
    """La instancia como grafo: burbujas para las entidades, rectángulos para los datos simples
    (textos, números, fechas) y flechas con el nombre de negocio de cada propiedad."""
    ns, names = answer.DOMAINS[domain]["namespace"], labels(domain)
    linked = [o for p, o in rows if o.startswith("http") and p != RDF_TYPE]
    named = {}
    if linked:
        values = " ".join(f"<{o}>" for o in set(linked))
        named = dict(run(f"SELECT ?o ?n WHERE {{ VALUES ?o {{ {values} }} ?o <{ns}name> ?n }}", domain)[1])
    own = next((o for p, o in rows if p == f"{ns}name"), None)
    # En estrella: la entidad al centro y cada propiedad alrededor
    lines = ['digraph {', 'layout=twopi; root=n0; ranksep=0.75; overlap=false; bgcolor="transparent";',
             'node [fontname="Helvetica", fontsize=22, margin="0.08,0.04"]; edge [fontname="Helvetica", fontsize=18, color="#7A8699", fontcolor="#7A8699"];',
             f'n0 [label="{dot_text(own or short_iri(iri, domain))}\\n{dot_text(short_iri(iri, domain), 34)}", shape=ellipse, '
             'style=filled, fillcolor="#2F6FB5", fontcolor="white", penwidth=0];']
    for k, (p, o) in enumerate(rows, start=1):
        if p == RDF_TYPE:
            lines.append(f'n{k} [label="{dot_text(names.get(o, short_iri(o, domain)))}\\n(clase)", shape=ellipse, '
                         'style="filled,dashed", fillcolor="#FFF3E6", color="#FF8C42"];')
            edge = "es un/a"
        elif o.startswith("http"):
            lines.append(f'n{k} [label="{dot_text(named.get(o) or short_iri(o, domain))}", shape=ellipse, '
                         'style=filled, fillcolor="#DCEBFA", color="#2F6FB5"];')
            edge = names.get(p) or short_iri(p, domain)
        else:
            lines.append(f'n{k} [label="{dot_text(o)}", shape=box, style="rounded,filled", fillcolor="#F4F6F9", color="#B8C2CF"];')
            edge = names.get(p) or short_iri(p, domain)
        lines.append(f'n0 -> n{k} [label="{dot_text(edge, 22)}"];')
    return "\n".join(lines + ["}"]), [o for o in dict.fromkeys(linked) if o not in names]


def show_instances(domain):
    """Una instancia real del grafo, dibujada como grafo: se puede seguir cada enlace a otra entidad,
    dentro de la app. Debajo, sus propiedades en una tabla y en Turtle."""
    examples = INSTANCES.get(domain)
    if not examples:
        return
    st.markdown("### Así se ve un dato del grafo", help=ayuda("instancia"))
    st.caption("Una entidad real del grafo. Burbuja azul: una entidad; burbuja naranja: su clase en el diccionario; "
               "rectángulo: un dato simple (texto, número o fecha). Cada flecha es una propiedad, con su nombre de "
               "negocio. Los enlaces traen su evidencia y su fuente (PROV-O).")
    key = f"{domain}_instancia"
    chosen = st.selectbox("Empezar por", list(examples), key=key)
    if st.session_state.get(f"{key}_desde") != chosen:      # un ejemplo nuevo vuelve a empezar el recorrido
        st.session_state[f"{key}_desde"], st.session_state[f"{key}_actual"] = chosen, examples[chosen]
    iri = st.session_state[f"{key}_actual"]
    _, rows = run(f"SELECT ?p ?o WHERE {{ <{iri}> ?p ?o }} ORDER BY ?p", domain)
    if not rows:
        st.info("Esta entidad no tiene más datos en el grafo.")
    graph, neighbours = instance_graph(iri, rows, domain)
    st.graphviz_chart(graph, use_container_width=True)
    nav, back = st.columns([4, 1])
    if neighbours:
        go = nav.selectbox("Seguir un enlace (ver esa entidad)", ["—"] + neighbours,
                           format_func=lambda o: o if o == "—" else short_iri(o, domain), key=f"{key}_ir_{iri}")
        if go != "—":
            st.session_state[f"{key}_actual"] = go
            st.rerun()
    if iri != examples[chosen] and back.button("Volver al ejemplo", key=f"{key}_volver"):
        st.session_state[f"{key}_actual"] = examples[chosen]
        st.rerun()
    st.caption(f"IRI: `{iri}`")
    names = labels(domain)
    with st.expander("Las mismas propiedades en una tabla"):
        table = [{"Propiedad": short_iri(p, domain),
                  "En el diccionario": "es un/a" if p == RDF_TYPE else names.get(p, ""),
                  "Valor": (f"{short_iri(o, domain)}" + (f" ({names[o]})" if o in names else "")) if o.startswith("http") else o}
                 for p, o in rows]
        st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
    lines = [f"<{short_iri(iri, domain)}>"]
    for k, (p, o) in enumerate(rows):
        value = short_iri(o, domain) if o.startswith("http") else '"' + o.replace('"', '\\"') + '"'
        value = f"<{value}>" if value.startswith("rastro:") else value
        lines.append(f"    {short_iri(p, domain)} {value}" + (" ." if k == len(rows) - 1 else " ;"))
    with st.expander("La misma instancia en Turtle (el formato estándar de RDF)"):
        st.code("\n".join(lines), language="turtle")
    st.divider()


def sparql_console(domain):
    """Una consola para escribir y ejecutar SPARQL sobre el Ontop del dominio, con el SQL que genera."""
    folder, port = CONSOLE[domain]
    show_instances(domain)
    st.markdown("### Consola SPARQL", help=ayuda("consola"))
    st.caption(f"Corre sobre el Ontop de este dominio. Otras herramientas pueden usar el mismo endpoint: "
               f"`http://localhost:{port}/sparql`.")
    examples = {}
    for f in sorted(Path(folder).glob("*.rq")):
        text = f.read_text()
        title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("#")), f.stem)
        examples[title] = text
    key = f"{domain}_console"
    chosen = st.selectbox("Empezar desde una consulta de ejemplo", ["(en blanco)"] + list(examples),
                          key=f"{key}_ejemplo")
    if st.session_state.get(f"{key}_cargada") != chosen:   # al cambiar de ejemplo, se carga en el editor
        st.session_state[f"{key}_cargada"] = chosen
        st.session_state[f"{key}_texto"] = examples.get(
            chosen, f"PREFIX {domain}: <{answer.DOMAINS[domain]['namespace']}>\nSELECT * WHERE {{ ?s ?p ?o }} LIMIT 10")
    query = st.text_area("Consulta", key=f"{key}_texto", height=280)
    if st.button("Ejecutar", type="primary", key=f"{key}_ejecutar"):
        started = time.time()
        try:
            columns, rows = run(query, domain)
        except Exception as e:  # noqa: BLE001 - el error de Ontop se muestra tal cual
            st.error(str(e).strip()[:2000])
            return
        st.caption(f"{len(rows)} fila{'s' if len(rows) != 1 else ''} en {time.time() - started:.1f} s.")
        st.dataframe(pd.DataFrame(rows, columns=columns), hide_index=True, use_container_width=True)
        with st.expander("El SQL que Ontop generó y ejecutó en Postgres"):
            try:
                st.code(sqlparse.format(answer.ontop_sql(query, domain), reindent=True, keyword_case="upper",
                                        indent_width=2), language="sql")
            except requests.RequestException:
                st.caption("Ontop no devolvió la traducción.")


GEO = "PREFIX geo: <http://www.opengis.net/ont/geosparql#>\n"


def wkt_coords(wkt):
    """Las coordenadas de un WKT simple: POINT → [x, y]; POLYGON → [[x, y], ...]; MULTILINESTRING → [[[x, y], ...], ...]."""
    groups = [[[float(v) for v in pair.split()] for pair in part.split(",")]
              for part in re.findall(r"\(([^()]+)\)", wkt)]
    if wkt.startswith("POINT"):
        return groups[0][0]
    return groups[0] if wkt.startswith("POLYGON") else groups


@st.cache_data(show_spinner="Armando el mapa…")
def map_data(domain):
    concessions = run(prefixed(GEO + """SELECT ?name ?operator ?wkt (COUNT(DISTINCT ?d) AS ?n) (SAMPLE(?why) AS ?reason) WHERE {
        ?c a energia:Concession ; energia:name ?name ; geo:asWKT ?wkt .
        OPTIONAL { ?c energia:operatorOnMap/energia:name ?operator }
        OPTIONAL { ?d a energia:DetectedVenting ; energia:inConcession ?c }
        OPTIONAL { ?c a energia:ConcessionToReview ; energia:reviewReason ?why }
    } GROUP BY ?name ?operator ?wkt""", domain), domain)[1]
    points = run(prefixed(GEO + "SELECT ?wkt WHERE { ?d a energia:DetectedVenting ; geo:asWKT ?wkt }", domain), domain)[1]
    pipes = run(prefixed(GEO + "SELECT ?name ?wkt WHERE { ?p a energia:Pipeline ; energia:name ?name ; geo:asWKT ?wkt }", domain), domain)[1]
    return concessions, points, pipes


def show_map(domain):
    """Concesiones, posibles venteos vistos por satélite y gasoductos de transporte, todo leído de Rastro."""
    import pydeck as pdk
    concessions, points, pipes = map_data(domain)
    polys = [{"contorno": wkt_coords(w), "nombre": n, "operadora": o or "—", "venteos": int(v or 0),
              "revisar": "Para revisar: " + r if r else "",
              "color": [214, 96, 77, 120] if r else ([47, 111, 181, 90] if int(v or 0) else [143, 184, 232, 40])}
             for n, o, w, v, r in concessions]
    dots = [{"pos": wkt_coords(w)} for (w,) in points]
    lines = [{"nombre": n, "trazado": path} for n, w in pipes for path in wkt_coords(w)]
    layers = [
        pdk.Layer("PolygonLayer", polys, get_polygon="contorno", get_fill_color="color", get_line_color=[20, 33, 61, 160],
                  line_width_min_pixels=1, pickable=True),
        pdk.Layer("PathLayer", lines, get_path="trazado", get_color=[245, 166, 35, 230], width_min_pixels=3, pickable=True),
        pdk.Layer("ScatterplotLayer", dots, get_position="pos", get_fill_color=[214, 39, 40, 170], radius_min_pixels=2,
                  get_radius=400),
    ]
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=-38.4, longitude=-68.9, zoom=6.4),
                             tooltip={"html": "<b>{nombre}</b><br>{operadora}<br>{venteos} posibles venteos<br>{revisar}"}),
                    use_container_width=True)
    st.caption("Puntos rojos: posibles venteos vistos por satélite desde 2024. Líneas ámbar: gasoductos de transporte "
               "(ENARGAS). Concesiones en rojo: para revisar, según la regla del diccionario; en azul, con posibles "
               "venteos. Todo sale de Rastro, con geometrías en el estándar de OGC (GeoSPARQL).", help=ayuda("mapa"))


def short(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        return str(len(value))
    return money(value)


def render(cfg_path, tech):
    cfg = load_config(cfg_path)
    domain = cfg["domain"]
    evaluation = read_json(cfg["evaluacion"]) if cfg.get("evaluacion") else {}
    changes = read_json(cfg["cambio"]) if cfg.get("cambio") else {}
    questions = cfg["preguntas"]

    with st.sidebar:
        if tech:
            available, status = llm_status()
            st.subheader("LLM", help=ayuda("llm"))
            st.markdown(("🟢 " if available else "⚪ ") + status)
            st.subheader("Fuentes", help=ayuda("fuentes_barra"))
            for key, info in sources(domain).items():
                st.markdown(f"🐘 **{info['name']}**  \n<small>{info['license']}</small>", unsafe_allow_html=True)
        else:
            st.caption(md(cfg["resumen"]))

    # «Por qué confiar» necesita una evaluación medida; un dominio sin ella no muestra la pestaña
    names = ["Preguntar"] + (["Por qué confiar"] if cfg.get("tarjetas") else []) + ["Preguntas frecuentes"] \
        + (["Consola SPARQL", "Diccionario, enlaces y mapeos"] if tech else [])
    tabs = dict(zip(names, st.tabs(names)))
    ask_tab, trust_tab, faq_tab = tabs["Preguntar"], tabs.get("Por qué confiar"), tabs["Preguntas frecuentes"]
    if tech:
        with tabs["Consola SPARQL"]:
            sparql_console(domain)
        with tabs["Diccionario, enlaces y mapeos"]:
            show_pieces(domain, cfg.get("diagrama", {}).get("archivo"))

    with ask_tab:
        modes = ((["Demo en 3 pasos"] if cfg.get("demo") else []) + ["Una pregunta de ejemplo"]
                 + (["Una pregunta sobre textos"] if cfg.get("texto") else []))
        mode = st.radio("Tipo de pregunta", modes + ["Mi propia pregunta"], help=ayuda("modo"),
                        horizontal=True, label_visibility="visible", key=f"{domain}_mode")
        if mode == "Demo en 3 pasos":
            show_demo(cfg, tech)
        elif mode == "Una pregunta sobre textos":
            show_text_question(cfg, tech)
        elif mode == "Una pregunta de ejemplo":
            # La misma pregunta en las dos vistas; la técnica suma su formulación precisa debajo
            options = {q["simple"]: q for q in questions}
            chosen = st.selectbox("Pregunta", list(options), key=f"{domain}_question", help=ayuda("pregunta"))
            item = options[chosen]
            if tech:
                st.caption("Formulación técnica: " + md(item["tecnica"]))
            if item.get("terminos"):
                with st.expander("¿Qué significa " + ", ".join(item["terminos"]) + "?"):
                    st.markdown("\n".join(f"- **{md(t)}:** {md(m)}" for t, m in item["terminos"].items()))
            query = Path(item["query"]).read_text()
            if st.button("Responder", type="primary", key=f"{domain}_answer"):
                st.session_state[f"{domain}_shown"] = (chosen, query, *run(query, domain))
            shown = st.session_state.get(f"{domain}_shown", (None,))
            if shown[0] == chosen:
                _, query, columns, rows = shown
                if item.get("antes_despues"):
                    before_after(item["antes_despues"])
                show_answer(cfg, tech, query, columns, rows, item,
                            note="Se ejecuta ahora, en vivo, sobre los datos.")
        else:
            available, _ = llm_status()
            question = st.text_area("Pregunta", placeholder=cfg.get("ejemplo_libre", ""), key=f"{domain}_free", help=ayuda("propia"))
            if st.button("Responder", type="primary", disabled=not available or not question.strip(),
                         key=f"{domain}_free_answer"):
                with st.spinner("El LLM está escribiendo la query..."):
                    result = answer.ask_rastro(question, domain)
                if result["query"] is None:
                    st.error("El LLM no logró una query que funcione en tres intentos.")
                else:
                    show_answer(cfg, tech, result["query"], result["columns"], result["rows"],
                                note=f"Intentos: {len(result['attempts'])}.")
            if not available:
                st.info("Para preguntas libres hace falta un LLM. Mientras tanto, pueden usarse las preguntas de ejemplo.")

    if trust_tab:
        with trust_tab:
            trust(cfg, tech, evaluation, changes)

    with faq_tab:
        diagram = cfg.get("diagrama", {})
        show_faq(domain, [(i["pregunta"], md(i["respuesta"]), i.get("tecnico", False)) for i in cfg.get("faq", [])], tech,
                 [(f"arquitectura-{domain}", "De las fuentes del dominio a una capa semántica."),
                  (diagram.get("archivo"), f"El {diagram.get('titulo')}: lo que lee el LLM.")],
                 diagram.get("titulo", "diccionario"))


@st.cache_data
def general_faq(mtime):
    return yaml.safe_load(Path("/app/faq-general.yaml").read_text())


def domain_name(domain):
    return next((d["name"] for d in yaml.safe_load(Path("/app/dominios.yaml").read_text()) if d["id"] == domain), domain)


def show_faq(domain, specific, tech, diagrams, diagram_title="diccionario"):
    """Las preguntas frecuentes: primero las que valen para todos los casos, después las de este caso.
    specific es una lista de (pregunta, respuesta, técnica)."""
    general = general_faq(Path("/app/faq-general.yaml").stat().st_mtime)

    def block(items):
        for question, answer_text in items:
            with st.expander(question):
                st.markdown(answer_text)

    st.markdown("##### Para todos los casos")
    block([(i["pregunta"], md(i["respuesta"])) for i in general if not i.get("tecnico")])
    st.markdown(f"##### De este caso: {domain_name(domain)}")
    block([(q, a) for q, a, t in specific if not t])
    if not tech:
        st.caption("Hay más preguntas para perfiles técnicos: active «Ver detalles técnicos» en la barra lateral.")
        return
    st.markdown("##### Para técnicos, en todos los casos")
    block([(i["pregunta"], md(i["respuesta"])) for i in general if i.get("tecnico")])
    st.markdown(f"##### Para técnicos, de este caso: {domain_name(domain)}")
    with st.expander(f"Cómo está armado Rastro: arquitectura y {diagram_title}"):
        for name, caption in diagrams:
            if not name or not Path(f"/app/{name}.svg").exists():
                continue
            st.caption(caption)
            image = base64.b64encode(Path(f"/app/{name}.svg").read_bytes()).decode()
            st.markdown(f'<img src="data:image/svg+xml;base64,{image}" style="width:100%;margin-bottom:24px">',
                        unsafe_allow_html=True)
    block([(q, a) for q, a, t in specific if t])


def before_after(card):
    """La misma tarjeta en cada momento de la demo: sin Rastro a la izquierda, con Rastro a la derecha."""
    left, right = st.columns(2)
    for col, key, title in [(left, "sin", card.get("titulo_sin", "Sin Rastro")), (right, "con", "Con Rastro")]:
        with col.container(border=True):
            st.caption(title, help=ayuda("sin_rastro" if key == "sin" else "con_rastro"))
            st.markdown(f"### {'⚪' if key == 'sin' else '🟢'} {md(card[key]['valor'])}")
            st.markdown(md(card[key]["detalle"]))


def show_demo(cfg, tech):
    """La demo en tres pasos, todos sobre Leidos: integración, trazabilidad y análisis de textos. Cada paso corre en vivo."""
    domain, steps = cfg["domain"], cfg["demo"]
    key = f"{domain}_demo_step"
    i = st.session_state.get(key, 0)
    st.markdown(" → ".join(f"**{n + 1} · {s['paso']}**" if n == i else f"{n + 1} · {s['paso']}"
                           for n, s in enumerate(steps)))
    step = steps[i]
    st.subheader(step["titulo"], help=ayuda("paso"))
    if step.get("texto"):
        show_text_question(cfg, tech, demo=True)
    else:
        item = next(q for q in cfg["preguntas"] if q["id"] == step["pregunta"])
        st.info(f"**{md(item['simple'])}**")
        if tech:
            st.caption("Formulación técnica: " + md(item["tecnica"]))
        query = Path(item["query"]).read_text()
        columns, rows = run(query, domain)
        if item.get("antes_despues"):
            before_after(item["antes_despues"])
        show_answer(cfg, tech, query, columns, rows, item, note="Se ejecuta ahora, en vivo, sobre los datos.")
    back, _, forward = st.columns([1, 4, 1])
    if i > 0 and back.button("← Anterior", key=f"{key}_back"):
        st.session_state[key] = i - 1
        st.rerun()
    if i < len(steps) - 1 and forward.button("Siguiente →", type="primary", key=f"{key}_next"):
        st.session_state[key] = i + 1
        st.rerun()


def show_text_question(cfg, tech, demo=False):
    """Una pregunta sobre textos: el grafo elige los contratos con una consulta exacta y un asistente de
    IA resume solo sus descripciones en temas, citando cada contrato. El resumen está guardado; los
    contratos y sus montos se leen en vivo."""
    domain = cfg["domain"]
    item = read_json(cfg["texto"])
    st.markdown("**Una pregunta sobre textos**", help=ayuda("texto"))
    st.info(f"**{md(item['simple'])}**")
    if tech:
        st.caption("Formulación técnica: " + md(item["pregunta"]))
    if not demo:
        if st.button("Responder", type="primary", key=f"{domain}_text_answer"):
            st.session_state[f"{domain}_text_shown"] = True
        if not st.session_state.get(f"{domain}_text_shown"):
            return
    query = Path(item["consulta"]).read_text()
    _, rows = run(query, domain)
    if "columnas" in item:   # registros cualesquiera (no contratos): temas que citan registros por su id
        show_records(item, query, rows, tech)
        return
    contracts = {c: (float(m), a, e, d) for c, m, a, e, d in rows}
    if demo and item.get("busqueda_texto"):
        compare_text_search(item, contracts, domain, tech, always=True)
    total = sum(m for m, *_ in contracts.values())
    st.markdown(f"Rastro seleccionó los **{len(contracts)} contratos más grandes** del grupo "
                f"(US\\$ {money(total / 1e6)} millones). Actividades principales:")
    for theme in item["temas"]:
        found = [c for c in theme["contratos"] if c in contracts]
        amount = sum(contracts[c][0] for c in found)
        st.markdown(f"- **{md(theme['tema'])}** · {len(found)} {'contrato' if len(found) == 1 else 'contratos'}, US\\$ {money(amount / 1e6)} millones. "
                    f"{md(theme['detalle'])}  \n<small>{', '.join(found)}</small>", unsafe_allow_html=True)
    if item.get("busqueda_texto") and not demo:
        compare_text_search(item, contracts, domain, tech)
    with st.expander("¿De dónde sale la respuesta?"):
        st.markdown(md(item["como"]))
        if tech:
            st.markdown("**1. La consulta que elige los contratos** (exacta: usa el grupo que arma Rastro):")
            st.code(query, language="sparql")
            st.markdown("**2. Las descripciones que leyó el asistente**, tal como están en el grafo (`proveedores:description`):")
        else:
            st.markdown("**Las descripciones analizadas**, tal como están en la base de contratos:")
        st.dataframe(pd.DataFrame([{"Contrato": c, "Millones de US$": round(m / 1e6, 1), "Agencia": a.title(),
                                    "Empresa": e.title(), "Descripción": d.capitalize()}
                                   for c, (m, a, e, d) in contracts.items()]),
                     hide_index=True, use_container_width=True)
        st.caption(f"Resumen guardado el {item['fecha']}. Los contratos y montos se leen en vivo; si cambian "
                   "los datos, el resumen hay que volver a generarlo.")


def show_records(item, query, rows, tech):
    """La pregunta sobre textos para registros cualesquiera: la consulta devuelve una fila por registro
    (la primera columna es su id), y el resumen guardado los agrupa en temas que los citan."""
    records = {r[0]: r for r in rows}
    st.markdown(md(item["intro"].format(n=len(records))))
    for theme in item["temas"]:
        found = [r for r in theme["registros"] if r in records]
        st.markdown(f"- **{md(theme['tema'])}** · {len(found)} {item['unidad'][0] if len(found) == 1 else item['unidad'][1]}. "
                    f"{md(theme['detalle'])}  \n<small>{', '.join(found)}</small>", unsafe_allow_html=True)
    with st.expander("¿De dónde sale la respuesta?"):
        st.markdown(md(item["como"]))
        if tech:
            st.markdown("**1. La consulta que elige los registros** (exacta, sobre el grafo):")
            st.code(query, language="sparql")
            st.markdown("**2. Los textos que leyó el asistente**, tal como están en el grafo:")
        else:
            st.markdown("**Los textos analizados**, tal como están en la fuente:")
        st.dataframe(pd.DataFrame([list(r) for r in records.values()], columns=item["columnas"]),
                     hide_index=True, use_container_width=True)
        st.caption(f"Resumen guardado el {item['fecha']}. Los registros se leen en vivo; si cambian los datos, "
                   "el resumen hay que volver a generarlo.")


def company(name):
    """«DYNETICS, INC.» → «Dynetics»: el nombre sin la forma legal, para leer en una frase."""
    name = re.sub(r",?\s+(INC|LLC|CORP|CORPORATION|CO|LTD)\.?$", "", name.strip(), flags=re.I)
    return " ".join(w if len(w) <= 3 and w.isupper() else w.capitalize() for w in name.split())


def compare_text_search(item, contracts, domain, tech, always=False):
    """Lo mismo, buscando «Leidos» en los textos en vez de usar el grafo (lo que haría un RAG común)."""
    if not always and not st.toggle("Comparar con una búsqueda por texto", key=f"{domain}_text_search"):
        return
    query = Path(item["busqueda_texto"]).read_text()
    _, rows = run(query, domain)
    found = {c for c, *_ in rows}
    missing = {c: v for c, v in contracts.items() if c not in found}
    lost = [t["tema"] for t in item["temas"] if t["contratos"] and all(c in missing for c in t["contratos"])]
    companies = sorted({company(e) for _, _, e, _ in missing.values()})
    before_after({
        "titulo_sin": "Sin Rastro: búsqueda de «Leidos» en los textos",
        "sin": {"valor": f"{len(contracts) - len(missing)} de {len(contracts)}",
                "detalle": (f"Omite {len(missing)} contratos (US$ {money(sum(m for m, *_ in missing.values()) / 1e6)} M) "
                            f"de empresas del grupo con otra razón social: {', '.join(companies)}."
                            + (f" Se pierden temas completos: {', '.join(lost).lower()}." if lost else ""))},
        "con": {"valor": f"{len(contracts)} de {len(contracts)}",
                "detalle": "Los 40 contratos más grandes del grupo, seleccionados con una consulta exacta."}})
    st.caption("La búsqueda considera la descripción del contrato y el nombre de la empresa, como lo haría una "
               "consulta SQL o un buscador. Rastro identifica esas empresas como parte del grupo porque el grupo "
               "se definió una sola vez, con la evidencia de cada vínculo.")
    if tech:
        st.code(query, language="sparql")


def llm_status():
    import os
    if answer.PROVIDER == "ollama":
        try:
            requests.get(f"{answer.OLLAMA}/api/tags", timeout=3).raise_for_status()
            return True, f"Ollama · {answer.MODEL}"
        except requests.RequestException:
            return False, f"Ollama no responde en {answer.OLLAMA}"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True, f"Claude API · {answer.MODEL}"
    return False, "Sin LLM configurado"


def trust(cfg, tech, evaluation, changes):
    totals = evaluation.get("totals", {})
    consistency = evaluation.get("consistency", {})
    broken = max((sum(n for s, n in changes.get(c["antes"], {}).get("totals", {}).get("B", {}).items() if s not in ("✅", "—"))
                  for c in cfg.get("cambios", [])), default=0)
    numbers = {"c_consistent": totals.get("C", {}).get("consistent", "—"),
               "b_consistent": totals.get("B", {}).get("consistent", "—"),
               "n_consistency": len(consistency), "b_broken": broken,
               "c_correct": totals.get("C", {}).get("correct", "—"), "b_correct": totals.get("B", {}).get("correct", "—"),
               "n_questions": len(evaluation.get("questions", {}))}
    st.markdown("### Por qué confiar", help=ayuda("confiar"))
    st.caption("El mismo asistente de IA, sin Rastro (escribe SQL sobre las bases tal como vienen) y con Rastro.")
    card_help = ["tarjeta_correctas", "tarjeta_consistencia", "tarjeta_cambio", "tarjeta_auditar"]
    for k, (col, card) in enumerate(zip(st.columns(len(cfg["tarjetas"])), cfg["tarjetas"])):
        with col.container(border=True):
            st.markdown(f"**{md(card['titulo'])}**", help=ayuda(card_help[k]) if k < len(card_help) else None)
            st.markdown(f'<p style="font-size:2.4rem;line-height:1.1;margin:0">{card["valor"].format(**numbers)}</p>',
                        unsafe_allow_html=True)
            st.caption(md(card["compara"].format(**numbers)))

    # En modo técnico se suma la línea de base justa: SQL con las tablas de enlaces de Rastro
    names = ({"B": "Sin Rastro", "D": "SQL + enlaces", "C": "Con Rastro"} if tech
             else {"B": "Sin Rastro", "C": "Con Rastro"})
    names = {k: v for k, v in names.items() if all(k in r for r in consistency.values())}
    change_names = {"B": "Sin Rastro", "C": "Con Rastro"}
    simple = {q["id"]: q["simple"] for q in cfg["preguntas"]}
    n = len(evaluation.get("questions", {}))
    # Las tres pruebas, separadas: en la vista técnica, una pestaña cada una, para que elegir una pregunta
    # en una prueba no parezca cambiar las otras
    if tech:
        tab_correct, tab_same, tab_change = st.tabs([f"1 · Correctas ({n} preguntas)",
                                                     f"2 · Misma respuesta de 4 formas ({len(consistency)} preguntas)",
                                                     f"3 · Cuando una base cambia (las {n} preguntas)"])
        with tab_correct:
            if evaluation.get("questions"):
                evaluation_detail(evaluation, totals)
    with tab_same if tech else st.expander(f"Ver las {4 * len(consistency)} respuestas"):
        st.caption(f"{len(consistency)} preguntas, cada una hecha de 4 formas con el mismo significado.")
        table = []
        for qid, row in consistency.items():
            line = {"Pregunta": row["texts"][0] if tech else simple.get(qid, row["texts"][0])}
            for k, title in names.items():
                line[title] = ("✅ " if row[k]["same"] else "❌ ") + " · ".join(short(a) for a in row[k]["answers"])
            table.append(line)
        st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True,
                     column_config={"Pregunta": st.column_config.TextColumn(width="medium")})
        st.caption("✅ la misma respuesta las 4 veces · ❌ cambió según cómo se preguntó. En las preguntas que "
                   "piden una lista, el número es cuántos nombres devolvió.")
        if consistency:
            labels = {qid: simple.get(qid, row["texts"][0]) for qid, row in consistency.items()}
            picked = st.selectbox("Ver las 4 formas de una pregunta", list(labels.values()),
                                  key=f"{cfg['domain']}_consistency")
            qid = next(k for k, v in labels.items() if v == picked)
            row = consistency[qid]
            st.dataframe(pd.DataFrame([{"Cómo se preguntó": t, **{names[k]: short(row[k]["answers"][i])
                                                                    for k in names}}
                                       for i, t in enumerate(row["texts"])]),
                         hide_index=True, use_container_width=True,
                         column_config={"Cómo se preguntó": st.column_config.TextColumn(width="large")})

    with tab_change if tech else st.expander("Ver los escenarios de cambio"):
        scenarios = {c["titulo"]: c for c in cfg.get("cambios", [])}
        st.caption(f"Qué pasa con las {n} preguntas de la evaluación, todas juntas, cuando una base cambia.")
        picked = st.radio("Escenario", list(scenarios), horizontal=True, label_visibility="visible", help=ayuda("escenario"),
                          key=f"{cfg['domain']}_scenario")
        change = scenarios[picked]
        before, after = changes.get(change["antes"]), changes.get(change["despues"])
        st.markdown(md(change["que"]))
        if tech:
            st.code(change["sql"], language="sql")
        if before and after:
            status = {"✅": "igual", "🟡": "distintas, sin aviso", "❌": "con error"}

            def summary(t):
                return " · ".join(f"{v} {status.get(s, s)}" for s, v in sorted(t.items(), key=lambda x: x[0] != "✅"))

            st.markdown("**Antes de arreglar nada:**")
            for col, k in zip(st.columns(2), change_names):
                col.metric(change_names[k], f"{before['totals'][k].get('✅', 0)}/{n}")
                col.caption(summary(before["totals"][k]))
            if "🟡" in before.get("vocabulary", ""):
                st.warning("Rastro avisa: " + md(before["vocabulary"].split(": ", 1)[-1]))
            if tech:
                st.markdown(f"**El arreglo en Rastro: una línea {change.get('donde', 'del mapeo')}**")
                st.code(f"- {change['arreglo'][0]}\n+ {change['arreglo'][1]}", language="diff")
            else:
                st.markdown("**El arreglo en Rastro:** una línea, en la traducción de esa base al diccionario de negocio.")
            st.markdown("**Después del arreglo:**")
            for col, k in zip(st.columns(2), change_names):
                col.metric(change_names[k], f"{after['totals'][k].get('✅', 0)}/{n}")
                col.caption(summary(after["totals"][k]) + ("" if k == "C" else ". Hay que encontrar y reescribir cada consulta."))
            if tech:
                st.markdown("**Pregunta por pregunta**")
                st.dataframe(pd.DataFrame([{"Pregunta": simple.get(qid, qid),
                                            **{f"{change_names[k]}, antes": before["cells"][qid][k] for k in change_names},
                                            **{f"{change_names[k]}, después": after["cells"][qid][k] for k in change_names}}
                                           for qid in before["cells"]]),
                             hide_index=True, use_container_width=True,
                             column_config={"Pregunta": st.column_config.TextColumn(width="medium")})
        st.info("Sin Rastro, cada consulta sabe cómo se llaman las columnas y en qué unidad están los valores: si la "
                "base cambia, hay que encontrar y arreglar cada una. Con Rastro, eso está en un solo lugar.")


def evaluation_detail(evaluation, totals):
    data = evaluation["questions"]
    names = {k: v for k, v in {"B": "Sin Rastro (SQL)", "D": "SQL + enlaces de Rastro", "C": "Con Rastro"}.items()
             if k in totals}
    st.markdown("##### Detalle técnico: las preguntas de la evaluación")
    cols = st.columns(len(names))
    for col, k in zip(cols, names):
        col.metric(names[k], f"{totals.get(k, {}).get('correct', 0)}/{len(data)}")
    if "D" in names:
        st.info("Con las tablas de enlaces de Rastro, el SQL acierta igual: la precisión viene de la integración "
                "hecha una vez. La capa semántica suma que esa integración se mantiene en un solo lugar, la "
                "evidencia de cada enlace y los datos de afuera.")
    chosen = st.selectbox("Pregunta", [e["question"] for e in data.values()], key="proveedores_eval_question")
    entry = next(e for e in data.values() if e["question"] == chosen)

    def fmt(v):
        if v is None:
            return "sin respuesta"
        if isinstance(v, list):
            return ", ".join(v[:10]) + (f" y {len(v) - 10} más" if len(v) > 10 else "")
        return money(v)

    st.markdown(f"**Respuesta correcta:** {md(fmt(entry['reference']))}")
    for col, k in zip(st.columns(len(names)), names):
        with col:
            e = entry.get(k)
            if not e:
                continue
            st.markdown(f"#### {names[k]}")
            st.markdown(("✅ " if e["ok"] else "❌ ") + md(fmt(e.get("answer"))))
            ok = [a for a in e["attempts"] if a["error"] is None]
            if ok:
                q = ok[-1]["query"]
                shown = sqlparse.format(q, reindent=True, keyword_case="upper", indent_width=2) if k in "BD" else q
                st.caption(f"{len(shown.splitlines())} líneas · {len(e['attempts'])} intento"
                           f"{'s' if len(e['attempts']) != 1 else ''}")
                st.code(shown, language="sql" if k in "BD" else "sparql")
