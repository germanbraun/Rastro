"""«Bajo el capó» (the technical view): dictionary, mappings, instances as RDF, quality rules, the SPARQL console and
the map.
"""

import base64
import re
import time
from pathlib import Path

import pandas as pd
import requests
import sqlparse
import streamlit as st

import answer
import enlaces
import idioma

from . import common


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
    g = rdflib.Graph().parse(common.ontology_file(domain))
    ns = answer.DOMAINS[domain]["namespace"]

    def name(x):
        return common.short_iri(str(x), domain) if x else ""

    def text(x, prop):
        return " ".join(str(o) for o in g.objects(x, prop))

    def col(key):
        return idioma.t(f"dominio.ontology_doc.col_{key}")

    sections = []   # (fixed internal name, visible title, rows)
    for section, kind in [("classes", OWL.Class), ("relations", OWL.ObjectProperty), ("attributes", OWL.DatatypeProperty)]:
        rows = []
        for s in sorted(set(g.subjects(RDF.type, kind)), key=str):
            if not str(s).startswith(ns):
                continue
            row = {col("term"): name(s), col("label"): text(s, RDFS.label), col("description"): text(s, RDFS.comment)}
            if kind == OWL.Class:
                row[col("subclass_of")] = ", ".join(name(o) for o in g.objects(s, RDFS.subClassOf)
                                                    if isinstance(o, rdflib.URIRef))
            else:
                row[col("from")] = ", ".join(name(o) for o in g.objects(s, RDFS.domain))
                row[col("to")] = ", ".join(name(o) for o in g.objects(s, RDFS.range))
            rows.append(row)
        sections.append((section, idioma.t(f"dominio.ontology_doc.{section}"), rows))
    return sections


def show_pieces(domain, diagram=None):
    """The technical tab «Diccionario, enlaces y mapeos»."""
    pieces = common.technical(domain).get("pieces", {})
    st.markdown(idioma.t("dominio.show_pieces.dictionary_title"), help=common.ayuda("ontologia"))
    st.caption(idioma.t("dominio.show_pieces.dictionary_caption", file=common.ontology_file(domain).replace('/ontology/', 'ontology/')))
    if diagram and Path(f"/app/{diagram}.svg").exists():
        with st.expander(idioma.t("dominio.show_pieces.drawn"), expanded=False):
            svg = base64.b64encode(Path(f"/app/{diagram}.svg").read_bytes()).decode()
            st.markdown(f'<img src="data:image/svg+xml;base64,{svg}" style="width:100%">', unsafe_allow_html=True)
    description = idioma.t("dominio.ontology_doc.col_description")
    for section, title, rows in ontology_doc(domain):
        with st.expander(f"{title} ({len(rows)})", expanded=section == "classes"):
            common.tabla(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                         column_config={description: st.column_config.TextColumn(width="large")})
    if pieces.get("enlaces"):
        st.markdown(idioma.t("dominio.show_pieces.links_title"), help=common.ayuda("enlaces"))
        st.caption(idioma.t("dominio.show_pieces.links_caption"))
        for title, query in pieces["enlaces"]:
            st.markdown(f"**{title}**")
            try:
                cols, rows = common.sql_table(query, domain)
                common.tabla(enlaces.add_status(pd.DataFrame(rows, columns=cols)), hide_index=True,
                      use_container_width=True, column_config=enlaces.column_help())
            except Exception as e:
                st.warning(idioma.t("dominio.show_pieces.unreadable", error=str(e)[:200]))
            with st.expander(idioma.t("dominio.show_pieces.query")):
                st.code(sqlparse.format(query, reindent=True, keyword_case="upper"), language="sql")
    if pieces.get("mapas"):
        st.markdown(idioma.t("dominio.show_pieces.mappings_title"), help=common.ayuda("mapeos"))
        st.caption(idioma.t("dominio.show_pieces.mappings_caption", file=pieces['mapeos'].lstrip('/')))
        for title, names in pieces["mapas"]:
            with st.expander(title):
                st.code("\n\n".join(mapping_blocks(pieces["mapeos"], names)), language="turtle")


def prov_names():
    """PROV-O terms in business words, in the interface's language."""
    return {common.PROV_NS + term: idioma.t(f"dominio.prov.{term}") for term in ("wasDerivedFrom", "wasGeneratedBy", "Entity")}


