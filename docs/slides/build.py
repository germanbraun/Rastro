"""Arma index.html con las diapositivas de slides/, en el orden de deck.json."""
import json
from pathlib import Path

here = Path(__file__).parent
order = json.loads((here / "deck.json").read_text())["order"]
slides = "\n".join(
    f'<div class="slide">\n{(here / "slides" / f"{i}.html").read_text().strip()}\n</div>' for i in order
)

(here / "index.html").write_text(f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rastro Layer</title>
<!-- Generado por build.py. No editar a mano: editar slides/ y volver a correr build.py. -->
<style>
*{{margin:0;box-sizing:border-box}}
body{{background:#3A3F4A;display:flex;flex-direction:column;align-items:center;gap:24px;padding:24px 0}}
.slide{{width:calc(1920px * var(--s));height:calc(1080px * var(--s));overflow:hidden}}
section{{width:1920px;height:1080px;transform:scale(var(--s));transform-origin:0 0}}
aside{{display:none}}
</style>
<script>
function fit(){{document.documentElement.style.setProperty('--s', Math.min(1, (innerWidth - 48) / 1920))}}
addEventListener('resize', fit); fit();
</script></head><body>
{slides}
</body></html>
""")
