"""Pantalla de un dominio a partir de su archivo de configuración (app/dominios/<dominio>.yaml).

Las mismas tres pestañas que oncología: Preguntar, Por qué confiar y Preguntas frecuentes,
con los dos modos (negocio por defecto, técnico con el interruptor). Todo lo propio del
dominio (preguntas, columnas, evidencia, tarjetas, escenarios de cambio) está en el YAML.
"""

import base64
import json
from pathlib import Path

import pandas as pd
import requests
import sqlparse
import streamlit as st
import yaml

import answer

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
def _load_json(path, mtime):
    return json.loads(Path(path).read_text())


@st.cache_data
def sources(domain):
    ns = answer.DOMAINS[domain]["namespace"]
    _, rows = answer.run_sparql_table(f"""PREFIX : <{ns}>
        SELECT ?id ?name ?license WHERE {{ ?s a :DataSource ; :name ?name ; :license ?license .
          BIND (STRAFTER(STR(?s), "/source/") AS ?id) }}""", domain)
    return {r[0]: {"name": r[1], "license": r[2]} for r in rows}


@st.cache_data
def run(query, domain):
    return answer.run_sparql_table(query, domain)


def prefixed(query, domain):
    """Agrega los prefijos que la consulta usa: el del dominio siempre, el de PROV-O solo si hace falta."""
    return f"PREFIX : <{answer.DOMAINS[domain]['namespace']}>\n" + (PROV if "prov:" in query else "") + query


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
            if v is not None and formats.get(c) == "dinero":
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
        st.markdown("**Fuentes que usó esta respuesta:** " + " · ".join(f"`{labels.get(s, s)}`" for s in used))
    else:
        names = [info[s]["name"] for s in used if s in info] + (["enlaces de Rastro"] if "rastro" in used else [])
        st.markdown("**Fuentes:** " + ", ".join(names))
    if not rows:
        st.info("La consulta no devolvió resultados.")
    else:
        st.dataframe(as_table(columns, rows, cfg, tech, col_sources), hide_index=True, use_container_width=True)
        st.caption(f"{len(rows)} fila{'s' if len(rows) != 1 else ''}."
                   + (" La evidencia está en «¿Cómo lo supe?»." if item and item.get("evidencia") else ""))

    with st.expander("¿Cómo lo supe?"):
        evidence = (item or {}).get("evidencia")
        if not tech:
            st.markdown("**Dónde buscó Rastro:**")
            for s in used:
                if s == "rastro":
                    st.markdown(f"- **{cfg.get('nota_rastro', 'Los enlaces de Rastro')}**")
                elif s in info:
                    st.markdown(f"- **{info[s]['name']}** · licencia: {info[s]['license']}")
            if item and item.get("ventaja"):
                st.markdown("**Qué hizo Rastro por vos:** " + md(item["ventaja"]))
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
            st.caption("¿Querés ver la consulta y el SQL? Activá «Ver detalles técnicos» en la barra lateral.")
            return
        if note:
            st.caption(note)
        st.markdown("**1. La consulta**, sobre los conceptos de Rastro (SPARQL):")
        st.code(query, language="sparql")
        st.markdown("**2. El SQL que Rastro generó y ejecutó en Postgres** (lo traduce Ontop con los mapeos):")
        try:
            st.code(sqlparse.format(answer.ontop_sql(query, domain), reindent=True, keyword_case="upper",
                                    indent_width=2), language="sql")
        except requests.RequestException:
            st.caption("Ontop no devolvió la traducción.")
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
            st.markdown("**4. La evidencia**, pedida al grafo (los enlaces son entidades PROV-O):")
            ev_query = prefixed(evidence["query"], domain)
            st.code(ev_query, language="sparql")
            ev_cols, ev_rows = run(ev_query, domain)
            st.dataframe(pd.DataFrame(ev_rows, columns=ev_cols), hide_index=True, use_container_width=True)