def instance_graph(iri, rows, domain, title=None):
    """The instance as a graph (app/grafo.py): bubbles for entities, orange bubbles for
    classes, rectangles for plain values and arrows with each property's business name.
    Returns the SVG and the linked entities, to follow them."""
    import grafo
    ns, names = answer.DOMAINS[domain]["namespace"], {**common.labels(domain), **prov_names()}
    linked = [o for p, o in rows if o.startswith("http") and p != common.RDF_TYPE]
    named = {}
    if linked:
        values = " ".join(f"<{o}>" for o in set(linked))
        named = dict(common.run(f"SELECT ?o ?n WHERE {{ VALUES ?o {{ {values} }} ?o <{ns}name> ?n }}", domain)[1])
    own = next((o for p, o in rows if p == f"{ns}name"), None)
    nodes = []
    for p, o in rows:
        prop = idioma.t("dominio.instance_graph.is_a") if p == common.RDF_TYPE else names.get(p) or common.short_iri(p, domain)
        if p == common.RDF_TYPE:
            nodes.append(("clase", names.get(o) or common.short_iri(o, domain), common.short_iri(o, domain), prop))
        elif o.startswith("http"):
            nodes.append(("entidad", named.get(o) or o.rstrip("/").split("/")[-1], common.short_iri(o, domain), prop))
        else:
            nodes.append(("dato", o, "", prop))
    drawing = grafo.svg((own or title or iri.rstrip("/").split("/")[-1], common.short_iri(iri, domain)), nodes,
                        width=1500, height=620 + 55 * max(0, len(nodes) - 8), scale=0.95,
                        font="Helvetica, Arial, sans-serif")   # more properties, taller: they do not overlap
    return drawing, [o for o in dict.fromkeys(linked) if o not in names]


def show_instances(domain):
    """A real instance of the graph, drawn as a graph: each link to another entity can be followed,
    inside the app. Below, its properties in a table and in Turtle."""
    examples = common.technical(domain).get("instances")
    if not examples:
        return
    st.markdown(idioma.t("dominio.show_instances.title"), help=common.ayuda("instancia"))
    st.caption(idioma.t("dominio.show_instances.caption"))
    key = f"{domain}_instancia"
    chosen = st.selectbox(idioma.t("dominio.show_instances.start"), list(examples), key=key)
    if st.session_state.get(f"{key}_desde") != chosen:      # a new example restarts the path
        st.session_state[f"{key}_desde"], st.session_state[f"{key}_actual"] = chosen, examples[chosen]
    iri = st.session_state[f"{key}_actual"]
    _, rows = common.run(f"SELECT ?p ?o WHERE {{ <{iri}> ?p ?o }} ORDER BY ?p", domain)
    if not rows:
        st.info(idioma.t("dominio.show_instances.no_more"))
    title = chosen.split(": ", 1)[-1] if iri == examples[chosen] else None
    graph, neighbours = instance_graph(iri, rows, domain, title)
    st.markdown(f'<img src="data:image/svg+xml;base64,{base64.b64encode(graph.encode()).decode()}" '
                'style="width:100%;border-radius:12px">', unsafe_allow_html=True)
    nav, back = st.columns([4, 1])
    if neighbours:
        go = nav.selectbox(idioma.t("dominio.show_instances.follow"), ["—"] + neighbours,
                           format_func=lambda o: o if o == "—" else common.short_iri(o, domain), key=f"{key}_ir_{iri}")
        if go != "—":
            st.session_state[f"{key}_actual"] = go
            st.rerun()
    if iri != examples[chosen] and back.button(idioma.t("dominio.show_instances.back"), key=f"{key}_volver"):
        st.session_state[f"{key}_actual"] = examples[chosen]
        st.rerun()
    st.caption(f"IRI: `{iri}`")
    names = common.labels(domain)
    with st.expander(idioma.t("dominio.show_instances.as_table")):
        prop, label, value = (idioma.t(f"dominio.show_instances.col_{c}") for c in ("property", "label", "value"))
        table = [{prop: common.short_iri(p, domain),
                  label: idioma.t("dominio.instance_graph.is_a") if p == common.RDF_TYPE else names.get(p, ""),
                  value: (f"{common.short_iri(o, domain)}" + (f" ({names[o]})" if o in names else "")) if o.startswith("http") else o}
                 for p, o in rows]
        common.tabla(pd.DataFrame(table), hide_index=True, use_container_width=True)
    lines = [f"<{common.short_iri(iri, domain)}>"]
    for k, (p, o) in enumerate(rows):
        value = common.short_iri(o, domain) if o.startswith("http") else '"' + o.replace('"', '\\"') + '"'
        value = f"<{value}>" if value.startswith("rastro:") else value
        lines.append(f"    {common.short_iri(p, domain)} {value}" + (" ." if k == len(rows) - 1 else " ;"))
    with st.expander(idioma.t("dominio.show_instances.turtle")):
        st.code("\n".join(lines), language="turtle")
    st.divider()


