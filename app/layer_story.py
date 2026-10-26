"""A configured Layer answer followed by its calculation, connections and evidence."""
from html import escape

import enlaces
import idioma


def map_link(text, links):
    """The company name used in the map's partner text, and whether its link to the company still waits for a
    person. links: rows with «nombre», «regla» and «evidencia»."""
    for link in sorted(links, key=lambda row: -len(row["nombre"])):
        if link["nombre"] and link["nombre"].upper() in str(text).upper():
            return link["nombre"], enlaces.status(link.get("regla"), link["evidencia"]) == "ia"
    return None, False

import pandas as pd
import streamlit as st


def show_story(domain, why, columns, rows, where, tech):
    from dominio import md, prefixed, run, tabla

    ui = why['recorrido']
    values = list(dict.fromkeys(row[columns.index(why['columna'])] for row in rows))
    if not values:
        return
    if not st.toggle(ui['title'], key=f'{domain}_{where}_story_open'):
        return
    with st.container(border=True):
        company = st.selectbox(ui['company'], values,
                               index=values.index(ui['example']) if ui['example'] in values else 0,
                               key=f'{domain}_{where}_story_company')
        query = prefixed(why['query'].replace('{valor}', str(company).replace('\\', '\\\\').replace('"', '\\"')), domain)
        cols, found = run(query, domain)
        if not found:
            st.info(ui['missing'])
            return
        records = [dict(zip(cols, row)) for row in found]
        st.caption(ui['definition'])
        st.markdown(ui['total'].format(company=md(company), count=len(records)))
        if 'operated' in columns and 'share' in columns:
            answer = next(row for row in rows if row[columns.index(why['columna'])] == company)
            with st.expander(ui['comparison_title']):
                for col, variable, label in zip(st.columns(2), ['operated', 'share'],
                                                [ui['operated_label'], ui['share_label']]):
                    value = answer[columns.index(variable)]
                    col.metric(label, f'{idioma.millions(value)} M m³' if value not in (None, '') else ui['unavailable'])
                st.caption(ui['comparison_note'])
        with st.expander(ui['breakdown_title']):
            visible = why['columnas']
            units = why['numeros'] if isinstance(why.get('numeros'), dict) else {}
            shown = [{k: idioma.millions(v, units[k]) if k in units and v not in (None, '') else v for k, v in r.items()}
                     for r in records]
            tabla(enlaces.add_status(pd.DataFrame(shown))[[enlaces.label('column'), *visible]].rename(columns=visible),
                  column_config=enlaces.column_help(), key=f'{domain}_{where}_story_breakdown')
            st.caption(ui['breakdown_note'])
        names = [r['concesion'] for r in records]
        concession = st.selectbox(ui['concession'], names,
                                  index=names.index(ui['example_concession']) if ui['example_concession'] in names else 0,
                                  key=f'{domain}_{where}_story_concession_{company}')
        record = records[names.index(concession)]
        link_query = prefixed(ui['linking_query'].replace('{valor}', str(company).replace('\\', '\\\\').replace('"', '\\"')), domain)
        link_cols, link_rows = run(link_query, domain)
        map_name, pending = map_link(record['texto'], [dict(zip(link_cols, row)) for row in link_rows])
        values = {**record, 'company': company, 'map_name': map_name or company,
                  'production': idioma.millions(record['produccion']), 'share': idioma.millions(record['parte']),
                  'percent': str(record['porcentaje']).rstrip('0').rstrip('.')
                  if '.' in str(record['porcentaje']) else str(record['porcentaje'])}
        st.markdown('##### ' + ui['calculation_title'])
        st.info(ui['calculation'].format(**{k: md(str(v)) for k, v in values.items()}))
        st.caption(ui['rounding'])
        st.markdown('##### ' + ui['connections_title'])
        cards = []
        for card in ui['sources']:
            cards.append('<div style="flex:1 1 230px;border:1px solid #c5d3e0;border-radius:12px;padding:16px">'
                         f'<strong>{escape(card["title"])}</strong><br>'
                         f'{escape(card["text"].format(**values))}</div>')
        st.markdown('<div style="display:flex;flex-wrap:wrap;gap:12px">' + ''.join(cards) + '</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;padding:12px;color:#2F6FB5;font-size:24px">↓</div>'
                    '<div style="border:2px solid #2F6FB5;border-radius:12px;padding:16px;text-align:center">'
                    f'<strong>{escape(ui["connection"].format(**values))}</strong><br>'
                    f'{escape(ui["connection_detail"].format(**values))}</div>', unsafe_allow_html=True)
        if pending:   # the number rests on a name link a person has not confirmed yet: say it where the number is
            st.warning(f"**{enlaces.label('ia')}.** " + ui['pending_link'].format(**values))
        st.caption(ui['contribution'])
        with st.expander(ui['records_title']):
            st.markdown(ui['original_text'].format(text=md(record['texto'])))
            visible = why['columnas']
            tabla(pd.DataFrame([record])[list(visible)].rename(columns=visible),
                  key=f'{domain}_{where}_story_records')
            st.caption(ui['records_note'])
            production_query = prefixed(ui['production_query'].replace('{concesion}',
                                        str(concession).replace('\\', '\\\\').replace('"', '\\"')), domain)
            production_cols, production_rows = run(production_query, domain)
            frame = pd.DataFrame(production_rows, columns=production_cols)
            tabla(frame[list(ui['production_columns'])].rename(columns=ui['production_columns']),
                  key=f'{domain}_{where}_story_production')
            st.caption(ui['production_note'])
            if tech:
                st.dataframe(frame, hide_index=True, use_container_width=True)
                st.code(production_query, language='sparql')
        with st.expander(ui['linking_title']):
            if link_rows:
                frame = enlaces.add_status(pd.DataFrame(link_rows, columns=link_cols))
                tabla(frame[[enlaces.label('column'), *ui['linking_columns']]].rename(columns=ui['linking_columns']),
                      column_config=enlaces.column_help(), key=f'{domain}_{where}_story_links')
            else:
                st.info(ui['missing'])
            st.caption(ui['linking_note'])
            if tech:
                st.markdown(ui['identity'])
                st.code(record['empresa'], language=None)
                st.code(link_query, language='sparql')
        if tech:
            with st.expander(ui['technical_title']):
                st.json({key: record[key] for key in ('empresa', 'concesionIri', 'participacion', 'origen', 'actividad', 'regla')})
                st.code(query, language='sparql')
