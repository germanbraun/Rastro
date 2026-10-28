"""«Preguntar»: an answer with its sources and evidence, «¿Por qué este número?», the demo, claims, outside data and
questions over texts.
"""

import base64
import io
import os
import re
from pathlib import Path

import pandas as pd
import requests
import sqlparse
import streamlit as st

import answer
import contraste
import enlaces
import idioma

from . import common
from . import extension
from . import hood
from . import trust_view


def as_table(columns, rows, cfg, tech, col_sources):
    """The answer as a table: columns with business names and readable numbers."""
    formats, names, units = cfg.get("formatos", {}), cfg.get("columnas", {}), cfg.get("unidades", {})
    decimals = {c: idioma.column_decimals([r[i] for r in rows], units[formats[c]]["escala"])
                for i, c in enumerate(columns) if formats.get(c) in units}
    data = []
    for row in rows:
        line = []
        for c, v in zip(columns, row):
            if v is not None and formats.get(c) in units:   # a declared unit, scaled; exact if technical
                v = common.money(v) if tech else idioma.scaled(v, units[formats[c]]["escala"], decimals=decimals[c])
            elif v is not None and formats.get(c) in ("dinero", "numero"):
                v = common.money(v)
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
    info = common.sources(domain)
    labels = cfg.get("fuentes", {})
    used, col_sources = answer.column_sources(query, domain)
    if tech:
        st.markdown(idioma.t("dominio.show_answer.sources_used") + " · ".join(f"`{labels.get(s, s)}`" for s in used),
                    help=common.ayuda("fuentes_respuesta"))
    else:
        names = [info[s]["name"] for s in used if s in info] + ([idioma.t("dominio.show_answer.rastro_links")] if "rastro" in used else [])
        st.markdown(idioma.t("dominio.show_answer.sources") + ", ".join(names), help=common.ayuda("fuentes_respuesta"))
    if not rows:
        st.info(idioma.t("dominio.show_answer.no_results"))
    else:
        visible = item.get("columnas_respuesta") if item and not tech else None
        shown_columns = [c for c in columns if not visible or c in visible]
        shown_rows = [[row[columns.index(c)] for c in shown_columns] for row in rows]
        table = as_table(shown_columns, shown_rows, cfg, tech, col_sources)
        common.tabla(table, hide_index=True, use_container_width=True,
              key=f"{where}_{item['id']}" if item and item.get("id") else None)
        if item and item.get("mapa"):
            hood.show_map(domain)
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
                st.markdown(idioma.t("dominio.show_answer.contributed") + common.md(item["ventaja"]))
            if item and item.get("definicion"):
                st.markdown(idioma.t("dominio.show_answer.rule_once"))
            if evidence:
                st.markdown(f"**{common.md(evidence['texto'])}**")
                ev_cols, ev_rows = common.run(common.prefixed(evidence["query"], domain), domain)
                for r in ev_rows:
                    st.markdown("- " + common.md(evidence["formato"].format(**dict(zip(ev_cols, r)))))
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
            ev_query = common.prefixed(evidence["query"], domain)
            st.code(ev_query, language="sparql")
            ev_cols, ev_rows = common.run(ev_query, domain)
            common.tabla(pd.DataFrame(ev_rows, columns=ev_cols), hide_index=True, use_container_width=True)


def explain(query, sql, domain, item=None, where="preguntar"):
    """«Explicame la consulta»: example questions bring their saved explanation; the user's own
    are explained live if an LLM is configured."""
    key = f"explain_{where}_{abs(hash(query))}"
    stored = (item or {}).get("explicacion")
    available, _ = common.llm_status()
    if st.button(idioma.t("dominio.explain.button"), key=f"{key}_boton", disabled=not stored and not available,
                 help=None if stored or available else idioma.t("dominio.explain.need_llm")):
        st.session_state[key] = stored
        if not stored:
            with st.spinner(idioma.t("dominio.explain.reading")):
                st.session_state[key] = answer.explain_query(query, sql, domain, idioma.lang())
    if st.session_state.get(key):
        st.info(common.md(st.session_state[key]))