def under_the_hood(domain, diagram=None, quality=None):
    """«Bajo el capó» (technical view): the SPARQL console, a graph instance and the dictionary, the
    links and the mappings, in a single tab."""
    names = ["console", "pieces"] + (["quality"] if quality else [])
    console, pieces, *rules = st.tabs([idioma.t(f"dominio.under_the_hood.tab_{name}") for name in names])
    with console:
        sparql_console(domain)
    with pieces:
        show_pieces(domain, diagram)
    if quality:
        with rules[0]:
            show_quality_shacl(quality)


def quality_result(quality):
    path = quality.get("archivo") if quality else None
    return common.read_json(path) if path and Path(path).exists() else None


def finding(rule, long=True):
    """A rule's result in words: violations do not hold; warnings and informational findings ask a person to review."""
    if not rule["revisados"]:
        return idioma.t("dominio.finding.no_data") if long else "⏳"
    counts = rule.get("por_severidad") or {"Violation": rule["fallas"]}
    words = {kind: idioma.t(f"dominio.finding.{kind.lower()}") if long else "" for kind in ("Violation", "Warning", "Info")}
    parts = [f"⚠️ {common.money(counts['Violation'])}" + words["Violation"] if counts.get("Violation") else "",
             f"🟡 {common.money(counts['Warning'])}" + words["Warning"] if counts.get("Warning") else "",
             f"ℹ️ {common.money(counts['Info'])}" + words["Info"] if counts.get("Info") else ""]
    return " · ".join(p for p in parts if p) or (idioma.t("dominio.finding.holds") if long else "✅")


