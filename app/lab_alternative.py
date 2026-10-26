"""Display a fingerprinted alternative-model evaluation without training libraries."""
import json
import base64
from math import isclose
from html import escape
from textwrap import wrap

import pandas as pd
import streamlit as st

import alternative
import idioma
import lab
from dominio import tabla


def load_artifact():
    try:
        result = json.loads(alternative.ARTIFACT.read_text())
        return result if isinstance(result, dict) and isinstance(result.get('predictions'), list) else None
    except (OSError, ValueError):
        return None


def select_model(ui):
    result = load_artifact()
    label = result['selected_label'] if result else ui['unavailable_name']
    labels = {'ridge': ui['ridge'], 'alternative': ui['alternative'].format(model=label)}
    return st.radio(ui['selector'], list(labels), format_func=labels.get, horizontal=True, key='lab_model_selector')


def compare_errors(predicted, ridge, actual):
    """Compare absolute errors against the same observed value, in gas units."""
    error, baseline = abs(predicted - actual), abs(ridge - actual)
    status = 'tie' if isclose(error, baseline, abs_tol=1e-9) else 'better' if error < baseline else 'worse'
    return status, error, baseline


def tree_svg(path, ui, well="", leaf_label=None, ensemble_label=None):
    """Draw the actual selected path; it is one tree, not the ensemble prediction."""
    labels = []
    for step in path['steps']:
        feature = step['feature']
        if '=' in feature:
            field, category = feature.split('=', 1)
            question = idioma.t("lab.alternative.tree_question", question=f"{ui['feature_labels'].get(field, field)} = {category}")
            outcome = step['value'] > .5
        else:
            field = ui['feature_labels'].get(feature, feature)
            question = idioma.t("lab.alternative.tree_question", question=f"{field} {step['operator']} {lab.num(step['threshold'], 2)}")
            outcome = step['yes']
        labels.append((question, ui['tree_value'].format(value=lab.num(step['value'], 2)),
                       ui['yes'] if outcome else ui['no']))
    height = len(labels) * 142 + 170
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" viewBox="0 0 420 {height}">',
             '<g font-family="sans-serif" font-size="17" fill="#14213D" text-anchor="middle">',
             f'<text x="210" y="27">{escape(ui["tree_heading"].format(well=well))}</text>',
             f'<text x="210" y="52" font-size="15">{escape(ui["tree_subtitle"])}</text>']
    for i, (question, value, answer) in enumerate(labels):
        top = 84 + i * 142
        parts.append(f'<rect x="12" y="{top}" width="396" height="108" rx="12" fill="#FFF0CF" stroke="#2F6FB5"/>')
        for j, line in enumerate(wrap(question, 40)):
            parts.append(f'<text x="210" y="{top+25+j*21}">{escape(line)}</text>')
        parts.append(f'<text x="210" y="{top+90}" font-size="15">{escape(value)}</text>')
        parts.append(f'<path d="M210,{top+108} L210,{top+132} l-5,-7 m5,7 l5,-7" fill="none" stroke="#7A8699"/>')
        parts.append(f'<text x="243" y="{top+121}">{escape(answer)}</text>')
    top = 84 + len(labels) * 142
    parts.append(f'<rect x="12" y="{top}" width="396" height="66" rx="12" fill="#EFF6FD" stroke="#2F6FB5"/>')
    if ensemble_label:
        parts.append(f'<text x="210" y="{top+26}">{escape(leaf_label)}</text>')
        parts.append(f'<text x="210" y="{top+51}" font-size="15">{escape(ensemble_label)}</text>')
    else:
        parts.append(f'<text x="210" y="{top+39}">{escape(leaf_label or ui["leaf"])}</text>')
    parts.append('</g></svg>')
    return ''.join(parts)


