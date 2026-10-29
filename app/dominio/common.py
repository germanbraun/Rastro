"""What every part of a domain's screen shares: the configuration, cached queries, tables and short texts."""

import hashlib
import json
import os
import re
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import yaml

import answer
import idioma


PROV = "PREFIX prov: <http://www.w3.org/ns/prov#>\n"


def load_config(path):
    return idioma.localized(path)


def read_json(path):
    p = Path(path)
    return _load_json(path, p.stat().st_mtime) if p.exists() else {}


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


_REMEMBERED = {}   # key → the last value read from the database while this app runs


def remembered(key, read):
    """read(), or, if the database stops answering, the last value it gave while this app runs: what was already read
    keeps showing (a demo does not fail in front of a client), with a notice that these are saved answers."""
    import psycopg
    try:
        _REMEMBERED[key] = read()
    except psycopg.OperationalError:
        if key not in _REMEMBERED:
            raise
        if not st.session_state.get("rastro_saved_notice"):
            st.session_state["rastro_saved_notice"] = True
            st.toast(idioma.t("dominio.saved_answers"), icon="💾")
    return _REMEMBERED[key]


def version(domain, reads=""):
    """data_version, remembered: with it, the answers saved on disk keep showing if the database stops answering."""
    return remembered(("version", domain, reads), lambda: data_version(domain, reads))


@st.cache_data(persist="disk", show_spinner=False)
def _run_saved(query, domain, version):
    return answer.run_sparql_table(query, domain)


def run(query, domain):
    """A query over Rastro. The answer is saved on disk: it survives an app restart, and it is
    recalculated if the data or the mappings change (data_version)."""
    return _run_saved(query, domain, version(domain))


@st.cache_resource
def warm_up():
    """Warm-up: the first time someone opens the app, all the domains' example questions and the two Rastro Lab
    models are computed in the background, so the demo does not wait."""
    import threading

    def lab_work():   # a model takes the longest: it starts at once, next to the questions
        from . import extension
        for config in sorted(p for p in Path("/app/dominios").glob("*.yaml") if not p.name.endswith(".en.yaml")):
            try:
                ext = extension.load(yaml.safe_load(config.read_text()))
                if ext:
                    ext.warm_up()
            except Exception:   # noqa: BLE001
                pass

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
    threading.Thread(target=lab_work, daemon=True).start()
    threading.Thread(target=work, daemon=True).start()
    return True


def prefixed(query, domain):
    """Adds the prefixes the query uses: the domain's always, PROV-O's only when needed."""
    ns = answer.DOMAINS[domain]["namespace"]
    return f"PREFIX {domain}: <{ns}>\n" + (PROV if "prov:" in query else "") + query


def check_text(recorded, warnings):
    """A change test's check in the interface's language. The test records it in Spanish; each domain declares the
    checks it knows («avisos_cambio»: a pattern and, in its English file, the text with {0}, {1}… for the pattern's
    groups). In English a known check is written again with its numbers; anything else is shown as recorded."""
    text = recorded.split(": ", 1)[-1]
    if idioma.lang() == "es":
        return text
    for warning in warnings or []:
        found = re.search(warning["patron"], recorded)
        if found and warning.get("texto"):
            return warning["texto"].format(*(spanish_number(g) for g in found.groups()))
    return text


def spanish_number(text):
    """A number as the Spanish text wrote it (12.345,6), in the interface's format with the same decimals; any other
    text as it is."""
    if not re.fullmatch(r"\d{1,3}(\.\d{3})*(,\d+)?|\d+(,\d+)?", text):
        return text
    decimals = len(text.split(",")[1]) if "," in text else 0
    return idioma.number(float(text.replace(".", "").replace(",", ".")), decimals)


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


def sql_table(query, domain, approach="D", params=None):
    """A read-only query: with approach «D», over Rastro's link tables; with «B», only over the
    sources as they come."""
    import psycopg
    user = answer.DOMAINS[domain]["readers"][approach]
    with psycopg.connect(answer.reader_dsn(user)) as conn:
        cur = conn.execute(query, params)
        return [c.name for c in cur.description], cur.fetchall()


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
    from lifecycle import question_status, read_state, validation_level
    state = read_state(registered, answer.ROOT)
    result = []
    for question in cfg["preguntas"]:
        entry = state["questions"].get(question["id"])
        try:
            if entry and question_status(entry, registered, answer.ROOT) == "validated":
                result.append({**question, "nivel": validation_level(entry) or "technical"})
        except (FileNotFoundError, ValueError):
            continue  # Missing or changed inputs cannot retain validation.
    return result


def llm_status():
    if answer.PROVIDER == "ollama":
        try:
            requests.get(f"{answer.OLLAMA}/api/tags", timeout=3).raise_for_status()
            return True, f"Ollama · {answer.MODEL}"
        except requests.RequestException:
            return False, idioma.t("dominio.llm_status.no_answer", url=answer.OLLAMA)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True, f"Claude API · {answer.MODEL}"
    return False, idioma.t("dominio.llm_status.none")