def show_why(domain, why, columns, rows, where="preguntar", tech=False):
    """«¿Por qué este número?»: pick a row of the answer and see the evidence behind it,
    drawn as a graph (the row in the center, each link around it) and in a table."""
    import grafo
    if why["columna"] not in columns:
        return
    if why.get("recorrido"):
        extension.load(common.domain_config(domain)).show_story(why, columns, rows, where, tech)
        return
    values = list(dict.fromkeys(r[columns.index(why["columna"])] for r in rows if r[columns.index(why["columna"])]))
    with st.container(border=True):
        st.markdown(idioma.t("dominio.show_why.title"), help=idioma.t("dominio.show_why.help"))
        value = st.selectbox(idioma.t("dominio.show_why.row"), values, key=f"{domain}_{where}_porque_{why['columna']}",
                             label_visibility="collapsed")
        st.markdown(f"**{common.md(why['titulo'].format(valor=value))}.** {common.md(why.get('explica', ''))}")
        cols, found = common.run(common.prefixed(why["query"].replace("{valor}", str(value).replace('"', '\\"')), domain), domain)
        if not found:
            st.info(idioma.t("dominio.show_why.no_evidence"))
            return
        records = [dict(zip(cols, r)) for r in found]
        # «numeros» lists the numbers, or maps each to one of the domain's units («unidades») to show it scaled
        numbers = why.get("numeros", ["parte"])
        declared = common.domain_config(domain).get("unidades", {})
        scales = {k: declared[unit]["escala"] for k, unit in numbers.items()} if isinstance(numbers, dict) else {}
        decimals = {k: idioma.column_decimals([r.get(k) for r in records], scale) for k, scale in scales.items()}

        def display(k, v):
            return idioma.scaled(v, scales[k], decimals=decimals[k]) if k in scales else common.money(v)

        def fmt(record, template):
            return template.format(**{k: (display(k, v) if k in numbers and v not in (None, "") else (v or "—"))
                                      for k, v in record.items()})

        shown = records[:8]
        nodes = [("entidad", fmt(r, why["nodo"]), fmt(r, why["detalle"]), why["flecha"]) for r in shown]
        if len(records) > len(shown):
            nodes.append(("dato", idioma.t("dominio.show_why.more", n=len(records) - len(shown)), "", why["flecha"]))
        drawing = grafo.svg((str(value), idioma.t("dominio.show_why.answer_row")), nodes, width=1500,
                            height=620 + 55 * max(0, len(nodes) - 8), scale=0.95, font="Helvetica, Arial, sans-serif")
        st.markdown(f'<img src="data:image/svg+xml;base64,{base64.b64encode(drawing.encode()).decode()}" '
                    'style="width:100%;border-radius:12px">', unsafe_allow_html=True)
        table = enlaces.add_status(pd.DataFrame([{k: display(k, v) if k in scales and v not in (None, "") else v
                                                  for k, v in r.items()} for r in records]))
        table = table.rename(columns=why.get("columnas", {}))
        common.tabla(table, hide_index=True, use_container_width=True, column_config=enlaces.column_help(),
              key=f"{domain}_{where}_porque_tabla")


def before_after(card, domain):
    """The same card at every moment of the demo: without Rastro on the left, with Rastro on the right. Its numbers are
    read now, the same way the slides read them (contraste.py)."""
    found = contraste.values(card, lambda q: _sql_saved(q, domain, common.data_version(domain, reads=q)),
                             lambda q: common.run(common.prefixed(q, domain), domain))
    card = contraste.fill(card, contraste.shown(card, found, idioma.number))
    left, right = st.columns(2)
    for col, key, title in [(left, "sin", card.get("titulo_sin", idioma.t("dominio.before_after.without"))),
                           (right, "con", idioma.t("dominio.before_after.with"))]:
        with col.container(border=True):
            st.caption(title, help=common.ayuda("sin_rastro" if key == "sin" else "con_rastro"))
            st.markdown(f"### {'⚪' if key == 'sin' else '🟢'} {common.md(card[key]['valor'])}")
            st.markdown(common.md(card[key]["detalle"]))
    if card.get("impacto"):
        st.warning(idioma.t("dominio.before_after.cost") + common.md(card["impacto"]))
    if card.get("fuentes"):
        st.caption(idioma.t("dominio.before_after.data", sources="; ".join(
            idioma.t("dominio.before_after.source", name=name, date=date) for name, date in loaded(tuple(card["fuentes"])))))


