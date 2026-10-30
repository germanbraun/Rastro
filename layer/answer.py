"""Three ways for an LLM to answer a business question.

  A. solo:   the LLM answers with what it knows, without access to data
  B. sql:    the LLM writes SQL over the source tables as they were loaded
  C. rastro: the LLM writes SPARQL over Rastro's ontology (Ontop)
  D. sql + enlaces: the LLM writes SQL over the same tables, plus Rastro's link tables,
             documented. It is the fair baseline: the same data as C,
             without the semantic layer

All of them use the same model, the same base instructions and, for B and C, the
same retries: if the query fails, the LLM sees the error and gets two more attempts.

What is specific to each domain is in dominios.yaml; each function receives the domain.

The LLM is chosen with RASTRO_PROVIDER:
  anthropic  Claude API (needs ANTHROPIC_API_KEY). Default model: claude-opus-5-5
  ollama     a local model on the Mac (needs Ollama running). Default model:
             qwen2.5-coder:7b. See layer/README.md
  openai     the OpenAI API (needs OPENAI_API_KEY and RASTRO_MODEL, the model's name; OPENAI_BASE_URL
             for another server with the same API)
  files      no API: each call is written to a file and its reply read from another (RASTRO_FILES), so an
             assistant without a key answers them; see layer/chat_eval.py
Without either, eval/manual.py prints the prompts to answer them by hand.
"""

import hashlib
import json
import os
from pathlib import Path

import psycopg
import requests
import yaml

PROVIDER = os.environ.get("RASTRO_PROVIDER") or "anthropic"
MODEL = os.environ.get("RASTRO_MODEL") or {"anthropic": "claude-opus-5-5", "ollama": "qwen2.5-coder:7b",
                                           "openai": "", "files": "files"}[PROVIDER]
OLLAMA = os.environ.get("OLLAMA_URL") or "http://host.docker.internal:11434"
MAX_ATTEMPTS = 3
ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).parent
DOMAINS = yaml.safe_load((HERE / "dominios.yaml").read_text())

# When the data is not enough, the LLM says so instead of making up a query
SIN_DATOS = "SIN DATOS:"
NO_DATA_RULE = """Si los datos no alcanzan para responder (falta el período, la medida o el tema), no \
inventes una query: devolvé en su lugar una sola línea que empiece con «SIN DATOS:» y diga qué falta."""

QUERY_RULES = """La query tiene que devolver una sola columna: los nombres si la respuesta \
es una lista, o una sola fila con el número si la respuesta es un número. No expliques \
nada: devolvé solo la query. """ + NO_DATA_RULE


# --- What the LLM receives in each approach ----------------------

def system_prompt(approach, domain):
    d = DOMAINS[domain]
    base = d["base"]
    if approach == "A":
        return (base + "\n\nNo tenés acceso a ninguna base de datos: respondé con lo que sabés. "
                "Si no sabés un número exacto, da tu mejor estimación.")
    if approach in "BD":
        return (base + "\n\nEscribí una sola query SQL para PostgreSQL que responda la pregunta. "
                + QUERY_RULES + "\n\n" + sql_schema(approach, domain))
    ontology = (ROOT / d["ontology"]).read_text()
    notes = (ROOT / d["sparql_notes"]).read_text()
    return (base + "\n\nEscribí una sola query SPARQL sobre la ontología de Rastro que responda "
            "la pregunta. " + QUERY_RULES + "\n\n" + notes + "\n\nOntología:\n" + ontology)


def output_schema(approach, kind):
    if approach == "A":
        item = {"type": "number"} if kind == "número" else {"type": "array", "items": {"type": "string"}}
        props = {"answer": item}
    else:
        props = {"query": {"type": "string"}}
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


# --- The LLM ------------------------------------------------------

def ask(system, messages, schema):
    """One call to the LLM with JSON output. Returns (assistant message, data)."""
    providers = {"ollama": ask_ollama, "openai": ask_openai, "files": ask_files}
    return providers.get(PROVIDER, ask_claude)(system, messages, schema)


def ask_claude(system, messages, schema):
    import anthropic

    response = anthropic.Anthropic().beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        # The large context (schema or ontology) goes in the system prompt and is cached: after
        # the first question it is billed at 10 %
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        # If a safety classifier rejects the request, the API retries it on the
        # recommended model instead of returning the rejection
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("El modelo rechazó la pregunta")
    text = next(b.text for b in response.content if b.type == "text")
    return response.content, json.loads(text)


