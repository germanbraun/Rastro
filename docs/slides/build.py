"""Arma un HTML por mazo (proveedores.html, energia.html, oncologia.html) con las diapositivas de
slides/, en el orden de cada mazos/<nombre>.json. Los tres comparten las diapositivas genéricas."""
import json
from pathlib import Path

here = Path(__file__).parent
for deck in sorted((here / "mazos").glob("*.json")):
    meta = json.loads(deck.read_text())
    slides = "\n".join(
        f'<div class="slide">\n{(here / "slides" / f"{i}.html").read_text().strip()}\n</div>' for i in meta["order"]
    )
    (here / f"{deck.stem}.html").write_text(f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{meta["title"]}</title>
{"".join(f'<link rel="stylesheet" href="{f["href"]}">' for f in meta.get("faces", {}).values() if f.get("href"))}
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
print("Mazos listos:", ", ".join(f"{d.stem}.html" for d in sorted((here / "mazos").glob("*.json"))))
