"""Pantalla de un dominio a partir de su archivo de configuración (app/dominios/<dominio>.yaml).

Las mismas tres pestañas que oncología: Preguntar, Por qué confiar y Preguntas frecuentes,
con los dos modos (negocio por defecto, técnico con el interruptor). Todo lo propio del
dominio (preguntas, columnas, evidencia, tarjetas, escenarios de cambio) está en el YAML.
"""

import base64
import hashlib
import io
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


@st.cache_data(ttl=60, show_spinner=False)
def data_version(domain):
    """Cambia cuando cambian los datos (cargas y enlaces) o el diccionario y los mapeos: con ella, las
    respuestas guardadas en disco se vuelven a calcular solo si hace falta."""
    import psycopg
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        # A cluster write invalidates cached answers, including domains with no Lab tables.
        loads = conn.execute("SELECT pg_current_wal_lsn()::text").fetchone()[0]
    cfg = answer.DOMAINS[domain]
    files = [answer.ROOT / path for path in (cfg["method"]["mapping"], cfg["ontology"], cfg["method"]["app"])]
    inserts = ""
    return f"{loads}|{inserts}|" + "|".join(str(f.stat().st_mtime) if f.exists() else "" for f in files)


@st.cache_data(persist="disk", show_spinner=False)
def _run_saved(query, domain, version):
    return answer.run_sparql_table(query, domain)


def run(query, domain):
    """Una consulta sobre Rastro. La respuesta se guarda en disco: sobrevive a que la app se reinicie, y se
    vuelve a calcular si cambian los datos o los mapeos (data_version)."""
    return _run_saved(query, domain, data_version(domain))


@st.cache_resource
def warm_up():
    """Precalentamiento: la primera vez que alguien abre la app, se calculan en segundo plano todas las
    preguntas de ejemplo de los dominios, para que la demo no espere."""
    import threading

    def work():
        for config in sorted(Path("/app/dominios").glob("*.yaml")):
            cfg = yaml.safe_load(config.read_text())
            for q in (validated_questions(cfg) if cfg.get("preguntas") else []):
                try:
                    columns, rows = run(Path(q["query"]).read_text(), cfg["domain"])
                    why = q.get("porque")
                    if why and rows and why["columna"] in columns:   # la primera fila de «¿Por qué este número?»
                        value = str(rows[0][columns.index(why["columna"])]).replace('"', '\\"')
                        run(prefixed(why["query"].replace("{valor}", value), cfg["domain"]), cfg["domain"])
                except Exception:   # noqa: BLE001 - un dominio apagado no frena a los otros
                    continue
        try:   # y los dos modelos de Rastro Lab
            import lab
            lab.datos()
        except Exception:   # noqa: BLE001
            pass

    threading.Thread(target=work, daemon=True).start()
    return True


def prefixed(query, domain):
    """Agrega los prefijos que la consulta usa: el del dominio siempre, el de PROV-O solo si hace falta."""
    ns = answer.DOMAINS[domain]["namespace"]
    return f"PREFIX {domain}: <{ns}>\n" + (PROV if "prov:" in query else "") + query


def tabla(data, hide_index=True, use_container_width=True, column_config=None, key=None, **kwargs):
    """Una tabla. Las celdas cortan el texto largo y no tienen scroll: si hay textos largos, al elegir
    una fila se muestra completa debajo."""
    df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    text = [c for c in df.columns if df[c].dtype == object
            and not df[c].astype(str).str.startswith("data:image").any()]
    long = len(df) > 0 and any(df[c].astype(str).str.len().max() > 60 for c in text)
    args = dict(hide_index=hide_index, use_container_width=use_container_width, column_config=column_config, **kwargs)
    if not long:
        return st.dataframe(df, **args)
    key = key or "tabla_" + hashlib.md5(f"{list(df.columns)}{len(df)}{df.iloc[0].tolist()}".encode()).hexdigest()[:12]
    event = st.dataframe(df, on_select="rerun", selection_mode="single-row", key=key, **args)
    picked = event.selection.rows if event else []
    if picked:
        row = df.iloc[picked[0]]
        with st.container(border=True):
            for c in text:
                if pd.notna(row[c]) and str(row[c]).strip():
                    st.markdown(f"**{str(c).strip()}:** {md(row[c])}")
    else:
        st.caption("Hay textos que no entran en la celda: elija una fila (la casilla de la izquierda) para leerla completa.")
    return event


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
            line.append("—" if v is None or v == "" else v)
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
        st.markdown("**Fuentes que usó esta respuesta:** " + " · ".join(f"`{labels.get(s, s)}`" for s in used),
                    help=ayuda("fuentes_respuesta"))
    else:
        names = [info[s]["name"] for s in used if s in info] + (["enlaces de Rastro"] if "rastro" in used else [])
        st.markdown("**Fuentes:** " + ", ".join(names), help=ayuda("fuentes_respuesta"))
    if not rows:
        st.info("La consulta no devolvió resultados.")
    else:
        table, config = logos.with_logos(as_table(columns, rows, cfg, tech, col_sources), columns)
        tabla(table, hide_index=True, use_container_width=True, column_config=config)
        if item and item.get("mapa"):
            show_map(domain)
        if item and item.get("porque"):
            show_why(domain, item["porque"], columns, rows)
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
        st.markdown("**2. El SQL que Rastro generó y ejecutó en Postgres** (lo traduce Rastro con los mapeos):")
        sql = None
        try:
            sql = sqlparse.format(answer.ontop_sql(query, domain), reindent=True, keyword_case="upper", indent_width=2)
            st.code(sql, language="sql")
        except requests.RequestException:
            st.caption("No se pudo obtener el SQL de esta consulta.")
        explain(query, sql, domain, item)
        st.markdown("**3. Las fuentes:**")
        for s in used:
            if s == "rastro":
                st.markdown(f"- 🐘 **Enlaces de Rastro**: {cfg.get('nota_rastro', '')}")
            elif s in info:
                st.markdown(f"- 🐘 **{info[s]['name']}** · licencia: {info[s]['license']}")
        if item and item.get("definicion"):
            st.markdown("**4. La regla de negocio, en la ontología.** Ningún mapeo la asigna: Rastro la deduce.")
            st.code(item["definicion"], language="turtle")
        if evidence:
            st.markdown("**4. La evidencia**, pedida al grafo"
                        + (" (cada enlace es una entidad PROV-O, con la fuente de la que se derivó):"
                           if "prov:" in evidence["query"] else ":"))
            ev_query = prefixed(evidence["query"], domain)
            st.code(ev_query, language="sparql")
            ev_cols, ev_rows = run(ev_query, domain)
            tabla(pd.DataFrame(ev_rows, columns=ev_cols), hide_index=True, use_container_width=True)


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


