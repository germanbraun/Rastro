"""Dibuja como grafo la instancia de las diapositivas «Así se ve un dato del grafo» (instancia-*.html):
burbujas para las entidades, burbujas naranjas para las clases, rectángulos para los datos simples y
flechas con el nombre de negocio de cada propiedad. Lee la tabla de la diapositiva y los nombres de
las entidades enlazadas en el Ontop de cada dominio.

    python3 docs/slides/grafo_instancia.py
"""
import csv
import sys
import html
import io
import re
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "app"))
import grafo  # noqa: E402  (el mismo dibujo que la app)
DOMAINS = {"energia": ("https://w3id.org/rastro/energia#", 8082),
           "proveedores": ("https://w3id.org/rastro/proveedores#", 8081),
           "oncologia": ("https://w3id.org/rastro/oncologia#", 8080)}


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


def nodes_of(rows, ns, port):
    """Las filas de la tabla (término, en el diccionario, valor) como nodos del dibujo."""
    out = []
    for term, meaning, value in rows:
        prop = re.sub(r"\s*\(.*", "", meaning or term)
        if term == "a":
            out.append(("clase", re.sub(r"^\S+\s*", "", value).strip("()") or value, value.split(" ")[0], prop))
        elif value.startswith("rastro:"):
            iri = "https://w3id.org/rastro/" + value[len("rastro:"):]
            out.append(("entidad", name_of(iri, ns, port) or value.split("/")[-1], value, prop))
        else:
            out.append(("dato", value, "", prop))
    return out


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
           f'{grafo.svg(center, nodes_of(rows, ns, port), height=640 + 55 * max(0, len(rows) - 8))}\n</div>\n{LEGEND}\n')
    path.write_text(text.replace(block.group(0), new))
    print(path.name, len(rows), "propiedades")
