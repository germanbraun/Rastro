"""Dibuja los dos diagramas de Rastro como SVG: arquitectura.svg y ontologia.svg.

Los usan las diapositivas (docs/slides) y la app. Para cambiarlos, editar acá y correr:
    python3 docs/diagramas/build.py
"""

from pathlib import Path

HERE = Path(__file__).parent
INK, BLUE, GRAY, LIGHT, LINE = "#14213D", "#2F6FB5", "#4A5568", "#F7F6F2", "#9AA5B8"
FONT = "font-family=\"'Times New Roman', Times, serif\""


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines=(), fill="#FFFFFF", color=INK, stroke=LINE, dash=False, size=26, sub=22):
    d = ' stroke-dasharray="8,6"' if dash else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"{d}/>']
    ty = y + 38 if lines else y + h / 2 + size / 3
    out.append(f'<text x="{x + w / 2}" y="{ty}" text-anchor="middle" font-size="{size}" font-weight="700" fill="{color}">{esc(title)}</text>')
    for i, line in enumerate(lines):
        out.append(f'<text x="{x + w / 2}" y="{y + 38 + (i + 1) * (sub + 8)}" text-anchor="middle" font-size="{sub}" '
                   f'fill="{color if fill != "#FFFFFF" else GRAY}">{esc(line)}</text>')
    return "\n".join(out)