def show_quality(quality):
    """The quality rules, in business words: what is checked and whether it holds."""
    result = quality_result(quality)
    if not result:
        return
    st.markdown(idioma.t("dominio.show_quality.title"), help=common.ayuda("calidad"))
    st.caption(common.md(quality["intro"]))
    rule, why = idioma.t("dominio.show_quality.col_rule"), idioma.t("dominio.show_quality.col_why")
    common.tabla(pd.DataFrame([{rule: r["nombre"], why: r["porque"],
                                idioma.t("dominio.show_quality.col_checked"): common.money(r["revisados"]),
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
        st.caption(idioma.t("dominio.show_quality_shacl.not_checked"))
        return
    st.markdown(idioma.t("dominio.show_quality_shacl.title"), help=common.ayuda("calidad_shacl"))
    st.caption(common.md(quality["tecnico"]))

    def col(key):
        return idioma.t(f"dominio.show_quality_shacl.col_{key}")

    for r in result["reglas"]:
        mark = finding(r, long=False)
        with st.expander(idioma.t("dominio.show_quality_shacl.rule", mark=mark, name=r['nombre'], n=common.money(r['revisados']))):
            st.markdown(idioma.t("dominio.show_quality_shacl.in_shacl"))
            st.code(r["shacl"], language="turtle")
            if r.get("un_dato"):
                good, bad = st.columns(2)
                with good:
                    st.markdown(idioma.t("dominio.show_quality_shacl.good"))
                    st.code(r["un_dato"], language="turtle")
                with bad:
                    st.markdown(idioma.t("dominio.show_quality_shacl.broken"))
                    st.code(r["roto"], language="turtle")
                    st.caption(idioma.t("dominio.show_quality_shacl.says") + " ".join(r["roto_dice"]))
            if r["ejemplos"]:
                st.markdown(idioma.t("dominio.show_quality_shacl.fails")
                            + (idioma.t("dominio.show_quality_shacl.first_10") if r["fallas"] > 10 else ""))
                common.tabla(pd.DataFrame([{col("data"): e["dato"], col("what_fails"): e["mensaje"],
                                     **({col("severity"): e["severidad"]} if e.get("severidad") else {}),
                                     col("predictions"):
                                         ", ".join(p.rsplit("/", 1)[-1] for p in e.get("predicciones", []))}
                                    for e in r["ejemplos"]]))
    st.caption(idioma.t("dominio.show_quality_shacl.triples", n=common.money(result['triples'])))


def sparql_console(domain):
    """A console to write and run SPARQL over the domain's Ontop, with the SQL it generates."""
    method = answer.DOMAINS[domain]["method"]
    folder, port = str(answer.ROOT / method["queries"]), method["ontop"]["port"]
    show_instances(domain)
    st.markdown(idioma.t("dominio.sparql_console.title"), help=common.ayuda("consola"))
    st.caption(idioma.t("dominio.sparql_console.caption", port=port))
    examples = {}
    for f in sorted(Path(folder).glob("*.rq")):
        text = f.read_text()
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), f.stem)
        examples[title] = text
    key = f"{domain}_console"
    chosen = st.selectbox(idioma.t("dominio.sparql_console.start"), [idioma.t("dominio.sparql_console.blank")] + list(examples),
                          key=f"{key}_ejemplo")
    if st.session_state.get(f"{key}_cargada") != chosen:   # when the example changes, it is loaded into the editor
        st.session_state[f"{key}_cargada"] = chosen
        st.session_state[f"{key}_texto"] = examples.get(
            chosen, f"PREFIX {domain}: <{answer.DOMAINS[domain]['namespace']}>\nSELECT * WHERE {{ ?s ?p ?o }} LIMIT 10")
    query = st.text_area(idioma.t("dominio.sparql_console.query"), key=f"{key}_texto", height=280)
    if st.button(idioma.t("dominio.sparql_console.run"), type="primary", key=f"{key}_ejecutar"):
        started = time.time()
        try:
            columns, rows = common.run(query, domain)
        except Exception as e:  # noqa: BLE001 - Ontop's error is shown as is
            st.error(str(e).strip()[:2000])
            return
        st.caption(idioma.t("dominio.sparql_console.rows_one" if len(rows) == 1 else "dominio.sparql_console.rows_many",
                            n=len(rows), seconds=f"{time.time() - started:.1f}"))
        common.tabla(pd.DataFrame(rows, columns=columns), hide_index=True, use_container_width=True)
        with st.expander(idioma.t("dominio.sparql_console.sql")):
            try:
                st.code(sqlparse.format(answer.ontop_sql(query, domain), reindent=True, keyword_case="upper",
                                        indent_width=2), language="sql")
            except requests.RequestException:
                st.caption(idioma.t("dominio.show_answer.no_sql"))


GEO = "PREFIX geo: <http://www.opengis.net/ont/geosparql#>\n"


def wkt_coords(wkt):
    """The coordinates of a simple WKT: POINT → [x, y]; POLYGON → [[x, y], ...]; MULTILINESTRING → [[[x, y], ...], ...]."""
    groups = [[[float(v) for v in pair.split()] for pair in part.split(",")]
              for part in re.findall(r"\(([^()]+)\)", wkt)]
    if wkt.startswith("POINT"):
        return groups[0][0]
    return groups[0] if wkt.startswith("POLYGON") else groups


def map_data(domain):
    with st.spinner(idioma.t("dominio.map_data.spinner")):
        return _map_data(domain)


@st.cache_data(show_spinner=False)
def _map_data(domain):
    config = common.technical(domain).get("map")
    if not config:
        raise ValueError("This domain has no map configuration")
    concessions, points, pipes = [common.run(common.prefixed(config["queries"][key], domain), domain)[1]
                                  for key in ("concessions", "points", "pipes")]
    return concessions, points, pipes


def show_map(domain):
    """Concessions, possible venting seen by satellite and transport gas pipelines, all read from Rastro."""
    import pydeck as pdk
    concessions, points, pipes = map_data(domain)
    review = idioma.t("dominio.show_map.review")
    polys = [{"contorno": wkt_coords(w), "nombre": n, "operadora": o or "—", "venteos": int(v or 0),
              "revisar": review + r if r else "",
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
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(**common.technical(domain)["map"]["view_state"]),
                             tooltip={"html": common.technical(domain)["map"]["tooltip"]}),
                    use_container_width=True)
    st.caption(common.technical(domain)["map"].get("caption", ""), help=common.ayuda("mapa"))