def ask_ollama(system, messages, schema):
    r = requests.post(f"{OLLAMA}/api/chat", timeout=600, json={
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, *messages],
        "format": schema,          # Ollama restricts the output to this JSON schema
        "stream": False,
        "options": {"temperature": 0, "num_ctx": 32768},
    })
    r.raise_for_status()
    text = r.json()["message"]["content"]
    return text, json.loads(text)


def ask_openai(system, messages, schema):
    if not MODEL:
        raise RuntimeError("RASTRO_PROVIDER=openai necesita RASTRO_MODEL, el nombre del modelo")
    base = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    r = requests.post(f"{base}/chat/completions", timeout=600,
                      headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                      json={"model": MODEL,
                            "messages": [{"role": "system", "content": system}, *messages],
                            # The reply is restricted to this JSON schema
                            "response_format": {"type": "json_schema",
                                                "json_schema": {"name": "respuesta", "schema": schema, "strict": True}}})
    r.raise_for_status()
    message = r.json()["choices"][0]["message"]
    if message.get("refusal"):
        raise RuntimeError("El modelo rechazó la pregunta")
    return message["content"], json.loads(message["content"])


class Pending(Exception):
    """A call written to a file whose reply is not there yet (RASTRO_PROVIDER=files)."""


def ask_files(system, messages, schema):
    """The call as a text file, named by its content, and the reply read from the JSON file next to it. The same call
    always has the same name, so a run that stopped for a missing reply goes on from there once it is written."""
    folder = Path(os.environ["RASTRO_FILES"])
    said = "\n\n".join(f"[{m['role']}]\n{m['content']}" for m in messages)
    text = (f"[system]\n{system}\n\n{said}\n\n[formato]\nRespondé solo con un objeto JSON que cumpla este "
            f"esquema, sin texto alrededor:\n{json.dumps(schema, ensure_ascii=False)}\n")
    key = hashlib.sha256(text.encode()).hexdigest()[:16]
    reply = folder / f"{key}.json"
    if reply.exists():
        content = reply.read_text()
        return content, json.loads(content)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{key}.txt").write_text(text)
    raise Pending(key)


# --- Answer -------------------------------------------------------

def answer(approach, question, kind, domain):
    system = system_prompt(approach, domain)
    schema = output_schema(approach, kind)
    messages = [{"role": "user", "content": question}]
    if approach == "A":
        _, data = ask(system, messages, schema)
        return {"answer": data["answer"], "attempts": []}

    attempts = []
    for _ in range(MAX_ATTEMPTS):
        assistant, data = ask(system, messages, schema)
        result = try_query(approach, data["query"], kind, domain)
        attempts.append(result["attempt"])
        if result["attempt"]["error"] is None:
            return {"answer": result["answer"], "attempts": attempts}
        messages += [{"role": "assistant", "content": assistant},
                     {"role": "user", "content": retry_message(result["attempt"]["error"])}]
    return {"answer": None, "attempts": attempts}


def explain_query(query, sql, domain, language="es"):
    """Explains in simple words a SPARQL query and the SQL that Ontop generated, for someone who
    knows SQL but not semantic technologies. Returns Markdown bullets, in Spanish or, with language="en", English."""
    system = ("Explicás consultas a una persona de negocio que sabe SQL pero no conoce tecnologías "
              "semánticas. En español, en 3 a 5 viñetas cortas: qué busca, qué une o filtra, qué "
              "devuelve, y qué habría que hacer a mano en SQL que acá ya resuelve el diccionario de "
              "negocio. Sin jerga: no digas RDF, tripletas ni IRI.\n\n" + (ROOT / DOMAINS[domain]["sparql_notes"]).read_text())
    if language == "en":   # the interface is in English; the Spanish default is what the evaluation was measured with
        system = system.replace("En español,", "In English,")
    content = f"Consulta SPARQL:\n{query}" + (f"\n\nSQL que generó Ontop:\n{sql}" if sql else "")
    _, data = ask(system, [{"role": "user", "content": content}],
                  {"type": "object", "properties": {"explicacion": {"type": "string"}},
                   "required": ["explicacion"], "additionalProperties": False})
    return data["explicacion"]


def retry_message(error):
    return f"La query falló con este error:\n{error}\n\nCorregila."


