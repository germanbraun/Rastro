# Plan: a generic app, with each domain's code in its own place

**Done (2026-10-28):** steps 1 to 4, each in its own commit. In step 3 the user chose to keep oncology's screen as it
is, as its own extension (`has_own_screen`), instead of rebuilding it on the template. The record is in
`docs/decisions.md`.

## Context

The domain screen (`app/dominio/`) already draws suppliers, oil and gas and affiliations from their YAML, but the app
is not independent of its domains:

- `app/app.py` (913 lines) still holds oncology's own screen, about 520 lines: drug evidence, its evaluation,
  consistency test, change scenarios and FAQ.
- Rastro Lab is oil and gas only, and the generic screen calls it directly (`screen.py:145-162`,
  `answers.py:254-316`, `common.warm_up` loads it for every domain). `lab.py` hard-codes `energia` in 5 places.
- Oil and gas units are written into generic code (`m3`, «M m³» in `answers.py`, `trust_view.py`, `layer_story.py`,
  `idioma.millions`), and the change-test warnings are recognized with Spanish regexes for three domains
  (`common.CHECKS`).
- `contraste.story_numbers` has oil and gas SPARQL and company keys for the slides.
- `layer/answer.py` falls back to oncology in 12 functions; `ontology/calidad.py` falls back to oil and gas.

**Goal:** the shell and the template know no domain. Everything specific to a domain is either configuration (its YAML)
or a domain **extension class** it declares, so adding a domain means adding YAML, and optionally one class, never
editing the generic code. Every step keeps each screen the same, and nothing is re-measured: no number changes.

## Design

**One small interface, `app/dominio/extension.py`:** a base class `Extension` whose methods have empty defaults, so a
domain implements only what it needs. The YAML declares it: `extension: gas_lab` → `app/extensions/gas_lab.py` with a
class that subclasses `Extension`. The template calls `ext.<method>(...)` and never imports a domain module.

| Method | Replaces |
|---|---|
| `tabs()` / `show_tab(name, tech)` | the hard-coded «Rastro Lab» tab in `screen.py` |
| `placeholders()` → `{"registro_ejemplo": …, "corrida_publicada": …}` | `{pozo_ejemplo}`, `{corrida_publicada}` and `lab.modelo.pozo_ejemplo` in `answers.py` |
| `show_step(flag, tech)` | `entrada_pozo`, `calculo_pozo`, `evidencia_pozo` in `show_integration_example` |
| `show_demo_step(step, tech)` | `tipo: lab` in `show_demo` |
| `warm_up()` | `import lab; lab.datos()` in `common.warm_up` |
| `story_numbers()` | Lab numbers in `contraste.story_numbers` |
| `answer_columns(columns, rows)`, `evaluation()`, `faq_values()`, scenario renderers | oncology's extras (step 3) |

A debugger sees one place per domain: `app/extensions/<name>.py`, and the template's call sites `ext.show_tab(...)`.

## Steps (each ends working, checked and committed on its own)

### 1. Rastro Lab becomes the oil and gas extension

- New `app/dominio/extension.py` (base class and `load(cfg)`), and `app/extensions/gas_lab.py` with `GasLab(Extension)`.
- Move `app/lab.py`, `lab_walkthrough.py`, `lab_alternative.py` into `app/extensions/gas_lab/` unchanged at first; the
  class wraps their functions. Their hard-coded `"energia"` and `/app/dominios/energia.yaml` come from the config the
  class receives.
- `screen.py`, `answers.py`, `common.warm_up`, `contraste.main` call the extension. Placeholders become
  `{registro_ejemplo}` (with `{pozo_ejemplo}` kept as an alias until the YAML is updated in the same commit).
- `energia.yaml`: `lab: gas` becomes `extension: gas_lab`.

### 2. Units, warnings and slide numbers as configuration; no default domain

- **Units:** each domain declares `unidades:` (`m3: {escala: 1e6, sufijo: "M m³"}`, …). `idioma.millions` becomes
  `idioma.scaled(value, unit)`; `answers.as_table`, `show_why`, `trust_view.show_correction` and `layer_story` read the
  unit, not `m3`. The correction view's `lab_*` columns move to the extension.
