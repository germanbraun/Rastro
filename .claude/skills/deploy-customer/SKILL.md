---
name: deploy-customer
description: Install, check, back up, restore and upgrade Rastro on a customer's machine, and say exactly what data reaches the language model. Use it before and during a pilot at a customer, when touching infra/customer/, infra/docker-compose.customer.yml or docs/data-sent-to-model.md, or when a feature that calls a model changes.
---

# Deploy Rastro at a customer

> **Project skill, not part of the generic method** (`docs/method.md`): it runs and maintains the installation the
> method's skills build on. The guide is `docs/customer-deployment.md`; this skill is its checklist.

## Contract

- **Takes:** a machine in the customer's network with Docker and Git, the domains to serve, read-only access to the
  sources, and the customer's written decision on what data may reach a model.
- **Returns:** a hardened installation that passes `infra/customer/check.py`, a checked backup, and the decision on
  the model written in `docs/decisions.md`.
- **Does not:** type or print passwords, change the password of a database that already exists, or claim a step
  passed without its check's output.

## Steps

1. **Before installing, the model question.** Read `docs/data-sent-to-model.md` with the customer: what each feature
   sends (the chat's answer step sends up to 50 result rows). They choose: the Claude API, Claude through their cloud,
   the OpenAI API (`RASTRO_PROVIDER=openai`), a local model, or none (`RASTRO_NO_MODEL=1`). Write it in `docs/decisions.md`.
   `RASTRO_PROVIDER=replay` is for Rastro's own demo: it answers only the conversations recorded before, never a
   customer's questions.
2. **Install:** `infra/customer/install.sh <domain>`. It fills in `.env` only what is missing, shows the login's
   password once (it keeps only its hash), starts the services in order and runs `check.py`. Every line must be ✅;
   a ❌ is fixed before anything else (a demo default password, a port open to the network).
3. **The app works as the read-only users:** `docker compose --env-file .env -f infra/docker-compose.yml -f
   infra/docker-compose.customer.yml exec -T app python /app/check_domain.py <domain>` opens every section.
4. **After loading a domain,** run `infra/customer/setup.sh` again: the domain's loader created its readers.
5. **Back up, and check the backup:** `RASTRO_BACKUP_PASSPHRASE=… infra/customer/backup.sh`, then
   `infra/customer/restore.sh <folder> --check` (it restores into a temporary database and drops it). Keep backups
   off the machine. Before a demo or a hand-over, a fresh one.
6. **Upgrade:** `infra/customer/upgrade.sh --dry-run <domain>` first, then without `--dry-run` (or `--no-restart` to
   restart in a maintenance window). It backs up, keeps people's changes in a local commit, pulls, rebuilds and runs
   the checks; a conflict or a failed check stops it and says how to go back.
7. **Restore** only with the customer: `infra/customer/restore.sh <folder>` asks to type the folder's name.

## When code changes

- A new call to a model (`ask(` anywhere) needs its row in `docs/data-sent-to-model.md` in the same commit:
  `tests/test_data_sent_to_model.py` fails otherwise.
- A new service or port goes into `infra/docker-compose.customer.yml` too, bound to 127.0.0.1;
  `tests/test_customer_setup.py` checks every Ontop service and that only the proxy is open.
- Try a change to the scripts with a copy of `.env` (`RASTRO_ENV_FILE=…`), never the customer's, and restore the demo
  machine after (the reader passwords, `rastro_readonly`, the proxy).

## A person approves

- What data may reach a model, and which model.
- Who gets the login, and where backups are kept.
- Every restore, and every upgrade's maintenance window.

Real runs and their numbers are in `examples.md`.