@st.cache_data(persist="disk", show_spinner=False)
def _sql_saved(query, domain, version):   # SQL over the sources as they come, recalculated when they change
    return common.sql_table(query, domain, approach="B")


@st.cache_data(ttl=60, show_spinner=False)
def loaded(source_ids):
    """Each source's name and the date of its latest load, from rastro_meta.load_run."""
    import psycopg
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        rows = conn.execute("""
            SELECT s.name, to_char(max(r.loaded_at), 'DD/MM/YYYY')
            FROM rastro_meta.source s JOIN rastro_meta.load_run r ON r.source_id = s.id
            WHERE s.id = ANY(%s) GROUP BY s.id, s.name ORDER BY array_position(%s, s.id)""",
                            (list(source_ids), list(source_ids))).fetchall()
    return rows


def show_integration_example(example, domain, tech, key=None, record=None, run_id=None, ext=None):
    """A walkthrough on real data: what it is for, which part of Rastro each step shows, and each step's live
    queries (raw sources with SQL as they come, Rastro with SPARQL), so every number on screen comes from a query.
    A model's walkthrough has its extension (ext): {registro_ejemplo} is the model's example record (record, if
    given), {corrida_publicada} its published run (run_id, if given), and the extension adds to each step."""
    steps = example["pasos"]
    if example.get("encabezado"):
        st.markdown(f"### {common.md(example['encabezado'])}")
    if example.get("para_que"):
        with st.container(border=True):
            st.markdown(idioma.t("dominio.show_integration_example.purpose", text=common.md(example["para_que"])))
            st.markdown(idioma.t("dominio.show_integration_example.parts")
                        + "\n".join(f"- **{s['titulo']}**: {common.md(s['parte'])}" for s in steps if s.get("parte")))
    st.caption(common.md(example["aviso"]))
    selected = st.radio(example["selector"], range(len(steps)),
                        format_func=lambda index: steps[index]["titulo"],
                        key=f"{key or domain}_integration_example", horizontal=True)
    step = steps[selected]
    if step.get("parte"):
        st.info(idioma.t("dominio.show_integration_example.part", part=common.md(step["parte"])))
    st.markdown(step["contenido"])
    missing_run_shown = False
    for n, query in enumerate(step.get("consultas", [])):
        if "{corrida_publicada}" in str(query):
            from urllib.parse import quote
            if run_id is None:
                run_id = ext.published_run() if ext else ""
            if not run_id:
                if not missing_run_shown:
                    st.info(example["ui"]["run_missing"])
                    missing_run_shown = True
                continue
            query = {k: v.replace("{corrida_publicada}", quote(str(run_id), safe=""))
                     for k, v in query.items()}
        if "{registro_ejemplo}" in str(query):   # the model's example record, the same one its tab opens with
            record = record if record is not None else ext.example_record()
            query = {k: v.replace("{registro_ejemplo}", str(record)) for k, v in query.items()}
        st.markdown(f"**{common.md(query['titulo'])}**")
        if query.get("sql"):
            columns, rows = common.sql_table(query["sql"], domain, approach="B")
        else:
            columns, rows = common.run(common.prefixed(query["sparql"], domain), domain)
        common.tabla(pd.DataFrame(rows, columns=columns), key=f"{key or domain}_paso{selected}_{n}")
        if tech:
            st.code(query.get("sql") or query["sparql"], language="sql" if query.get("sql") else "sparql")
    if ext:
        ext.show_step(step, example, record, tech, key or domain)
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
            st.markdown(common.md(cfg["demo_porque"]))
    st.markdown(" → ".join(f"**{n + 1} · {s['paso']}**" if n == i else f"{n + 1} · {s['paso']}"
                           for n, s in enumerate(steps)))
    step = steps[i]
    st.subheader(step["titulo"], help=common.ayuda("paso"))
    if step.get("que_es"):   # the other use cases still explain what each step is
        st.markdown(idioma.t("dominio.show_demo.what_is", step=common.md(step["paso"]).lower(), text=common.md(step["que_es"])))
    if step.get("muestra"):
        st.markdown(common.md(step["muestra"]))
    tipo = step.get("tipo", "pregunta")
    if tipo == "cambio":
        trust_view.show_change_short(cfg, common.read_json(cfg["cambio"]), step.get("escenario"), tech)
    elif tipo not in ("pregunta", "texto"):   # a moment of the domain's own (a model's prediction, say)
        extension.load(cfg).show_demo_moment(step, key, tech)
    elif step.get("texto"):
        show_text_question(cfg, tech, demo=True)
    else:
        item = next(q for q in cfg["preguntas"] if q["id"] == step["pregunta"])
        st.info(f"**{common.md(item['simple'])}**")
        if tech:
            st.caption(idioma.t("dominio.show_demo.tech_wording") + common.md(item["tecnica"]))
        query = Path(item["query"]).read_text()
        columns, rows = common.run(query, domain)
        if item.get("antes_despues"):
            before_after(item["antes_despues"], domain)
        show_answer(cfg, tech, query, columns, rows, item, note=idioma.t("dominio.show_demo.live_note"), where="demo")
    back, _, forward = st.columns([2, 3, 2])
    if i > 0 and back.button(idioma.t("dominio.show_demo.back"), key=f"{key}_back"):
        st.session_state[key] = i - 1
        st.rerun()
    if i < len(steps) - 1 and forward.button(idioma.t("dominio.show_demo.next"), type="primary", key=f"{key}_next"):
        st.session_state[key] = i + 1
        st.rerun()


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
    st.markdown(common.md(claims["intro"]))
    chosen = st.radio(idioma.t("dominio.show_claims.claim"), [c["texto"] for c in claims["ejemplos"]], key=f"{domain}_afirmacion")
    claim = next(c for c in claims["ejemplos"] if c["texto"] == chosen)
    st.markdown(f"> {claim['texto']}")
    for reading in claim["lecturas"]:
        rows = common.run(common.prefixed(reading["consulta"], domain), domain)[1] if reading.get("consulta") else []
        mark, verdict, detail = claim_verdict(reading, rows)
        with st.container(border=True):
            st.markdown(f"**{reading['nombre']}**")
            st.markdown(f"{mark} **{verdict}.** {common.md(detail)}")
            if tech and reading.get("consulta"):
                st.code(reading["consulta"].strip(), language="sparql")
    if claim.get("nota"):
        st.caption(common.md(claim["nota"]))


