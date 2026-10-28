"""«Por qué confiar»: the measured evaluation, the change and correction tests and the «sin dato» test."""

from pathlib import Path

import pandas as pd
import sqlparse
import streamlit as st

import answer
import contraste
import idioma

from . import common
from . import hood


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
    st.markdown(common.md(change["que"]))
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
    common.tabla(df, key="demo_correccion")
    st.markdown(common.md(idioma.t("dominio.show_correction.where_fixed", places=result["lugares_sin_rastro"])))
    if tech:
        st.caption(idioma.t("dominio.show_correction.measured"))


def card_status(cfg, evaluation):
    """What each trust card's number is, in one line: when the evaluation was measured and whether its references are
    confirmed by a person (the publication gate decides), and how the change test and the evidence were measured."""
    from method import publication_errors
    try:
        pending = bool(publication_errors(answer.DOMAINS[cfg["domain"]], answer.ROOT))
    except Exception:   # noqa: BLE001 - a domain without the gate's files has no independent references either
        pending = True
    date = evaluation.get("date", "")
    date = f"{date[8:10]}/{date[5:7]}/{date[:4]}" if len(date) == 10 else date
    measured = (idioma.t("dominio.trust.status_pending", date=date) if pending
                else idioma.t("dominio.trust.status_confirmed", date=date))
    return [measured, measured, idioma.t("dominio.trust.status_change"), idioma.t("dominio.trust.status_evidence")]


def trust(cfg, tech, evaluation, changes):
    if not cfg.get("tarjetas"):   # not measured yet: say so, and show only what has been checked
        st.markdown(idioma.t("dominio.trust.title"), help=common.ayuda("confiar"))
        if cfg.get("sin_medir"):
            st.info(common.md(cfg["sin_medir"]))
        hood.show_quality(cfg.get("calidad"))
        show_no_data(cfg.get("fuera"), tech)
        return
    totals, consistency = evaluation.get("totals", {}), evaluation.get("consistency", {})
    evidence = common.read_json(cfg["evidencia"]) if cfg.get("evidencia") and Path(cfg["evidencia"]).exists() else {}
    numbers = contraste.trust_numbers(cfg, evaluation, changes, evidence, common.money)   # the slides read the same numbers
    if not evidence:
        numbers.update(pct_evidencia=idioma.t("dominio.trust.yes"), n_enlaces=idioma.t("dominio.trust.all_links"),
                       cols=idioma.t("dominio.trust.the_columns"), cols_ok=idioma.t("dominio.trust.all_columns"))
    st.markdown(idioma.t("dominio.trust.title"), help=common.ayuda("confiar"))
    st.caption(idioma.t("dominio.trust.same_assistant"))
    card_help = ["tarjeta_correctas", "tarjeta_consistencia", "tarjeta_cambio", "tarjeta_auditar"]
    statuses = card_status(cfg, evaluation)
    for k, (col, card) in enumerate(zip(st.columns(len(cfg["tarjetas"])), cfg["tarjetas"])):
        with col.container(border=True):
            st.markdown(f"**{common.md(card['titulo'])}**", help=common.ayuda(card_help[k]) if k < len(card_help) else None)
            st.markdown(f'<p style="font-size:2.4rem;line-height:1.1;margin:0">{card["valor"].format(**numbers)}</p>',
                        unsafe_allow_html=True)
            st.caption(common.md(card["compara"].format(**numbers)))
            if k < len(statuses):
                st.caption(statuses[k])

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
                line[title] = ("✅ " if row[k]["same"] else "❌ ") + " · ".join(common.short(a) for a in row[k]["answers"])
            table.append(line)
        common.tabla(pd.DataFrame(table), hide_index=True, use_container_width=True,
                     column_config={question_col: st.column_config.TextColumn(width="medium")})
        st.caption(idioma.t("dominio.trust.same_legend"))
        if consistency:
            labels = {qid: simple.get(qid, row["texts"][0]) for qid, row in consistency.items()}
            picked = st.selectbox(idioma.t("dominio.trust.see_four"), list(labels.values()),
                                  key=f"{cfg['domain']}_consistency")
            qid = next(k for k, v in labels.items() if v == picked)
            row = consistency[qid]
            common.tabla(pd.DataFrame([{asked_col: t, **{names[k]: common.short(row[k]["answers"][i])
                                                                    for k in names}}
                                       for i, t in enumerate(row["texts"])]),
                         hide_index=True, use_container_width=True,
                         column_config={asked_col: st.column_config.TextColumn(width="large")})

    with tab_change if tech else st.expander(idioma.t("dominio.trust.see_scenarios")):
        scenarios = {c["titulo"]: c for c in cfg.get("cambios", [])}
        st.caption(idioma.t("dominio.trust.scenarios_caption"))
        picked = st.radio(idioma.t("dominio.trust.scenario"), list(scenarios), horizontal=True, label_visibility="visible",
                          help=common.ayuda("escenario"), key=f"{cfg['domain']}_scenario")
        change = scenarios[picked]
        before, after = changes.get(change["antes"]), changes.get(change["despues"])
        st.markdown(common.md(change["que"]))
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
                st.warning(idioma.t("dominio.trust.warns") + common.md(common.check_text(before["vocabulary"])))
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
                common.tabla(pd.DataFrame([{question_col: simple.get(qid, qid),
                                            **{idioma.t("dominio.trust.col_before", name=change_names[k]): before["cells"][qid][k]
                                               for k in change_names},
                                            **{idioma.t("dominio.trust.col_after", name=change_names[k]): after["cells"][qid][k]
                                               for k in change_names}}
                                           for qid in before["cells"]]),
                             hide_index=True, use_container_width=True,
                             column_config={question_col: st.column_config.TextColumn(width="medium")})
        st.info(idioma.t("dominio.trust.one_place"))
    hood.show_quality(cfg.get("calidad"))
    show_no_data(cfg.get("fuera"), tech)