def show_alternative(tech, pozo, ui, walkthrough):
    result = load_artifact()
    st.markdown('#### ' + ui['title'])
    st.markdown(ui['scope'])
    if result is None:
        st.info(ui['missing'])
        if tech:
            st.caption(ui['command'])
        return
    b = lab.datos()[1]
    if not alternative.compatible(result, b):
        st.warning(ui['stale'])
        if tech:
            st.caption(ui['command'])
        return
    prediction = next((row for row in result['predictions'] if row['idpozo'] == str(pozo)), None)
    if prediction is None:
        st.info(ui['missing'])
        return
    st.info(ui['experimental'])
    st.markdown(ui['selected'].format(model=result['selected_label']))
    st.caption(ui['training_scale'].format(scale=ui['transforms'][result.get('target_transform', 'log')]))
    st.caption(ui['sample'].format(train=result['train'], test=result['test']))
    st.markdown(ui['well'].format(well=pozo))
    tree, ridge, actual = st.columns(3)
    tree.metric(ui['prediction'].format(model=result['selected_label']), f"{lab.num(prediction['prediction'])} M m³")
    ridge.metric(ui['ridge_label'], f"{lab.num(prediction['ridge_prediction'])} M m³")
    actual.metric(ui['actual'], f"{lab.num(prediction['actual'])} M m³")
    status, error, baseline = compare_errors(prediction['prediction'], prediction['ridge_prediction'], prediction['actual'])
    message = ui['well_comparison'][status].format(error=lab.num(error, 2), ridge=lab.num(baseline, 2))
    {'better': st.success, 'worse': st.warning, 'tie': st.info}[status](message)
    st.caption(ui['accuracy_note'])
    st.markdown('##### ' + ui['evaluation'])
    best = min(item['mae'] for item in result['test_2025'])
    rows = [{ui['model']: ui['ridge_label'], ui['transformation']: ui['transforms']['direct'],
             ui['distinction']: '',
             ui['error']: result['ridge_test']['mae'], ui['r2']: result['ridge_test']['r2']}]
    rows.extend({ui['model']: item['label'],
                 ui['transformation']: ui['transforms'][item.get('target_transform', 'log')],
                 ui['distinction']: ' · '.join(label for applies, label in [
                     (item['name'] == result['selected'], ui['chosen_badge']),
                     (item['mae'] == best, ui['best_badge'])] if applies),
                 ui['error']: item['mae'], ui['r2']: item['r2']} for item in result['test_2025'])
    selected_index = 1 + next(i for i, item in enumerate(result['test_2025']) if item['name'] == result['selected'])
    frame = pd.DataFrame(rows).round(3)
    st.dataframe(frame.style.apply(lambda row: [
        'background-color: #e1f3e5; color: #143820; font-weight: bold' if row.name == selected_index else ''
    ] * len(row), axis=1), hide_index=True, use_container_width=True, key='lab_alternative_evaluation',
        column_config={ui['error']: st.column_config.NumberColumn(format='%.2f'),
                       ui['r2']: st.column_config.NumberColumn(format='%.3f')})
    st.caption(ui['ranking_note'])
    selected = next(item for item in result['test_2025'] if item['name'] == result['selected'])
    st.caption(ui['source_comparison'].format(raw=lab.num(result['raw_test']['mae']), semantic=lab.num(selected['mae'])))
    with st.expander(ui['validation']):
        tabla(pd.DataFrame([{ui['model']: item['label'],
                             ui['transformation']: ui['transforms'][item.get('target_transform', 'log')],
                             ui['selection_error']: round(item['selection_mae'], 3)}
                            for item in result['candidates']]), key='lab_alternative_validation')
    with st.expander(ui['tree']):
        st.caption(ui['tree_scope'])
        leaf_label = ensemble_label = None
        if result['selected'] == 'rf_direct':
            leaf_label = ui['forest_leaf'].format(gas=lab.num(prediction['path']['leaf']))
            ensemble_label = ui['forest_prediction'].format(gas=lab.num(prediction['prediction']))
        diagram = tree_svg(prediction['path'], ui, well=str(pozo), leaf_label=leaf_label, ensemble_label=ensemble_label)
        encoded = base64.b64encode(diagram.encode()).decode()
        st.markdown(f'<img src="data:image/svg+xml;base64,{encoded}" style="width:100%;max-width:420px;height:auto" '
                    f'alt="{escape(ui["tree_heading"].format(well=pozo))}">', unsafe_allow_html=True)
        if ensemble_label:
            st.caption(ui['forest_average'].format(single=lab.num(prediction['path']['leaf']),
                                                   prediction=lab.num(prediction['prediction'])))
        st.download_button(ui['download_tree'], diagram, file_name=f'pozo-{pozo}-arbol.svg', mime='image/svg+xml')
    with st.expander(ui['inputs']):
        st.caption(ui['input_note'])
        tabla(pd.DataFrame(lab.input_rows(pozo, walkthrough)), key='lab_alternative_inputs')
        variables = [item['variable'] for item in walkthrough['inputs']]
        variable = st.selectbox(ui['source_selector'], variables, format_func=lab.variable_label, key='lab_alternative_source')
        lab.show_source_evidence(pozo, variable, walkthrough, key='lab_alternative', tech=tech)
    st.caption(ui['identity'].format(date=pd.Timestamp(result['created_utc']).tz_convert(ui['timezone']).strftime('%d/%m/%Y %H:%M'),
                                      version=result['code_sha256'][:8],
                                      inputs=result['input_sha256'][:8]))
    st.caption(ui['publication'])
    if tech:
        with st.expander(ui['technical']):
            st.json({'selected': result['selected'], 'selection_rule': result['selection_rule'],
                     'code_sha256': result['code_sha256'], 'input_sha256': result['input_sha256'],
                     'records': prediction['records'], 'first_tree_path': prediction['path']})
            st.caption(ui['command'])
