"""A domain's screen from its configuration file (app/dominios/<dominio>.yaml).

The same three tabs as oncology: Preguntar, Por qué confiar and Preguntas frecuentes,
with the two modes (business by default, technical with the switch). Everything specific to the
domain (questions, columns, evidence, cards, change scenarios) is in the YAML.
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
import idioma
import logos

PROV = "PREFIX prov: <http://www.w3.org/ns/prov#>\n"


def load_config(path):
    return idioma.localized(path)


def read_json(path):
    p = Path(path)
    return _load_json(path, p.stat().st_mtime) if p.exists() else {}


@st.cache_data
def _load_yaml(path, mtime):   # the file's date is part of the key: if it changes, it is read again
    return yaml.safe_load(Path(path).read_text())


def ayuda(key):
    """The text of the «?» icon for each part of the app (app/ayuda.yaml, with its English overlay)."""
    p = Path("/app/ayuda.yaml")
    return (idioma.localized(p) or {}).get(key) if p.exists() else None


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
def data_version(domain, reads=""):
    """Changes when the data (loads and links) or the dictionary and the mappings change: with it, the
    answers saved on disk are recalculated only when needed."""
    import psycopg
    cfg = answer.DOMAINS[domain]
    files = [answer.ROOT / path for path in (cfg["method"]["mapping"], cfg["ontology"], cfg["method"]["app"])]
    # Only the tables this domain's mapping reads, plus any SQL the caller reads directly (reads): a load or a
    # linker run in another domain does not invalidate its answers. A table's id changes when it is recreated, its
    # counters when its rows change.
    tables = sorted(set(re.findall(r'\b([a-z_][a-z0-9_]*)\.\\?"?([a-z_][a-z0-9_]*)', files[0].read_text() + reads)))
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        loads = conn.execute("""
            SELECT md5(coalesce(string_agg(concat_ws(':', relid, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup), ','
                                           ORDER BY relid), ''))
            FROM pg_stat_user_tables WHERE (schemaname, relname) IN (SELECT * FROM unnest(%s::text[], %s::text[]))""",
                             ([s for s, _ in tables], [n for _, n in tables])).fetchone()[0]
    inserts = ""
    return f"{loads}|{inserts}|" + "|".join(str(f.stat().st_mtime) if f.exists() else "" for f in files)


@st.cache_data(persist="disk", show_spinner=False)
def _run_saved(query, domain, version):
    return answer.run_sparql_table(query, domain)


def run(query, domain):
    """A query over Rastro. The answer is saved on disk: it survives an app restart, and it is
    recalculated if the data or the mappings change (data_version)."""
    return _run_saved(query, domain, data_version(domain))


@st.cache_resource
def warm_up():
    """Warm-up: the first time someone opens the app, all the domains' example questions are computed
    in the background, so the demo does not wait."""
    import threading

    def work():
        for config in sorted(p for p in Path("/app/dominios").glob("*.yaml") if not p.name.endswith(".en.yaml")):
            cfg = yaml.safe_load(config.read_text())
            for q in (validated_questions(cfg) if cfg.get("preguntas") else []):
                try:
                    columns, rows = run(Path(q["query"]).read_text(), cfg["domain"])
                    why = q.get("porque")
                    if why and rows and why["columna"] in columns:   # the first row of «¿Por qué este número?»
                        value = str(rows[0][columns.index(why["columna"])]).replace('"', '\\"')
                        run(prefixed(why["query"].replace("{valor}", value), cfg["domain"]), cfg["domain"])
                except Exception:   # noqa: BLE001 - a domain that is down does not stop the others
                    continue
        try:   # and the two Rastro Lab models
            import lab
            lab.datos()
        except Exception:   # noqa: BLE001
            pass

    threading.Thread(target=work, daemon=True).start()
    return True


def prefixed(query, domain):
    """Adds the prefixes the query uses: the domain's always, PROV-O's only when needed."""
    ns = answer.DOMAINS[domain]["namespace"]
    return f"PREFIX {domain}: <{ns}>\n" + (PROV if "prov:" in query else "") + query


def tabla(data, hide_index=True, use_container_width=True, column_config=None, key=None, **kwargs):
    """A table. Cells cut long text and do not scroll: if there are long texts, picking
    a row shows it in full below."""
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
        st.caption(idioma.t("dominio.tabla.long_text"))
    return event


def md(text):
    """Text for st.markdown: «$» is a formula in Streamlit, and amounts say «US$»."""
    return str(text).replace("$", "\\$")


def money(value):
    return idioma.number(value)


def as_table(columns, rows, cfg, tech, col_sources):
    """The answer as a table: columns with business names and readable numbers."""
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


def show_answer(cfg, tech, query, columns, rows, item=None, note=None, where="preguntar"):
    # where: the tab drawing it; the demo and «Preguntar» can show the same question at once, so keys include it
    domain = cfg["domain"]
    info = sources(domain)
    labels = cfg.get("fuentes", {})
    used, col_sources = answer.column_sources(query, domain)
    if tech:
        st.markdown(idioma.t("dominio.show_answer.sources_used") + " · ".join(f"`{labels.get(s, s)}`" for s in used),
                    help=ayuda("fuentes_respuesta"))
    else:
        names = [info[s]["name"] for s in used if s in info] + ([idioma.t("dominio.show_answer.rastro_links")] if "rastro" in used else [])
        st.markdown(idioma.t("dominio.show_answer.sources") + ", ".join(names), help=ayuda("fuentes_respuesta"))
    if not rows:
        st.info(idioma.t("dominio.show_answer.no_results"))
    else:
        visible = item.get("columnas_respuesta") if item and not tech else None
        shown_columns = [c for c in columns if not visible or c in visible]
        shown_rows = [[row[columns.index(c)] for c in shown_columns] for row in rows]
        table, config = logos.with_logos(as_table(shown_columns, shown_rows, cfg, tech, col_sources), shown_columns)
        tabla(table, hide_index=True, use_container_width=True, column_config=config,
              key=f"{where}_{item['id']}" if item and item.get("id") else None)
        if item and item.get("mapa"):
            show_map(domain)
        if item and item.get("porque"):
            show_why(domain, item["porque"], columns, rows, where, tech)
        st.caption(idioma.t("dominio.show_answer.rows_one" if len(rows) == 1 else "dominio.show_answer.rows_many", n=len(rows))
                   + (idioma.t("dominio.show_answer.evidence_hint") if item and item.get("evidencia") else ""))

    with st.expander(idioma.t("dominio.show_answer.where_from")):
        evidence = (item or {}).get("evidencia")
        if not tech:
            st.markdown(idioma.t("dominio.show_answer.where_looked"))
            for s in used:
                if s == "rastro":
                    st.markdown(f"- **{cfg.get('nota_rastro', idioma.t('dominio.show_answer.rastro_links_default'))}**")
                elif s in info:
                    st.markdown(idioma.t("dominio.show_answer.source_line", name=info[s]["name"], license=info[s]["license"]))
            if item and item.get("ventaja"):
                st.markdown(idioma.t("dominio.show_answer.contributed") + md(item["ventaja"]))
            if item and item.get("definicion"):
                st.markdown(idioma.t("dominio.show_answer.rule_once"))
            if evidence:
                st.markdown(f"**{md(evidence['texto'])}**")
                ev_cols, ev_rows = run(prefixed(evidence["query"], domain), domain)
                for r in ev_rows:
                    st.markdown("- " + md(evidence["formato"].format(**dict(zip(ev_cols, r)))))
                st.caption(idioma.t("dominio.show_answer.auditable"))
            st.caption(idioma.t("dominio.show_answer.tech_hint"))
            return
        if note:
            st.caption(note)
        st.markdown(idioma.t("dominio.show_answer.step_query"))
        st.code(query, language="sparql")
        st.markdown(idioma.t("dominio.show_answer.step_sql"))
        sql = None
        try:
            sql = sqlparse.format(answer.ontop_sql(query, domain), reindent=True, keyword_case="upper", indent_width=2)
            st.code(sql, language="sql")
        except requests.RequestException:
            st.caption(idioma.t("dominio.show_answer.no_sql"))
        explain(query, sql, domain, item, where)
        st.markdown(idioma.t("dominio.show_answer.step_sources"))
        for s in used:
            if s == "rastro":
                st.markdown(idioma.t("dominio.show_answer.tech_rastro_line", note=cfg.get("nota_rastro", "")))
            elif s in info:
                st.markdown(idioma.t("dominio.show_answer.tech_source_line", name=info[s]["name"], license=info[s]["license"]))
        if item and item.get("definicion"):
            st.markdown(idioma.t("dominio.show_answer.step_rule"))
            st.code(item["definicion"], language="turtle")
        if evidence:
            st.markdown(idioma.t("dominio.show_answer.step_evidence")
                        + (idioma.t("dominio.show_answer.step_evidence_prov") if "prov:" in evidence["query"] else ":"))
            ev_query = prefixed(evidence["query"], domain)
            st.code(ev_query, language="sparql")
            ev_cols, ev_rows = run(ev_query, domain)
            tabla(pd.DataFrame(ev_rows, columns=ev_cols), hide_index=True, use_container_width=True)


def explain(query, sql, domain, item=None, where="preguntar"):
    """«Explicame la consulta»: example questions bring their saved explanation; the user's own
    are explained live if an LLM is configured."""
    key = f"explain_{where}_{abs(hash(query))}"
    stored = (item or {}).get("explicacion")
    available, _ = llm_status()
    if st.button("💬 Explicame la consulta", key=f"{key}_boton", disabled=not stored and not available,
                 help=None if stored or available else "Para explicar preguntas propias hace falta un LLM."):
        st.session_state[key] = stored
        if not stored:
            with st.spinner("El LLM está leyendo la consulta..."):
                st.session_state[key] = answer.explain_query(query, sql, domain, idioma.lang())
    if st.session_state.get(key):
        st.info(md(st.session_state[key]))


# The technical view's SPARQL console: where the example queries are and the port that is
# opened on the computer for other tools


# Example instances for «Así se ve un dato del grafo»: one per important class of each domain
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
    """The dictionary's Spanish labels: term → «business words»."""
    import rdflib
    g = rdflib.Graph().parse(ontology_file(domain))
    return {str(s): str(o) for s, o in g.subject_objects(rdflib.RDFS.label)}


