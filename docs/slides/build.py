"""Builds one HTML per deck (proveedores.html, energia.html, oncologia.html, ejecutivo.html, …) with the slides in
slides/, in the order of each mazos/<nombre>.json. Decks share slides; a deck may replace a shared slide's speaker
notes (`notes`: slide id → text) and set `"lang": "en"` for English number formats.

    python3 docs/slides/build.py                       # every deck, as HTML
    python3 docs/slides/build.py --export <deck> <dir> # one deck as the shared deck's files (<dir>/project/…)
"""
import html
import json
import re
import sys
from pathlib import Path

here = Path(__file__).parent
# The numbers the app reads live, as the app shows them: «{{energia.e01.ypf_sin}}» is the value ypf_sin of the
# contrast card of question e01 in numeros/energia.json (written by app/contraste.py)
NUMBERS = {path.stem: json.loads(path.read_text()) for path in (here / "numeros").glob("*.json")}


def number(match, lang="es"):
    domain, card, name = match.group(1).split(".")
    value = NUMBERS[domain][card][name]   # a missing number fails the build: never a stale typed copy
    # The numbers are written the Spanish way («3.600», «21,4», «100 %»); English swaps the separators
    return value.translate(str.maketrans(",.", ".,")).replace(" %", "%") if lang == "en" else value


# A slide's footer carries its page number; a slide shared by several decks gets each deck's own number
FOOTER = re.compile(r'(<div style="position:absolute;left:128px;bottom:64px;[^"]*">.*?<p>)\d+(</p></div>)', re.S)


def slide(name, page=None, meta=None):
    meta = meta or {}
    text = re.sub(r"\{\{([\w.]+)\}\}", lambda m: number(m, meta.get("lang", "es")),
                  (here / "slides" / f"{name}.html").read_text().strip())
    if name in meta.get("notes", {}):   # this deck's own speaker notes for a shared slide
        notes = re.sub(r"\{\{([\w.]+)\}\}", lambda m: number(m, meta.get("lang", "es")), meta["notes"][name])
        text = re.sub(r"<aside>.*?</aside>", lambda _: f"<aside>{html.escape(notes, quote=False)}</aside>", text,
                      flags=re.S)
    return FOOTER.sub(lambda m: f"{m.group(1)}{page}{m.group(2)}", text) if page else text


def export(name, folder):
    """Write one deck as the shared deck's files: project/slides/<id>.html, numbers filled, and its order."""
    meta = json.loads((here / "mazos" / f"{name}.json").read_text())
    (folder / "project/slides").mkdir(parents=True, exist_ok=True)
    for page, slide_id in enumerate(meta["order"], 1):
        (folder / "project/slides" / f"{slide_id}.html").write_text(slide(slide_id, page, meta) + "\n")
    print(f"{len(meta['order'])} slides in {folder}/project/slides; order: {meta['order']}")


if sys.argv[1:2] == ["--export"]:
    export(sys.argv[2], Path(sys.argv[3]))
    sys.exit()

for deck in sorted((here / "mazos").glob("*.json")):
    meta = json.loads(deck.read_text())
    slides = "\n".join(f'<div class="slide">\n{slide(i, n, meta)}\n</div>' for n, i in enumerate(meta["order"], 1))
    (here / f"{deck.stem}.html").write_text(f"""<!doctype html>
<html lang="{meta.get('lang', 'es')}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
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