def show_no_data(fuera, tech):
    """Does it say when it lacks the data? The questions outside the data, approach by approach."""
    path = fuera.get("archivo") if fuera else None
    if not path or not Path(path).exists():
        return
    result = common.read_json(path)
    st.markdown(idioma.t("dominio.show_no_data.title"), help=common.ayuda("fuera"))
    st.caption(common.md(fuera["intro"]))
    # The approaches' names come from the measurement file, in Spanish; in English they are mapped by their code
    names = {k: v if idioma.lang() == "es" else idioma.t(f"dominio.paths.{k}")
             for k, v in result["caminos"].items() if tech or k != "D"}
    n = len(result["preguntas"])
    for col, (k, name) in zip(st.columns(len(names)), names.items()):
        col.metric(name, idioma.t("dominio.show_no_data.of", found=result["totales"][k], n=n))
    question_col = idioma.t("dominio.show_no_data.col_question")
    common.tabla(pd.DataFrame([{question_col: row["pregunta"], idioma.t("dominio.show_no_data.col_missing"): row["falta"],
                         **{name: f"{row[k]['marca']} {row[k]['respuesta']}" for k, name in names.items()}}
                        for row in result["preguntas"].values()]),
          column_config={question_col: st.column_config.TextColumn(width="medium")})
    st.caption(idioma.t("dominio.show_no_data.legend"))


def evaluation_detail(evaluation, totals, domain):
    data = evaluation["questions"]
    names = {k: idioma.t(f"dominio.paths.{k}") for k in "BDC" if k in totals}
    st.markdown(idioma.t("dominio.evaluation_detail.title"))
    cols = st.columns(len(names))
    for col, k in zip(cols, names):
        col.metric(names[k], f"{totals.get(k, {}).get('correct', 0)}/{len(data)}")
    if "D" in names:
        st.info(idioma.t("dominio.evaluation_detail.links_note"))
    chosen = st.selectbox(idioma.t("dominio.evaluation_detail.question"), [e["question"] for e in data.values()],
                          key=f"{domain}_eval_question")
    entry = next(e for e in data.values() if e["question"] == chosen)

    def fmt(v):
        if v is None:
            return idioma.t("dominio.evaluation_detail.no_answer")
        if isinstance(v, list):
            return ", ".join(v[:10]) + (" " + idioma.t("dominio.show_why.more", n=len(v) - 10) if len(v) > 10 else "")
        return common.money(v)

    st.markdown(idioma.t("dominio.evaluation_detail.correct", answer=common.md(fmt(entry['reference']))))
    for col, k in zip(st.columns(len(names)), names):
        with col:
            e = entry.get(k)
            if not e:
                continue
            st.markdown(f"#### {names[k]}")
            st.markdown(("✅ " if e["ok"] else "❌ ") + common.md(fmt(e.get("answer"))))
            ok = [a for a in e["attempts"] if a["error"] is None]
            if ok:
                q = ok[-1]["query"]
                shown = sqlparse.format(q, reindent=True, keyword_case="upper", indent_width=2) if k in "BD" else q
                attempts = "dominio.evaluation_detail.attempts_one" if len(e['attempts']) == 1 \
                    else "dominio.evaluation_detail.attempts_many"
                st.caption(idioma.t(attempts, lines=len(shown.splitlines()), n=len(e['attempts'])))
                st.code(shown, language="sql" if k in "BD" else "sparql")