def short_iri(iri, domain):
    ns = answer.DOMAINS[domain]["namespace"]
    return (iri.replace(ns, f"{domain}:").replace(PROV_NS, "prov:").replace(RDF_TYPE, "a")
            .replace("https://w3id.org/rastro/", "rastro:"))


# «Diccionario, enlaces y mapeos» (technical view): the parts of Rastro the demo uses, in 3 steps.
# The links are read live from Rastro's tables; the mappings, from the domain's R2RML file.


def sql_table(query, domain, approach="D", params=None):
    """A read-only query: with approach «D», over Rastro's link tables; with «B», only over the
    sources as they come."""
    import psycopg
    user = answer.DOMAINS[domain]["readers"][approach]
    with psycopg.connect(answer.READER.format(user) % os.environ["PG_DB"]) as conn:
        cur = conn.execute(query, params)
        return [c.name for c in cur.description], cur.fetchall()


def mapping_blocks(path, names):
    """The requested TriplesMaps, as they are in the R2RML file."""
    text = Path(path).read_text()
    blocks = {}
    for m in re.finditer(r"^<#(\w+)> a rr:TriplesMap ;.*?(?=^<#|\Z)", text, re.S | re.M):
        blocks[m.group(1)] = m.group(0).strip()
    return [blocks[n] for n in names if n in blocks]


def ontology_doc(domain):
    """The dictionary as documentation (in the style of WIDOCO): classes, relations and attributes, with their
    label, their description and which classes they connect."""
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
    """The technical tab «Diccionario, enlaces y mapeos»."""
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
    """The instance as a graph (app/grafo.py): bubbles for entities, orange bubbles for
    classes, rectangles for plain values and arrows with each property's business name.
    Returns the SVG and the linked entities, to follow them."""
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
                        font="Helvetica, Arial, sans-serif")   # more properties, taller: they do not overlap
    return drawing, [o for o in dict.fromkeys(linked) if o not in names]


def show_instances(domain):
    """A real instance of the graph, drawn as a graph: each link to another entity can be followed,
    inside the app. Below, its properties in a table and in Turtle."""
    examples = technical(domain).get("instances")
    if not examples:
        return
    st.markdown("### Así se ve un dato del grafo", help=ayuda("instancia"))
    st.caption("Una entidad real del grafo. Burbuja azul: una entidad; burbuja naranja: su clase en el diccionario; "
               "rectángulo: un dato simple (texto, número o fecha). Cada flecha es una propiedad, con su nombre de "
               "negocio. Los enlaces traen su evidencia y su fuente (PROV-O).")
    key = f"{domain}_instancia"
    chosen = st.selectbox("Empezar por", list(examples), key=key)
    if st.session_state.get(f"{key}_desde") != chosen:      # a new example restarts the path
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
    """«Bajo el capó» (technical view): the SPARQL console, a graph instance and the dictionary, the
    links and the mappings, in a single tab."""
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


def finding(rule, long=True):
    """A rule's result in words: violations do not hold; warnings and informational findings ask a person to review."""
    if not rule["revisados"]:
        return idioma.t("dominio.finding.no_data") if long else "⏳"
    counts = rule.get("por_severidad") or {"Violation": rule["fallas"]}
    words = {kind: idioma.t(f"dominio.finding.{kind.lower()}") if long else "" for kind in ("Violation", "Warning", "Info")}
    parts = [f"⚠️ {money(counts['Violation'])}" + words["Violation"] if counts.get("Violation") else "",
             f"🟡 {money(counts['Warning'])}" + words["Warning"] if counts.get("Warning") else "",
             f"ℹ️ {money(counts['Info'])}" + words["Info"] if counts.get("Info") else ""]
    return " · ".join(p for p in parts if p) or (idioma.t("dominio.finding.holds") if long else "✅")


