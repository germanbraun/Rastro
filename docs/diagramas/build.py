"""Draws Rastro's diagrams as SVG: the architecture and each domain's dictionary.

The slides (docs/slides) and the app use them. To change them, edit here and run:
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


# What is specific to each domain in the architecture diagram
ARCH = {
    "proveedores": {
        "fuente": ("Proveedores", ["(EE. UU.)", "", "USAspending", "NAICS", "GLEIF", "listas de control", "Wikidata"]),
        "enlaces": ["empresa → grupo (USAspending + GLEIF)", "empresa → LEI · → lista de control", "cada uno con su evidencia (PROV-O)"],
        "graphrag": ["el grafo elige los contratos;", "el LLM resume sus descripciones", "y cita cada uno"],
        "graphdb": False,
    },
    "energia": {
        "fuente": ("Petróleo y gas", ["(Argentina)", "", "Capítulo IV", "mapas (WFS)", "ENARGAS · IGN", "GLEIF", "estudios ambientales"]),
        "enlaces": ["empresa entre fuentes · socios", "operadora · punto → concesión", "con su evidencia (PROV-O)"],
        "graphrag": ["el grafo elige los estudios;", "el LLM resume solo sus textos", "y cita cada uno"],
        "graphdb": False,
    },
    "oncologia": {
        "fuente": ("Oncología", ["", "AACT", "ChEMBL", "openFDA", "MeSH"]),
        "enlaces": ["ensayo → fármaco · ensayo → MeSH", "motivo escrito → motivo clasificado", "cada uno con su evidencia (PROV-O)"],
        "graphrag": ["el grafo elige los ensayos;", "el LLM resume sus motivos", "y cita cada uno"],
        "graphdb": True,
    },
}


def architecture(domain):
    a = ARCH[domain]
    b = []
    for x, t in [(140, "FUENTES PÚBLICAS"), (440, "ALMACENAMIENTO"), (900, "CAPA SEMÁNTICA"), (1440, "QUIÉN LA USA")]:
        b.append(f'<text x="{x}" y="34" text-anchor="middle" font-size="22" font-weight="700" letter-spacing="2" fill="{BLUE}">{t}</text>')
    # The domain's sources
    b.append(box(20, 60, 240, 400 if a["graphdb"] else 530, a["fuente"][0], a["fuente"][1]))
    # Storage
    b.append(box(320, 60, 240, 400, "Postgres", ["un esquema", "por fuente", "", "+ los enlaces", "de Rastro,", "con su evidencia"]))
    b.append(arrow(262, 260, 318, 260))
    if a["graphdb"]:
        b.append(box(20, 490, 240, 100, "MeSH", ["vocabulario médico"]))
        b.append(box(320, 490, 240, 100, "Base de grafos", ["MeSH completo"]))
        b.append(arrow(262, 540, 318, 540))
    b.append(f'<text x="140" y="628" text-anchor="middle" font-size="20" fill="{GRAY}">un cargador por fuente</text>')
    # Semantic layer
    b.append(f'<rect x="620" y="50" width="560" height="590" rx="20" fill="{BLUE}"/>')
    b.append(box(650, 72, 500, 136, "Entity linking", a["enlaces"], fill="#4A84C4", color="#FFFFFF", stroke="#4A84C4", sub=20))
    b.append(box(650, 220, 240, 130, "Ontología", ["el diccionario", "de negocio"], fill="#4A84C4", color="#FFFFFF", stroke="#4A84C4"))
    b.append(box(910, 220, 240, 130, "Mapeos", ["columna → concepto", "(R2RML)"], fill="#4A84C4", color="#FFFFFF", stroke="#4A84C4"))
    b.append(box(650, 400, 500, 130, "Ontop", ["traduce cada consulta SPARQL", "a SQL sobre Postgres"], fill="#FFFFFF", color=INK, stroke="#FFFFFF"))
    b.append('<text x="900" y="600" text-anchor="middle" font-size="22" fill="#FFFFFF">Grafo virtual: los datos no se mueven</text>')
    b.append(arrow(562, 270, 618, 270))
    b.append(arrow(900, 352, 900, 396, color="#FFFFFF", head="white"))
    # Who uses it
    b.append(box(1250, 50, 380, 130, "App Rastro", ["el LLM lee el diccionario", "y escribe la consulta SPARQL"]))
    b.append(box(1250, 196, 380, 150, "GraphRAG anclado", a["graphrag"], fill="#E8F0FA", stroke=BLUE))
    b.append(box(1250, 362, 380, 76, "Otras herramientas", ["cualquier cliente SPARQL"], sub=20))
    b.append(arrow(1182, 115, 1248, 115))
    b.append(arrow(1182, 270, 1248, 270))
    b.append(arrow(1182, 400, 1248, 400))
    if a["graphdb"]:
        b.append(box(1250, 454, 380, 90, "Consulta federada", ["Rastro + MeSH + Wikidata"], sub=20))
        b.append(box(1250, 572, 380, 70, "Wikidata", [], fill=LIGHT, dash=True))
        b.append(arrow(1182, 490, 1248, 490))
        b.append(arrow(1440, 546, 1440, 568))
        b.append(f'<polyline points="562,560 600,560 600,662 1215,662 1215,515 1246,515" fill="none" stroke="{GRAY}" stroke-width="2.5" marker-end="url(#arrow)"/>')
    return svg(1664, 680, "\n".join(b))


def ontology():
    b = []
    # Drug classes
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
    # Center
    b.append(box(540, 300, 300, 160, "Ensayo", ["fase · estado · título", "motivo (clasificado)"], fill=LIGHT, stroke=INK))
    b.append(box(1010, 300, 280, 160, "Fármaco", ["nombre · ChEMBL ID", "aprobado"], fill=LIGHT, stroke=INK))
    b.append(box(1400, 300, 240, 160, "Target", ["nombre · gen"], fill=LIGHT, stroke=INK))
    b.append(box(40, 320, 260, 120, "Sponsor", ["nombre · es industria"], fill=LIGHT, stroke=INK))
    b.append(box(540, 560, 300, 130, "Condición", ["descriptor de MeSH"], fill=LIGHT, stroke=INK))
    b.append(box(1180, 580, 230, 110, "Reportes por año", ["año · reportes · serios"], size=24, sub=20))
    b.append(box(1430, 580, 230, 110, "Reacción reportada", ["reacción · reportes"], size=24, sub=20))
    b.append(box(930, 560, 230, 140, "Evidencia", ["de cada enlace y", "de cada motivo:", "texto y regla (PROV-O)"], size=24, sub=19, dash=True))
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
    # Provenance
    b.append(box(40, 560, 380, 130, "Fuente", ["cada dato apunta a su fuente", "y su licencia (proviene de)"], size=24, sub=20))
    return svg(1680, 740, "\n".join(b))


def ontology_suppliers():
    b = []
    # Supplier classes
    b.append(box(560, 10, 300, 70, "Con matriz extranjera", [], size=24))
    b.append(box(900, 10, 300, 70, "Coincide con una lista", [], size=24))
    b.append(box(720, 130, 320, 80, "Proveedor para revisar", ["deducida, sin mapeo"], dash=True, size=24, sub=19))
    b.append(arrow(710, 80, 830, 128, head="sub"))
    b.append(arrow(1050, 80, 930, 128, head="sub"))
    b.append(arrow(880, 212, 880, 298, head="sub"))
    b.append(f'<text x="1640" y="40" text-anchor="end" font-size="20" fill="{GRAY}">▷ es un tipo de (subclase)</text>')
    # Center
    b.append(box(40, 320, 240, 120, "Agencia", ["nombre"], fill=LIGHT, stroke=INK))
    b.append(box(380, 300, 300, 160, "Contrato", ["monto · fechas", "descripción"], fill=LIGHT, stroke=INK))
    b.append(box(760, 300, 240, 160, "Proveedor", ["nombre · UEI", "estado"], fill=LIGHT, stroke=INK))
    b.append(box(1120, 300, 280, 160, "Grupo", ["nombre · cotiza", "sede (Wikidata)"], fill=LIGHT, stroke=INK))
    b.append(box(380, 560, 300, 130, "Sector", ["código NAICS"], fill=LIGHT, stroke=INK))
    b.append(box(1120, 560, 280, 130, "Entidad legal", ["LEI · país"], fill=LIGHT, stroke=INK))
    b.append(box(760, 560, 240, 130, "Lista de control", ["entrada · alias"], fill=LIGHT, stroke=INK))
    b.append(arrow(378, 380, 284, 380, "agencia"))
    b.append(arrow(682, 380, 756, 380, "proveedor"))
    b.append(arrow(1002, 380, 1116, 380, "grupo"))
    b.append(arrow(530, 462, 530, 556, "sector", lx=580, ly=515))
    b.append(f'<path d="M 682 600 C 745 600 745 660 682 660" fill="none" stroke="{GRAY}" stroke-width="2.5" marker-end="url(#arrow)"/>')
    b.append(f'<text x="530" y="725" text-anchor="middle" font-size="22" fill="{BLUE}" font-style="italic">está dentro de <tspan fill="{GRAY}" font-style="normal" font-size="19">(sus subsectores)</tspan></text>')
    b.append(arrow(880, 462, 880, 556, "coincide con", lx=950, ly=515))
    b.append(arrow(1260, 462, 1260, 556, "entidad legal", lx=1340, ly=515))
    b.append(f'<path d="M 1402 600 C 1465 600 1465 660 1402 660" fill="none" stroke="{GRAY}" stroke-width="2.5" marker-end="url(#arrow)"/>')
    b.append(f'<text x="1260" y="725" text-anchor="middle" font-size="22" fill="{BLUE}" font-style="italic">matriz final</text>')
    # Evidence and source
    b.append(box(1450, 300, 210, 160, "Enlaces", ["evidencia de", "cada unión", "(PROV-O)"], size=24, sub=19, dash=True))
    b.append(box(40, 560, 260, 130, "Fuente", ["cada dato apunta", "a su fuente"], size=24, sub=20))
    return svg(1680, 740, "\n".join(b))


def ontology_energy():
    b = []
    # Production and venting classes
    b.append(box(40, 10, 200, 70, "Shale", [], size=24))
    b.append(box(280, 10, 200, 70, "Tight", [], size=24))
    b.append(box(110, 130, 300, 80, "No convencional", ["deducida, sin mapeo"], dash=True, size=24, sub=19))
    b.append(arrow(140, 80, 220, 128, head="sub"))
    b.append(arrow(380, 80, 300, 128, head="sub"))
    b.append(arrow(400, 212, 500, 298, head="sub"))
    b.append(box(1180, 10, 260, 70, "Visto por satélite", [], size=24))
    b.append(box(1460, 10, 200, 70, "Declarado", [], size=24))
    b.append(arrow(1310, 80, 1360, 298, head="sub"))
    b.append(arrow(1560, 80, 1440, 298, head="sub"))
    b.append(f'<text x="1660" y="728" text-anchor="end" font-size="20" fill="{GRAY}">▷ es un tipo de (subclase)</text>')
    # Center
    b.append(box(40, 300, 240, 160, "Pozo", ["identificador"], fill=LIGHT, stroke=INK))
    b.append(box(380, 300, 320, 160, "Producción de un pozo", ["petróleo · gas (2025)", "formación · cuenca"], fill=LIGHT, stroke=INK, size=24))
    b.append(box(800, 300, 280, 160, "Concesión", ["nombre · código", "gasoducto más cercano", "(ENARGAS)"], fill=LIGHT, stroke=INK))
    b.append(box(1260, 300, 280, 160, "Venteo", ["fecha · satélite", "localidad cercana y", "área protegida (IGN)"], fill=LIGHT, stroke=INK))
    b.append(box(380, 560, 320, 130, "Empresa", ["sus nombres en cada", "fuente · LEI (GLEIF)"], fill=LIGHT, stroke=INK))
    b.append(box(800, 560, 280, 130, "Participación", ["porcentaje"], fill=LIGHT, stroke=INK))
    b.append(arrow(378, 380, 284, 380, "pozo"))
    b.append(arrow(702, 380, 796, 380, "concesión"))
    b.append(arrow(1258, 380, 1084, 380, "en la concesión"))
    b.append(arrow(540, 462, 540, 556, "la declara", lx=610, ly=515))
    b.append(arrow(160, 462, 376, 600, "operadora hoy", lx=330, ly=548))
    b.append(arrow(820, 462, 704, 570, "operadora en el mapa", lx=690, ly=482))
    b.append(arrow(940, 556, 940, 466, "en la concesión", lx=1030, ly=515))
    b.append(arrow(798, 650, 704, 650, "socia", lx=750, ly=640))
    # Evidence and source
    b.append(box(1260, 560, 280, 130, "Enlaces", ["evidencia de cada unión,", "ubicación y distancia", "(PROV-O)"], size=24, sub=19, dash=True))
    b.append(box(40, 560, 240, 130, "Fuente", ["cada dato apunta", "a su fuente"], size=24, sub=20))
    return svg(1680, 740, "\n".join(b))


# The same images go to the app and, each inside a slide, to the deck
ROOT = HERE.parent.parent
SLIDE = """<section id="{id}" style="background:#F7F6F2;color:#14213D;font-family:'Times New Roman', Times, serif;padding:80px 120px;display:flex;flex-direction:column;gap:28px">
<p style="font-size:28px;font-weight:600;color:#2F6FB5;letter-spacing:2px;text-transform:uppercase">{label}</p>
<h2 style="font-size:56px;font-weight:700;line-height:1.1">{title}</h2>
<div style="width:1680px">{svg}</div>
<aside>{notes}</aside>
</section>
"""
for name, drawing, sid, label, title, notes in [
    ("arquitectura-proveedores", architecture("proveedores"), "arquitectura-proveedores", "Cómo está armado", "De cinco fuentes a una capa semántica",
     "De izquierda a derecha. Las fuentes públicas del dominio se cargan tal como vienen, en Postgres. La capa semántica tiene cuatro piezas: el entity linking, que crea las claves que faltan entre fuentes, con su evidencia; la ontología, con los conceptos de negocio; los mapeos, que dicen qué columna es qué concepto; y Ontop, que traduce cada consulta a SQL. Los datos no se mueven. La usa la app de dos formas: para preguntas, el LLM lee el diccionario y escribe la consulta; y como GraphRAG anclado en la capa: el grafo elige los registros con una consulta exacta y el LLM resume solo esos textos, citando cada uno. También la puede usar cualquier herramienta que hable SPARQL."),
    ("arquitectura-energia", architecture("energia"), "arquitectura-energia", "Cómo está armado", "De seis fuentes a una capa semántica",
     "De izquierda a derecha. Las fuentes públicas del dominio se cargan tal como vienen, en Postgres. La capa semántica tiene cuatro piezas: el entity linking, que crea las claves que faltan entre fuentes, con su evidencia; la ontología, con los conceptos de negocio; los mapeos, que dicen qué columna es qué concepto; y Ontop, que traduce cada consulta a SQL. Los datos no se mueven. La usa la app de dos formas: para preguntas, el LLM lee el diccionario y escribe la consulta; y como GraphRAG anclado en la capa: el grafo elige los registros con una consulta exacta y el LLM resume solo esos textos, citando cada uno. También la puede usar cualquier herramienta que hable SPARQL."),
    ("arquitectura-oncologia", architecture("oncologia"), "arquitectura-oncologia", "Cómo está armado", "De cuatro fuentes a una capa semántica",
     "De izquierda a derecha. Las fuentes públicas del dominio se cargan tal como vienen, en Postgres. La capa semántica tiene cuatro piezas: el entity linking, que crea las claves que faltan entre fuentes, con su evidencia; la ontología, con los conceptos de negocio; los mapeos, que dicen qué columna es qué concepto; y Ontop, que traduce cada consulta a SQL. Los datos no se mueven. La usa la app de dos formas: para preguntas, el LLM lee el diccionario y escribe la consulta; y como GraphRAG anclado en la capa: el grafo elige los registros con una consulta exacta y el LLM resume solo esos textos, citando cada uno. También la puede usar cualquier herramienta que hable SPARQL. En oncología, MeSH vive también en una base de grafos, que puede unir Rastro con MeSH y Wikidata en una sola consulta."),
    ("ontologia-proveedores", ontology_suppliers(), "ontologiaprov", "El diccionario de proveedores",
     "Contratos, empresas y grupos",
     "El diccionario del dominio de proveedores. Un contrato tiene una agencia, un sector y un proveedor; "
     "el proveedor pertenece a un grupo, y el grupo y el proveedor tienen su entidad legal en el registro "
     "global (LEI), con su país y su matriz final. Los sectores incluyen sus subsectores. Arriba, una regla "
     "de negocio: «proveedor para revisar» no tiene mapeo; Ontop la deduce de dos clases: matriz extranjera "
     "o coincidencia con una lista de control. Cada unión guarda su evidencia, con PROV-O."),
    ("ontologia-energia", ontology_energy(), "ontologiaenergia", "El diccionario de petróleo y gas",
     "Pozos, concesiones y socios",
     "El diccionario del dominio de petróleo y gas. La producción de cada pozo en 2025 la declara una empresa y "
     "pertenece a una concesión; cada concesión tiene socios, con su porcentaje, y una operadora en el mapa. Cada "
     "pozo tiene su operadora de hoy, según una regla escrita. Los venteos, vistos por satélite o declarados, caen "
     "en una concesión. Cada concesión sabe a qué distancia está el gasoducto de transporte más cercano (ENARGAS); "
     "cada venteo, su localidad más cercana y si cae en un área protegida (IGN); y las empresas que lo tienen, su LEI "
     "(GLEIF). Arriba, una regla de negocio: «no convencional» no tiene mapeo; Ontop la deduce de shale y tight. Cada "
     "unión guarda su evidencia, con PROV-O."),
    ("ontologia", ontology(), "ontologia", "El diccionario de oncología", "Ensayos, fármacos y enfermedades",
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
