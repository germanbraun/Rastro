# Rastro · on one page

> **The data changes. The questions don't.**

**Rastro integrates your data once. You ask in business words, and every answer says where it comes from and can be
audited.**

Spanish version: [one-pager.md](one-pager.md). The two must say the same.

## The problem

Databases don't talk to each other. In oil and gas, production is reported by each well's operator, but what belongs
to each company depends on its stake in the concession, which lives in another database, sometimes inside a text,
and the same company is written several ways. Every query solves it on its own, and each solves it differently.

## What Rastro does

It puts a **business dictionary** between the databases and the questions: well, concession, operator, stake. It
translates each database into those words once, links the same companies across sources (each link with its
evidence) and checks the data with quality rules. Then anyone asks in those words, and Rastro looks in each database.

## Four tests, measured on Argentina's public data

| | Without Rastro | With Rastro |
|---|---|---|
| **How much of 2025's oil belongs to YPF?** | summing by the reporting company, 21.4 million m³: it adds its partners' share | **12.6**, its share of each concession, with the evidence |
| **The same question, asked 4 ways** | the same answer in 2 of 5 questions | **in 5 of 5** |
| **The source renames a column** | broken queries you have to find | **fixed in 1 line** |
| **A document corrects a stake** | the value lives in 5 places | **corrected in 1**, and the answer, the model and its explanation change on their own |

**And a machine-learning model** (the gas of new Vaca Muerta wells): with Rastro's inputs it predicts just as well,
and every prediction says where each value comes from and which ones are worth checking.

## Good to know

- The value is in integrating the data once and keeping it in one place: with the same links, well-written SQL also
  gets it right, and the demo shows it.
- The demo uses 2025 public data from Argentina's Energy Secretariat and other open sources.
- The tests' references were built by an AI assistant; a person still has to confirm them.

## Next step

A 6-week pilot with your data and your questions: [piloto-en.md](piloto-en.md).

---

Where each number comes from: `layer/energia/resultados.json`, `layer/energia/cambio/*.json` and
`docs/slides/numeros/energia.json`, which also feed the demo and the slides.