def show_quality(quality):
    """The quality rules, in business words: what is checked and whether it holds."""
    result = quality_result(quality)
    if not result:
        return
    st.markdown(idioma.t("dominio.show_quality.title"), help=ayuda("calidad"))
    st.caption(md(quality["intro"]))
    rule, why = idioma.t("dominio.show_quality.col_rule"), idioma.t("dominio.show_quality.col_why")
    tabla(pd.DataFrame([{rule: r["nombre"], why: r["porque"], idioma.t("dominio.show_quality.col_checked"): money(r["revisados"]),
                         idioma.t("dominio.show_quality.col_result"): finding(r),
                         idioma.t("dominio.show_quality.col_predictions"): len(r.get("predicciones_afectadas", [])) or ""}
                        for r in result["reglas"]]),
          column_config={rule: st.column_config.TextColumn(width="medium"), why: st.column_config.TextColumn(width="large")})
    date = result["fecha"]
    st.caption(idioma.t("dominio.show_quality.checked_on", day=date[8:10], month=date[5:7], year=date[:4]))


def show_quality_shacl(quality):
    """The same rules, in SHACL, with what fails them."""
    result = quality_result(quality)
    if not result:
        st.caption("Todavía no se comprobaron: `docker compose run --rm calidad`.")
        return
    st.markdown("### Reglas de calidad en SHACL", help=ayuda("calidad_shacl"))
    st.caption(md(quality["tecnico"]))
    for r in result["reglas"]:
        mark = finding(r, long=False)
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
                                     **({"Severidad": e["severidad"]} if e.get("severidad") else {}),
                                     "Predicciones que lo usan (prov:used)":
                                         ", ".join(p.rsplit("/", 1)[-1] for p in e.get("predicciones", []))}
                                    for e in r["ejemplos"]]))
    st.caption(f"{money(result['triples'])} triples traídos de Rastro con CONSTRUCT. Las reglas están en "
               "el archivo de reglas del dominio; se comprueban con el comando registrado para ese dominio.")


def sparql_console(domain):
    """A console to write and run SPARQL over the domain's Ontop, with the SQL it generates."""
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
    if st.session_state.get(f"{key}_cargada") != chosen:   # when the example changes, it is loaded into the editor
        st.session_state[f"{key}_cargada"] = chosen
        st.session_state[f"{key}_texto"] = examples.get(
            chosen, f"PREFIX {domain}: <{answer.DOMAINS[domain]['namespace']}>\nSELECT * WHERE {{ ?s ?p ?o }} LIMIT 10")
    query = st.text_area("Consulta", key=f"{key}_texto", height=280)
    if st.button("Ejecutar", type="primary", key=f"{key}_ejecutar"):
        started = time.time()
        try:
            columns, rows = run(query, domain)
        except Exception as e:  # noqa: BLE001 - Ontop's error is shown as is
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
    """The coordinates of a simple WKT: POINT → [x, y]; POLYGON → [[x, y], ...]; MULTILINESTRING → [[[x, y], ...], ...]."""
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
    """Concessions, possible venting seen by satellite and transport gas pipelines, all read from Rastro."""
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
        st.info(idioma.t("dominio.render.no_questions"))
        return
    if answer.DOMAINS[domain].get("method", {}).get("lifecycle") and cfg.get("tarjetas"):
        from method import publication_errors
        if publication_errors(answer.DOMAINS[domain], answer.ROOT):
            cfg = {**cfg, "tarjetas": None, "demo": None}
            st.caption(idioma.t("dominio.render.pending_review"))

    with st.sidebar:
        if tech:
            available, status = llm_status()
            st.subheader("LLM", help=ayuda("llm"))
            st.markdown(("🟢 " if available else "⚪ ") + status)
            st.subheader(idioma.t("dominio.render.sources"), help=ayuda("fuentes_barra"))
            for info in sources(domain).values():
                st.markdown(f"🐘 **{info['name']}**  \n<small>{info['license']}</small>", unsafe_allow_html=True)
        else:
            st.caption(md(cfg["resumen"]))

    # «Por qué confiar» needs a measured evaluation or quality rules; a domain with neither does not show the tab
    # Few tabs: the demo, asking, why trust and frequent questions; in the technical view, everything
    # inside (console, dictionary, links and mappings) together in «Bajo el capó»
    # Each tab has a fixed internal name; only its label is translated
    names = (["demo"] if cfg.get("demo") else []) + ["ask"] \
        + (["trust"] if cfg.get("tarjetas") or cfg.get("calidad") else []) + (["lab"] if cfg.get("lab") else []) \
        + (["example"] if cfg.get("ejemplo_integracion") else []) + ["faq"] + (["hood"] if tech else [])
    labels = [cfg["ejemplo_integracion"]["titulo"] if name == "example" else idioma.t(f"dominio.render.tab_{name}")
              for name in names]
    tabs = dict(zip(names, st.tabs(labels)))
    ask_tab, trust_tab, faq_tab = tabs["ask"], tabs.get("trust"), tabs["faq"]
    if cfg.get("demo"):
        with tabs["demo"]:
            show_demo(cfg, tech)
    if cfg.get("ejemplo_integracion"):
        with tabs["example"]:
            show_integration_example(cfg["ejemplo_integracion"], domain, tech)
    if cfg.get("lab"):
        with tabs["lab"]:
            import lab
            import lab_alternative
            # The experimental alternative models are a technical detail: the business view keeps the regression
            choice = lab_alternative.select_model(cfg["alternative_lab"]) if cfg.get("alternative_lab") and tech else "ridge"
            pozo = lab.select_well(cfg["ejemplo_lab"]) if cfg.get("ejemplo_lab") else None
            if choice == "alternative":
                lab_alternative.show_alternative(tech, pozo, cfg["alternative_lab"], cfg["ejemplo_lab"])
            else:
                if cfg.get("ejemplo_lab"):
                    run_status = lab.show_run_status(pozo, cfg["ejemplo_lab"])
                    with st.expander(cfg["ejemplo_lab"]["titulo"]):
                        show_integration_example(cfg["ejemplo_lab"], domain, tech, key=f"{domain}_lab", pozo=pozo,
                                                 run_id=run_status["run_id"])
                lab.show_lab(tech, pozo=pozo)
    if tech:
        with tabs["hood"]:
            under_the_hood(domain, cfg.get("diagrama", {}).get("archivo"), cfg.get("calidad"))

    with ask_tab:
        # Fixed internal names for the modes; the radio shows (and returns) their labels
        mode_labels = {"example": idioma.t("dominio.render.mode_example"), "text": idioma.t("dominio.render.mode_text"),
                       "claims": (cfg.get("afirmaciones") or {}).get("titulo"), "external": (cfg.get("externo") or {}).get("titulo"),
                       "free": idioma.t("dominio.render.mode_free")}
        modes = ["example"] + (["text"] if cfg.get("texto") else []) + (["claims"] if cfg.get("afirmaciones") else []) \
            + (["external"] if cfg.get("externo") else [])
        by_label = {mode_labels[m]: m for m in modes + ["free"]}
        mode = by_label.get(st.radio(idioma.t("dominio.render.mode_label"), list(by_label), help=ayuda("modo"),
                                     horizontal=True, label_visibility="visible", key=f"{domain}_mode"))
        if mode == "text":
            show_text_question(cfg, tech)
        elif mode == "external":
            show_external(cfg, tech)
        elif mode == "claims":
            show_claims(cfg, tech)
        elif mode == "example":
            # The same question in both views; the technical one adds its precise wording below
            options = {q["simple"]: q for q in questions}
            chosen = st.selectbox(idioma.t("dominio.render.question"), list(options), key=f"{domain}_question", help=ayuda("pregunta"))
            item = options[chosen]
            if tech:
                st.caption(idioma.t("dominio.render.tech_wording") + md(item["tecnica"]))
            if item.get("terminos"):
                with st.expander(idioma.t("dominio.render.terms", terms=", ".join(item["terminos"]))):
                    st.markdown("\n".join(f"- **{md(t)}:** {md(m)}" for t, m in item["terminos"].items()))
            query = Path(item["query"]).read_text()
            if st.button(idioma.t("dominio.render.answer"), type="primary", key=f"{domain}_answer"):
                st.session_state[f"{domain}_shown"] = (chosen, query, *run(query, domain))
            shown = st.session_state.get(f"{domain}_shown", (None,))
            if shown[0] == chosen:
                _, query, columns, rows = shown
                if item.get("antes_despues") and not item.get("porque", {}).get("recorrido"):
                    before_after(item["antes_despues"])
                show_answer(cfg, tech, query, columns, rows, item,
                            note=idioma.t("dominio.render.live_note"))
        else:
            available, _ = llm_status()
            question = st.text_area(idioma.t("dominio.render.question"), placeholder=cfg.get("ejemplo_libre", ""),
                                    key=f"{domain}_free", help=ayuda("propia"))
            if st.button(idioma.t("dominio.render.answer"), type="primary", disabled=not available or not question.strip(),
                         key=f"{domain}_free_answer"):
                with st.spinner(idioma.t("dominio.render.writing")):
                    result = answer.ask_rastro(question, domain, idioma.lang())
                if result.get("sin_datos"):
                    st.warning(idioma.t("dominio.render.no_data", missing=result["sin_datos"]))
                elif result["query"] is None:
                    st.error(idioma.t("dominio.render.failed"))
                else:
                    show_answer(cfg, tech, result["query"], result["columns"], result["rows"],
                                note=idioma.t("dominio.render.attempts", n=len(result["attempts"])))
            if not available:
                st.info(idioma.t("dominio.render.need_llm"))

    if trust_tab:
        with trust_tab:
            trust(cfg, tech, evaluation, changes)

    with faq_tab:
        diagram = cfg.get("diagrama", {})
        show_faq(domain, [(i["pregunta"], md(i["respuesta"]), i.get("tecnico", False)) for i in cfg.get("faq", [])], tech,
                 [(f"arquitectura-{domain}", idioma.t("dominio.render.architecture_caption")),
                  (diagram.get("archivo"), idioma.t("dominio.render.dictionary_caption", title=diagram.get("titulo")))],
                 diagram.get("titulo", idioma.t("dominio.render.dictionary")))


