# Deploying Rastro at a customer

What it takes to build and run a semantic layer with Rastro on a customer's data: what can be done today, and what
is left for a version the customer runs on its own. The pilot offer is in [piloto.md](piloto.md)
([English](piloto-en.md)); this document is the technical side of it.

## In short

| | Today: a pilot run by a consultant | Future: a wizard the customer runs |
|---|---|---|
| Who builds the layer | A consultant with Claude Code and the repo's skills | An agent behind a web wizard, through the Claude API |
| Where approvals happen | In the conversation, with the customer's business person | Screens in the wizard, one per decision |
| How sources are connected | A loader script per source, written by the agent (`add-source`) | A form: a database connection, a file or an API |
| What the customer gets | The app, the dictionary, mappings and links in open standards, the measured results | The same, plus the wizard to keep extending it |
| Ready | Yes | No: the pieces in [section 3.4](#34-what-is-left) |

The method does not change between the two: the same steps, skills, checks and human approvals
([method.md](method.md)). What changes is who drives it and where the person approves.

## 1. What runs at the customer

Everything is Docker Compose (`infra/docker-compose.yml`), on one machine:

| Service | What it does | Memory measured on the demo |
|---|---|---|
| `postgres` | Rastro's database: the loaded sources (one schema each), the links and `rastro_meta` (sources and loads) | ~0.6 GB; 4.4 GB on disk with all public domains |
| `ontop-<domain>` | The domain's semantic endpoint (SPARQL), translating each question to SQL over Postgres | ~0.45 GB each |
| `app` | The Streamlit app, business and technical views | ~0.1 GB |
| loaders, linker, `layer-eval`, `calidad`, `ontology-check` | Run on demand, then stop | — |

GraphDB is only needed for oncology (MeSH); a customer domain does not need it. A machine with 4 CPUs, 8 GB of RAM
and 50 GB of disk is enough for a pilot of a few sources; the size of the customer's data decides the disk.

An API key for Claude is needed for free-form questions in the app and for measuring (independent evaluators). The
saved example questions, the demo, quality rules and the Lab model work without it. `layer/answer.py` can also use a
local model (`RASTRO_PROVIDER=ollama`), with lower quality.

## 2. Today: a pilot run by a consultant

### 2.1 Before starting

- **Agreement:** the pilot's questions and sources ([piloto.md](piloto.md)), who approves on the customer's side, and
  the licence ([LICENSE](../LICENSE), [NOTICE](../NOTICE)).
- **Data access:** a read-only user on each source, or a copy (a dump, files). Never an owner's account.
- **What may leave the customer's network.** The agent reads source structure and samples to propose mappings and
  links, and the app sends questions to the Claude API. Agree in writing which data may be sent, or use Claude through
  the customer's cloud provider, or a local model for the app. Write the decision in `docs/decisions.md`.
- **Where it runs:** a VM in the customer's network (recommended, so data stays there) or the consultant's machine
  with a copy of the data.

### 2.2 Install

On the VM, with Docker and Git, from the repository root. The demo's compose file is set up for a laptop (Ontop in
dev mode with open CORS, everything reading as the database owner, no login, ports open on every interface). The
**customer setup** (`infra/docker-compose.customer.yml`) lays the hardening over it:

| | Demo | Customer setup |
|---|---|---|
| Ontop | dev mode, CORS `*`, the database owner | dev mode off, CORS to the app's address, `rastro_readonly` |
| App | the database owner, port open | `rastro_readonly`, port only on this machine |
| SQL readers (`readers` in `layer/dominios.yaml`) | password = their name | the password of `.env` |
| Postgres, Ontop, GraphDB ports | open on every interface | only on this machine |
| Login | none | a proxy (Caddy) with a user and password, over HTTPS |

`rastro_readonly` reads every table, present and future, and writes nothing (`pg_read_all_data`).

**In one command,** with the domains to serve:

```bash
infra/customer/install.sh <domain>
```