# Instancias de ejemplo para «Así se ve un dato del grafo»: una por clase importante de cada dominio
PROV_NS, RDF_TYPE = "http://www.w3.org/ns/prov#", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"


def domain_config(domain):
    """The registry owns each domain's app configuration path."""
    path = answer.DOMAINS[domain].get("method", {}).get("app")
    return load_config(answer.ROOT / path) if path else {}


def technical(domain):
    return domain_config(domain).get("technical", {})


def ontology_file(domain):
    return str(answer.ROOT / answer.DOMAINS[domain]["ontology"])


@st.cache_data
def labels(domain):
    """Las etiquetas en español del diccionario: término → «palabras de negocio»."""
    import rdflib
    g = rdflib.Graph().parse(ontology_file(domain))
    return {str(s): str(o) for s, o in g.subject_objects(rdflib.RDFS.label)}


def short_iri(iri, domain):
    ns = answer.DOMAINS[domain]["namespace"]
    return (iri.replace(ns, f"{domain}:").replace(PROV_NS, "prov:").replace(RDF_TYPE, "a")
            .replace("https://w3id.org/rastro/", "rastro:"))


# «Diccionario, enlaces y mapeos» (vista técnica): las piezas de Rastro que usa la demo en 3 pasos.
# Los enlaces se leen en vivo de las tablas de Rastro; los mapeos, del archivo R2RML del dominio.


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
    g = rdflib.Graph().parse(ontology_file(domain))
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
    pieces = technical(domain).get("pieces", {})
    st.markdown("### El diccionario (la ontología)", help=ayuda("ontologia"))
    st.caption(f"Documentación generada del archivo de la ontología (`{ontology_file(domain).replace('/ontology/', 'ontology/')}`), "
               "como la que arman herramientas de documentación de ontologías (por ejemplo, WIDOCO).")
    if diagram and Path(f"/app/{diagram}.svg").exists():
        with st.expander("El diccionario dibujado", expanded=False):
            svg = base64.b64encode(Path(f"/app/{diagram}.svg").read_bytes()).decode()
            st.markdown(f'<img src="data:image/svg+xml;base64,{svg}" style="width:100%">', unsafe_allow_html=True)
    for title, rows in ontology_doc(domain):
        with st.expander(f"{title} ({len(rows)})", expanded=title == "Clases"):
            tabla(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                         column_config={"Descripción": st.column_config.TextColumn(width="large")})
    if pieces.get("enlaces"):
        st.markdown("### Entity linking: algunos enlaces que usa la demo", help=ayuda("enlaces"))
        st.caption("Registros reales de las tablas de enlaces de Rastro: qué decía cada fuente, qué decidió Rastro y con qué regla.")
        for title, query in pieces["enlaces"]:
            st.markdown(f"**{title}**")
            try:
                cols, rows = sql_table(query, domain)
                tabla(pd.DataFrame(rows, columns=cols), hide_index=True, use_container_width=True)
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


PROV_NAMES = {PROV_NS + "wasDerivedFrom": "se derivó de", PROV_NS + "wasGeneratedBy": "lo generó",
              PROV_NS + "Entity": "Dato con procedencia"}


def instance_graph(iri, rows, domain, title=None):
    """La instancia como grafo (app/grafo.py): burbujas para las entidades, burbujas naranjas para las
    clases, rectángulos para los datos simples y flechas con el nombre de negocio de cada propiedad.
    Devuelve el SVG y las entidades enlazadas, para seguirlas."""
    import grafo
    ns, names = answer.DOMAINS[domain]["namespace"], {**labels(domain), **PROV_NAMES}
    linked = [o for p, o in rows if o.startswith("http") and p != RDF_TYPE]
    named = {}
    if linked:
        values = " ".join(f"<{o}>" for o in set(linked))
        named = dict(run(f"SELECT ?o ?n WHERE {{ VALUES ?o {{ {values} }} ?o <{ns}name> ?n }}", domain)[1])
    own = next((o for p, o in rows if p == f"{ns}name"), None)
    nodes = []
    for p, o in rows:
        prop = "es un/a" if p == RDF_TYPE else names.get(p) or short_iri(p, domain)
        if p == RDF_TYPE:
            nodes.append(("clase", names.get(o) or short_iri(o, domain), short_iri(o, domain), prop))
        elif o.startswith("http"):
            nodes.append(("entidad", named.get(o) or o.rstrip("/").split("/")[-1], short_iri(o, domain), prop))
        else:
            nodes.append(("dato", o, "", prop))
    drawing = grafo.svg((own or title or iri.rstrip("/").split("/")[-1], short_iri(iri, domain)), nodes,
                        width=1500, height=620 + 55 * max(0, len(nodes) - 8), scale=0.95,
                        font="Helvetica, Arial, sans-serif")   # más propiedades, más alto: no se pisan
    return drawing, [o for o in dict.fromkeys(linked) if o not in names]