def general_faq():
    return idioma.localized("/app/faq-general.yaml")


def domain_name(domain):
    return next((d["name"] for d in idioma.localized("/app/dominios.yaml") if d["id"] == domain), domain)


def show_faq(domain, specific, tech, diagrams, diagram_title="diccionario"):
    """The frequent questions: first those that apply to every case, then this case's.
    specific is a list of (question, answer, technical)."""
    general = general_faq()

    def block(items):
        for question, answer_text in items:
            with st.expander(question):
                st.markdown(answer_text)

    st.markdown(idioma.t("dominio.show_faq.all_cases"))
    block([(i["pregunta"], md(i["respuesta"])) for i in general if not i.get("tecnico")])
    st.markdown(idioma.t("dominio.show_faq.this_case", name=domain_name(domain)))
    block([(q, a) for q, a, t in specific if not t])
    if not tech:
        st.caption(idioma.t("dominio.show_faq.more_technical"))
        return
    st.markdown(idioma.t("dominio.show_faq.technical_all"))
    block([(i["pregunta"], md(i["respuesta"])) for i in general if i.get("tecnico")])
    st.markdown(idioma.t("dominio.show_faq.technical_case", name=domain_name(domain)))
    with st.expander(idioma.t("dominio.show_faq.architecture", title=diagram_title)):
        for name, caption in diagrams:
            if not name or not Path(f"/app/{name}.svg").exists():
                continue
            st.caption(caption)
            image = base64.b64encode(Path(f"/app/{name}.svg").read_bytes()).decode()
            st.markdown(f'<img src="data:image/svg+xml;base64,{image}" style="width:100%;margin-bottom:24px">',
                        unsafe_allow_html=True)
    block([(q, a) for q, a, t in specific if t])


def show_why(domain, why, columns, rows, where="preguntar", tech=False):
    """«¿Por qué este número?»: pick a row of the answer and see the evidence behind it,
    drawn as a graph (the row in the center, each link around it) and in a table."""
    import grafo
    if why["columna"] not in columns:
        return
    if why.get("recorrido"):
        from layer_story import show_story
        show_story(domain, why, columns, rows, where, tech)
        return
    values = list(dict.fromkeys(r[columns.index(why["columna"])] for r in rows if r[columns.index(why["columna"])]))
    with st.container(border=True):
        st.markdown(idioma.t("dominio.show_why.title"), help=idioma.t("dominio.show_why.help"))
        value = st.selectbox(idioma.t("dominio.show_why.row"), values, key=f"{domain}_{where}_porque_{why['columna']}",
                             label_visibility="collapsed")
        st.markdown(f"**{md(why['titulo'].format(valor=value))}.** {md(why.get('explica', ''))}")
        cols, found = run(prefixed(why["query"].replace("{valor}", str(value).replace('"', '\\"')), domain), domain)
        if not found:
            st.info(idioma.t("dominio.show_why.no_evidence"))
            return
        records = [dict(zip(cols, r)) for r in found]

        def fmt(record, template):
            numbers = why.get("numeros", ["parte"])
            return template.format(**{k: (money(v) if k in numbers and v not in (None, "") else (v or "—"))
                                      for k, v in record.items()})

        shown = records[:8]
        nodes = [("entidad", fmt(r, why["nodo"]), fmt(r, why["detalle"]), why["flecha"]) for r in shown]
        if len(records) > len(shown):
            nodes.append(("dato", idioma.t("dominio.show_why.more", n=len(records) - len(shown)), "", why["flecha"]))
        drawing = grafo.svg((str(value), idioma.t("dominio.show_why.answer_row")), nodes, width=1500,
                            height=620 + 55 * max(0, len(nodes) - 8), scale=0.95, font="Helvetica, Arial, sans-serif")
        st.markdown(f'<img src="data:image/svg+xml;base64,{base64.b64encode(drawing.encode()).decode()}" '
                    'style="width:100%;border-radius:12px">', unsafe_allow_html=True)
        table = pd.DataFrame(records).rename(columns=why.get("columnas", {}))
        tabla(table, hide_index=True, use_container_width=True, key=f"{domain}_{where}_porque_tabla")


def before_after(card):
    """The same card at every moment of the demo: without Rastro on the left, with Rastro on the right."""
    left, right = st.columns(2)
    for col, key, title in [(left, "sin", card.get("titulo_sin", idioma.t("dominio.before_after.without"))),
                           (right, "con", idioma.t("dominio.before_after.with"))]:
        with col.container(border=True):
            st.caption(title, help=ayuda("sin_rastro" if key == "sin" else "con_rastro"))
            st.markdown(f"### {'⚪' if key == 'sin' else '🟢'} {md(card[key]['valor'])}")
            st.markdown(md(card[key]["detalle"]))
    if card.get("impacto"):
        st.warning(idioma.t("dominio.before_after.cost") + md(card["impacto"]))