def arrow(x1, y1, x2, y2, label="", lx=None, ly=None, head="arrow", color=GRAY):
    out = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5" marker-end="url(#{head})"/>']
    if label:
        lx = (x1 + x2) / 2 if lx is None else lx
        ly = (y1 + y2) / 2 - 10 if ly is None else ly
        out.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="22" fill="{BLUE}" font-style="italic">{esc(label)}</text>')
    return "\n".join(out)


def svg(w, h, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" {FONT}>
<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{GRAY}"/></marker>
<marker id="sub" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="12" markerHeight="12" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#FFFFFF" stroke="{GRAY}" stroke-width="1.5"/></marker>
<marker id="white" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#FFFFFF"/></marker>
</defs>
{body}
</svg>
'''


def architecture():
    b = []
    # Encabezados de columna
    for x, t in [(132, "FUENTES PÚBLICAS"), (440, "ALMACENAMIENTO"), (900, "CAPA SEMÁNTICA"), (1440, "QUIÉN LA USA")]:
        b.append(f'<text x="{x}" y="34" text-anchor="middle" font-size="22" font-weight="700" letter-spacing="2" fill="{BLUE}">{t}</text>')
    # Fuentes
    for i, (t, s) in enumerate([("AACT", "ensayos clínicos"), ("ChEMBL", "fármacos y targets"),
                                ("openFDA", "eventos adversos"), ("MeSH", "enfermedades")]):
        b.append(box(20, 60 + i * 150, 220, 120, t, [s]))
    # Almacenamiento
    b.append(box(320, 60, 240, 420, "Postgres", ["aact · chembl", "openfda", "copia de la", "jerarquía MeSH", "", "linking:", "los enlaces"]))
    b.append(box(320, 510, 240, 120, "GraphDB", ["MeSH completo"]))
    for i in range(3):
        b.append(arrow(240, 120 + i * 150, 318, 120 + i * 150 if i < 2 else 330))
    b.append(arrow(240, 570, 318, 570))
    b.append(f'<text x="130" y="668" text-anchor="middle" font-size="20" fill="{GRAY}">un cargador por fuente</text>')
    # Capa semántica
    b.append(f'<rect x="620" y="50" width="560" height="590" rx="20" fill="{BLUE}"/>')
    b.append(box(650, 80, 500, 120, "Entity linking", ["ensayo → fármaco · ensayo → MeSH", "clases de fármaco (ATC)"], fill="#4A84C4", color="#FFFFFF", stroke="#4A84C4"))
    b.append(box(650, 220, 240, 130, "Ontología", ["conceptos de", "negocio (OWL)"], fill="#4A84C4", color="#FFFFFF", stroke="#4A84C4"))
    b.append(box(910, 220, 240, 130, "Mapeos", ["columna →", "concepto (R2RML)"], fill="#4A84C4", color="#FFFFFF", stroke="#4A84C4"))
    b.append(box(650, 400, 500, 130, "Ontop", ["traduce cada consulta SPARQL", "a SQL sobre Postgres"], fill="#FFFFFF", color=INK, stroke="#FFFFFF"))
    b.append(f'<text x="900" y="600" text-anchor="middle" font-size="22" fill="#FFFFFF">Grafo virtual: los datos no se mueven</text>')
    b.append(arrow(562, 270, 618, 270))
    b.append(arrow(900, 352, 900, 396, color="#FFFFFF", head="white"))
    # Quién la usa
    b.append(box(1250, 60, 380, 170, "App Rastro Layer", ["el LLM lee la ontología", "y escribe SPARQL", "cada dato con su fuente"]))
    b.append(box(1250, 260, 380, 120, "Otras herramientas", ["cualquier cliente SPARQL"]))
    b.append(box(1250, 410, 380, 120, "GraphDB federa", ["Rastro + MeSH + Wikidata"]))
    b.append(box(1250, 560, 380, 90, "Wikidata", [], fill=LIGHT, dash=True))
    b.append(arrow(1182, 145, 1248, 145))
    b.append(arrow(1182, 320, 1248, 320))
    b.append(arrow(1182, 470, 1248, 470))
    b.append(arrow(1440, 532, 1440, 556))
    # MeSH de GraphDB entra a la consulta federada por debajo de la capa
    b.append(f'<polyline points="562,600 600,600 600,662 1215,662 1215,500 1246,500" fill="none" stroke="{GRAY}" stroke-width="2.5" marker-end="url(#arrow)"/>')
    return svg(1664, 680, "\n".join(b))


def ontology():
    b = []
    # Clases de fármaco
    b.append(box(700, 10, 250, 70, "Inhibidor de quinasa", [], size=24))
    b.append(box(970, 10, 270, 70, "Anticuerpo monoclonal", [], size=24))
    b.append(box(840, 130, 250, 80, "Terapia dirigida", ["deducida, sin mapeo"], dash=True, size=24, sub=19))
    b.append(box(1120, 135, 200, 70, "Quimioterapia", [], size=24))
    b.append(box(1340, 135, 230, 70, "Terapia hormonal", [], size=24))
    b.append(arrow(825, 80, 930, 128, head="sub"))
    b.append(arrow(1105, 80, 1010, 128, head="sub"))
    b.append(arrow(965, 212, 1090, 298, head="sub"))
    b.append(arrow(1220, 207, 1150, 298, head="sub"))
    b.append(arrow(1455, 207, 1210, 298, head="sub"))
    b.append(f'<text x="1600" y="60" text-anchor="end" font-size="20" fill="{GRAY}">▷ es un tipo de (subclase)</text>')
    # Centro
    b.append(box(540, 300, 300, 160, "Ensayo", ["fase · estado", "fecha de inicio · título"], fill=LIGHT, stroke=INK))
    b.append(box(1010, 300, 280, 160, "Fármaco", ["nombre · ChEMBL ID", "aprobado"], fill=LIGHT, stroke=INK))
    b.append(box(1400, 300, 240, 160, "Target", ["nombre · gen"], fill=LIGHT, stroke=INK))
    b.append(box(40, 320, 260, 120, "Sponsor", ["nombre · es industria"], fill=LIGHT, stroke=INK))
    b.append(box(540, 560, 300, 130, "Condición", ["descriptor de MeSH"], fill=LIGHT, stroke=INK))
    b.append(box(1180, 580, 230, 110, "Reportes por año", ["año · reportes · serios"], size=24, sub=20))
    b.append(box(1430, 580, 230, 110, "Reacción reportada", ["reacción · reportes"], size=24, sub=20))
    b.append(box(930, 560, 230, 140, "Enlace", ["evidencia: texto del", "sponsor, coincidencia", "y regla (PROV-O)"], size=24, sub=19, dash=True))
    b.append(arrow(842, 380, 1006, 380, "prueba el fármaco"))
    b.append(arrow(1292, 380, 1396, 380, "actúa sobre"))
    b.append(arrow(538, 380, 304, 380, "sponsor"))
    b.append(arrow(690, 462, 690, 556, "condición", lx=750, ly=515))
    b.append(f'<path d="M 842 600 C 905 600 905 660 842 660" fill="none" stroke="{GRAY}" stroke-width="2.5" marker-end="url(#arrow)"/>')
    b.append(f'<text x="690" y="725" text-anchor="middle" font-size="22" fill="{BLUE}" font-style="italic">está dentro de <tspan fill="{GRAY}" font-style="normal" font-size="19">(sus subtipos)</tspan></text>')
    b.append(arrow(960, 558, 842, 462, "ensayo", lx=880, ly=500))
    b.append(arrow(1060, 558, 1100, 464, "fármaco", lx=1112, ly=520))
    b.append(arrow(1290, 578, 1200, 464))
    b.append(arrow(1540, 578, 1285, 450))
    # Procedencia
    b.append(box(40, 560, 380, 130, "Fuente", ["cada dato apunta a su fuente", "y su licencia (proviene de)"], size=24, sub=20))
    return svg(1680, 740, "\n".join(b))


# Las mismas imágenes van a la app y, dentro de una diapositiva cada una, al mazo
ROOT = HERE.parent.parent
SLIDE = """<section id="{id}" style="background:#F7F6F2;color:#14213D;font-family:'Times New Roman', Times, serif;padding:80px 120px;display:flex;flex-direction:column;gap:28px">
<p style="font-size:28px;font-weight:600;color:#2F6FB5;letter-spacing:2px;text-transform:uppercase">{label}</p>
<h2 style="font-size:56px;font-weight:700;line-height:1.1">{title}</h2>
<div style="width:1680px">{svg}</div>
<aside>{notes}</aside>
</section>
"""
for name, drawing, sid, label, title, notes in [
    ("arquitectura", architecture(), "arquitectura", "Cómo está armado", "De cuatro fuentes a una capa semántica",
     "De izquierda a derecha. Cuatro fuentes públicas se cargan tal como vienen: tres en Postgres y MeSH en GraphDB. "
     "La capa semántica tiene cuatro piezas: el entity linking, que crea las claves que faltan entre fuentes; la "
     "ontología, con los conceptos de negocio; los mapeos, que dicen qué columna es qué concepto; y Ontop, que traduce "
     "cada consulta a SQL. Los datos no se mueven. La usan la app, cualquier herramienta que hable SPARQL, y GraphDB, "
     "que puede unirla con MeSH y con Wikidata en una sola consulta."),
    ("ontologia", ontology(), "ontologia", "La ontología", "Los conceptos de negocio y cómo se relacionan",
     "Esto es lo que lee el LLM en lugar de las tablas. Un ensayo prueba fármacos, tiene un sponsor y estudia una "
     "condición, que es un descriptor de MeSH: así cáncer de pulmón incluye sus subtipos. Un fármaco actúa sobre "
     "targets y tiene reportes de eventos adversos. Arriba, las clases de fármaco: terapia dirigida no tiene ningún "
     "mapeo, Ontop la deduce de sus subclases. Abajo, el enlace: cada «ensayo prueba fármaco» guarda su evidencia "
     "(el texto del sponsor, lo que coincidió y la regla) con PROV-O, el estándar del W3C para procedencia. "
     "Cada dato apunta a su fuente y su licencia."),
]:
    (HERE / f"{name}.svg").write_text(drawing)
    (ROOT / "app" / f"{name}.svg").write_text(drawing)
    inline = drawing.replace('width="1664" height="680"', 'width="100%"').replace('width="1680" height="740"', 'width="100%"')
    (ROOT / "docs" / "slides" / "slides" / f"{sid}.html").write_text(
        SLIDE.format(id=sid, label=label, title=title, svg=inline, notes=notes))
print("Diagramas listos: docs/diagramas, app y docs/slides/slides")