It fills in `.env` what is missing (it never changes a value already there): the database owner's password for a new
database, the read-only and reader passwords, and a login whose password it shows once (only its hash is kept). Then it
starts Postgres, creates the users, starts each domain's Ontop, the app and the proxy, and runs `check.py`. Running it
again changes nothing. If the database already exists with the demo password, it says so instead of changing it.

The same, step by step, for when something needs to be done by hand:

1. **`.env`:** copy `.env.example` and fill in, before the first start (Postgres takes `PG_PASSWORD` when it creates
   the database): `PG_PASSWORD`, `RASTRO_READONLY_PASSWORD`, `RASTRO_READER_PASSWORD` (for example
   `openssl rand -hex 16`), `RASTRO_HOST` (the name users type), `RASTRO_LOGIN_USER`, `RASTRO_LOGIN_HASH` and,
   if needed, `ANTHROPIC_API_KEY`. The hash goes between single quotes, because it contains `$`:

   ```bash
   docker run --rm caddy:2.8.4 caddy hash-password --plaintext 'the password'
   ```

2. **Start Postgres, create the users, start the rest.** `--env-file .env` is needed: Compose looks for `.env` next
   to the first file, in `infra/`:

   ```bash
   docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.customer.yml up -d postgres
   ```
   ```bash
   infra/customer/setup.sh
   ```
   ```bash
   docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.customer.yml up -d postgres ontop-<domain> app proxy
   ```

   Run `setup.sh` again after loading a domain: its loader creates the domain's readers.

3. **Check it took effect:**

   ```bash
   RASTRO_LOGIN_PASSWORD='the password' python3 infra/customer/check.py
   ```

   Each point says ✅ or ❌: dev mode off, who each service reads as, which ports are reachable, that
   `rastro_readonly` reads and cannot write, that no reader logs in with its own name, that the app asks for a login
   and opens with it. Then `docker compose ... exec -T app python /app/check_domain.py <domain>` opens every section
   of the app as the read-only users.

Users open `https://<RASTRO_HOST>:8443` (`RASTRO_HTTPS_PORT`). With `RASTRO_TLS=internal` the certificate is Caddy's
own and the browser warns once; with an email and a public name, Caddy gets a public certificate. For the customer's
single sign-on, replace the `proxy` service with the customer's own proxy, pointing at `app:8501`.

**What changes for the work:** with dev mode off, Ontop does not reload an edited mapping: restart it
(`docker compose ... restart ontop-<domain>`), as the skills already do. The mapping editor of «Bajo el capó» can
still save mappings, so in the customer setup anyone who can log in can change them: give the login only to the
team that builds the layer, or mount `mappings/` read-only.

### 2.3 Build the layer with the method

The consultant opens Claude Code in the repository on the VM (or with SSH to it), and runs the method's skills in
order. Each step ends in a check that decides, and in an approval only where there is a business decision:

| Week | Step | Skill | The customer approves |
|---|---|---|---|
| 1 | Inspect the candidate sources, read-only | `inspect-sources` | Which sources and which questions |
| 1 | Start the domain: registry, scope, experiment log | `start-domain` | The scope (sources, period, region) |
| 1 | Business questions, with their definitions | `add-question` | Each question and what each word means |
| 2 | Connect each source: loader, load record | `add-source` | What goes in |
| 2–3 | Dictionary and mappings | `map-source` | The definitions |
| 2–3 | Links between sources, with evidence | `link-entities` | The doubtful links |
| 4 | Quality rules | `quality-rules` | Thresholds; whether the source gets corrected |
| 4 | Measure: without Rastro, SQL with links, with Rastro; change test | `evaluate`, `change-tests` | The adjudication where approaches differ |
| 5 | Show it in the app, and a «Paso a paso» on one real case | `show-in-app`, `walkthrough` | The wording and the demo questions |
| 6 | Verify, close and hand over | `verify`, `close-phase` | — |

