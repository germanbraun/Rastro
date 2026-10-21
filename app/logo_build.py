"""Dibuja el logo de Rastro: una huella digital hecha de datos (las crestas son puntos, como un
rastro), con el centro naranja y el borde azul. Escribe app/logo.svg y app/logo-horizontal.svg.

    python3 app/logo_build.py
"""
from pathlib import Path

HERE = Path(__file__).parent
NAVY = "#14213D"
BLUE = "#2F6FB5"   # se lee sobre fondo claro y oscuro (la app usa tema oscuro)


def color(i, n):
    """Naranja en el centro y azul hacia afuera, sin pasar por gris."""
    oranges = ["#FF7A2F", "#FF8C42", "#FFA05A", "#FFB577"]
    if i < len(oranges):
        return oranges[i]
    t = (i - len(oranges)) / max(1, n - len(oranges) - 1)
    a, b = (120, 190, 245), (38, 120, 210)
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def ridges(cx, cy):
    """Crestas de una huella: lazos concéntricos abiertos abajo, cortados por el contorno de la yema
    del dedo. Los de adentro, enteros; los de afuera, punteados, como datos."""
    import math
    out, n = [], 11
    for i in range(n):
        rx, ry = 2.0 + i * 2.55, (2.0 + i * 2.55) * 1.35
        y0 = cy - 2 + i * 0.4
        gap = math.radians(max(18, 50 - i * 4))          # la abertura de abajo se cierra hacia afuera
        a1, a2 = math.pi / 2 + gap / 2, math.pi / 2 - gap / 2 + 2 * math.pi
        x1, y1 = cx + rx * math.cos(a1), y0 + ry * math.sin(a1)
        x2, y2 = cx + rx * math.cos(a2), y0 + ry * math.sin(a2)
        d = f"M{x1:.2f},{y1:.2f} A{rx:.2f},{ry:.2f} 0 1 1 {x2:.2f},{y2:.2f}"
        dash = "" if i < 4 else f' stroke-dasharray="{0.6 + i * 0.12:.1f} {0.9 + i * 0.06:.1f}"'
        out.append(f'<path d="{d}" fill="none" stroke="{color(i, n)}" stroke-width="1.45" stroke-linecap="round"{dash}/>')
    return "\n    ".join(out)


DEFS = """<defs>
    <clipPath id="yema"><ellipse cx="32" cy="32" rx="22" ry="28"/></clipPath>
    <radialGradient id="halo" cx="50%" cy="48%" r="50%">
      <stop offset="0%" stop-color="#FFB27A" stop-opacity="0.55"/>
      <stop offset="45%" stop-color="#8FC3F2" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#8FC3F2" stop-opacity="0"/>
    </radialGradient>
  </defs>"""


def mark(cx=32, cy=31):
    return f"""<ellipse cx="{cx}" cy="{cy + 2}" rx="31" ry="31" fill="url(#halo)"/>
  <g clip-path="url(#yema)">
    {ridges(cx, cy)}
  </g>
  <circle cx="{cx}" cy="{cy - 2}" r="1.3" fill="#FF7A2F"/>"""


icon = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" aria-label="Rastro">
  <!-- Una huella digital hecha de datos: el rastro de cada dato -->
  {DEFS}
  {mark()}
</svg>
"""
horizontal = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 270 64" width="270" height="64" aria-label="Rastro">
  {DEFS}
  {mark()}
  <text x="76" y="45" font-family="Montserrat, 'Helvetica Neue', Arial, sans-serif" font-size="38" font-weight="800"
        letter-spacing="1" fill="{BLUE}">RASTRO</text>
</svg>
"""
(HERE / "logo.svg").write_text(icon)
(HERE / "logo-horizontal.svg").write_text(horizontal)
print("logo.svg y logo-horizontal.svg listos")
