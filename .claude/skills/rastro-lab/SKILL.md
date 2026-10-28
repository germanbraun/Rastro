---
name: rastro-lab
description: Train, measure and explain the Rastro Lab gas model (new Vaca Muerta shale gas wells) with features from the raw tables and from Rastro, validate it and build the blind test of the explanations. Use it when you touch lab/, app/lab.py, energia:WellStart or energia:Fracturing, or when you publish a Lab number.
---

# Rastro Lab

> **Domain skill, not part of the generic method** (`docs/method.md`): it covers the oil and gas gas model. A generic "explain predictions with evidence" skill can be extracted from it when a second domain needs one.

Rastro Lab shows what semantic technology adds to machine learning. **What is measured is the explanation, not the accuracy.** The study is in `docs/lab-gas-vaca-muerta.md`.

## What it is

- **What is predicted:** the gas of months 2 to 7 of a new Vaca Muerta shale gas well, in millions of m³ (`energia:gasMonths2to7`; the first month is usually partial).
- **The same model, twice** (`lab/gas/modelo.py`): a linear regression (ridge, in numpy). A takes the features with SQL from the raw tables; B, from Rastro (SPARQL). The same feature ideas: operator, concession, share, fracturing (lateral length, stages, sand, water, pressure) and the trajectory's vertical depth.
- **Train and test by date:** it trains on the wells that started before 2025 and tests on those from 2025.
- **The explanation** is exact: the prediction is the average well plus the contribution of each feature. With Rastro it is grouped into two factors (the concession with its operator and partners, and how it was fractured), each with why it adds or subtracts and its facts with rule, evidence and source.

## Rules

1. **Do not use the future.** The operator and the well type are those of the first month (`energia:WellStart`), not today's. The fracturing is what was reported up to the month it started. The load date of each value (`energia:loadedOn`) is stored and flagged if it arrived later.
2. **A must be what a reasonable analyst would do with SQL,** not something badly built on purpose. If a value is computed by both paths (the gas), it must match: the script checks it.
3. **The explanation cannot contradict the model.** If two features go together (the operator and the partners are fixed within a concession; lateral length and stages grow together), say so and show them together; never a general rule («más rama, más gas», more lateral, more gas) that the model does not follow.
4. **The explanation does not show what is predicted** (the well's real gas does not go into any evidence).
5. **What is loaded only for Lab does not change Layer** (`data/lab-gas/`, schemas `capitulo4_anterior`, `fractura` and `trayectoria`). After loading, the `evaluate` skill with `rerun` must give the same results.
6. **Honest numbers:** accuracy depends on the date split. Report the error and the R² toward the future and say it is the best case if it is.

## Commands (on the machine, with `requirements-dev.txt` and the energy Ontop on :8082)

```bash
python3 lab/gas/modelo.py                 # A and B error, doubtful data, what it learned, one well explained
python3 lab/gas/modelo.py <idpozo>        # another well's explanation
python3 lab/gas/modelo.py --12-meses      # validation with 12-month gas
python3 lab/gas/modelo.py --como-trabajo-publicado # validation with the design of a published work on the same sources
python3 lab/gas/a_ciegas.py               # builds docs/lab-explicaciones-a-ciegas.md (key in lab/gas/a-ciegas-clave.json)
python3 lab/gas/modelo.py --publicar      # saves the run, its input and its predictions in Rastro (schema lab_gas)
python3 lab/gas/modelo.py --comparar      # what changed between the last two runs, well by well
```

The app shows it in the **Rastro Lab** tab and in moment 3 of the demo, through the oil and gas extension
(`app/extensions/energia/`: the class `OilAndGas`, and `lab.py` for the tab).

- **After editing `lab/gas/modelo.py`:** run `python3 lab/gas/modelo.py --publicar`, then `docker compose restart app`. The run's version is the fingerprint of `modelo.py`, so any edit, even a comment, makes the app report the published run as different until it is published again.
- **After editing `app/extensions/energia/`:** `docker compose restart app`.
- **Explanation sentences** are not in the code: they are in `app/textos/modelo.yaml`, each key with `es` and `en` (`modelo.texto(key, lang)` reads them). Edit both languages, and the Lab texts of the app in `app/textos/lab.yaml` and `app/dominios/energia.en.yaml` (`ejemplo_lab`) next to their Spanish ones. Check the Lab tab in Spanish and in English.

## The predictions, in Rastro

Every published run is stored in Rastro: `energia:ModelRun` (version = fingerprint of `lab/gas/modelo.py`, date, split, error, `energia:current`), `energia:Prediction` (value, range, `prov:wasGeneratedBy` the run, `prov:used` the well start, its fracturing and the operator's share) and `energia:Contribution` (the contribution of each factor). The source records are there too, one by one: `energia:FractureReport` (each reported fracturing) and `energia:MonthlyGas` (each month of gas), and the fracturing and the well start say which ones they come from (`prov:wasDerivedFrom`). Questions 11 to 14 of `ontology/energia/competency-questions.md` query them, and the AI assistant can answer them in «Mi propia pregunta» (My own question). The tables (`lab_gas`) are not deleted when the links are rebuilt.

- **Publish a new run** every time the model or its data change, and check that question 11 counts the same as the model's «datos dudosos» (doubtful data).
- **Each run stores its input** (`lab_gas.entrada`: what the model saw, well by well). With the same code and the same data, two runs give the same result (`--comparar` gives 0 changes); if a source changes, `--comparar` says which wells, in which feature and how much the prediction moved.
- **The range** comes from the errors of the year before the test (without looking at the test): report what share of the test wells fell inside (`energia:inRangeShare` of the current `energia:ModelRun`), even if it does not reach the 80 % sought.

## Sources and questions about the predictions

- **Lab sources** (`data/lab-gas/`): Capítulo IV from 2018 to 2022, fracturing data and well trajectories. A new source follows the `add-source` skill: its rule goes into the link (`linking/energia/links.sql`), it is mapped with `prov:wasDerivedFrom` and enters the model by both paths (raw SQL in A, SPARQL in B). Measure the effort on each side and the accuracy, and say it even if it does not improve.
- **The assistant on the predictions** is measured with the `evaluate` skill and the `energia_lab` set (`layer/energia_lab/`): `evaluar.py energia_lab prompt|try|puntaje`. Without Rastro it sees the sources and the tables the model leaves (`lab_gas`), like any machine learning process.

## When you change something

1. Run `python3 lab/gas/modelo.py` and read the explanation of two or three wells: does it say something false? does it show a value it should not?
2. Publish the run (`--publicar`) and restart the app (above).
3. Rebuild the blind test if the explanation changed.
4. Update the numbers in `docs/lab-gas-vaca-muerta.md` and `docs/decisions.md` from what the model prints; the script and the slides follow the skill `decks` (slide numbers are placeholders, never typed).
