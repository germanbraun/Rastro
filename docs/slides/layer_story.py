"""Build three Layer story slides from a captured live answer and its evidence."""
import json
from decimal import Decimal
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def number(value):
    return f'{Decimal(value):,.0f}'.replace(',', '.')


def build():
    snapshot = json.loads((ROOT / 'docs/experiments/layer-answer/chevron.json').read_text())
    company = snapshot['company']
    answer = next(row for row in snapshot['answer'] if row['company'] == company)
    record = next(row for row in snapshot['explanation'] if row['concesion'] == snapshot['concession'])
    escaped = {key: escape(str(value)) for key, value in record.items()}
    titles = ['La respuesta', 'Lo que Rastro conectó', 'La evidencia de este número']
    bodies = [
        f'''<p>¿Cuánto petróleo de 2025 le corresponde a cada empresa?</p>
        <div class="card"><h3>{escape(company)}</h3><p class="value">{number(answer['share'])} m³</p>
        <p>Su parte, sumada en {len(snapshot['explanation'])} concesiones.</p></div>
        <p><b>¿Por qué este número?</b> Elegimos una concesión y seguimos el cálculo hasta su fuente.</p>
        <p>Producción operada y participación son medidas distintas. Aquí calculamos la participación registrada.</p>''',
        f'''<div class="cards"><div class="card"><h3>Declaraciones de producción</h3>
<p>Los pozos de {escaped['concesion']}</p>
<p>{number(record['produccion'])} m³ de petróleo</p></div>
        <div class="card"><h3>Mapa de concesiones</h3>
<p>{escape(company)} · {escaped['porcentaje']} %</p>
<p>Socios y porcentajes en el texto original.</p></div></div>
        <p class="arrow">↓</p><div class="card"><h3>{escaped['concesion']} → Participación → {escape(company)}</h3>
        <p>{number(record['produccion'])} m³ × {escaped['porcentaje']} % = {number(record['parte'])} m³</p></div>
        <p>Los mapeos traducen las fuentes al mismo vocabulario. Los enlaces conectan las entidades.</p>''',
        f'''<div class="card"><h3>El texto original del mapa</h3>
<p>{escaped['texto']}</p></div>
        <div class="card"><h3>Una empresa, distintos nombres</h3>
<p>Los nombres de origen apuntan a {escape(company)}, con una regla y su evidencia.</p></div>
        <p><b>En la app:</b> «Ver los registros originales» y «Ver cómo se conectaron los nombres».</p>
        <p>Rastro reutiliza las definiciones en cada pregunta. SQL sobre los mismos enlaces también puede obtener la respuesta.</p>'''
    ]
    for step, (name, title, body) in enumerate(zip(['e-integracion', 'e-layer-conexiones', 'e-layer-evidencia'], titles, bodies), 1):
        html = f'''<section id="{name}" style="background:#F7F6F2;color:#14213D;font-family:'Times New Roman', Times, serif;
padding:90px 128px 180px;
display:flex;flex-direction:column;gap:24px">
<style>#{name} p{{font-size:32px;line-height:1.35}}
#{name} h3{{font-size:40px}}
#{name} .card{{background:#fff;border:1px solid #E1E4E8;border-radius:16px;padding:26px;flex:1}}
#{name} .cards{{display:flex;gap:28px}}
#{name} .value{{font-size:72px;color:#2F6FB5}}
#{name} .arrow{{text-align:center;color:#2F6FB5}}</style>
<p style="color:#2F6FB5">Rastro Layer · {step} · Pregunta → Conexiones → Evidencia</p>
<h2 style="font-size:56px;line-height:1.1">{title}</h2>
{body}
<aside>Snapshot: docs/experiments/layer-answer/chevron.json, captured {escape(snapshot['created_utc'])}.
App queries current loaded data. Whole cubic metres are rounded for display.
Name-link corrections retain their recorded review status; an AI review is not human approval.
This is a worked example, not an independently reviewed accuracy measurement.</aside>
</section>'''
        order = json.loads((HERE / 'mazos/energia.json').read_text())['order']
        footer = ('<div style="position:absolute;left:128px;bottom:64px;width:1664px;display:flex;'
                  'justify-content:space-between;font-size:24px;color:#7A8699">'
                  f'<span>Rastro · Petróleo y gas en Argentina</span><span>{order.index(name) + 1}</span></div>')
        html = html.replace('<aside>', footer + '\n<aside>')
        (HERE / 'slides' / f'{name}.html').write_text(html + '\n')


if __name__ == '__main__':
    build()