def try_query(approach, query, kind, domain):
    """Runs the query of B (SQL) or C (SPARQL) and returns the answer or the error."""
    if sin_datos(query):
        return {"answer": None, "attempt": {"query": query, "error": None}}
    try:
        column = run_sparql(query, domain) if approach == "C" else run_sql(query, approach, domain)
    except Exception as e:  # noqa: BLE001 - the error is returned to the model as is
        return {"answer": None, "attempt": {"query": query, "error": str(e).strip()[:2000]}}
    return {"answer": to_answer(column, kind), "attempt": {"query": query, "error": None}}


def sin_datos(query):
    """The LLM said the data is not enough (returns the reason) or wrote a query (None)."""
    text = (query or "").strip()
    return text[len(SIN_DATOS):].strip() or "los datos no alcanzan" if text.upper().startswith(SIN_DATOS) else None


def to_answer(column, kind):
    if kind == "número":
        return float(column[0]) if column and column[0] is not None else None
    return [str(v) for v in column if v is not None]


# --- Where the queries run ----------------------------------------

# B sees the sources as they were loaded; D also sees Rastro's link tables
# (each domain's users are in dominios.yaml)
def reader_dsn(user):
    """A read-only user's connection. Its password is RASTRO_READER_PASSWORD (the customer setup sets one for every
    reader: infra/customer/setup.sh); without it, the user's own name, as on the demo machine."""
    password = os.environ.get("RASTRO_READER_PASSWORD") or user
    return f"host=postgres port=5432 dbname={os.environ['PG_DB']} user={user} password={password}"


def run_sql(query, approach, domain):
    user = DOMAINS[domain]["readers"][approach]
    with psycopg.connect(reader_dsn(user)) as conn:
        return [row[0] for row in conn.execute(query).fetchall()]


def sql_schema(approach, domain):
    """The schema of the tables the read-only user sees, with their documentation."""
    d = DOMAINS[domain]
    user = d["readers"][approach]
    with psycopg.connect(reader_dsn(user)) as conn:
        rows = conn.execute("""
            SELECT c.table_schema, c.table_name, string_agg(c.column_name || ' ' || c.data_type, ', '
                                                          ORDER BY c.ordinal_position)
            FROM information_schema.columns c
            JOIN information_schema.table_privileges p
              ON p.table_schema = c.table_schema AND p.table_name = c.table_name
             AND p.grantee = %s AND p.privilege_type = 'SELECT'
            GROUP BY 1, 2 ORDER BY 1, 2""", (user,)).fetchall()
    tables = "\n".join(f"{s}.{t}({cols})" for s, t, cols in rows)
    notes = (ROOT / d["sql_notes"]).read_text()
    if approach == "D":
        notes += "\n" + (ROOT / d["links_notes"]).read_text()
    return f"{notes}\n\nTablas:\n{tables}"


def run_sparql(query, domain):
    r = requests.post(DOMAINS[domain]["ontop"], data={"query": query}, timeout=120,
                      headers={"Accept": "application/sparql-results+json"})
    if not r.ok:
        raise RuntimeError(r.text)
    data = r.json()
    var = data["head"]["vars"][0]
    return [b[var]["value"] if var in b else None for b in data["results"]["bindings"]]


# --- Free questions for the interface ------------------------------

FREE_RULES = """La query puede devolver varias columnas, con nombres de variable claros en \
español (por ejemplo ?farmaco, ?ensayos). Limitá el resultado a 50 filas. No expliques \
nada: devolvé solo la query. """ + NO_DATA_RULE

# Which source each ontology term comes from (dominios.yaml)
def term_sources(domain):
    return {term: source for source, terms in DOMAINS[domain]["term_sources"].items() for term in terms}



def ask_rastro(question, domain, language="es"):
    """Answers a free question with SPARQL over Rastro. Needs a configured LLM. With language="en", the explanation
    after «SIN DATOS:» is written in English (the marker stays, the code looks for it)."""
    system = system_prompt("C", domain).replace(QUERY_RULES, FREE_RULES)
    if language == "en":
        system += "\n\nThe person reads English: after «SIN DATOS:», explain in English what is missing."
    schema = output_schema("C", "lista")
    messages = [{"role": "user", "content": question}]
    attempts = []
    for _ in range(MAX_ATTEMPTS):
        assistant, data = ask(system, messages, schema)
        if sin_datos(data["query"]):
            return {"query": None, "columns": [], "rows": [], "attempts": attempts, "sin_datos": sin_datos(data["query"])}
        try:
            columns, rows = run_sparql_table(data["query"], domain)
        except Exception as e:  # noqa: BLE001 - the error is returned to the model as is
            attempts.append({"query": data["query"], "error": str(e).strip()[:2000]})
            messages += [{"role": "assistant", "content": assistant},
                         {"role": "user", "content": retry_message(attempts[-1]["error"])}]
            continue
        attempts.append({"query": data["query"], "error": None})
        return {"query": data["query"], "columns": columns, "rows": rows, "attempts": attempts}
    return {"query": None, "columns": [], "rows": [], "attempts": attempts}