def show_instances(domain):
    """Una instancia real del grafo, dibujada como grafo: se puede seguir cada enlace a otra entidad,
    dentro de la app. Debajo, sus propiedades en una tabla y en Turtle."""
    examples = technical(domain).get("instances")
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
    title = chosen.split(": ", 1)[-1] if iri == examples[chosen] else None
    graph, neighbours = instance_graph(iri, rows, domain, title)
    st.markdown(f'<img src="data:image/svg+xml;base64,{base64.b64encode(graph.encode()).decode()}" '
                'style="width:100%;border-radius:12px">', unsafe_allow_html=True)
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
        tabla(pd.DataFrame(table), hide_index=True, use_container_width=True)
    lines = [f"<{short_iri(iri, domain)}>"]
    for k, (p, o) in enumerate(rows):
        value = short_iri(o, domain) if o.startswith("http") else '"' + o.replace('"', '\\"') + '"'
        value = f"<{value}>" if value.startswith("rastro:") else value
        lines.append(f"    {short_iri(p, domain)} {value}" + (" ." if k == len(rows) - 1 else " ;"))
    with st.expander("La misma instancia en Turtle (el formato estándar de RDF)"):
        st.code("\n".join(lines), language="turtle")
    st.divider()


def under_the_hood(domain, diagram=None, quality=None):
    """«Bajo el capó» (vista técnica): la consola SPARQL, una instancia del grafo y el diccionario, los
    enlaces y los mapeos, en una sola pestaña."""
    names = ["Consola SPARQL y una instancia", "Diccionario, enlaces y mapeos"] + (["Reglas de calidad (SHACL)"] if quality else [])
    console, pieces, *rules = st.tabs(names)
    with console:
        sparql_console(domain)
    with pieces:
        show_pieces(domain, diagram)
    if quality:
        with rules[0]:
            show_quality_shacl(quality)


def quality_result(quality):
    path = quality.get("archivo") if quality else None
    return read_json(path) if path and Path(path).exists() else None


def show_quality(quality):
    """Las reglas de calidad, en palabras de negocio: qué se comprueba y si se cumple."""
    result = quality_result(quality)
    if not result:
        return
    st.markdown("### Reglas de calidad", help=ayuda("calidad"))
    st.caption(md(quality["intro"]))
    tabla(pd.DataFrame([{"Regla": r["nombre"], "Por qué importa": r["porque"], "Datos revisados": money(r["revisados"]),
                         "Resultado": ("⏳ sin datos revisados" if not r["revisados"] else
                                       "✅ se cumple" if not r["fallas"] else f"⚠️ {money(r['fallas'])} no cumplen"),
                         "Predicciones que los usan": len(r.get("predicciones_afectadas", [])) or ""}
                        for r in result["reglas"]]),
          column_config={"Regla": st.column_config.TextColumn(width="medium"),
                         "Por qué importa": st.column_config.TextColumn(width="large")})
    st.caption(f"Comprobadas el {result['fecha'][8:10]}/{result['fecha'][5:7]}/{result['fecha'][:4]}, sobre los datos de Rastro.")


def show_quality_shacl(quality):
    """Las mismas reglas, en SHACL, con lo que no cumple."""
    result = quality_result(quality)
    if not result:
        st.caption("Todavía no se comprobaron: `docker compose run --rm calidad`.")
        return
    st.markdown("### Reglas de calidad en SHACL", help=ayuda("calidad_shacl"))
    st.caption(md(quality["tecnico"]))
    for r in result["reglas"]:
        mark = "⏳" if not r["revisados"] else "✅" if not r["fallas"] else f"⚠️ {money(r['fallas'])}"
        with st.expander(f"{mark} · {r['nombre']} · {money(r['revisados'])} datos revisados"):
            st.markdown("**La regla, en SHACL**")
            st.code(r["shacl"], language="turtle")
            if r.get("un_dato"):
                good, bad = st.columns(2)
                with good:
                    st.markdown("**Un dato de Rastro, en RDF** ✅ la cumple")
                    st.code(r["un_dato"], language="turtle")
                with bad:
                    st.markdown("**Un dato roto, de ejemplo** ❌")
                    st.code(r["roto"], language="turtle")
                    st.caption("SHACL dice: " + " ".join(r["roto_dice"]))
            if r["ejemplos"]:
                st.markdown("**Lo que no cumple**" + (" (los primeros 10)" if r["fallas"] > 10 else ""))
                tabla(pd.DataFrame([{"Dato": e["dato"], "Qué falla": e["mensaje"],
                                     "Predicciones que lo usan (prov:used)":
                                         ", ".join(p.rsplit("/", 1)[-1] for p in e.get("predicciones", []))}
                                    for e in r["ejemplos"]]))
    st.caption(f"{money(result['triples'])} triples traídos de Rastro con CONSTRUCT. Las reglas están en "
               "el archivo de reglas del dominio; se comprueban con el comando registrado para ese dominio.")


def sparql_console(domain):
    """Una consola para escribir y ejecutar SPARQL sobre el Ontop del dominio, con el SQL que genera."""
    method = answer.DOMAINS[domain]["method"]
    folder, port = str(answer.ROOT / method["queries"]), method["ontop"]["port"]
    show_instances(domain)
    st.markdown("### Consola SPARQL", help=ayuda("consola"))
    st.caption(f"Corre sobre Rastro, en el endpoint SPARQL de este dominio. Otras herramientas pueden usar el mismo endpoint: "
               f"`http://localhost:{port}/sparql`.")
    examples = {}
    for f in sorted(Path(folder).glob("*.rq")):
        text = f.read_text()
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), f.stem)
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
        tabla(pd.DataFrame(rows, columns=columns), hide_index=True, use_container_width=True)
        with st.expander("El SQL que Rastro generó y ejecutó en Postgres"):
            try:
                st.code(sqlparse.format(answer.ontop_sql(query, domain), reindent=True, keyword_case="upper",
                                        indent_width=2), language="sql")
            except requests.RequestException:
                st.caption("No se pudo obtener el SQL de esta consulta.")


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
    config = technical(domain).get("map")
    if not config:
        raise ValueError("This domain has no map configuration")
    concessions, points, pipes = [run(prefixed(config["queries"][key], domain), domain)[1]
                                  for key in ("concessions", "points", "pipes")]
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
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(**technical(domain)["map"]["view_state"]),
                             tooltip={"html": technical(domain)["map"]["tooltip"]}),
                    use_container_width=True)
    st.caption(technical(domain)["map"].get("caption", ""), help=ayuda("mapa"))