A new domain starts with one command, `python layer/method.py new-domain <domain> --title "..."`: its folders,
registry entry and Ontop service (also in the customer setup), checked before anything is written. The app entry
comes with `show-in-app`.

**Connecting the customer's sources.** Two ways; for a pilot, the first:

1. **A copy in Rastro's Postgres** (how every demo domain works): a loader reads the source (database, files or API)
   and loads only what the questions need, recording each load in `rastro_meta.load_run`. Simple, repeatable, and
   the links live next to the data.
2. **Reading in place:** Ontop connects to the customer's database over JDBC, and no data is copied. One Ontop
   instance reads one database, and Rastro's links and precomputed tables need a place to live, so several sources
   need a SQL federation layer or a database the customer allows Rastro to write to. A step for after the pilot.

The experiment log (`layer/method.py experiment <domain>`) records hours, interventions and decisions as the work
goes. It is the pilot's evidence of how much a person had to do.

### 2.4 Applications on the layer

Once the layer exists, the same dictionary serves several applications; the customer picks which ones to deploy.
Each one is a module of the app, switched on in the domain's YAML (skill `show-in-app`):

| Application | What it does | Needs |
|---|---|---|
| Business questions | The approved questions, answered with «¿Por qué este número?» | The layer |
| Talk to the data (chat) | Free questions and follow-ups; the model's context is the ontology; every number of an answer is checked against the data | The Claude API |
| Questions over texts (GraphRAG) | The graph picks the records by concept; the model reads only their texts and cites them | Free-text records; the Claude API |
| Check a claim | Holds, does not hold, or no data, for a number read in a report | The layer |
| Enrichment | Data from an outside source through a shared key, live or saved | A shared key (an identifier) |
| A model with its evidence (like Rastro Lab) | Predictions explained with the layer's evidence | Custom work (an extension) |

### 2.5 What the customer keeps

- The dictionary (OWL), the mappings (R2RML), the quality rules (SHACL) and the links with their evidence (PROV-O):
  open standards that other knowledge-graph platforms or tools can read.
- The app with its questions, both views, and the measured results with their limits.
- The experiment log and `docs/decisions.md`: every decision, why, and who approved it.

### 2.6 Checklist

- [ ] Read-only access to each source; the decision on what data may be sent to the model, in writing
- [ ] VM with Docker; `infra/customer/install.sh <domain>`, with `check.py` all ✅ (section 2.2)
- [ ] Domain started; scope approved; questions approved
- [ ] Each source loaded and recorded; dictionary and mappings checked; links reviewed by the customer
- [ ] Quality rules run; evaluation measured and adjudicated; change test recorded
- [ ] App checked in both views (`app/check_domain.py`); `verify` passed
- [ ] Hand-over: files, decisions, experiment log, results

## 3. Future: a wizard the customer runs

### 3.1 What the customer would see

A web wizard with one screen per step of the method. On each screen the agent has already done the work and the
customer only decides what is theirs to decide:

1. **Sources:** add a database connection (read-only), upload files or give an API. The agent inspects each one and
   shows what it found: tables, keys, sample rows, how it could join the others.
2. **Questions:** write business questions in plain words. The agent proposes the definitions and the expected answer
   type; the customer approves or corrects each one.
3. **Dictionary:** the concepts the questions need, drawn as a diagram, in the customer's words. Approve.
4. **Links:** the proposed joins between sources, grouped by rule, with the doubtful ones first. Confirm or reject
   each doubtful link, with its evidence on screen.
5. **Quality:** the rules and what fails them today. Set thresholds.
6. **Results:** each question answered with its evidence, measured with and without Rastro. Adjudicate where the
   approaches differ.
7. **Publish:** the app goes live for the customer's users.

Every approval is stored with the exact text approved (as `layer/lifecycle.py` already does), and changing an approved
piece sends it back to the customer.

### 3.2 How it would work

