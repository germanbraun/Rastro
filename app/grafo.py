"""Dibuja una instancia del grafo como SVG: la entidad al centro y cada propiedad alrededor.
Burbuja azul: una entidad; burbuja naranja punteada: su clase; rectángulo: un dato simple
(texto, número o fecha). Cada flecha lleva el nombre de negocio de la propiedad.

Lo usan la app («Así se ve un dato del grafo») y las diapositivas (docs/slides/grafo_instancia.py).
El dibujo va sobre un fondo claro propio, así se lee igual con tema claro u oscuro.
"""
import html
import math

NAVY, GREY, EDGE = "#14213D", "#4A5568", "#7A8699"


def cut(text, n):
    text = str(text)
    return text if len(text) <= n else text[:n - 1] + "…"


def svg(center, nodes, width=1664, height=640, scale=1.0, font="'Times New Roman', Times, serif"):
    """center = (título, subtítulo). nodes = [(tipo, etiqueta, subtítulo, propiedad)], tipo:
    "entidad", "clase" o "dato"."""
    s = scale
    cx, cy = width / 2, height / 2
    rx, ry = width / 2 - 250 * s, height / 2 - 70 * s
    n = max(1, len(nodes))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" '
             f'font-family="{font}">',
             f'<rect width="{width}" height="{height}" rx="{18 * s:.0f}" fill="#FFFFFF"/>',
             '<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
             f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{EDGE}"/></marker></defs>']
    placed = []
    for k, (kind, label, sub, prop) in enumerate(nodes):
        a = -math.pi / 2 + 2 * math.pi * k / n
        placed.append((cx + rx * math.cos(a), cy + ry * math.sin(a), kind, cut(label, 22), cut(sub, 30), cut(prop, 22)))
    for x, y, _kind, _label, _sub, prop in placed:       # flechas debajo de los nodos
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy) or 1
        x1, y1 = cx + dx / d * 175 * s, cy + dy / d * 60 * s
        x2, y2 = x - dx / d * 150 * s, y - dy / d * 46 * s
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{EDGE}" '
                     f'stroke-width="{2 * s:.1f}" marker-end="url(#flecha)"/>')
        parts.append(f'<rect x="{mx - 120 * s:.0f}" y="{my - 18 * s:.0f}" width="{240 * s:.0f}" height="{32 * s:.0f}" '
                     f'rx="6" fill="#FFFFFF"/><text x="{mx:.0f}" y="{my + 6 * s:.0f}" font-size="{23 * s:.0f}" '
                     f'text-anchor="middle" fill="{GREY}" font-style="italic">{html.escape(prop)}</text>')
    for x, y, kind, label, sub, _prop in placed:
        if kind == "dato":
            parts.append(f'<rect x="{x - 150 * s:.0f}" y="{y - 32 * s:.0f}" width="{300 * s:.0f}" height="{64 * s:.0f}" '
                         f'rx="10" fill="#F4F6F9" stroke="#B8C2CF" stroke-width="{2 * s:.1f}"/>'
                         f'<text x="{x:.0f}" y="{y + 8 * s:.0f}" font-size="{25 * s:.0f}" text-anchor="middle" '
                         f'fill="{NAVY}">{html.escape(label)}</text>')
            continue
        fill, stroke, dash = (("#FFF3E6", "#FF8C42", f' stroke-dasharray="{7 * s:.0f} {5 * s:.0f}"') if kind == "clase"
                              else ("#DCEBFA", "#2F6FB5", ""))
        parts.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{160 * s:.0f}" ry="{48 * s:.0f}" fill="{fill}" '
                     f'stroke="{stroke}" stroke-width="{2 * s:.1f}"{dash}/>'
                     f'<text x="{x:.0f}" y="{y + (0 if sub else 8) * s:.0f}" font-size="{25 * s:.0f}" font-weight="700" '
                     f'text-anchor="middle" fill="{NAVY}">{html.escape(label)}</text>')
        if sub:
            parts.append(f'<text x="{x:.0f}" y="{y + 24 * s:.0f}" font-size="{17 * s:.0f}" text-anchor="middle" '
                         f'fill="{GREY}">{html.escape(sub)}</text>')
    title, subtitle = center
    parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{185 * s:.0f}" ry="{62 * s:.0f}" fill="#2F6FB5"/>'
                 f'<text x="{cx}" y="{cy - 2 * s:.0f}" font-size="{27 * s:.0f}" font-weight="700" text-anchor="middle" '
                 f'fill="#FFFFFF">{html.escape(cut(title, 26))}</text>'
                 f'<text x="{cx}" y="{cy + 26 * s:.0f}" font-size="{17 * s:.0f}" text-anchor="middle" '
                 f'fill="#DCEBFA">{html.escape(cut(subtitle, 36))}</text>')
    return "\n".join(parts + ["</svg>"])
