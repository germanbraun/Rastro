# Rastro · Pilot proposal

> **The data changes. The questions don't.**

**For:** [company name] · **Prepared by:** [name] · **Date:** [__]

Spanish version: [piloto.md](piloto.md). The two must say the same.

## The problem it solves

Business questions span databases that don't talk to each other: the same company written three ways, the partners
inside a text, a column renamed in the source's new version. Every query, every dashboard and every model solves it
on its own, and each solves it differently. The result is numbers that don't match, that nobody can explain and that
break when the source changes.

## What Rastro does

It puts a **business dictionary** between the databases and the questions, and solves the hard part **once**: it
translates each database into that dictionary, links the same entities across sources (each link with its rule and
its evidence) and checks the data with quality rules. The data is not copied: each question is translated to the
sources on the fly. Everything stays in open W3C standards that other tools can read.

## What the demo already shows, with public oil and gas data

Measured on 2025 production from Argentina's Energy Secretariat (the demo's numbers are read from its result files;
see `docs/demo-guion-energia.md`):

| | Without Rastro | With Rastro |
|---|---|---|
| **How much oil belongs to YPF?** | summing by the reporting company, 21.4 million m³: it also gets its partners' share | **12.6**, its share of each concession, with the evidence |
| **Over-assigned when summing by the reporting company** | 8.8 million m³: about US$ 3,600 million at US$ 65 a barrel (an assumption) | — |
| **The source renames a column** | 3 broken queries you have to find | **1 line** |
| **A document corrects a stake** | 5 places to correct | **1 place**, and the answer, the model and its explanation change on their own |
| **A machine-learning model** | predicts, but doesn't say what it relies on | **predicts just as well** and every prediction says where each value comes from and what to check |

## The pilot

**Length:** 6 weeks. **Scope:** up to 3 of [company]'s sources, plus the public sources that apply, and up to 10
business questions agreed at the start.

| Weeks | What is done | What [company] sees at the end |
|---|---|---|
| 1 | Choose the questions and the sources; inspect the sources (read-only) | The questions approved by a business person, and which source answers each |
| 2–3 | The business dictionary, the translation of each source, the links between sources with their evidence | Every question answered in the Rastro app, with «Why this number?» |
| 4 | Quality rules and the measured tests: with and without Rastro, the same question in several wordings, a source that changes | The result of each test, measured on your data |
| 5–6 | Optional: one of your models with its inputs taken from Rastro, and its explanation; results presentation | A report with the numbers, the limits and a recommended next step |

## How success is measured

Agreed at the start and measured on [company]'s data, with the same tests as the demo:

- Every agreed question is answered with its evidence: which source each number comes from and by which rule it was
  linked.
- The same question, written different ways, gives the same answer.
- A change in a source (a renamed column) is fixed in one place.
- Every link between sources has its evidence, and those an AI assistant reviewed are confirmed by a person from
  [company].
- [A criterion of [company]'s own, for example: a number computed by hand today, the same and in minutes.]

## What we need from [company]

- **Read-only** access to the sources (or a copy), on your own infrastructure if you prefer: Rastro does not copy
  the data out of where it lives.
- A business person, about 2 hours a week, to approve the questions and definitions and confirm doubtful links.
- A technical person, for access to the sources.

## What stays at the end

The business dictionary, each source's translations and the links with their evidence, in open standards (OWL,
R2RML, SHACL, PROV-O): they belong to [company] and don't depend on Rastro to be read. The app with its questions,
and the results report.

## Good to know

- The value is in integrating the data once and keeping it in one place, not in the technology itself: with the
  same links, well-written SQL also gets it right, and the demo shows it.
- The demo uses public data; the references for its tests were built by an AI assistant and a person still has to
  confirm them. In the pilot, a person from [company] confirms them.

## Investment

[US$ __] for the 6-week pilot · [payment terms] · [what happens if it continues]

**Contact:** [name · email · phone]
