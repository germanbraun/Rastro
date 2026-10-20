"""Dibuja como grafo la instancia de las diapositivas «Así se ve un dato del grafo» (instancia-*.html):
burbujas para las entidades, burbujas naranjas para las clases, rectángulos para los datos simples y
flechas con el nombre de negocio de cada propiedad. Lee la tabla de la diapositiva y los nombres de
las entidades enlazadas en el Ontop de cada dominio.

    python3 docs/slides/grafo_instancia.py
"""
import csv
import html
import io
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DOMAINS = {"energia": ("https://w3id.org/rastro/energia#", 8082),
           "proveedores": ("https://w3id.org/rastro/proveedores#", 8081),
           "oncologia": ("https://w3id.org/rastro/oncologia#", 8080)}
W, H = 1664, 640


def name_of(iri, ns, port):
    q = f"SELECT ?n WHERE {{ <{iri}> <{ns}name> ?n }} LIMIT 1"
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"http://localhost:{port}/sparql",
                                   data=urllib.parse.urlencode({"query": q}).encode(),
                                   headers={"Accept": "text/csv"}), timeout=60)
        rows = list(csv.reader(io.StringIO(r.read().decode())))[1:]
        return rows[0][0] if rows else None
    except Exception:
        return None


def cut(text, n):
    return text if len(text) <= n else text[:n - 1] + "…"


def svg(center, rows, ns, port):
    cx, cy, rx, ry = W / 2, H / 2, 560, 232
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
             'font-family="\'Times New Roman\', Times, serif">',
             '<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" '
             'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#7A8699"/></marker></defs>']
    nodes = []
    for k, (term, meaning, value) in enumerate(rows):
        a = -math.pi / 2 + 2 * math.pi * k / len(rows)
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
        if term == "a":
            kind, label, sub = "clase", re.sub(r"^\S+\s*", "", value).strip("()") or value, value.split(" ")[0]
        elif value.startswith("rastro:"):
            iri = "https://w3id.org/rastro/" + value[len("rastro:"):]
            kind, label, sub = "entidad", name_of(iri, ns, port) or value.split("/")[-1], value
        else:
            kind, label, sub = "dato", value, ""
        nodes.append((x, y, kind, cut(label, 22), cut(sub, 30), re.sub(r"\s*\(.*", "", meaning or term), term))
    for x, y, kind, label, sub, meaning, term in nodes:          # flechas primero, debajo de los nodos
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        x1, y1 = cx + dx / d * 170, cy + dy / d * 58
        x2, y2 = x - dx / d * 150, y - dy / d * 46
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#7A8699" '
                     'stroke-width="2" marker-end="url(#flecha)"/>')
        parts.append(f'<rect x="{mx - 125:.0f}" y="{my - 20:.0f}" width="250" height="34" rx="6" fill="#F7F6F2"/>'
                     f'<text x="{mx:.0f}" y="{my + 5:.0f}" font-size="25" text-anchor="middle" fill="#4A5568" '
                     f'font-style="italic">{html.escape(cut(meaning, 22))}</text>')
    for x, y, kind, label, sub, meaning, term in nodes:
        if kind == "dato":
            parts.append(f'<rect x="{x - 150:.0f}" y="{y - 32:.0f}" width="300" height="64" rx="10" fill="#FFFFFF" '
                         f'stroke="#B8C2CF" stroke-width="2"/><text x="{x:.0f}" y="{y + 8:.0f}" font-size="26" '
                         f'text-anchor="middle" fill="#14213D">{html.escape(label)}</text>')
        else:
            fill, stroke, dash = (("#FFF3E6", "#FF8C42", ' stroke-dasharray="7 5"') if kind == "clase"
                                  else ("#DCEBFA", "#2F6FB5", ""))
            parts.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="160" ry="48" fill="{fill}" stroke="{stroke}" '
                         f'stroke-width="2"{dash}/><text x="{x:.0f}" y="{y - 2:.0f}" font-size="26" font-weight="700" '
                         f'text-anchor="middle" fill="#14213D">{html.escape(label)}</text>'
                         f'<text x="{x:.0f}" y="{y + 25:.0f}" font-size="18" text-anchor="middle" fill="#4A5568">'
                         f'{html.escape(sub)}</text>')
    parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="180" ry="62" fill="#2F6FB5"/>'
                 f'<text x="{cx}" y="{cy - 4}" font-size="28" font-weight="700" text-anchor="middle" fill="#FFFFFF">'
                 f'{html.escape(center[0])}</text><text x="{cx}" y="{cy + 24}" font-size="17" text-anchor="middle" '
                 f'fill="#DCEBFA">{html.escape(center[1])}</text>')
    return "\n".join(parts + ["</svg>"])


LEGEND = ('<p style="font-size:24px;color:#4A5568">Burbuja azul: una entidad · burbuja naranja: su clase en el '
          'diccionario · rectángulo: un dato simple (texto o número) · cada flecha: una propiedad, con su nombre de negocio.</p>')

for domain, (ns, port) in DOMAINS.items():
    path = HERE / "slides" / f"instancia-{domain}.html"
    text = path.read_text()
    title = re.search(r"<h2[^>]*>(.*?)</h2>", text).group(1)
    iri = html.unescape(re.search(r'<p style="font-size:26px;color:#4A5568">(.*?)</p>', text).group(1)).strip("<>")
    block = re.search(r'<div style="background:#FFFFFF;border-radius:20px;padding:(?:28px 32px|12px 0);width:1664px">.*?</div>\n'
                      r'(?:<p style="font-size:24px;color:#4A5568">Burbuja.*?</p>\n)?', text, re.S)
    rows = re.findall(r"<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", block.group(0))
    if not rows:   # ya dibujada: las filas están guardadas en el comentario
        rows = [tuple(html.unescape(c) for c in r.split("\t")) for r in
                re.search(r"<!-- filas\n(.*?)\n-->", block.group(0), re.S).group(1).split("\n")]
    rows = [tuple(html.unescape(c) for c in r) for r in rows]
    center = (re.sub(r"^[^:]+:\s*", "", title), iri)
    saved = "<!-- filas\n" + "\n".join("\t".join(html.escape(c) for c in r) for r in rows) + "\n-->"
    new = (f'<div style="background:#FFFFFF;border-radius:20px;padding:12px 0;width:1664px">{saved}\n'
           f'{svg(center, rows, ns, port)}\n</div>\n{LEGEND}\n')
    path.write_text(text.replace(block.group(0), new))
    print(path.name, len(rows), "propiedades")
