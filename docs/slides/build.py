"""Builds one HTML per deck (proveedores.html, energia.html, oncologia.html) with the slides in
slides/, in the order of each mazos/<nombre>.json. The three share the generic slides."""
import json
import re
from pathlib import Path

here = Path(__file__).parent
# The numbers the app reads live, as the app shows them: «{{energia.e01.ypf_sin}}» is the value ypf_sin of the
# contrast card of question e01 in numeros/energia.json (written by app/contraste.py)
NUMBERS = {path.stem: json.loads(path.read_text()) for path in (here / "numeros").glob("*.json")}


def number(match):
    domain, card, name = match.group(1).split(".")
    return NUMBERS[domain][card][name]   # a missing number fails the build: never a stale typed copy


def slide(name):
    return re.sub(r"\{\{([\w.]+)\}\}", number, (here / "slides" / f"{name}.html").read_text().strip())


for deck in sorted((here / "mazos").glob("*.json")):
    meta = json.loads(deck.read_text())
    slides = "\n".join(f'<div class="slide">\n{slide(i)}\n</div>' for i in meta["order"])
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
