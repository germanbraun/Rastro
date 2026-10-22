---
name: close-phase
description: Close a step or a phase of the Rastro plan, in any domain (verify, check the numbers match, mark the plan, document decisions and commit). Use it when a checkpoint or a block of work is finished.
---

# Close a phase

Read `docs/method-contracts.md` for lifecycle states, executable gates, approval reuse and experiment evidence.
For a new domain, run `start-domain` first. Record measured time, interventions and caught errors as work happens.


## Constraints

- **Never commit with a failing check** (verify, lint or tests).
- **Never commit secrets or data:** no `.env`, no keys in `.env.example`, nothing from `data/raw/`.
- **Stage only the files you changed,** never `git add -A`.
- **Never push unless the user asks.**

## Steps

1. **Experiment evidence:** for a new-domain experiment run `python layer/method.py experiment <domain> --check`.
   Verify measured agent/person time, interventions, errors caught, method changes, version and outcomes. Missing
   evidence blocks claiming a completed experiment. Legacy maintenance uses decisions.md without invented history.
   Confirm business approvals and quality-defect dispositions; routine technical checks need no extra approval.
2. **Verify** with the skill `verify`. Do not close a phase with its checkpoint failing.
3. **Publication:** run `python layer/method.py publication <domain>` before new accuracy claims; independently reviewed references must cover agreement cases too.
4. **Check that the numbers match** everywhere: what changed in the app (which reads them from its JSON files) must say the same in `docs/decisions.md`, the domain's docs and the demo material (script and slides: skill `decks`).
5. **Mark the plan** in `docs/plan.md`: finished steps with `[x]`. Keep the plan short: a summary of what was achieved, not the history.
6. **Decisions:** one entry in `docs/decisions.md` for each new decision, with date, what was decided, why and the numbers that back it. If a decision is a rule that must always be followed, it also goes to `CLAUDE.md` or to a skill.
7. **README and `CLAUDE.md`:** if how something is started, loaded or measured changed.
8. **Before committing, check secrets and names:**
   ```bash
   grep -E '^[A-Z_]*(KEY|TOKEN|PASSWORD|USER)=.+' .env.example   # only local development values, never keys
   git status --short                                            # no .env or data/raw
   python3 -m ruff check .                                       # no errors
   python3 -m pytest -q                                          # tests pass
   ```
   And that there are no names of commercial knowledge-graph products or companies (see `CLAUDE.md`).
9. **Commit in English, staging only the files you changed** (`git add <files>`, never `git add -A`: another session may have work in progress in the same folder): a title that says what looks different (prefixed with the area or domain, "<Area>: …") and a short paragraph with the numbers. It ends with the matching `Co-Authored-By` line.
10. **Push only if the user asks.**
