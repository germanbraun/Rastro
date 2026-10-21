"""Le da al mazo de petróleo y gas un estilo parejo, siempre igual, para no retocar diapositiva por diapositiva:

- Tipografía: Times New Roman en todo el mazo (la del sistema: no se descarga nada).
- Una escala de seis tamaños: 24, 28, 32, 40, 56 (títulos) y 72 (números grandes); la portada conserva los suyos.
- Tarjetas blancas con un borde fino y el mismo radio.
- Un pie igual en cada diapositiva de contenido: el nombre del mazo a la izquierda y el número a la derecha.

Las diapositivas que el mazo comparte con los otros (Qué es Rastro, Beneficios, el separador del anexo) se copian con el sufijo -energia,
para que su pie y su número sean de este mazo. Los dibujos (<svg>) no se tocan. Se puede correr las veces que haga
falta: da lo mismo. Después: python3 docs/slides/build.py

    python3 docs/slides/estilo.py
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).parent
MAZO = AQUI / "mazos" / "energia.json"
PIE_TEXTO = "Rastro · Petróleo y gas en Argentina"
SIN_PIE = {"cover-energia", "anexo-energia"}    # portada y separador del anexo
COMPARTIDAS = {"quees", "beneficios", "anexo"}  # se copian para este mazo
ALTO_DIBUJO = {"arquitectura-energia": 600, "ontologiaenergia": 600, "instancia-energia": 440}   # px, para que entren sobre el pie
TEXTO = "'Times New Roman', Times, serif"
TITULOS = TEXTO
FACES = {}                                       # Times New Roman es del sistema
PIE = re.compile(r'\n?<div style="position:absolute;left:128px;bottom:64px;width:1664px;display:flex;justify-content:space-between[^"]*">'
                 r".*?</div>", re.S)


def tamano(n):
    """La escala del mazo."""
    if n <= 24:
        return 24
    if n <= 30:
        return 28
    if n <= 36:
        return 32
    if n <= 48:
        return 40
    if n <= 60:
        return 56
    if n <= 80:
        return 72
    return n                                     # la portada


def fuera_de_dibujos(html, cambio):
    """Aplica cambio() al texto de la diapositiva, salvo dentro de los <svg>."""
    partes = re.split(r"(<svg.*?</svg>)", html, flags=re.S)
    return "".join(p if p.startswith("<svg") else cambio(p) for p in partes)


def estilar(html, slide_id, numero, oscura):
    def cambio(t):
        # títulos en la tipografía de títulos, con su tamaño
        def titulo(m):
            estilo = re.sub(r"font-family:[^;\"]+;?", "", m.group(2))
            estilo = re.sub(r"font-weight:\d+", "font-weight:600", estilo)
            estilo = re.sub(r"font-size:\d+px", "font-size:56px", estilo) if m.group(1) == "h2" else estilo
            return f'<{m.group(1)} style="font-family:{TITULOS};{estilo.lstrip(";")}"'
        t = re.sub(r'<(h1|h2) style="([^"]*)"', titulo, t)
        # la escala, en lo que no es título
        t = re.sub(r"(<(?!h2)[a-z]+[^>]*?)font-size:(\d+)px", lambda m: f"{m.group(1)}font-size:{tamano(int(m.group(2)))}px", t)
        # tarjetas blancas con borde fino
        t = re.sub(r"background:#FFFFFF;(?:border:1px solid #[0-9A-Fa-f]{6};)?border-radius:\d+px",
                   "background:#FFFFFF;border:1px solid #E1E4E8;border-radius:16px", t)
        return t

    html = fuera_de_dibujos(html, cambio)
    # los dibujos: la tipografía del mazo y, en los que ocupan todo el ancho, una altura que entra
    html = re.sub(r'(<svg[^>]*?)font-family="[^"]*"', rf'\1font-family="{TEXTO.replace(chr(39), "")}"', html)
    if slide_id in ALTO_DIBUJO:
        html = re.sub(r'(<svg[^>]*?width="100%")(?: height="\d+")?', rf'\1 height="{ALTO_DIBUJO[slide_id]}"', html, count=1)
    # el texto de la diapositiva en la tipografía de texto
    html = re.sub(r'(<section[^>]*style="[^"]*?)font-family:[^;"]+', rf"\1font-family:{TEXTO}", html, count=1)
    html = PIE.sub("", html)
    if slide_id in SIN_PIE:
        return html
    # margen de abajo para el pie, y el pie
    html = re.sub(r'(<section[^>]*style="[^"]*?)padding:[0-9px ]+(;|")', r"\1padding:128px 128px 160px\2", html, count=1)
    color = "#9AA5B8" if oscura else "#7A8699"
    pie = (f'\n<div style="position:absolute;left:128px;bottom:64px;width:1664px;display:flex;justify-content:space-between;'
           f'font-size:24px;color:{color}"><p>{PIE_TEXTO}</p><p>{numero}</p></div>')
    if "<aside>" in html:
        return html.replace("<aside>", pie.lstrip("\n") + "\n<aside>", 1)
    return html.replace("</section>", pie.lstrip("\n") + "\n</section>", 1)


def main():
    mazo = json.loads(MAZO.read_text())
    orden = []
    for s in mazo["order"]:
        if s in COMPARTIDAS:
            nuevo = f"{s}-energia"
            fuente = (AQUI / "slides" / f"{s}.html").read_text()
            (AQUI / "slides" / f"{nuevo}.html").write_text(fuente.replace(f'<section id="{s}"', f'<section id="{nuevo}"', 1))
            s = nuevo
        orden.append(s)
    mazo["order"] = orden
    mazo["faces"] = FACES
    for numero, s in enumerate(orden, 1):
        f = AQUI / "slides" / f"{s}.html"
        html = f.read_text()
        oscura = re.search(r'<section[^>]*style="background:#(14213D|2F6FB5)', html) is not None
        f.write_text(estilar(html, s, numero, oscura))
    MAZO.write_text(json.dumps(mazo, ensure_ascii=False))
    print(f"{len(orden)} diapositivas con el estilo del mazo")


if __name__ == "__main__":
    main()
