---
name: decks
description: Keep the demo story consistent across the app, the demo script and the slide decks, build the HTML decks and publish them. Use it when you change a number or a message of the demo, a slide or the script.
---

# The demo, the script and the decks

> **Project skill, not part of the generic method** (`docs/method.md`): it keeps Rastro's own demo material (in Spanish) consistent.

The oil and gas story is **four moments, one sentence each**, and it is told in three minutes:

1. **Ask:** Rastro answers with evidence (YPF's share: 21.4 by who reports versus 12.6 split among the partners).
2. **The source changes:** without Rastro, broken queries you have to find; with Rastro, one line.
3. **Predict:** the same model with and without Rastro predicts the same; with Rastro the prediction is explained and flags the doubtful data.
4. **One correction:** you correct once and the answer, what goes into the model and its explanation all change on their own.

The same thing in three places, which must say the same:

| Where | File |
|---|---|
| App, Demo tab | `demo` and `demo_porque` in `app/dominios/energia.yaml` (the numbers come from the measured JSON files) |
| Script | `docs/demo-guion-energia.md` |
| Deck | `docs/slides/mazos/energia.json` (order) and `docs/slides/slides/*.html` (one slide per file) |

## Steps

1. **Before new accuracy claims**, run `python layer/method.py publication <domain>`; missing independent evidence blocks those claims. **Change the text in all three places at once.** Every number on a slide or in the script must be measured (in `layer/**/resultados.json`, `layer/energia/cambio/*.json` or what `lab/gas/modelo.py` prints).
2. **A slide** is a 1920×1080 `<section>` in `docs/slides/slides/<nombre>.html`, with the style of the others (background `#F7F6F2`, titles in `#14213D`, «Sin Rastro» (without Rastro) and «Con Rastro» (with Rastro) in two cards) and the speaker notes in `<aside>`. The first seven are the story; the rest goes after `anexo`.
3. **Style and HTML:** `python3 docs/slides/estilo.py` gives the oil and gas deck an even style (Times New Roman across the whole deck, as the user asked; a scale of six sizes, cards with a thin border, the footer with each slide's number, drawings at a height that fits); you can always run it, it is idempotent. Then `python3 docs/slides/build.py` (generates `docs/slides/<mazo>.html` with its fonts; not edited by hand).
4. **Check it in the browser:** open `docs/slides/energia.html` and look at the slides you changed. Measure that nothing goes past the footer: each slide's content ends before 920 px of height (the browser measurement is in `docs/decisions.md`, October 21). If something goes past, shorten the text: nothing gets smaller.
5. **Publish to the shared deck** (if the user uses it): copy `order`, `sections` and `faces` from `docs/slides/mazos/energia.json` to the deck's `project/deck.json` and the slides to `project/slides/`, and publish it to the same artifact (read it first if it changed since last time). `root` is the folder that **contains** `project/`, and paths start with `project/`: with `root` at `project/` the files end up one level up and the deck does not see them. A slide that left the order is deleted on publish (`null` in `files`): otherwise it shows up at the end.
6. **Walk through the Demo tab** of the app and the script from start to end, out loud: if it does not fit in three minutes, something has to go.

## Rules

- Only oil and gas in the story; suppliers and oncology are proof that it generalizes (technical view, appendix).
- No tool names in the business view («Rastro deduce» (Rastro deduces), not the engine's name) and no commercial knowledge-graph products.
- Nothing the measured number does not back: if a value barely moves, do not say it changes.