def show_integration_example(example, domain, tech, key=None, pozo=None, run_id=None):
    """A walkthrough on real data: what it is for, which part of Rastro each step shows, and each step's live
    queries (raw sources with SQL as they come, Rastro with SPARQL), so every number on screen comes from a query."""
    steps = example["pasos"]
    if example.get("encabezado"):
        st.markdown(f"### {md(example['encabezado'])}")
    if example.get("para_que"):
        with st.container(border=True):
            st.markdown(idioma.t("dominio.show_integration_example.purpose", text=md(example["para_que"])))
            st.markdown(idioma.t("dominio.show_integration_example.parts")
                        + "\n".join(f"- **{s['titulo']}**: {md(s['parte'])}" for s in steps if s.get("parte")))
    st.caption(md(example["aviso"]))
    selected = st.radio(example["selector"], range(len(steps)),
                        format_func=lambda index: steps[index]["titulo"],
                        key=f"{key or domain}_integration_example", horizontal=True)
    step = steps[selected]
    if step.get("parte"):
        st.info(idioma.t("dominio.show_integration_example.part", part=md(step["parte"])))
    st.markdown(step["contenido"])
    missing_run_shown = False
    for n, query in enumerate(step.get("consultas", [])):
        if "{corrida_publicada}" in str(query):
            import lab
            from urllib.parse import quote
            if run_id is None:
                snapshot = lab.published_snapshot()
                run_id = snapshot["run"]["id"] if snapshot else ""
            if not run_id:
                if not missing_run_shown:
                    st.info(example["ui"]["run_missing"])
                    missing_run_shown = True
                continue
            query = {k: v.replace("{corrida_publicada}", quote(str(run_id), safe=""))
                     for k, v in query.items()}
        if "{pozo_ejemplo}" in str(query):   # the model's example well, the same one the Lab tab opens with
            import lab
            pozo = pozo if pozo is not None else lab.modelo.pozo_ejemplo(lab.datos()[1])
            query = {k: v.replace("{pozo_ejemplo}", str(pozo)) for k, v in query.items()}
        st.markdown(f"**{md(query['titulo'])}**")
        if query.get("sql"):
            columns, rows = sql_table(query["sql"], domain, approach="B")
        else:
            columns, rows = run(prefixed(query["sparql"], domain), domain)
        tabla(pd.DataFrame(rows, columns=columns), key=f"{key or domain}_paso{selected}_{n}")
        if tech:
            st.code(query.get("sql") or query["sparql"], language="sql" if query.get("sql") else "sparql")
    if step.get("entrada_pozo"):
        import lab
        lab.show_input_row(pozo, example, tech)
    if step.get("calculo_pozo"):
        import lab
        lab.show_calculation(pozo=pozo, config=example, tech=tech)
    if step.get("evidencia_pozo"):
        import lab
        st.markdown(example["ui"]["current_evidence_title"])
        tabla(lab.current_evidence(pozo).rename(columns=example["ui"]["evidence_columns"]),
              key=f"{key or domain}_current_evidence")
    if tech and step.get("tecnico"):
        st.code(step["tecnico"], language=step.get("lenguaje", "turtle"))


def show_demo(cfg, tech):
    """The demo: a few moments, each with a title, a sentence and something that runs live. Each moment is an
    example question, a change to a database, a Rastro Lab prediction or a correction."""
    domain, steps = cfg["domain"], cfg["demo"]
    key = f"{domain}_demo_step"
    i = min(st.session_state.get(key, 0), len(steps) - 1)
    if cfg.get("demo_porque"):
        with st.expander(idioma.t("dominio.show_demo.why_moments", n=len(steps))):
            st.markdown(md(cfg["demo_porque"]))
    st.markdown(" → ".join(f"**{n + 1} · {s['paso']}**" if n == i else f"{n + 1} · {s['paso']}"
                           for n, s in enumerate(steps)))
    step = steps[i]
    st.subheader(step["titulo"], help=ayuda("paso"))
    if step.get("que_es"):   # the other use cases still explain what each step is
        st.markdown(idioma.t("dominio.show_demo.what_is", step=md(step["paso"]).lower(), text=md(step["que_es"])))
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
            st.caption(idioma.t("dominio.show_demo.tech_wording") + md(item["tecnica"]))
        query = Path(item["query"]).read_text()
        columns, rows = run(query, domain)
        if item.get("antes_despues") and not item.get("porque", {}).get("recorrido"):
            before_after(item["antes_despues"])
        show_answer(cfg, tech, query, columns, rows, item, note=idioma.t("dominio.show_demo.live_note"), where="demo")
    back, _, forward = st.columns([2, 3, 2])
    if i > 0 and back.button(idioma.t("dominio.show_demo.back"), key=f"{key}_back"):
        st.session_state[key] = i - 1
        st.rerun()
    if i < len(steps) - 1 and forward.button(idioma.t("dominio.show_demo.next"), type="primary", key=f"{key}_next"):
        st.session_state[key] = i + 1
        st.rerun()


def show_change_short(cfg, changes, escenario, tech):
    """A change-test scenario, short: how many questions are still right before and after the fix."""
    change = next((c for c in cfg["cambios"] if c["antes"] == escenario), cfg["cambios"][0])
    before, after = changes.get(change["antes"]), changes.get(change["despues"])
    if not (before and after):
        st.info(idioma.t("dominio.show_change_short.missing"))
        return
    n = len(before["cells"])
    rotas = before["totals"]["B"].get("❌", 0) + before["totals"]["B"].get("🟡", 0)
    sin_query = before["totals"]["B"].get("—", 0)
    st.markdown(md(change["que"]))
    antes, despues = st.columns(2)
    with antes.container(border=True):
        st.markdown(idioma.t("dominio.show_change_short.just_changed"))
        st.markdown(idioma.t("dominio.show_change_short.without_broken", broken=rotas))
        st.markdown(idioma.t("dominio.show_change_short.with_fail", n=n))
        st.caption(idioma.t("dominio.show_change_short.fails_loud"))
    with despues.container(border=True):
        st.markdown(idioma.t("dominio.show_change_short.to_fix"))
        st.markdown(idioma.t("dominio.show_change_short.without_fix", broken=rotas))
        st.markdown(idioma.t("dominio.show_change_short.with_fix", ok=after["totals"]["C"].get("✅", 0), n=n))
        st.caption(idioma.t("dominio.show_change_short.never", n=n, never=sin_query))
    if tech:
        st.code(f"- {change['arreglo'][0]}\n+ {change['arreglo'][1]}", language="diff")