def short(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        return str(len(value))
    return money(value)


def validated_questions(cfg):
    """New domains expose only questions whose lifecycle receipts are still current."""
    registered = answer.DOMAINS[cfg["domain"]]
    if not registered.get("method", {}).get("lifecycle"):
        return cfg["preguntas"]
    from lifecycle import question_status, read_state
    state = read_state(registered, answer.ROOT)
    result = []
    for question in cfg["preguntas"]:
        entry = state["questions"].get(question["id"])
        try:
            if entry and question_status(entry, registered, answer.ROOT) == "validated":
                result.append(question)
        except (FileNotFoundError, ValueError):
            continue  # Missing or changed inputs cannot retain validation.
    return result


def render(cfg_path, tech):
    warm_up()
    cfg = load_config(cfg_path)
    domain = cfg["domain"]
    evaluation = read_json(cfg["evaluacion"]) if cfg.get("evaluacion") else {}
    changes = read_json(cfg["cambio"]) if cfg.get("cambio") else {}
    questions = validated_questions(cfg)
    if not questions:
        st.info("Las preguntas de este dominio están pendientes de aprobación o validación.")
        return
    if answer.DOMAINS[domain].get("method", {}).get("lifecycle") and cfg.get("tarjetas"):
        from method import publication_errors
        if publication_errors(answer.DOMAINS[domain], answer.ROOT):
            cfg = {**cfg, "tarjetas": None, "demo": None}
            st.caption("Los resultados de evaluación están pendientes de revisión independiente.")

    with st.sidebar:
        if tech:
            available, status = llm_status()
            st.subheader("LLM", help=ayuda("llm"))
            st.markdown(("🟢 " if available else "⚪ ") + status)
            st.subheader("Fuentes", help=ayuda("fuentes_barra"))
            for info in sources(domain).values():
                st.markdown(f"🐘 **{info['name']}**  \n<small>{info['license']}</small>", unsafe_allow_html=True)
        else:
            st.caption(md(cfg["resumen"]))

    # «Por qué confiar» necesita una evaluación medida; un dominio sin ella no muestra la pestaña
    # Pocas pestañas: la demo, preguntar, por qué confiar y preguntas frecuentes; en la vista técnica, todo
    # lo de adentro (consola, diccionario, enlaces y mapeos) junto en «Bajo el capó»
    names = (["Demo"] if cfg.get("demo") else []) + ["Preguntar"] \
        + (["Por qué confiar"] if cfg.get("tarjetas") else []) + (["Rastro Lab"] if cfg.get("lab") else []) \
        + ["Preguntas frecuentes"] + (["Bajo el capó"] if tech else [])
    tabs = dict(zip(names, st.tabs(names)))
    ask_tab, trust_tab, faq_tab = tabs["Preguntar"], tabs.get("Por qué confiar"), tabs["Preguntas frecuentes"]
    if cfg.get("demo"):
        with tabs["Demo"]:
            show_demo(cfg, tech)
    if cfg.get("lab"):
        with tabs["Rastro Lab"]:
            import lab
            lab.show_lab(tech)
    if tech:
        with tabs["Bajo el capó"]:
            under_the_hood(domain, cfg.get("diagrama", {}).get("archivo"), cfg.get("calidad"))

    with ask_tab:
        modes = ["Una pregunta de ejemplo"] + (["Una pregunta sobre textos"] if cfg.get("texto") else []) \
            + ([cfg["afirmaciones"]["titulo"]] if cfg.get("afirmaciones") else []) \
            + ([cfg["externo"]["titulo"]] if cfg.get("externo") else [])
        mode = st.radio("Tipo de pregunta", modes + ["Mi propia pregunta"], help=ayuda("modo"),
                        horizontal=True, label_visibility="visible", key=f"{domain}_mode")
        if mode == "Una pregunta sobre textos":
            show_text_question(cfg, tech)
        elif cfg.get("externo") and mode == cfg["externo"]["titulo"]:
            show_external(cfg, tech)
        elif cfg.get("afirmaciones") and mode == cfg["afirmaciones"]["titulo"]:
            show_claims(cfg, tech)
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
                if result.get("sin_datos"):
                    st.warning(f"Rastro no tiene ese dato: {result['sin_datos']}")
                elif result["query"] is None:
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


def show_why(domain, why, columns, rows):
    """«¿Por qué este número?»: se elige una fila de la respuesta y se ve la evidencia que hay detrás,
    dibujada como grafo (la fila al centro, cada enlace alrededor) y en una tabla."""
    import grafo
    if why["columna"] not in columns:
        return
    values = list(dict.fromkeys(r[columns.index(why["columna"])] for r in rows if r[columns.index(why["columna"])]))
    with st.container(border=True):
        st.markdown("**¿Por qué este número?**", help="Elija una fila de la respuesta: se ve de dónde sale, enlace por "
                    "enlace, con la fuente y la regla de cada uno.")
        value = st.selectbox("Fila", values, key=f"{domain}_porque_{why['columna']}", label_visibility="collapsed")
        st.markdown(f"**{md(why['titulo'].format(valor=value))}.** {md(why.get('explica', ''))}")
        cols, found = run(prefixed(why["query"].replace("{valor}", str(value).replace('"', '\\"')), domain), domain)
        if not found:
            st.info("No hay evidencia guardada para esta fila.")
            return
        records = [dict(zip(cols, r)) for r in found]

        def fmt(record, template):
            numbers = why.get("numeros", ["parte"])
            return template.format(**{k: (money(v) if k in numbers and v not in (None, "") else (v or "—"))
                                      for k, v in record.items()})

        shown = records[:8]
        nodes = [("entidad", fmt(r, why["nodo"]), fmt(r, why["detalle"]), why["flecha"]) for r in shown]
        if len(records) > len(shown):
            nodes.append(("dato", f"y {len(records) - len(shown)} más", "", why["flecha"]))
        drawing = grafo.svg((str(value), "la fila de la respuesta"), nodes, width=1500,
                            height=620 + 55 * max(0, len(nodes) - 8), scale=0.95, font="Helvetica, Arial, sans-serif")
        st.markdown(f'<img src="data:image/svg+xml;base64,{base64.b64encode(drawing.encode()).decode()}" '
                    'style="width:100%;border-radius:12px">', unsafe_allow_html=True)
        table = pd.DataFrame(records).rename(columns=why.get("columnas", {}))
        tabla(table, hide_index=True, use_container_width=True)


def before_after(card):
    """La misma tarjeta en cada momento de la demo: sin Rastro a la izquierda, con Rastro a la derecha."""
    left, right = st.columns(2)
    for col, key, title in [(left, "sin", card.get("titulo_sin", "Sin Rastro")), (right, "con", "Con Rastro")]:
        with col.container(border=True):
            st.caption(title, help=ayuda("sin_rastro" if key == "sin" else "con_rastro"))
            st.markdown(f"### {'⚪' if key == 'sin' else '🟢'} {md(card[key]['valor'])}")
            st.markdown(md(card[key]["detalle"]))
    if card.get("impacto"):
        st.warning("**Lo que cuesta no integrar:** " + md(card["impacto"]))


def show_demo(cfg, tech):
    """La demo: pocos momentos, cada uno con un título, una frase y algo que corre en vivo. Cada momento es una
    pregunta de ejemplo, el cambio de una base, una predicción de Rastro Lab o una corrección."""
    domain, steps = cfg["domain"], cfg["demo"]
    key = f"{domain}_demo_step"
    i = min(st.session_state.get(key, 0), len(steps) - 1)
    if cfg.get("demo_porque"):
        with st.expander(f"¿Por qué estos {len(steps)} momentos?"):
            st.markdown(md(cfg["demo_porque"]))
    st.markdown(" → ".join(f"**{n + 1} · {s['paso']}**" if n == i else f"{n + 1} · {s['paso']}"
                           for n, s in enumerate(steps)))
    step = steps[i]
    st.subheader(step["titulo"], help=ayuda("paso"))
    if step.get("que_es"):   # los demás casos de uso todavía explican qué es cada paso
        st.markdown(f"**¿Qué es {md(step['paso']).lower()}?** {md(step['que_es'])}")
    if step.get("muestra"):
        st.markdown(md(step["muestra"]))
    tipo = step.get("tipo", "pregunta")
    if tipo == "cambio":
        show_change_short(cfg, read_json(cfg["cambio"]), step.get("escenario"), tech)
    elif tipo == "lab":
        import lab
        lab.show_well(key=f"{key}_pozo", pozo=lab.modelo.pozo_ejemplo(lab.datos()[1]))
    elif tipo == "correccion":
        show_correction(read_json(cfg["correccion"]), tech)
    elif step.get("texto"):
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
    back, _, forward = st.columns([2, 3, 2])
    if i > 0 and back.button("← Anterior", key=f"{key}_back"):
        st.session_state[key] = i - 1
        st.rerun()
    if i < len(steps) - 1 and forward.button("Siguiente →", type="primary", key=f"{key}_next"):
        st.session_state[key] = i + 1
        st.rerun()


def show_change_short(cfg, changes, escenario, tech):
    """Un escenario de la prueba de cambio, corto: cuántas preguntas siguen bien antes y después del arreglo."""
    change = next((c for c in cfg["cambios"] if c["antes"] == escenario), cfg["cambios"][0])
    before, after = changes.get(change["antes"]), changes.get(change["despues"])
    if not (before and after):
        st.info("Falta registrar la prueba de cambio.")
        return
    n = len(before["cells"])
    rotas = before["totals"]["B"].get("❌", 0) + before["totals"]["B"].get("🟡", 0)
    sin_query = before["totals"]["B"].get("—", 0)
    st.markdown(md(change["que"]))
    antes, despues = st.columns(2)
    with antes.container(border=True):
        st.markdown("**Recién cambiada la base**")
        st.markdown(f"Sin Rastro: **{rotas} consultas rotas**, que hay que encontrar")
        st.markdown(f"Con Rastro: **las {n} preguntas fallan juntas**")
        st.caption("Rastro no arranca hasta arreglarlo: falla en voz alta, todo junto.")
    with despues.container(border=True):
        st.markdown("**Para arreglarlo**")
        st.markdown(f"Sin Rastro: **reescribir las {rotas} consultas** a mano")
        st.markdown(f"Con Rastro: **una línea**, y responden las {after['totals']['C'].get('✅', 0)} de {n}")
        st.caption(f"De las {n} preguntas, sin Rastro {sin_query} nunca tuvieron una consulta que funcionara.")
    if tech:
        st.code(f"- {change['arreglo'][0]}\n+ {change['arreglo'][1]}", language="diff")


def show_correction(result, tech):
    """Una corrección, todos los resultados: qué cambia en Rastro Layer y en Rastro Lab al poner la participación
    corregida de una concesión, sin tocar nada más."""
    con, sin = result.get("con"), result.get("sin")
    if not (con and sin):
        st.info("Falta registrar la prueba de la corrección (layer/energia/cambio/correccion.sh registrar).")
        return

    def m3(v):
        return f"{v / 1e6:,.2f} M m³".replace(",", "X").replace(".", ",").replace("X", ".")

    def pct(v):
        return f"{v:g} %".replace(".", ",")

    filas = [   # (dónde, sin la corrección, con la corrección)
        ("Respuesta de Rastro", m3(sin["layer_C"]), m3(con["layer_C"])),
        ("Respuesta con SQL sobre Rastro", m3(sin["layer_D"]), m3(con["layer_D"])),
        ("Respuesta sin Rastro", m3(sin["layer_B"]), m3(con["layer_B"])),
        ("Entrada del modelo, con Rastro", pct(sin["lab_B_pct"]), pct(con["lab_B_pct"])),
        ("Entrada del modelo, sin Rastro", pct(sin["lab_A_pct"]), pct(con["lab_A_pct"])),
        ("Explicación, con Rastro", "sin marca", "marcada" if con["lab_B_marca"] else "sin marca"),
    ]
    df = pd.DataFrame([{"Dónde": a, "Antes": b, "Después": c, "¿Cambió solo?": "sí" if b != c else "no"}
                       for a, b, c in filas])
    st.caption("La respuesta es el petróleo de 2025 que le corresponde a YPF según su participación; la entrada del "
               "modelo, la participación de Total en Aguada Pichana Este.")
    tabla(df, key="demo_correccion")
    st.markdown(md(f"**Dónde se corrigió:** en un solo lugar, el archivo de participaciones revisadas (con el documento). "
                   f"Sin Rastro, el mismo dato se lee del texto del mapa en {result['lugares_sin_rastro']} lugares "
                   f"(cada consulta y el código del modelo), y hay que encontrarlos y corregirlos uno por uno."))
    if tech:
        st.caption("Se mide con layer/energia/cambio/correccion.sh: saca la corrección, rearma Rastro, mide y la vuelve a poner.")


GRAPHDB = "http://graphdb:7200/repositories/rastro"


def claim_verdict(reading, rows):
    """El veredicto de una lectura de la afirmación, calculado con lo que devolvió Rastro."""
    if reading["tipo"] == "sin_datos":
        return "🔍", "Rastro no tiene el dato", reading["falta"]
    def fmt(v):
        return f"{float(v) / reading['divisor']:,.1f} {reading['unidad']}".replace(",", "X").replace(".", ",").replace("X", ".")
    if reading["tipo"] == "numero":
        value = float(rows[0][0]) / reading["divisor"]
        holds = abs(value - reading["valor"]) <= 0.05 * reading["valor"]
        return ("✅", "Se sostiene", f"Rastro dice {fmt(rows[0][0])}.") if holds else \
            ("❌", "No se sostiene", f"Rastro dice {fmt(rows[0][0])}.")
    names = [r[0] for r in rows]
    place = next((i for i, n in enumerate(names) if reading["empresa"] in n.upper()), None)
    ranking = " · ".join(f"{i + 1}. {r[0]} ({fmt(r[1])})" for i, r in enumerate(rows[:3]))
    if place == 0:
        return "✅", "Se sostiene", ranking
    where = f"es la {place + 1}.ª" if place is not None else f"no está entre las {len(rows)} primeras"
    return "❌", f"No se sostiene: {where}", ranking


def show_claims(cfg, tech):
    """Comprobar una afirmación: cada ejemplo se compara en vivo con Rastro, lectura por lectura."""
    claims, domain = cfg["afirmaciones"], cfg["domain"]
    st.markdown(md(claims["intro"]))
    chosen = st.radio("Afirmación", [c["texto"] for c in claims["ejemplos"]], key=f"{domain}_afirmacion")
    claim = next(c for c in claims["ejemplos"] if c["texto"] == chosen)
    st.markdown(f"> {claim['texto']}")
    for reading in claim["lecturas"]:
        rows = run(prefixed(reading["consulta"], domain), domain)[1] if reading.get("consulta") else []
        mark, verdict, detail = claim_verdict(reading, rows)
        with st.container(border=True):
            st.markdown(f"**{reading['nombre']}**")
            st.markdown(f"{mark} **{verdict}.** {md(detail)}")
            if tech and reading.get("consulta"):
                st.code(reading["consulta"].strip(), language="sparql")
    if claim.get("nota"):
        st.caption(md(claim["nota"]))


def show_external(cfg, tech):
    """Enriquecer con datos de afuera: una consulta federada en GraphDB une Rastro con Wikidata por un
    identificador compartido. Corre en vivo si se pide; si no, se muestra el resultado guardado. Debajo, el mismo
    enriquecimiento guardado en Rastro (show_enrichment_saved)."""
    ext, domain = cfg["externo"], cfg["domain"]
    st.markdown(f"**{ext['titulo']}**", help=ayuda("externo"))
    st.markdown(md(ext["intro"]))
    st.graphviz_chart("""digraph { rankdir=LR; bgcolor="transparent";
        node [fontname="Helvetica", fontsize=14, style=filled, penwidth=0];
        r [label="Rastro\\nempresa · LEI · petróleo 2025", shape=ellipse, fillcolor="#2F6FB5", fontcolor="white"];
        w [label="Wikidata (internet)\\nsede · bolsa · dueño · sitio web", shape=ellipse, fillcolor="#FFF3E6", color="#FF8C42", penwidth=2];
        q [label="una consulta\\n(GraphDB)", shape=box, style="rounded,filled", fillcolor="#F4F6F9", color="#B8C2CF", penwidth=1];
        r -> q [label="  el mismo LEI  ", dir=both, color="#7A8699", fontcolor="#7A8699", fontname="Helvetica"];
        q -> w [dir=both, color="#7A8699"]; }""", use_container_width=True)
    key = f"{domain}_externo"
    if st.button("Consultar en vivo", type="primary", key=f"{key}_boton",
                 help="Une Rastro y Wikidata ahora mismo. Tarda unos 15 segundos y necesita internet."):
        try:
            r = requests.post(GRAPHDB, data={"query": Path(ext["consulta"]).read_text()},
                              headers={"Accept": "text/csv"}, timeout=90)
            r.raise_for_status()
            st.session_state[key] = (pd.read_csv(io.StringIO(r.text)), "en vivo, ahora")
        except Exception as e:
            st.session_state[key] = None
            st.warning(f"Wikidata no respondió ({str(e)[:120]}). Se muestra el resultado guardado; Wikidata a veces "
                       "limita las consultas: probar de nuevo en un par de minutos.")
    table, when = st.session_state.get(key) or (pd.read_csv(ext["guardado"]), f"guardado el {ext['fecha_guardado']}")
    columns = [c for c in ext["columnas"] if c in table.columns and (tech or c not in ("lei", "wikidata"))]
    shown = table[columns].copy()
    for c in ("su_parte_m3", "declara_m3"):
        if c in shown:
            shown[c] = shown[c].map(lambda v: money(v) if pd.notna(v) else "—")
    shown = shown.fillna("—").rename(columns=ext["columnas"])
    shown, config = logos.with_logos(shown, columns)
    tabla(shown, hide_index=True, use_container_width=True, column_config=config)
    st.caption(f"Resultado {when}. Fuentes: Rastro (Capítulo IV, mapas de la Secretaría de Energía y GLEIF) y Wikidata.")
    st.info(md(ext["conclusion"]))
    with st.expander("La consulta: dos grafos en una"):
        st.code(Path(ext["consulta"]).read_text(), language="sparql")
    if ext.get("materializado"):
        show_enrichment_saved(ext, domain, tech)


def show_enrichment_saved(ext, domain, tech):
    """El mismo enriquecimiento, guardado en Rastro: lo que respondió la fuente de afuera queda como una fuente más,
    con su fecha, y se consulta como cualquier dato."""
    st.markdown("**Guardado en Rastro**", help=ayuda("externo"))
    query = Path(ext["materializado"]).read_text()
    columns, rows = run(query, domain)
    if not rows:
        st.info("Todavía no se guardó: `docker compose run --rm wikidata-energia-loader` y después el enlazador.")
        return
    tabla(pd.DataFrame(rows, columns=columns).rename(columns={
        "empresa": "Empresa", "bolsa": "Cotiza en", "sede": "Sede", "consultado": "Consultado el", "wikidata": "Wikidata"}),
        hide_index=True, use_container_width=True)
    st.caption(md(
        "Lo mismo, guardado: lo que respondió Wikidata queda en Rastro como una fuente más, con el día de la consulta "
        "y la huella del archivo, unido por el LEI. No depende de internet, se puede repetir y lo usan las preguntas, el "
        "asistente de IA y el modelo de Rastro Lab. En vivo está siempre al día; guardado, queda como estaba ese día."))
    if tech:
        st.code(query, language="sparql")


def text_step(n, title, help_text=None):
    st.markdown(f"#### {n} · {title}", help=help_text)


def show_text_question(cfg, tech, demo=False):
    """Una pregunta sobre textos, paso a paso (GraphRAG anclado en el grafo): el grafo elige los
    registros con una consulta exacta, un asistente de IA lee solo esos textos y los resume en temas que
    citan cada registro, y cualquiera puede comprobarlo. El resumen está guardado; los registros se leen
    en vivo."""
    domain = cfg["domain"]
    item = read_json(cfg["texto"])
    st.markdown("**1 · La pregunta → 2 · El grafo elige → 3 · La IA lee solo eso → 4 · El resumen, con citas "
                "→ 5 · Comprobar**", help=ayuda("texto"))
    text_step(1, "La pregunta")
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
    graph_part, _, ai_part = item["como"].partition("Un asistente de IA")
    ai_part = ("Un asistente de IA" + ai_part) if ai_part else ""

    # Los registros, con sus textos y lo que cita cada tema: contratos (con montos) o registros cualesquiera
    if "columnas" in item:
        records = {r[0]: r for r in rows}
        unit = item["unidad"]
        table = pd.DataFrame([list(r) for r in records.values()], columns=item["columnas"])
        themes = [(th["tema"], [r for r in th["registros"] if r in records], th["detalle"], "") for th in item["temas"]]
    else:
        records = {c: (float(m), a, e, d) for c, m, a, e, d in rows}
        unit = ["contrato", "contratos"]
        table = pd.DataFrame([{"Contrato": c, "Millones de US$": round(m / 1e6, 1), "Agencia": a.title(),
                               "Empresa": e.title(), "Descripción": d.capitalize()} for c, (m, a, e, d) in records.items()])
        themes = []
        for th in item["temas"]:
            found = [c for c in th["contratos"] if c in records]
            themes.append((th["tema"], found, th["detalle"],
                           f", US\\$ {money(sum(records[c][0] for c in found) / 1e6)} millones"))
    n = len(records)

    text_step(2, "El grafo elige, con una consulta exacta",
              "No es una búsqueda por palabras: la consulta usa los conceptos y los enlaces del diccionario, así que "
              "trae exactamente lo que pide la pregunta, siempre lo mismo.")
    st.markdown(md(graph_part.strip()))
    st.metric(f"{unit[1].capitalize()} elegidos por el grafo", n)
    with st.expander("La consulta SPARQL que elige los registros", expanded=tech):
        st.caption("Pide conceptos del diccionario, no palabras: por eso trae exactamente estos registros, siempre los mismos.")
        st.code(query, language="sparql")
    if demo and item.get("busqueda_texto"):
        compare_text_search(item, records, domain, tech, always=True)

    text_step(3, "La IA lee solo esos textos",
              "El asistente de IA no busca nada por su cuenta: recibe estos textos y ninguno más.")
    st.markdown(md(ai_part.strip()) or f"Un asistente de IA leyó solo los textos de esos {n} {unit[1]}.")
    with st.expander(f"Los {n} textos que leyó, tal como están en la fuente"):
        tabla(table, hide_index=True, use_container_width=True)

    text_step(4, "El resumen, con citas")
    for theme, found, detail, extra in themes:
        st.markdown(f"- **{md(theme)}** · {len(found)} {unit[0] if len(found) == 1 else unit[1]}{extra}. "
                    f"{md(detail)}  \n<small>Cita: {', '.join(found)}</small>", unsafe_allow_html=True)

    text_step(5, "Comprobar",
              "Cada tema cita sus registros por número: se abren en la tabla del paso 3 y se lee el texto original.")
    st.markdown(f"Cada tema cita sus {unit[1]}: en el paso 3 está el texto original de cada uno. "
                f"Resumen guardado el {item['fecha']}; los {unit[1]} se leen en vivo, y si cambian los datos el "
                "resumen se vuelve a generar.")
    if item.get("busqueda_texto") and not demo:
        compare_text_search(item, records, domain, tech)


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
    evidence = read_json(cfg["evidencia"]) if cfg.get("evidencia") and Path(cfg["evidencia"]).exists() else {}
    if evidence:
        numbers.update(pct_evidencia=f"{100 * evidence['enlaces_con_evidencia'] / evidence['enlaces']:.0f} %",
                       n_enlaces=money(evidence["enlaces"]), cols=evidence["columnas"], cols_ok=evidence["columnas_con_fuente"])
    else:
        numbers.update(pct_evidencia="Sí", n_enlaces="todos los", cols="las", cols_ok="todas")
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
                evaluation_detail(evaluation, totals, cfg["domain"])
    with tab_same if tech else st.expander(f"Ver las {4 * len(consistency)} respuestas"):
        st.caption(f"{len(consistency)} preguntas, cada una hecha de 4 formas con el mismo significado.")
        table = []
        for qid, row in consistency.items():
            line = {"Pregunta": row["texts"][0] if tech else simple.get(qid, row["texts"][0])}
            for k, title in names.items():
                line[title] = ("✅ " if row[k]["same"] else "❌ ") + " · ".join(short(a) for a in row[k]["answers"])
            table.append(line)
        tabla(pd.DataFrame(table), hide_index=True, use_container_width=True,
                     column_config={"Pregunta": st.column_config.TextColumn(width="medium")})
        st.caption("✅ la misma respuesta las 4 veces · ❌ cambió según cómo se preguntó. En las preguntas que "
                   "piden una lista, el número es cuántos nombres devolvió.")
        if consistency:
            labels = {qid: simple.get(qid, row["texts"][0]) for qid, row in consistency.items()}
            picked = st.selectbox("Ver las 4 formas de una pregunta", list(labels.values()),
                                  key=f"{cfg['domain']}_consistency")
            qid = next(k for k, v in labels.items() if v == picked)
            row = consistency[qid]
            tabla(pd.DataFrame([{"Cómo se preguntó": t, **{names[k]: short(row[k]["answers"][i])
                                                                    for k in names}}
                                       for i, t in enumerate(row["texts"])]),
                         hide_index=True, use_container_width=True,
                         column_config={"Cómo se preguntó": st.column_config.TextColumn(width="large")})

    with tab_change if tech else st.expander("Ver los escenarios de cambio"):
        scenarios = {c["titulo"]: c for c in cfg.get("cambios", [])}
        st.caption("Qué pasa con las preguntas de la prueba de cambio, todas juntas, cuando una base cambia.")
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
                col.metric(change_names[k], f"{before['totals'][k].get('✅', 0)}/{len(before['cells'])}")
                col.caption(summary(before["totals"][k]))
            if before["totals"]["C"].get("❌", 0) > before["totals"]["B"].get("❌", 0):
                st.caption("Rastro falla más, y todo junto: el mapeo lee la columna que cambió y Rastro no arranca hasta "
                           "arreglarla. Falla en voz alta y se arregla en un lugar; sin Rastro, cada consulta rota hay que "
                           "encontrarla y reescribirla.")
            if "🟡" in before.get("vocabulary", ""):
                st.warning("Rastro avisa: " + md(before["vocabulary"].split(": ", 1)[-1]))
            if tech:
                st.markdown(f"**El arreglo en Rastro: una línea {change.get('donde', 'del mapeo')}**")
                st.code(f"- {change['arreglo'][0]}\n+ {change['arreglo'][1]}", language="diff")
            else:
                st.markdown("**El arreglo en Rastro:** una línea, en la traducción de esa base al diccionario de negocio.")
            st.markdown("**Después del arreglo:**")
            for col, k in zip(st.columns(2), change_names):
                col.metric(change_names[k], f"{after['totals'][k].get('✅', 0)}/{len(after['cells'])}")
                col.caption(summary(after["totals"][k]) + ("" if k == "C" else ". Hay que encontrar y reescribir cada consulta."))
            if tech:
                st.markdown("**Pregunta por pregunta**")
                tabla(pd.DataFrame([{"Pregunta": simple.get(qid, qid),
                                            **{f"{change_names[k]}, antes": before["cells"][qid][k] for k in change_names},
                                            **{f"{change_names[k]}, después": after["cells"][qid][k] for k in change_names}}
                                           for qid in before["cells"]]),
                             hide_index=True, use_container_width=True,
                             column_config={"Pregunta": st.column_config.TextColumn(width="medium")})
        st.info("Sin Rastro, cada consulta sabe cómo se llaman las columnas y en qué unidad están los valores: si la "
                "base cambia, hay que encontrar y arreglar cada una. Con Rastro, eso está en un solo lugar.")
    show_quality(cfg.get("calidad"))
    show_no_data(cfg.get("fuera"), tech)


def show_no_data(fuera, tech):
    """¿Dice cuándo no tiene el dato? Las preguntas fuera de los datos, camino por camino."""
    path = fuera.get("archivo") if fuera else None
    if not path or not Path(path).exists():
        return
    result = read_json(path)
    st.markdown("### Cuando no tiene el dato", help=ayuda("fuera"))
    st.caption(md(fuera["intro"]))
    names = {k: v for k, v in result["caminos"].items() if tech or k != "D"}
    n = len(result["preguntas"])
    for col, (k, name) in zip(st.columns(len(names)), names.items()):
        col.metric(name, f"{result['totales'][k]} de {n}")
    tabla(pd.DataFrame([{"Pregunta": row["pregunta"], "Qué falta": row["falta"],
                         **{name: f"{row[k]['marca']} {row[k]['respuesta']}" for k, name in names.items()}}
                        for row in result["preguntas"].values()]),
          column_config={"Pregunta": st.column_config.TextColumn(width="medium")})
    st.caption("✅ dijo qué falta (o respondió la de control) · ❌ respondió lo que no sabe (o no respondió la de control).")


def evaluation_detail(evaluation, totals, domain):
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
    chosen = st.selectbox("Pregunta", [e["question"] for e in data.values()], key=f"{domain}_eval_question")
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