- **Change warnings:** each domain's `probar.py` writes its check as `{clave, valores}` next to the Spanish text; the
  app formats it with `dominio.trust.<clave>` in either language. `common.CHECKS` and its regexes go. Saved results
  keep working: an old result without `clave` is shown as recorded.
- **Slide numbers:** `story_numbers` keeps its generic loops (claims, «sin dato», quality, outside data); the oil and
  gas queries move to `energia.yaml` (`numeros_demo: [{clave, sparql, decimales}]`), the Lab ones to
  `GasLab.story_numbers()`. The JSON for the slides must come out identical.
- **No default domain:** `layer/answer.py` and `ontology/calidad.py` require it; oncology's scripts in `layer/eval/`,
  `layer/consistencia/`, `layer/composicion/`, `layer/cambio/` pass `"oncologia"`.
- Rename `layer_story.py` to a generic «recorrido» with its column names from the YAML.

### 3. Oncology on the same template; `app.py` becomes a shell

- `app/dominios/oncologia.yaml` gets what the others have: `resumen`, `preguntas` (from `layer/eval/questions.yaml`
  and `app/preguntas-simples.yaml`), `porque` (today's `DRUG_WHY`), `evidencia`, `texto`, `tarjetas`, `cambios`,
  `faq`, `diagrama`, plus its English overlay.
- **No re-measuring:** oncology keeps its measured files (`layer/eval/results.json`, `layer/consistencia/`).
  `app/extensions/oncologia.py` reads them and hands the template the same shape `layer/evaluar.py` writes, so its
  cards and evaluation show the same numbers (20/20, 18/20…).
- **Made generic, because any domain can use them:** the evaluation shows whichever approaches the file has (oncology
  has A, «LLM alone»); failure reasons and the link method come from optional files named in the YAML; FAQ texts can
  use `{values}` an extension provides; the trust example expander becomes an optional key.
- **Kept in the oncology extension:** the «recognized in N trials» column, the «definición» and Wikidata change
  scenarios, and the 6th step of the text question (cq11 facts).
- `app/app.py` keeps only the shell: language, logo, view switch, domain selector, `dominio.render`. Oncology's ~180
  `app.*` texts move to its YAML or are deleted when unused; `app/faq.yaml` and `preguntas-simples.yaml` move into
  its config.
- `layer/dominios.yaml`: oncology's `app_mode: legacy` goes, so `check_domain.py` and `layer/experiment.py` check it
  like the others.

### 4. A guard so it stays generic

- A test that fails if `app/app.py`, `app/dominio/`, `app/idioma.py`, `app/contraste.py` or `layer/answer.py` names
  a domain (`energia`, `oncologia`, `proveedores`, `afiliaciones`), a domain prefix or a source.
- Update `docs/code-structure.md`, ONBOARDING, the `show-in-app` skill (extensions, units), `docs/decisions.md`, and
  `docs/demo-guion-oncologia.md` where the screen changes.

## Verification

- **Before any change**, capture every visible text of every domain in both languages with `app/text_snapshot.py`
  (it already renders oncology's old screen too). After steps 1 and 2, the snapshots must be identical for all four
  domains. After step 3, oncology's will differ in layout; every number the demo script shows must be the same, and
  the differences are listed for you.
- `docker compose run --rm --no-deps -T app python /app/check_domain.py <domain>` for all four domains, both views.
- `pytest` and `ruff` (CI runs both); the slide numbers JSON identical (`contraste.py energia`); the Lab published run
  check still passes (`modelo.py` is not edited, so its version does not change).
- A look in the browser at each domain, in both languages.

## Size and risk

Steps 1, 2 and 4 are moderate and low risk: the snapshots prove nothing visible changed. Step 3 is the largest,
roughly a day of work: oncology's screen has features nobody else uses, and its demo script must still work
end to end. Each step is its own commit, so we can stop after any of them.