def show_correction(result, tech):
    """One correction, every result: what changes in Rastro Layer and in Rastro Lab when a concession's corrected
    share is set, without touching anything else."""
    con, sin = result.get("con"), result.get("sin")
    if not (con and sin):
        st.info(idioma.t("dominio.show_correction.missing"))
        return

    def m3(v):
        return f"{idioma.number(v / 1e6, 2)} M m³"

    def pct(v):
        return f"{v:g} %" if idioma.lang() == "en" else f"{v:g} %".replace(".", ",")

    filas = [   # (where, without the correction, with the correction)
        (idioma.t("dominio.show_correction.row_rastro"), m3(sin["layer_C"]), m3(con["layer_C"])),
        (idioma.t("dominio.show_correction.row_sql_rastro"), m3(sin["layer_D"]), m3(con["layer_D"])),
        (idioma.t("dominio.show_correction.row_without"), m3(sin["layer_B"]), m3(con["layer_B"])),
        (idioma.t("dominio.show_correction.row_input_with"), pct(sin["lab_B_pct"]), pct(con["lab_B_pct"])),
        (idioma.t("dominio.show_correction.row_input_without"), pct(sin["lab_A_pct"]), pct(con["lab_A_pct"])),
        (idioma.t("dominio.show_correction.row_explanation"), idioma.t("dominio.show_correction.unmarked"),
         idioma.t("dominio.show_correction.marked") if con["lab_B_marca"] else idioma.t("dominio.show_correction.unmarked")),
    ]
    yes, no = idioma.t("dominio.show_correction.yes"), idioma.t("dominio.show_correction.no")
    headers = [idioma.t(f"dominio.show_correction.col_{c}") for c in ("where", "before", "after", "changed")]
    df = pd.DataFrame([dict(zip(headers, (a, b, c, yes if b != c else no))) for a, b, c in filas])
    st.caption(idioma.t("dominio.show_correction.what"))
    tabla(df, key="demo_correccion")
    st.markdown(md(idioma.t("dominio.show_correction.where_fixed", places=result["lugares_sin_rastro"])))
    if tech:
        st.caption(idioma.t("dominio.show_correction.measured"))


GRAPHDB = "http://graphdb:7200/repositories/rastro"


def claim_verdict(reading, rows):
    """The verdict on one reading of the claim, computed from what Rastro returned."""
    if reading["tipo"] == "sin_datos":
        return "🔍", idioma.t("dominio.claim_verdict.no_data"), reading["falta"]
    def fmt(v):
        return f"{idioma.number(float(v) / reading['divisor'], 1)} {reading['unidad']}"
    if reading["tipo"] == "numero":
        value = float(rows[0][0]) / reading["divisor"]
        holds = abs(value - reading["valor"]) <= 0.05 * reading["valor"]
        says = idioma.t("dominio.claim_verdict.says", value=fmt(rows[0][0]))
        return ("✅", idioma.t("dominio.claim_verdict.holds"), says) if holds else \
            ("❌", idioma.t("dominio.claim_verdict.does_not_hold"), says)
    names = [r[0] for r in rows]
    place = next((i for i, n in enumerate(names) if reading["empresa"] in n.upper()), None)
    ranking = " · ".join(f"{i + 1}. {r[0]} ({fmt(r[1])})" for i, r in enumerate(rows[:3]))
    if place == 0:
        return "✅", idioma.t("dominio.claim_verdict.holds"), ranking
    where = idioma.t("dominio.claim_verdict.place", place=place + 1) if place is not None \
        else idioma.t("dominio.claim_verdict.not_in_top", n=len(rows))
    return "❌", idioma.t("dominio.claim_verdict.does_not_hold_where", where=where), ranking


def show_claims(cfg, tech):
    """Check a claim: each example is compared live with Rastro, reading by reading."""
    claims, domain = cfg["afirmaciones"], cfg["domain"]
    st.markdown(md(claims["intro"]))
    chosen = st.radio(idioma.t("dominio.show_claims.claim"), [c["texto"] for c in claims["ejemplos"]], key=f"{domain}_afirmacion")
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
    """Enrich with outside data: a federated query in GraphDB joins Rastro with Wikidata through a
    shared identifier. It runs live if asked; otherwise, the saved result is shown. Below, the same
    enrichment saved in Rastro (show_enrichment_saved)."""
    ext, domain = cfg["externo"], cfg["domain"]
    st.markdown(f"**{ext['titulo']}**", help=ayuda("externo"))
    st.markdown(md(ext["intro"]))
    graph = {name: idioma.t(f"dominio.show_external.graph_{name}") for name in ("rastro", "wikidata", "query", "lei")}
    st.graphviz_chart(f"""digraph {{ rankdir=LR; bgcolor="transparent";
        node [fontname="Helvetica", fontsize=14, style=filled, penwidth=0];
        r [label="{graph['rastro']}", shape=ellipse, fillcolor="#2F6FB5", fontcolor="white"];
        w [label="{graph['wikidata']}", shape=ellipse, fillcolor="#FFF3E6", color="#FF8C42", penwidth=2];
        q [label="{graph['query']}", shape=box, style="rounded,filled", fillcolor="#F4F6F9", color="#B8C2CF", penwidth=1];
        r -> q [label="{graph['lei']}", dir=both, color="#7A8699", fontcolor="#7A8699", fontname="Helvetica"];
        q -> w [dir=both, color="#7A8699"]; }}""", use_container_width=True)
    key = f"{domain}_externo"
    if st.button(idioma.t("dominio.show_external.live"), type="primary", key=f"{key}_boton",
                 help=idioma.t("dominio.show_external.live_help")):
        try:
            r = requests.post(GRAPHDB, data={"query": Path(ext["consulta"]).read_text()},
                              headers={"Accept": "text/csv"}, timeout=90)
            r.raise_for_status()
            st.session_state[key] = (pd.read_csv(io.StringIO(r.text)), idioma.t("dominio.show_external.live_now"))
        except Exception as e:
            st.session_state[key] = None
            st.warning(idioma.t("dominio.show_external.no_answer", error=str(e)[:120]))
    table, when = st.session_state.get(key) or (pd.read_csv(ext["guardado"]),
                                                idioma.t("dominio.show_external.saved_on", date=ext["fecha_guardado"]))
    columns = [c for c in ext["columnas"] if c in table.columns and (tech or c not in ("lei", "wikidata"))]
    shown = table[columns].copy()
    for c in ("su_parte_m3", "declara_m3"):
        if c in shown:
            shown[c] = shown[c].map(lambda v: money(v) if pd.notna(v) else "—")
    shown = shown.fillna("—").rename(columns=ext["columnas"])
    shown, config = logos.with_logos(shown, columns)
    tabla(shown, hide_index=True, use_container_width=True, column_config=config)
    st.caption(idioma.t("dominio.show_external.result", when=when))
    st.info(md(ext["conclusion"]))
    with st.expander(idioma.t("dominio.show_external.query")):
        st.code(Path(ext["consulta"]).read_text(), language="sparql")
    if ext.get("materializado"):
        show_enrichment_saved(ext, domain, tech)


def show_enrichment_saved(ext, domain, tech):
    """The same enrichment, saved in Rastro: what the outside source answered stays as one more source,
    with its date, and is queried like any other data."""
    st.markdown(idioma.t("dominio.show_enrichment_saved.title"), help=ayuda("externo"))
    query = Path(ext["materializado"]).read_text()
    columns, rows = run(query, domain)
    if not rows:
        st.info(idioma.t("dominio.show_enrichment_saved.not_saved"))
        return
    headers = {c: idioma.t(f"dominio.show_enrichment_saved.col_{name}")
               for c, name in [("empresa", "company"), ("bolsa", "exchange"), ("sede", "headquarters"), ("consultado", "queried")]}
    tabla(pd.DataFrame(rows, columns=columns).rename(columns=headers | {"wikidata": "Wikidata"}),
          hide_index=True, use_container_width=True)
    st.caption(md(idioma.t("dominio.show_enrichment_saved.explain")))
    if tech:
        st.code(query, language="sparql")


