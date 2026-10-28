---
name: decks
description: Keep the demo story consistent across the app, the demo script and the slide decks, build the HTML decks and publish them. Use it when you change a number or a message of the demo, a slide or the script.
---

# The demo, the script and the decks

> **Project skill, not part of the generic method** (`docs/method.md`): it keeps Rastro's own demo material (in Spanish) consistent.

The oil and gas story is **four moments, one sentence each**, and it is told in three minutes:

1. **Ask:** Rastro answers with evidence (YPF's oil by who reports, `{{energia.e01.ypf_sin}}`, versus split among the partners, `{{energia.e01.ypf_con}}`).
2. **The source changes:** without Rastro, broken queries you have to find; with Rastro, one line.
3. **Predict:** the same model with and without Rastro predicts the same; with Rastro the prediction is explained and flags the doubtful data.
4. **One correction:** you correct once and the answer, what goes into the model and its explanation all change on their own.

The same thing in three places, which must say the same:

| Where | File |
|---|---|
| App, Demo tab | `demo` and `demo_porque` in `app/dominios/energia.yaml` and, in English, in `app/dominios/energia.en.yaml` (the numbers come from the measured JSON files and the contrast cards' queries) |
| Script | `docs/demo-guion-energia.md` |
| Deck | `docs/slides/mazos/energia.json` (order) and `docs/slides/slides/*.html` (one slide per file) |

## Steps

1. **Before new accuracy claims**, run `python layer/method.py publication <domain>`; missing independent evidence blocks those claims. The gate covers new claims; numbers already published stay as they are, labelled provisional until the gate passes. **Change the text in all three places at once;** in the app, edit the Spanish text and its English counterpart (`app/dominios/energia.en.yaml`, `app/dominios.en.yaml`, `app/textos/*.yaml`). The script and the decks are in Spanish only. Every number on a slide or in the script must be measured (in `layer/**/resultados.json`, `layer/energia/cambio/*.json` or what `lab/gas/modelo.py` prints).
2. **A slide** is a 1920×1080 `<section>` in `docs/slides/slides/<nombre>.html`, with the style of the others (background `#F7F6F2`, titles in `#14213D`, «Sin Rastro» (without Rastro) and «Con Rastro» (with Rastro) in two cards) and the speaker notes in `<aside>`. The story is everything before `anexo-energia` in `docs/slides/mazos/energia.json`; the rest goes after it.
3. **Measured numbers are placeholders, never typed:** a slide writes `{{energia.e01.ypf_sin}}` (a contrast card), `{{energia.confiar.c_correct}}` («Por qué confiar») or `{{energia.demo.error_b}}` (the other demo numbers: claims, quality, missing data, the saved enrichment and Rastro Lab, from `story_numbers` in `app/contraste.py`). A case value with no placeholder goes in the `<aside>` with its query and date.
4. **Refresh the numbers:** `docker compose exec -T app python /app/contraste.py energia 2>/dev/null > docs/slides/numeros/energia.json` (about a minute: it trains the Lab models). If Lab's code changed, publish its run first (skill `rastro-lab`).
5. **Style:** `python3 docs/slides/estilo.py` (Times New Roman, six sizes, thin-bordered cards, drawings that fit, and the footer with each slide's number, so footers are never numbered by hand). It restyles every slide edited since its last run, not only yours: read its diff and keep only the slides you meant to change (the order file in `mazos/` too).
6. **Build:** `python3 docs/slides/build.py` fills the placeholders from `docs/slides/numeros/<domain>.json` (a missing number fails the build) and writes `docs/slides/<mazo>.html`, never edited by hand. Update slide numbers cited in the script.
7. **Check it in the browser:** open `docs/slides/energia.html` and look at the slides you changed. Measure that nothing goes past the footer: each slide's content ends before 920 px of height (the browser measurement is in `docs/decisions.md`, October 21). If something goes past, shorten the text: nothing gets smaller.
8. **Publish to the shared deck** (if the user uses it): copy `order`, `sections` and `faces` from `docs/slides/mazos/energia.json` to the deck's `project/deck.json` and the slides to `project/slides/`, and publish it to the same artifact: the artifact URL the user gave; ask if unknown (read it first if it changed since last time). `root` is the folder that **contains** `project/`, and paths start with `project/`: with `root` at `project/` the files end up one level up and the deck does not see them. A slide that left the order is deleted on publish (`null` in `files`): otherwise it shows up at the end.
9. **Walk through the Demo tab** of the app (after `docker compose restart app` if its code changed), in Spanish and in English, and the script from start to end, out loud: if it does not fit in three minutes, something has to go.

## Rules

- Only oil and gas in the story; suppliers and oncology are proof that it generalizes (technical view, appendix).
- No tool names in the business view («Rastro deduce» (Rastro deduces), not the engine's name) and no commercial knowledge-graph products.
- Nothing the measured number does not back: if a value barely moves, do not say it changes.