def short(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        return str(len(value))
    return money(value)


def render(cfg_path, tech):
    cfg = load_config(cfg_path)
    domain = cfg["domain"]
    evaluation = read_json(cfg["evaluacion"])
    changes = read_json(cfg["cambio"])
    questions = cfg["preguntas"]

    with st.sidebar:
        if tech:
            available, status = llm_status()
            st.subheader("LLM")
            st.markdown(("🟢 " if available else "⚪ ") + status)
            st.subheader("Fuentes")
            for key, info in sources(domain).items():
                st.markdown(f"🐘 **{info['name']}**  \n<small>{info['license']}</small>", unsafe_allow_html=True)
        else:
            st.caption(md(cfg["resumen"]))

    ask_tab, trust_tab, faq_tab = st.tabs(["Preguntar", "Por qué confiar", "Preguntas frecuentes"])

    with ask_tab:
        modes = ["Una pregunta de ejemplo"] + (["Una pregunta sobre textos"] if cfg.get("texto") else [])
        mode = st.radio("¿Qué querés preguntar?", modes + ["Mi propia pregunta"],
                        horizontal=True, label_visibility="collapsed", key=f"{domain}_mode")
        if mode == "Una pregunta sobre textos":
            show_text_question(cfg, tech)
        elif mode == "Una pregunta de ejemplo":
            options = {(q["tecnica"] if tech else q["simple"]): q for q in questions}
            chosen = st.selectbox("Pregunta", list(options), key=f"{domain}_question_{tech}")
            item = options[chosen]
            if item.get("terminos"):
                with st.expander("¿Qué significa " + ", ".join(item["terminos"]) + "?"):
                    st.markdown("\n".join(f"- **{md(t)}:** {md(m)}" for t, m in item["terminos"].items()))
            query = Path(item["query"]).read_text()
            if st.button("Responder", type="primary", key=f"{domain}_answer"):
                st.session_state[f"{domain}_shown"] = (chosen, query, *run(query, domain))
            shown = st.session_state.get(f"{domain}_shown", (None,))
            if shown[0] == chosen:
                _, query, columns, rows = shown
                show_answer(cfg, tech, query, columns, rows, item,
                            note="Se ejecuta ahora, en vivo, sobre los datos.")
        else:
            available, _ = llm_status()
            question = st.text_area("Pregunta", placeholder=cfg.get("ejemplo_libre", ""), key=f"{domain}_free")
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
                st.info("Para preguntas libres hace falta un LLM. Mientras tanto, probá las preguntas de ejemplo.")

    with trust_tab:
        trust(cfg, tech, evaluation, changes)

    with faq_tab:
        for item in [i for i in cfg.get("faq", []) if not i.get("tecnico")]:
            with st.expander(item["pregunta"]):
                st.markdown(md(item["respuesta"]))
        if tech:
            st.markdown("##### Para técnicos")
            with st.expander("Cómo está armado Rastro: arquitectura y diccionario de proveedores"):
                for name, caption in [("arquitectura", "De las fuentes de cada dominio a una capa semántica."),
                                      ("ontologia-proveedores", "El diccionario de proveedores: lo que lee el LLM.")]:
                    st.caption(caption)
                    image = base64.b64encode(Path(f"/app/{name}.svg").read_bytes()).decode()
                    st.markdown(f'<img src="data:image/svg+xml;base64,{image}" style="width:100%;margin-bottom:24px">',
                                unsafe_allow_html=True)
            for item in [i for i in cfg.get("faq", []) if i.get("tecnico")]:
                with st.expander(item["pregunta"]):
                    st.markdown(md(item["respuesta"]))
        else:
            st.caption("Hay más preguntas para técnicos: activá «Ver detalles técnicos» en la barra lateral.")


def show_text_question(cfg, tech):
    """Una pregunta sobre textos: el grafo elige los contratos con una consulta exacta y un asistente de
    IA resume solo sus descripciones en temas, citando cada contrato. El resumen está guardado; los
    contratos y sus montos se leen en vivo."""
    domain = cfg["domain"]
    item = read_json(cfg["texto"])
    st.info(f"**{item['pregunta'] if tech else item['simple']}**")
    if not st.button("Responder", type="primary", key=f"{domain}_text_answer"):
        return
    query = Path(item["consulta"]).read_text()
    _, rows = run(query, domain)
    contracts = {c: (float(m), a, e, d) for c, m, a, e, d in rows}
    total = sum(m for m, *_ in contracts.values())
    st.markdown(f"Rastro eligió los **{len(contracts)} contratos más grandes** del grupo "
                f"(US\\$ {money(total / 1e6)} millones). En qué trabaja:")
    for theme in item["temas"]:
        found = [c for c in theme["contratos"] if c in contracts]
        amount = sum(contracts[c][0] for c in found)
        st.markdown(f"- **{md(theme['tema'])}** · {len(found)} {'contrato' if len(found) == 1 else 'contratos'}, US\\$ {money(amount / 1e6)} millones. "
                    f"{md(theme['detalle'])}  \n<small>{', '.join(found)}</small>", unsafe_allow_html=True)
    with st.expander("¿Cómo lo supe?"):
        st.markdown(md(item["como"]))
        if tech:
            st.markdown("**1. La consulta que elige los contratos** (exacta: usa el grupo que arma Rastro):")
            st.code(query, language="sparql")
            st.markdown("**2. Las descripciones que leyó el asistente**, tal como están en el grafo (`:description`):")
        else:
            st.markdown("**Las descripciones que leyó**, tal como están en la base de contratos:")
        st.dataframe(pd.DataFrame([{"Contrato": c, "Millones de US$": round(m / 1e6, 1), "Agencia": a.title(),
                                    "Empresa": e.title(), "Descripción": d.capitalize()}
                                   for c, (m, a, e, d) in contracts.items()]),
                     hide_index=True, use_container_width=True)
        st.caption(f"Resumen guardado el {item['fecha']}. Los contratos y montos se leen en vivo; si cambian "
                   "los datos, el resumen hay que volver a generarlo.")


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
    broken = max((sum(n for s, n in changes.get(c["antes"], {}).get("totals", {}).get("B", {}).items() if s != "✅")
                  for c in cfg.get("cambios", [])), default=0)
    numbers = {"c_consistent": totals.get("C", {}).get("consistent", "—"),
               "b_consistent": totals.get("B", {}).get("consistent", "—"),
               "n_consistency": len(consistency), "b_broken": broken}
    st.markdown("### Por qué confiar")
    st.caption("El mismo asistente de IA, sin Rastro (escribe SQL sobre las bases tal como vienen) y con Rastro.")
    for col, card in zip(st.columns(len(cfg["tarjetas"])), cfg["tarjetas"]):
        with col.container(border=True):
            st.markdown(f"**{md(card['titulo'])}**")
            st.markdown(f'<p style="font-size:2.4rem;line-height:1.1;margin:0">{card["valor"].format(**numbers)}</p>',
                        unsafe_allow_html=True)
            st.caption(md(card["compara"].format(**numbers)))

    # En modo técnico se suma la línea de base justa: SQL con las tablas de enlaces de Rastro
    names = ({"B": "Sin Rastro", "D": "SQL + enlaces", "C": "Con Rastro"} if tech
             else {"B": "Sin Rastro", "C": "Con Rastro"})
    names = {k: v for k, v in names.items() if all(k in r for r in consistency.values())}
    change_names = {"B": "Sin Rastro", "C": "Con Rastro"}
    simple = {q["id"]: q["simple"] for q in cfg["preguntas"]}
    with st.container() if tech else st.expander(f"Ver las {4 * len(consistency)} respuestas"):
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
        if tech and evaluation.get("questions"):
            evaluation_detail(evaluation, totals)

    with st.container() if tech else st.expander("Ver los escenarios de cambio"):
        scenarios = {c["titulo"]: c for c in cfg.get("cambios", [])}
        n = len(evaluation.get("questions", {}))
        st.caption(f"Qué pasa con las {n} preguntas de la evaluación cuando una base cambia.")
        picked = st.radio("Escenario", list(scenarios), horizontal=True, label_visibility="collapsed",
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
                st.markdown("**El arreglo en Rastro: una línea del mapeo**")
                st.code(f"- {change['arreglo'][0]}\n+ {change['arreglo'][1]}", language="diff")
            else:
                st.markdown("**El arreglo en Rastro:** una línea, en la traducción de esa base al diccionario de negocio.")
            st.markdown("**Después del arreglo:**")
            for col, k in zip(st.columns(2), change_names):
                col.metric(change_names[k], f"{after['totals'][k].get('✅', 0)}/{n}")
                col.caption(summary(after["totals"][k]) + ("" if k == "C" else ". Hay que encontrar y reescribir cada consulta."))
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