def text_step(n, title, help_text=None):
    st.markdown(f"#### {n} · {title}", help=help_text)


def show_text_question(cfg, tech, demo=False):
    """A question over texts, step by step (GraphRAG grounded in the graph): the graph picks the
    records with an exact query, an AI assistant reads only those texts and summarizes them in themes that
    cite each record, and anyone can check it. The summary is saved; the records are read
    live."""
    domain = cfg["domain"]
    item = read_json(cfg["texto"])
    st.markdown(idioma.t("dominio.show_text_question.steps"), help=ayuda("texto"))
    text_step(1, idioma.t("dominio.show_text_question.question"))
    st.info(f"**{md(item['simple'])}**")
    if tech:
        st.caption(idioma.t("dominio.show_text_question.tech_wording") + md(item["pregunta"]))
    if not demo:
        if st.button(idioma.t("dominio.show_text_question.answer"), type="primary", key=f"{domain}_text_answer"):
            st.session_state[f"{domain}_text_shown"] = True
        if not st.session_state.get(f"{domain}_text_shown"):
            return
    query = Path(item["consulta"]).read_text()
    _, rows = run(query, domain)
    graph_part, _, ai_part = item["como"].partition("Un asistente de IA")
    ai_part = ("Un asistente de IA" + ai_part) if ai_part else ""

    # The records, with their texts and what each theme cites: contracts (with amounts) or any records
    if "columnas" in item:
        records = {r[0]: r for r in rows}
        unit = item["unidad"]
        table = pd.DataFrame([list(r) for r in records.values()], columns=item["columnas"])
        themes = [(th["tema"], [r for r in th["registros"] if r in records], th["detalle"], "") for th in item["temas"]]
    else:
        records = {c: (float(m), a, e, d) for c, m, a, e, d in rows}
        unit = [idioma.t("dominio.show_text_question.contract"), idioma.t("dominio.show_text_question.contracts")]
        headers = [idioma.t(f"dominio.show_text_question.col_{c}") for c in ("contract", "millions", "agency", "company", "description")]
        table = pd.DataFrame([dict(zip(headers, (c, round(m / 1e6, 1), a.title(), e.title(), d.capitalize())))
                              for c, (m, a, e, d) in records.items()])
        themes = []
        for th in item["temas"]:
            found = [c for c in th["contratos"] if c in records]
            themes.append((th["tema"], found, th["detalle"],
                           idioma.t("dominio.show_text_question.amount", amount=money(sum(records[c][0] for c in found) / 1e6))))
    n = len(records)

    text_step(2, idioma.t("dominio.show_text_question.graph_picks"), idioma.t("dominio.show_text_question.graph_picks_help"))
    st.markdown(md(graph_part.strip()))
    st.metric(idioma.t("dominio.show_text_question.picked", units=unit[1].capitalize()), n)
    with st.expander(idioma.t("dominio.show_text_question.query"), expanded=tech):
        st.caption(idioma.t("dominio.show_text_question.query_caption"))
        st.code(query, language="sparql")
    if demo and item.get("busqueda_texto"):
        compare_text_search(item, records, domain, tech, always=True)

    text_step(3, idioma.t("dominio.show_text_question.ai_reads"), idioma.t("dominio.show_text_question.ai_reads_help"))
    st.markdown(md(ai_part.strip()) or idioma.t("dominio.show_text_question.ai_read", n=n, units=unit[1]))
    with st.expander(idioma.t("dominio.show_text_question.texts_read", n=n)):
        tabla(table, hide_index=True, use_container_width=True)

    text_step(4, idioma.t("dominio.show_text_question.summary"))
    for theme, found, detail, extra in themes:
        st.markdown(idioma.t("dominio.show_text_question.theme", theme=md(theme), n=len(found),
                             unit=unit[0] if len(found) == 1 else unit[1], extra=extra, detail=md(detail),
                             cited=", ".join(found)), unsafe_allow_html=True)

    text_step(5, idioma.t("dominio.show_text_question.check"), idioma.t("dominio.show_text_question.check_help"))
    st.markdown(idioma.t("dominio.show_text_question.check_text", units=unit[1], date=item["fecha"]))
    if item.get("busqueda_texto") and not demo:
        compare_text_search(item, records, domain, tech)


def company(name):
    """«DYNETICS, INC.» → «Dynetics»: the name without the legal form, to read in a sentence."""
    name = re.sub(r",?\s+(INC|LLC|CORP|CORPORATION|CO|LTD)\.?$", "", name.strip(), flags=re.I)
    return " ".join(w if len(w) <= 3 and w.isupper() else w.capitalize() for w in name.split())