```
Wizard (web) ──► Orchestrator ──► Agent with the method's skills ──► Workspace (a Git repo per customer)
     ▲                │                     │                                │
     │                │                     └─ runs the checks ──────────────┤
     └── approvals ◄──┘                        (method.py, ontology-check,   ▼
                                                calidad, evaluate)      Rastro stack (Postgres, Ontop, app)
```

- **The agent** is the same as today: one agent that loads the skill it needs ([method.md](method.md), «Agents: one,
  with skills»), with tools to read and write files and run commands in the workspace. Evaluators stay separate
  agents that only see their prompt.
- **The orchestrator** walks the method's steps, starts the agent with the right skill, runs the check that decides,
  and stops at each approval until the customer answers in the wizard.
- **The workspace** is what the repository is today: registry, ontology, mappings, linker, app configuration and
  decisions, versioned, so every change can be reviewed and undone.

Two ways to run the agent through the Claude API:

| | Claude Agent SDK, in the customer's network | Managed agents, hosted by Anthropic |
|---|---|---|
| What it is | The agent loop of Claude Code as a library, inside our orchestrator | Anthropic runs the agent loop and the sandbox where its tools run |
| Data | Stays in the customer's network; only what the model reads goes to the API | The workspace and its data live in the hosted sandbox |
| Fits | Customers whose data must not leave (most) | Public data, or customers who accept it |

The recommendation is the Agent SDK in the customer's network: it reuses the skills as they are, keeps the data where
it is, and changes only who drives the agent.

### 3.3 What already exists and is reused

- **The method and its skills** (`.claude/skills/`), generic per domain: each domain's paths and commands come from its
  `method:` block in `layer/dominios.yaml`.
- **The checks that decide,** as commands: `method.py registry|verify|publication|experiment`, `ontology-check`,
  `calidad`, `evaluar.py`, `check_domain.py`.
- **Approvals bound to the exact text** (`layer/lifecycle.py`), and the experiment log with each human intervention.
- **The app is generic:** a domain is a YAML file plus an optional extension class (`app/dominio/extension.py`).
- **The change guard** (`layer/change_guard.py`): every test that changes data snapshots it and restores it exactly.

### 3.4 What is left

| Piece | Why it is needed | Size |
|---|---|---|
| Source connectors as configuration | Today each source is a loader written by the agent; the wizard needs a form for a database (JDBC), files and common APIs, with a generic loader | Large |
| Domain set-up without hand edits | Done for the scaffold (`method.py new-domain`); the app entry is still added by hand in `show-in-app` | Small |
| The orchestrator | Walks the steps, runs each check, stores each approval, resumes after a failure | Large |
| The wizard screens | One per approval (section 3.1); most can reuse the app's technical view (dictionary, links, quality, evaluation) | Large |
| Agent runtime | The Agent SDK with the repo's skills and tools, sandboxed to the workspace | Medium |
| Single sign-on and roles | The customer setup has one shared login (section 2.2); the wizard needs the customer's sign-on, and who may approve or only read | Medium |
| Several databases read in place | Federation, or a writable database for links (section 2.3) | Medium |
| One deployment per customer | Packaging and upgrades (images, migrations of the workspace) | Medium |

Sizes are rough, to compare the pieces (small: days; medium: one to two weeks; large: several weeks); a plan needs
its own estimate.

### 3.5 Open questions

- **How much the agent gets right without a consultant.** The pilots' experiment logs measure it: hours, how many
  times a person stepped in and why. The wizard is worth building when those numbers say a business user can answer
  what is left.
- **What data reaches the model.** Structure and samples for mappings and links, and evidence texts for doubtful
  links. Some customers will need an option to mask samples.
- **Domain extensions.** Rastro Lab is custom code (an extension class). The wizard covers the layer; a model like
  Lab stays consulting work.

## 4. Recommendation

Run the first customers as consultant-run pilots (section 2), on a VM in their network, with the hardening of section
2.2, and record the experiment log for every step. Build the wizard after two or three pilots, starting with what the
logs show takes the most consultant time, which today is likely to be connecting sources and reviewing links.
