---
name: verify
description: Check that Rastro starts and answers, for one domain or all of them (services, count per source, ontologies, competency queries, quality rules, evaluation and the app). Use it after a change and before closing a phase or committing.
---

# Verify Rastro

Run everything and report what happened, with the numbers. If something fails, say it as it is.

Everything a domain needs is in its `method:` block in `layer/dominios.yaml`: `ontop {service, port}`, `queries`, `quality`, `evaluation {folder, run}`. Verify the domain you touched; before a release, verify all of them.

## Constraints

- **Never "fix" a check by changing its expected value** (a saved score, a count, a query): find what changed.
- **Report failures as they are,** with the command and its output.
- **Never leave running** an optional service that was stopped before verifying.

## Checklist for one domain

```bash
docker compose ps                                      # postgres, <ontop service> and app up; Ontop healthy
docker compose exec -T postgres psql -U rastro -c "select * from rastro_meta.source_counts"   # rows per source, none at 0
docker compose run --rm ontology-check                 # OK on every query of every domain
for q in <queries folder>/cq*.rq; do echo "$q $(curl -s -H 'Accept: text/csv' --data-urlencode "query@$q" http://localhost:<port>/sparql | wc -l) rows"; done
<quality run>                                          # only if method.quality exists
<evaluation run> rerun
<evaluation run> puntaje                                # same scores as <evaluation folder>/resultados.md
git diff --stat <evaluation folder>                    # only the date should change: if so, git checkout <evaluation folder>/resultados.*
```

What to expect:

- The domain's Ontop `healthy`. If it does not start, `docker compose logs <ontop service>`: almost always a mapping term that is not in the ontology, or a source column that changed.
- Every competency query with rows, in a few seconds each.
- Quality rules: all of them hold; if one does not, the detail is in `method.quality.result` and in the app.
- The evaluation with the same scores as the saved results. If they change, it is not a detail: find which value or rule changed.
- Anything else the domain publishes (for example, a model on top of the layer) runs and its own consistency check passes.

## The app

Open http://localhost:8501 and walk through the demo for the domain you touched. If you changed a module the app imports, restart it: `docker compose restart app`. The first load after changing data is slow (values are recomputed and cached).

## Domains that are stopped

Some services are stopped to save memory. Start them, verify and stop them again:

```bash
docker compose start <ontop service> [other services]
curl -s -H 'Accept: text/csv' --data-urlencode 'query@<queries folder>/cq1.rq' http://localhost:<port>/sparql | head -3
docker compose stop <ontop service> [other services]
```

## Lessons

- A score that changes after a rerun is a signal, not noise: find the changed value or rule before going on.
- After a rerun, only the date should change in the saved results; revert the files if that is all.
- Ontop that does not start almost always means the mapping and the ontology or the source disagree.
- If a service restarts on its own, check Docker memory and which other containers are running.

See examples.md for the commands and expected numbers from Rastro's domains.