def compare_text_search(item, contracts, domain, tech, always=False):
    """The same, searching for «Leidos» in the texts instead of using the graph (what a common RAG would do)."""
    if not always and not st.toggle(idioma.t("dominio.compare_text_search.toggle"), key=f"{domain}_text_search"):
        return
    query = Path(item["busqueda_texto"]).read_text()
    _, rows = run(query, domain)
    found = {c for c, *_ in rows}
    missing = {c: v for c, v in contracts.items() if c not in found}
    lost = [t["tema"] for t in item["temas"] if t["contratos"] and all(c in missing for c in t["contratos"])]
    companies = sorted({company(e) for _, _, e, _ in missing.values()})
    before_after({
        "titulo_sin": idioma.t("dominio.compare_text_search.without_title"),
        "sin": {"valor": idioma.t("dominio.compare_text_search.of", found=len(contracts) - len(missing), total=len(contracts)),
                "detalle": (idioma.t("dominio.compare_text_search.misses", n=len(missing),
                                     amount=money(sum(m for m, *_ in missing.values()) / 1e6), companies=", ".join(companies))
                            + (idioma.t("dominio.compare_text_search.lost", themes=", ".join(lost).lower()) if lost else ""))},
        "con": {"valor": idioma.t("dominio.compare_text_search.of", found=len(contracts), total=len(contracts)),
                "detalle": idioma.t("dominio.compare_text_search.with_detail")}})
    st.caption(idioma.t("dominio.compare_text_search.caption"))
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
    if not cfg.get("tarjetas"):   # not measured yet: say so, and show only what has been checked
        st.markdown(idioma.t("dominio.trust.title"), help=ayuda("confiar"))
        if cfg.get("sin_medir"):
            st.info(md(cfg["sin_medir"]))
        show_quality(cfg.get("calidad"))
        show_no_data(cfg.get("fuera"), tech)
        return
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
        numbers.update(pct_evidencia=idioma.t("dominio.trust.yes"), n_enlaces=idioma.t("dominio.trust.all_links"),
                       cols=idioma.t("dominio.trust.the_columns"), cols_ok=idioma.t("dominio.trust.all_columns"))
    st.markdown(idioma.t("dominio.trust.title"), help=ayuda("confiar"))
    st.caption(idioma.t("dominio.trust.same_assistant"))
    card_help = ["tarjeta_correctas", "tarjeta_consistencia", "tarjeta_cambio", "tarjeta_auditar"]
    for k, (col, card) in enumerate(zip(st.columns(len(cfg["tarjetas"])), cfg["tarjetas"])):
        with col.container(border=True):
            st.markdown(f"**{md(card['titulo'])}**", help=ayuda(card_help[k]) if k < len(card_help) else None)
            st.markdown(f'<p style="font-size:2.4rem;line-height:1.1;margin:0">{card["valor"].format(**numbers)}</p>',
                        unsafe_allow_html=True)
            st.caption(md(card["compara"].format(**numbers)))

    # In technical mode the fair baseline is added: SQL with Rastro's link tables
    without, with_rastro = idioma.t("dominio.trust.without"), idioma.t("dominio.trust.with")
    names = ({"B": without, "D": idioma.t("dominio.trust.sql_links"), "C": with_rastro} if tech
             else {"B": without, "C": with_rastro})
    names = {k: v for k, v in names.items() if all(k in r for r in consistency.values())}
    change_names = {"B": without, "C": with_rastro}
    question_col, asked_col = idioma.t("dominio.trust.col_question"), idioma.t("dominio.trust.col_asked")
    simple = {q["id"]: q["simple"] for q in cfg["preguntas"]}
    n = len(evaluation.get("questions", {}))
    # The three tests, kept apart: in the technical view, one tab each, so that picking a question
    # in one test does not seem to change the others
    if tech:
        tab_correct, tab_same, tab_change = st.tabs([idioma.t("dominio.trust.tab_correct", n=n),
                                                     idioma.t("dominio.trust.tab_same", n=len(consistency)),
                                                     idioma.t("dominio.trust.tab_change", n=n)])
        with tab_correct:
            if evaluation.get("questions"):
                evaluation_detail(evaluation, totals, cfg["domain"])
    with tab_same if tech else st.expander(idioma.t("dominio.trust.see_answers", n=4 * len(consistency))):
        st.caption(idioma.t("dominio.trust.four_ways", n=len(consistency)))
        table = []
        for qid, row in consistency.items():
            line = {question_col: row["texts"][0] if tech else simple.get(qid, row["texts"][0])}
            for k, title in names.items():
                line[title] = ("✅ " if row[k]["same"] else "❌ ") + " · ".join(short(a) for a in row[k]["answers"])
            table.append(line)
        tabla(pd.DataFrame(table), hide_index=True, use_container_width=True,
                     column_config={question_col: st.column_config.TextColumn(width="medium")})
        st.caption(idioma.t("dominio.trust.same_legend"))
        if consistency:
            labels = {qid: simple.get(qid, row["texts"][0]) for qid, row in consistency.items()}
            picked = st.selectbox(idioma.t("dominio.trust.see_four"), list(labels.values()),
                                  key=f"{cfg['domain']}_consistency")
            qid = next(k for k, v in labels.items() if v == picked)
            row = consistency[qid]
            tabla(pd.DataFrame([{asked_col: t, **{names[k]: short(row[k]["answers"][i])
                                                                    for k in names}}
                                       for i, t in enumerate(row["texts"])]),
                         hide_index=True, use_container_width=True,
                         column_config={asked_col: st.column_config.TextColumn(width="large")})

    with tab_change if tech else st.expander(idioma.t("dominio.trust.see_scenarios")):
        scenarios = {c["titulo"]: c for c in cfg.get("cambios", [])}
        st.caption(idioma.t("dominio.trust.scenarios_caption"))
        picked = st.radio(idioma.t("dominio.trust.scenario"), list(scenarios), horizontal=True, label_visibility="visible",
                          help=ayuda("escenario"), key=f"{cfg['domain']}_scenario")
        change = scenarios[picked]
        before, after = changes.get(change["antes"]), changes.get(change["despues"])
        st.markdown(md(change["que"]))
        if tech:
            st.code(change["sql"], language="sql")
        if before and after:
            status = {"✅": idioma.t("dominio.trust.status_same"), "🟡": idioma.t("dominio.trust.status_different"),
                      "❌": idioma.t("dominio.trust.status_error")}

            def summary(t):
                return " · ".join(f"{v} {status.get(s, s)}" for s, v in sorted(t.items(), key=lambda x: x[0] != "✅"))

            st.markdown(idioma.t("dominio.trust.before_fix"))
            for col, k in zip(st.columns(2), change_names):
                col.metric(change_names[k], f"{before['totals'][k].get('✅', 0)}/{len(before['cells'])}")
                col.caption(summary(before["totals"][k]))
            if before["totals"]["C"].get("❌", 0) > before["totals"]["B"].get("❌", 0):
                st.caption(idioma.t("dominio.trust.fails_more"))
            if "🟡" in before.get("vocabulary", ""):
                st.warning(idioma.t("dominio.trust.warns") + md(before["vocabulary"].split(": ", 1)[-1]))
            if tech:
                st.markdown(idioma.t("dominio.trust.fix_tech", where=change.get("donde", idioma.t("dominio.trust.of_mapping"))))
                st.code(f"- {change['arreglo'][0]}\n+ {change['arreglo'][1]}", language="diff")
            else:
                st.markdown(idioma.t("dominio.trust.fix"))
            st.markdown(idioma.t("dominio.trust.after_fix"))
            for col, k in zip(st.columns(2), change_names):
                col.metric(change_names[k], f"{after['totals'][k].get('✅', 0)}/{len(after['cells'])}")
                col.caption(summary(after["totals"][k]) + ("" if k == "C" else idioma.t("dominio.trust.rewrite_each")))
            if tech:
                st.markdown(idioma.t("dominio.trust.by_question"))
                tabla(pd.DataFrame([{question_col: simple.get(qid, qid),
                                            **{idioma.t("dominio.trust.col_before", name=change_names[k]): before["cells"][qid][k]
                                               for k in change_names},
                                            **{idioma.t("dominio.trust.col_after", name=change_names[k]): after["cells"][qid][k]
                                               for k in change_names}}
                                           for qid in before["cells"]]),
                             hide_index=True, use_container_width=True,
                             column_config={question_col: st.column_config.TextColumn(width="medium")})
        st.info(idioma.t("dominio.trust.one_place"))
    show_quality(cfg.get("calidad"))
    show_no_data(cfg.get("fuera"), tech)


def show_no_data(fuera, tech):
    """Does it say when it lacks the data? The questions outside the data, approach by approach."""
    path = fuera.get("archivo") if fuera else None
    if not path or not Path(path).exists():
        return
    result = read_json(path)
    st.markdown(idioma.t("dominio.show_no_data.title"), help=ayuda("fuera"))
    st.caption(md(fuera["intro"]))
    # The approaches' names come from the measurement file, in Spanish; in English they are mapped by their code
    names = {k: v if idioma.lang() == "es" else idioma.t(f"dominio.paths.{k}")
             for k, v in result["caminos"].items() if tech or k != "D"}
    n = len(result["preguntas"])
    for col, (k, name) in zip(st.columns(len(names)), names.items()):
        col.metric(name, idioma.t("dominio.show_no_data.of", found=result["totales"][k], n=n))
    question_col = idioma.t("dominio.show_no_data.col_question")
    tabla(pd.DataFrame([{question_col: row["pregunta"], idioma.t("dominio.show_no_data.col_missing"): row["falta"],
                         **{name: f"{row[k]['marca']} {row[k]['respuesta']}" for k, name in names.items()}}
                        for row in result["preguntas"].values()]),
          column_config={question_col: st.column_config.TextColumn(width="medium")})
    st.caption(idioma.t("dominio.show_no_data.legend"))


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
