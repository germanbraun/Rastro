---
name: decks
description: Keep the demo story consistent across the app, the demo script and the slide decks, build the HTML decks and publish them. Use it when you change a number or a message of the demo, a slide or the script.
---

# The demo, the script and the decks

> **Project skill, not part of the generic method** (`docs/method.md`): it keeps Rastro's own demo material (in Spanish) consistent.

The oil and gas story is **two acts, four moments, one sentence each**, and it is told in three minutes:

**Rastro Layer, a number you can trust:**

1. **Ask:** Rastro answers with evidence (YPF's oil by who reports, `{{energia.e01.ypf_sin}}`, versus split among the partners, `{{energia.e01.ypf_con}}`).
2. **The source changes:** oil arrives in barrels. Without Rastro, YPF's number silently jumps (`{{energia.cambio.antes}}` → `{{energia.cambio.sin}}`); with Rastro, a check warns and one line fixes it. The renamed column (broken queries) stays in «Por qué confiar».
3. **One correction:** you correct once and every answer that depends on it changes on its own: Total's gas in Aguada Pichana Este, `{{energia.demo.gas_total_sin}}` → `{{energia.demo.gas_total_con}}`. Do not mention the model yet.

**Rastro Lab, a prediction you can defend** (opened by one bridge sentence: everything Rastro knows, a model inherits too):

4. **Predict:** the same model with and without Rastro predicts the same; with Rastro the prediction is explained and flags the doubtful data. It comes back to moment 3: the same correction already reached the model's input and its explanation, without touching the model.

**The close:** «Lo que cuesta sin Rastro» (the three measured numbers of the app's start page: `{{energia.e01.dolares}}`, `{{energia.confiar.b_broken}}`, `{{energia.correccion.lugares}}`; hours saved are not measured, so never said), the limits and the pilot offer (`e-piloto`, shared with the executive deck).

In the app, each moment has its `acto`; the correction shows its Layer half (`parte: layer`) and the Lab moment its Lab half (`correccion: true`) as one sentence, both read from the measured correction test. In the business view each moment shows one number; the tables go behind «Ver detalles técnicos».

The same thing in three places, which must say the same:

| Where | File |
|---|---|
| App, Demo tab | `demo` and `demo_porque` in `app/dominios/energia.yaml` and, in English, in `app/dominios/energia.en.yaml` (the numbers come from the measured JSON files and the contrast cards' queries) |
| Script | `docs/demo-guion-energia.md` |
| Deck | `docs/slides/mazos/energia.json` (order) and `docs/slides/slides/*.html` (one slide per file) |
| Pocket card | `docs/slides/mazos/tarjeta.json`: the four sentences and the five questions that always come up, for whoever gives the demo (printed) |

The sales material repeats some of these numbers and must say the same too, in both languages (each page links its
twin): the executive decks (`mazos/ejecutivo.json`, `mazos/ejecutivo-en.json`), the one-pagers and the pilot offer
(`docs/one-pager*.md`, `docs/piloto*.md`) and the email draft (`docs/email-prospecto.md`). The README's «Selling
Rastro» lists them all. The documents type the numbers with their source file: update them when the numbers change.

## Steps

1. **Before new accuracy claims**, run `python layer/method.py publication <domain>`; missing independent evidence blocks those claims. The gate covers new claims; numbers already published stay as they are, labelled provisional until the gate passes. **Change the text in all three places at once;** in the app, edit the Spanish text and its English counterpart (`app/dominios/energia.en.yaml`, `app/dominios.en.yaml`, `app/textos/*.yaml`). The script and the decks are in Spanish, except the executive deck's English version (`mazos/ejecutivo-en.json`, slides `en-*.html`): a change to an executive slide goes to its `en-` twin too. Every number on a slide or in the script must be measured (in `layer/**/resultados.json`, `layer/energia/cambio/*.json` or what `lab/gas/modelo.py` prints).
2. **A slide** is a 1920×1080 `<section>` in `docs/slides/slides/<nombre>.html`, with the style of the others (background `#F7F6F2`, titles in `#14213D`, «Sin Rastro» (without Rastro) and «Con Rastro» (with Rastro) in two cards) and the speaker notes in `<aside>`. The story is everything before `anexo-energia` in `docs/slides/mazos/energia.json`. After it, the frequent questions (one slide per «Si preguntan» answer in the script); after `anexo-tecnico-energia`, the technical detail.
3. **Measured numbers are placeholders, never typed:** a slide writes `{{energia.e01.ypf_sin}}` (a contrast card), `{{energia.confiar.c_correct}}` («Por qué confiar») or `{{energia.demo.error_b}}` (the other demo numbers: claims, quality, missing data, the saved enrichment and Rastro Lab, from `story_numbers` in `app/contraste.py`). A case value with no placeholder goes in the `<aside>` with its query and date.
4. **Refresh the numbers:** `docker compose exec -T app python /app/contraste.py energia 2>/dev/null > docs/slides/numeros/energia.json` (about a minute: it trains the Lab models). If Lab's code changed, publish its run first (skill `rastro-lab`).
5. **Style:** `python3 docs/slides/estilo.py` (Times New Roman, six sizes, thin-bordered cards, drawings that fit, and the footer with each slide's number, so footers are never numbered by hand). It restyles every slide edited since its last run, not only yours: read its diff and keep only the slides you meant to change (the order file in `mazos/` too).
6. **Build:** `python3 docs/slides/build.py` fills the placeholders from `docs/slides/numeros/<domain>.json` (a missing number fails the build) and writes `docs/slides/<mazo>.html`, never edited by hand. Update slide numbers cited in the script.
7. **Check it in the browser:** open `docs/slides/energia.html` and look at the slides you changed. Measure that nothing goes past the footer: each slide's content ends before 920 px of height (the browser measurement is in `docs/decisions.md`, October 21). If something goes past, shorten the text: nothing gets smaller. A hidden preview pane can lay a slide out bottom-up (the header at the bottom): then measure the content's height plus the 128 px top padding, and check against a slide you did not change.
8. **Publish to the shared deck** (if the user uses it). `python3 docs/slides/build.py --export <mazo> <folder>` writes `<folder>/project/slides/` with the numbers, the page numbers and the deck's own notes filled in. A deck may give a shared slide its own speaker notes (`notes` in its `mazos/*.json`, used by the executive deck for a sales talk track) and set `"lang": "en"` for English number formats. Then copy `order`, `sections` and `faces` from `docs/slides/mazos/energia.json` to the deck's `project/deck.json` and those slides to `project/slides/`, and publish it to the same artifact: the artifact URL the user gave; ask if unknown (read it first if it changed since last time). `root` is the folder that **contains** `project/`, and paths start with `project/`: with `root` at `project/` the files end up one level up and the deck does not see them. A slide that left the order is deleted on publish (`null` in `files`): otherwise it shows up at the end. An inserted slide renumbers every slide after it: publish those too, with the new `order`. Before publishing, read the live files you will replace and compare them with your last export: if one differs, someone edited it in the deck, so merge instead of overwriting. The executive decks (`ejecutivo`, `ejecutivo-en`) have their own shared decks, also from `--export`: a number that changes in a slide they share must be published there too.
9. **Walk through the Demo tab** of the app (the Spanish scripts open it with `?inicio=demo&lang=es`: the app opens in
   English, on its start page) (after `docker compose restart app` if its code changed), in Spanish and in English, and the script from start to end, out loud: if it does not fit in three minutes, something has to go.
10. **Capture the backup again** when a demo number or screen changed: `python3 docs/respaldo/capturar.py` (needs Playwright and the app running) saves each moment of the Demo tab to `docs/respaldo/<lang>/` and a video to `data/raw/respaldo/`. Look at every screenshot before committing it; the script links them in its «Antes de empezar».
11. **Before each demo:** `python3 docs/respaldo/revisar.py` says whether the app, Rastro, the built deck, the backup and the chat's model are ready, or the command that fixes each. Without a key, the chat answers the recorded conversations (`RASTRO_PROVIDER=replay`, `RASTRO_RECORD=/layer/energia/chat/llamadas-gpt-5.5`): say they are recorded, and ask them as written in `layer/energia/chat/conversaciones.yaml`.

## Rules

- Only oil and gas in the story; suppliers and oncology are proof that it generalizes (technical view, appendix).
- No tool names in the business view («Rastro deduce» (Rastro deduces), not the engine's name) and no commercial knowledge-graph products.
- Nothing the measured number does not back: if a value barely moves, do not say it changes.
