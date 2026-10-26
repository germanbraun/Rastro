"""Build three Layer story slides from a captured live answer and its evidence."""
import json
from decimal import Decimal
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def millions(value):
    """A volume in m³ as millions of m³, the app's unit (app/idioma.millions)."""
    v = Decimal(value) / Decimal(1_000_000)
    return f'{v:,.{1 if abs(v) >= 10 else 2}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def percent(value):
    return f'{Decimal(str(value)).normalize():f}'.replace('.', ',')


def map_link(text, links):
    """Same check as app/layer_story.map_link (that module imports Streamlit): the name used in the map's partner
    text, and whether its link still waits for a person."""
    for link in sorted(links, key=lambda row: -len(row['nombre'])):
        if link['nombre'] and link['nombre'].upper() in str(text).upper():
            return link['nombre'], 'a confirmar por una persona' in str(link['evidencia'])
    return None, False


def build():
    snapshot = json.loads((ROOT / 'docs/experiments/layer-answer/chevron.json').read_text())
    company = snapshot['company']
    answer = next(row for row in snapshot['answer'] if row['company'] == company)
    record = next(row for row in snapshot['explanation'] if row['concesion'] == snapshot['concession'])
    escaped = {key: escape(str(value)) for key, value in record.items()}
    map_name, pending = map_link(record['texto'], snapshot['links'])
    pct = percent(record['porcentaje'])
    pending_note = (f'<p><b>🟠 Revisada por IA, falta una persona.</b> En el mapa figura «{escape(map_name)}». '
                    f'Rastro la une a {escape(company)} por una '
                    'corrección revisada por un asistente de IA, que espera la confirmación de una persona.</p>'
                    if pending else '')
    answer_note = ('<p>Parte de este número depende de una unión de nombres que todavía espera la confirmación '
                   'de una persona (siguiente diapositiva).</p>' if pending else '')
    evidence_note = (f' La unión de «{escape(map_name)}» la revisó un asistente de IA y espera la confirmación de una '
                     'persona.' if pending else '')
    titles = ['La respuesta', 'Lo que Rastro conectó', 'La evidencia de este número']
    bodies = [
        f'''<p>¿Cuánto petróleo de 2025 le corresponde a cada empresa?</p>
        <div class="card"><h3>{escape(company)}</h3><p class="value">{millions(answer['share'])} M m³</p>
        <p>Su parte, sumada en {len(snapshot['explanation'])} concesiones.</p></div>
        <p><b>¿Por qué este número?</b> Elegimos una concesión y seguimos el cálculo hasta su fuente.</p>
        <p>Producción operada y participación son medidas distintas. Aquí calculamos la participación registrada.</p>
        {answer_note}''',
        f'''<div class="cards"><div class="card"><h3>Declaraciones de producción</h3>
<p>Los pozos de {escaped['concesion']}</p>
<p>{millions(record['produccion'])} millones de m³ de petróleo</p></div>
        <div class="card"><h3>Mapa de concesiones</h3>
<p>«{escape(map_name or company)}» · {pct} %</p>
<p>Socios y porcentajes en el texto original.</p></div></div>
        <p class="arrow">↓</p><div class="card"><h3>{escaped['concesion']} → Participación → {escape(company)}</h3>
        <p>{millions(record['produccion'])} millones de m³ × {pct} % = {millions(record['parte'])} millones de m³</p></div>
        {pending_note}
        <p>Los mapeos traducen las fuentes al mismo vocabulario. Los enlaces conectan las entidades.</p>''',
        f'''<div class="card"><h3>El texto original del mapa</h3>
<p>{escaped['texto']}</p></div>
        <div class="card"><h3>Una empresa, distintos nombres</h3>
<p>Los nombres de origen apuntan a {escape(company)}, con una regla y su evidencia.{evidence_note}</p></div>
        <p><b>En la app:</b> «Ver los registros originales» y «Ver cómo se conectaron los nombres».</p>
        <p>Rastro reutiliza las definiciones en cada pregunta. SQL sobre los mismos enlaces también puede obtener la respuesta.</p>'''
    ]
    for step, (name, title, body) in enumerate(zip(['e-layer-respuesta', 'e-layer-conexiones', 'e-layer-evidencia'], titles, bodies), 1):
        html = f'''<section id="{name}" style="background:#F7F6F2;color:#14213D;font-family:'Times New Roman', Times, serif;
padding:90px 128px 180px;
display:flex;flex-direction:column;gap:24px">
<style>#{name} p{{font-size:32px;line-height:1.35}}
#{name} h3{{font-size:40px}}
#{name} .card{{background:#fff;border:1px solid #E1E4E8;border-radius:16px;padding:26px;flex:1}}
#{name} .cards{{display:flex;gap:28px}}
#{name} .value{{font-size:72px;color:#2F6FB5}}
#{name} .arrow{{text-align:center;color:#2F6FB5}}</style>
<p style="color:#2F6FB5">Anexo · Del número a la evidencia · {step} de 3</p>
<h2 style="font-size:56px;line-height:1.1">{title}</h2>
{body}
<aside>Cifras de docs/experiments/layer-answer/chevron.json, tomadas el {escape(snapshot['created_utc'][:10])};
la app consulta los datos cargados hoy, así que conviene mostrarlas en vivo. Los metros cúbicos se redondean al
mostrarlos. Decir que la unión de nombres que sostiene la parte de {escape(company)} la revisó un asistente de IA
y que todavía falta que una persona la confirme. Es un ejemplo trabajado, no una medición de exactitud revisada
por una persona.</aside>
</section>'''
        order = json.loads((HERE / 'mazos/energia.json').read_text())['order']
        footer = ('<div style="position:absolute;left:128px;bottom:64px;width:1664px;display:flex;'
                  'justify-content:space-between;font-size:24px;color:#7A8699">'
                  f'<span>Rastro · Petróleo y gas en Argentina</span><span>{order.index(name) + 1}</span></div>')
        html = html.replace('<aside>', footer + '\n<aside>')
        (HERE / 'slides' / f'{name}.html').write_text(html + '\n')


if __name__ == '__main__':
    build()