def show_external(cfg, tech):
    """Enrich with outside data: a federated query in GraphDB joins Rastro with Wikidata through a
    shared identifier. It runs live if asked; otherwise, the saved result is shown. Below, the same
    enrichment saved in Rastro (show_enrichment_saved)."""
    ext, domain = cfg["externo"], cfg["domain"]
    st.markdown(f"**{ext['titulo']}**", help=common.ayuda("externo"))
    st.markdown(common.md(ext["intro"]))
    graph = ext["grafo"]   # the diagram's labels: Rastro, the outside source, the query that joins them, the shared key
    st.graphviz_chart(f"""digraph {{ rankdir=LR; bgcolor="transparent";
        node [fontname="Helvetica", fontsize=14, style=filled, penwidth=0];
        r [label="{graph['rastro']}", shape=ellipse, fillcolor="#2F6FB5", fontcolor="white"];
        w [label="{graph['fuente']}", shape=ellipse, fillcolor="#FFF3E6", color="#FF8C42", penwidth=2];
        q [label="{graph['consulta']}", shape=box, style="rounded,filled", fillcolor="#F4F6F9", color="#B8C2CF", penwidth=1];
        r -> q [label="{graph['clave']}", dir=both, color="#7A8699", fontcolor="#7A8699", fontname="Helvetica"];
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
    # «tecnicas»: the columns only the technical view shows (identifiers); «numericas»: the numbers to format
    columns = [c for c in ext["columnas"] if c in table.columns and (tech or c not in ext.get("tecnicas", []))]
    shown = table[columns].copy()
    for c in ext.get("numericas", []):
        if c in shown:
            shown[c] = shown[c].map(lambda v: common.money(v) if pd.notna(v) else "—")
    shown = shown.fillna("—").rename(columns=ext["columnas"])
    common.tabla(shown, hide_index=True, use_container_width=True)
    st.caption(idioma.t("dominio.show_external.result", when=when))
    st.info(common.md(ext["conclusion"]))
    with st.expander(idioma.t("dominio.show_external.query")):
        st.code(Path(ext["consulta"]).read_text(), language="sparql")
    if ext.get("materializado"):
        show_enrichment_saved(ext, domain, tech)


def show_enrichment_saved(ext, domain, tech):
    """The same enrichment, saved in Rastro: what the outside source answered stays as one more source,
    with its date, and is queried like any other data."""
    st.markdown(idioma.t("dominio.show_enrichment_saved.title"), help=common.ayuda("externo"))
    query = Path(ext["materializado"]).read_text()
    columns, rows = common.run(query, domain)
    if not rows:
        st.info(idioma.t("dominio.show_enrichment_saved.not_saved"))
        return
    common.tabla(pd.DataFrame(rows, columns=columns).rename(columns=ext.get("columnas_guardado", {})),
          hide_index=True, use_container_width=True)
    st.caption(common.md(idioma.t("dominio.show_enrichment_saved.explain")))
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
    item = common.read_json(cfg["texto"])
    st.markdown(idioma.t("dominio.show_text_question.steps"), help=common.ayuda("texto"))
    text_step(1, idioma.t("dominio.show_text_question.question"))
    st.info(f"**{common.md(item['simple'])}**")
    if tech:
        st.caption(idioma.t("dominio.show_text_question.tech_wording") + common.md(item["pregunta"]))
    if not demo:
        if st.button(idioma.t("dominio.show_text_question.answer"), type="primary", key=f"{domain}_text_answer"):
            st.session_state[f"{domain}_text_shown"] = True
        if not st.session_state.get(f"{domain}_text_shown"):
            return
    query = Path(item["consulta"]).read_text()
    _, rows = common.run(query, domain)
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
                           idioma.t("dominio.show_text_question.amount", amount=common.money(sum(records[c][0] for c in found) / 1e6))))
    n = len(records)

    text_step(2, idioma.t("dominio.show_text_question.graph_picks"), idioma.t("dominio.show_text_question.graph_picks_help"))
    st.markdown(common.md(graph_part.strip()))
    st.metric(idioma.t("dominio.show_text_question.picked", units=unit[1].capitalize()), n)
    with st.expander(idioma.t("dominio.show_text_question.query"), expanded=tech):
        st.caption(idioma.t("dominio.show_text_question.query_caption"))
        st.code(query, language="sparql")
    if demo and item.get("busqueda_texto"):
        compare_text_search(item, records, domain, tech, always=True)

    text_step(3, idioma.t("dominio.show_text_question.ai_reads"), idioma.t("dominio.show_text_question.ai_reads_help"))
    st.markdown(common.md(ai_part.strip()) or idioma.t("dominio.show_text_question.ai_read", n=n, units=unit[1]))
    with st.expander(idioma.t("dominio.show_text_question.texts_read", n=n)):
        common.tabla(table, hide_index=True, use_container_width=True)

    text_step(4, idioma.t("dominio.show_text_question.summary"))
    for theme, found, detail, extra in themes:
        st.markdown(idioma.t("dominio.show_text_question.theme", theme=common.md(theme), n=len(found),
                             unit=unit[0] if len(found) == 1 else unit[1], extra=extra, detail=common.md(detail),
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
    _, rows = common.run(query, domain)
    found = {c for c, *_ in rows}
    missing = {c: v for c, v in contracts.items() if c not in found}
    lost = [t["tema"] for t in item["temas"] if t["contratos"] and all(c in missing for c in t["contratos"])]
    companies = sorted({company(e) for _, _, e, _ in missing.values()})
    before_after({
        "titulo_sin": idioma.t("dominio.compare_text_search.without_title"),
        "sin": {"valor": idioma.t("dominio.compare_text_search.of", found=len(contracts) - len(missing), total=len(contracts)),
                "detalle": (idioma.t("dominio.compare_text_search.misses", n=len(missing),
                                     amount=common.money(sum(m for m, *_ in missing.values()) / 1e6), companies=", ".join(companies))
                            + (idioma.t("dominio.compare_text_search.lost", themes=", ".join(lost).lower()) if lost else ""))},
        "con": {"valor": idioma.t("dominio.compare_text_search.of", found=len(contracts), total=len(contracts)),
                "detalle": idioma.t("dominio.compare_text_search.with_detail")}})
    st.caption(idioma.t("dominio.compare_text_search.caption"))
    if tech:
        st.code(query, language="sparql")
