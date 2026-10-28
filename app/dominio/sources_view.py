"""«Las fuentes de datos»: what each source is, what Rastro takes from it and what to watch out for.

The texts come from the domain's YAML (`fuentes_detalle`); the name, license, link and what was loaded (rows,
version, date) come from Rastro's load records (rastro_meta.source and rastro_meta.load_run), never typed.
"""

import os

import streamlit as st

import idioma

from . import common


@st.cache_data(ttl=300, show_spinner=False)
def load_records(source_ids):
    """For each source id: its registry row and the latest load of each of its tables."""
    import psycopg
    with psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                         f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}") as conn:
        sources = {row[0]: {"name": row[1], "homepage": row[2], "license": row[3], "tables": []} for row in conn.execute(
            "SELECT id, name, homepage, license FROM rastro_meta.source WHERE id = ANY(%s)", (list(source_ids),))}
        for source, table, rows, version, loaded in conn.execute("""
                SELECT DISTINCT ON (source_id, table_name) source_id, table_name, row_count, version, loaded_at::date
                FROM rastro_meta.load_run WHERE source_id = ANY(%s)
                ORDER BY source_id, table_name, loaded_at DESC""", (list(source_ids),)):
            sources[source]["tables"].append((table, rows, version, str(loaded)))
    return sources


def show_source(entry, record, tech):
    st.markdown(f"*{entry['organismo']}*")
    st.markdown(f"**{idioma.t('dominio.sources.what')}** {common.md(entry['que_es'])}")
    st.markdown(f"**{idioma.t('dominio.sources.use')}** {common.md(entry['que_usa'])}")
    if entry.get("cuidado"):
        st.markdown(f"**{idioma.t('dominio.sources.watch')}**")
        st.markdown("\n".join(f"- {common.md(item)}" for item in entry["cuidado"]))
    if record:
        # A source shared by several domains names this domain's schemas (esquemas); the others are not counted
        schemas = entry.get("esquemas")
        tables = [t for t in record["tables"] if not schemas or t[0].split(".")[0] in schemas]
        last = max((t[3] for t in tables), default=None)
        rows = sum(t[1] for t in tables)
        st.caption(idioma.t("dominio.sources.loaded", license=record["license"], url=record["homepage"],
                            date=last or "—", rows=idioma.number(rows)))
        if tech:
            st.markdown("\n".join(f"- `{t[0]}`: {idioma.number(t[1])} · {t[2] or '—'} · {t[3]}" for t in tables))
    if tech and entry.get("tecnico"):
        st.caption(common.md(entry["tecnico"]))


@st.dialog(" ", width="large")
def sources_dialog(cfg, tech):
    st.subheader(idioma.t("dominio.sources.title"))
    st.caption(idioma.t("dominio.sources.intro"))
    entries = cfg["fuentes_detalle"]
    records = load_records(tuple(e["id"] for e in entries))
    for entry in entries:
        record = records.get(entry["id"])
        with st.expander(entry.get("nombre") or (record["name"] if record else entry["id"])):
            show_source(entry, record, tech)