def run_sparql_table(query, domain):
    """Runs SPARQL on Ontop and returns (columns, rows)."""
    r = requests.post(DOMAINS[domain]["ontop"], data={"query": query}, timeout=120,
                      headers={"Accept": "application/sparql-results+json"})
    if not r.ok:
        raise RuntimeError(r.text)
    data = r.json()
    columns = data["head"]["vars"]
    rows = [[b[c]["value"] if c in b else None for c in columns] for b in data["results"]["bindings"]]
    return columns, rows


def ontop_sql(query, domain):
    """The SQL that Ontop generates and runs on Postgres for a SPARQL query."""
    r = requests.get(DOMAINS[domain]["ontop"].replace("/sparql", "/ontop/reformulate"),
                     params={"query": query}, timeout=60)
    r.raise_for_status()
    lines = r.text.splitlines()
    native = next((i for i, line in enumerate(lines) if line.strip().startswith("NATIVE")), None)
    return "\n".join(lines[native + 1:]).strip() if native is not None else r.text.strip()


def column_sources(query, domain):
    """Sources of a query: (all the ones it uses, the ones of each result column).

    A column that is the object of a term (?farmaco in ?d :name ?farmaco) takes the
    source of that term, or that of the subject's class if the term is shared
    (:name). A computed column (COUNT, SUM) takes all the sources of the query.
    """
    from rdflib import URIRef
    from rdflib.plugins.sparql import prepareQuery

    algebra = prepareQuery(query).algebra
    triples, seen = [], set()

    def walk(node):
        if id(node) in seen:
            return
        seen.add(id(node))
        if isinstance(node, dict) or hasattr(node, "items"):
            if "triples" in node:
                triples.extend(node["triples"])
            for v in node.values():
                walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                walk(v)

    walk(algebra)
    ns, sources_of_term = DOMAINS[domain]["namespace"], term_sources(domain)
    label_source = DOMAINS[domain].get("label_source")   # the source of rdfs:label, if the domain declares one
    link_from = {}   # term of a Rastro link → the sources it comes from
    for source, terms in DOMAINS[domain].get("link_sources", {}).items():
        for term in terms:
            link_from.setdefault(term, set()).add(source)
    types = {s: str(o) for s, p, o in triples if str(p).endswith("#type") and isinstance(o, URIRef)}

    def direct_source(predicate):
        if str(predicate).endswith("rdf-schema#label"):
            return label_source
        return sources_of_term.get(str(predicate).replace(ns, ""))

    def source_of(subject, predicate):
        """Source of the term; if it is shared (:name), that of the subject's class
        or, if the query does not declare it, that of the other terms of the same subject."""
        found = direct_source(predicate)
        if found:
            return found
        cls = sources_of_term.get(types.get(subject, "").replace(ns, ""))
        if cls:
            return cls
        others = {direct_source(p) for s, p, o in triples if s == subject} - {None, "rastro", label_source}
        return others.pop() if len(others) == 1 else None

    def steps(predicate):
        """The terms of a path (:supplier/:group) or the term alone."""
        return [x for a in predicate.args for x in steps(a)] if hasattr(predicate, "args") else [predicate]

    def sources_for(subject, predicate):
        """The source of the term and, if it is a Rastro link, also the sources the link comes from."""
        found = source_of(subject, predicate)
        if found != "rastro":
            return {found} - {None}
        term = str(predicate).replace(ns, "")
        if term.endswith("#type"):
            term = types.get(subject, "").replace(ns, "")
        return {"rastro"} | link_from.get(term, set())

    all_sources = set().union(*(sources_for(s, q) for s, p, o in triples for q in steps(p)))
    per_column = {}
    for var in algebra.get("PV", []):
        direct = set().union(*(sources_for(s, steps(p)[-1]) for s, p, o in triples if o == var))
        per_column[str(var)] = sorted(direct or all_sources)
    return sorted(all_sources), per_column
