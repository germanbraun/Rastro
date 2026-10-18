"""Tres formas de que un LLM responda una pregunta de negocio.

  A. solo:   el LLM responde con lo que sabe, sin acceso a datos
  B. sql:    el LLM escribe SQL sobre las tablas de las fuentes tal como se cargaron
  C. rastro: el LLM escribe SPARQL sobre la ontología de Rastro (Ontop)
  D. sql + enlaces: el LLM escribe SQL sobre las mismas tablas, más las tablas de enlaces
             de Rastro, documentadas. Es la línea de base justa: los mismos datos que C,
             sin la capa semántica

Las tres usan el mismo modelo, las mismas instrucciones de base y, para B y C, los
mismos reintentos: si la query falla, el LLM ve el error y tiene dos intentos más.

El LLM se elige con RASTRO_PROVIDER:
  anthropic  Claude API (necesita ANTHROPIC_API_KEY). Modelo por defecto: claude-opus-5-5
  ollama     un modelo local en la Mac (necesita Ollama corriendo). Modelo por defecto:
             qwen2.5-coder:7b. Ver layer/README.md
Sin ninguno de los dos, eval/manual.py imprime los prompts para responderlos a mano.
"""

import json
import os
from pathlib import Path

import psycopg
import requests

PROVIDER = os.environ.get("RASTRO_PROVIDER") or "anthropic"
MODEL = os.environ.get("RASTRO_MODEL") or {"anthropic": "claude-opus-5-5",
                                           "ollama": "qwen2.5-coder:7b"}[PROVIDER]
OLLAMA = os.environ.get("OLLAMA_URL") or "http://host.docker.internal:11434"
MAX_ATTEMPTS = 3
ONTOP = "http://ontop:8080/sparql"
ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).parent

BASE = """Respondés preguntas de negocio sobre ensayos clínicos de oncología, fármacos, \
sus targets y sus eventos adversos. Seguí al pie de la letra las definiciones que trae \
la pregunta (qué fases o estados cuentan). Si la respuesta es una lista, devolvé solo \
los nombres pedidos; si es un número, un solo número."""

QUERY_RULES = """La query tiene que devolver una sola columna: los nombres si la respuesta \
es una lista, o una sola fila con el número si la respuesta es un número. No expliques \
nada: devolvé solo la query."""


# --- Qué recibe el LLM en cada enfoque ----------------------------

def system_prompt(approach):
    if approach == "A":
        return (BASE + "\n\nNo tenés acceso a ninguna base de datos: respondé con lo que sabés. "
                "Si no sabés un número exacto, da tu mejor estimación.")
    if approach in "BD":
        return (BASE + "\n\nEscribí una sola query SQL para PostgreSQL que responda la pregunta. "
                + QUERY_RULES + "\n\n" + sql_schema(approach))
    ontology = (ROOT / "ontology" / "rastro.ttl").read_text()
    notes = (HERE / "sparql-notes.md").read_text()
    return (BASE + "\n\nEscribí una sola query SPARQL sobre la ontología de Rastro que responda "
            "la pregunta. " + QUERY_RULES + "\n\n" + notes + "\n\nOntología:\n" + ontology)


def output_schema(approach, kind):
    if approach == "A":
        item = {"type": "number"} if kind == "número" else {"type": "array", "items": {"type": "string"}}
        props = {"answer": item}
    else:
        props = {"query": {"type": "string"}}
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


# --- El LLM -------------------------------------------------------

def ask(system, messages, schema):
    """Una llamada al LLM con salida JSON. Devuelve (mensaje del asistente, datos)."""
    return ask_ollama(system, messages, schema) if PROVIDER == "ollama" else ask_claude(system, messages, schema)


def ask_claude(system, messages, schema):
    import anthropic

    response = anthropic.Anthropic().beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        # El contexto grande (esquema u ontología) va en el system y se cachea: después de
        # la primera pregunta se cobra a un 10 %
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        # Si un clasificador de seguridad rechaza el pedido, la API lo reintenta en el
        # modelo recomendado en lugar de devolver el rechazo
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
        "format": schema,          # Ollama restringe la salida a este esquema JSON
        "stream": False,
        "options": {"temperature": 0, "num_ctx": 32768},
    })
    r.raise_for_status()
    text = r.json()["message"]["content"]
    return text, json.loads(text)


# --- Responder ----------------------------------------------------

def answer(approach, question, kind):
    system = system_prompt(approach)
    schema = output_schema(approach, kind)
    messages = [{"role": "user", "content": question}]
    if approach == "A":
        _, data = ask(system, messages, schema)
        return {"answer": data["answer"], "attempts": []}

    attempts = []
    for _ in range(MAX_ATTEMPTS):
        assistant, data = ask(system, messages, schema)
        result = try_query(approach, data["query"], kind)
        attempts.append(result["attempt"])
        if result["attempt"]["error"] is None:
            return {"answer": result["answer"], "attempts": attempts}
        messages += [{"role": "assistant", "content": assistant},
                     {"role": "user", "content": retry_message(result["attempt"]["error"])}]
    return {"answer": None, "attempts": attempts}


def retry_message(error):
    return f"La query falló con este error:\n{error}\n\nCorregila."


def try_query(approach, query, kind):
    """Ejecuta la query de B (SQL) o C (SPARQL) y devuelve la respuesta o el error."""
    try:
        column = run_sparql(query) if approach == "C" else run_sql(query, approach)
    except Exception as e:  # noqa: BLE001 - el error se le devuelve al modelo tal cual
        return {"answer": None, "attempt": {"query": query, "error": str(e).strip()[:2000]}}
    return {"answer": to_answer(column, kind), "attempt": {"query": query, "error": None}}


def to_answer(column, kind):
    if kind == "número":
        return float(column[0]) if column and column[0] is not None else None
    return [str(v) for v in column if v is not None]


# --- Dónde corren las queries --------------------------------------

# B ve las fuentes tal como se cargaron; D, además, las tablas de enlaces de Rastro
READERS = {"B": "rastro_reader", "D": "rastro_reader_links"}
READER = "host=postgres port=5432 dbname=%s user={0} password={0}"


def run_sql(query, approach="B"):
    with psycopg.connect(READER.format(READERS[approach]) % os.environ["PG_DB"]) as conn:
        return [row[0] for row in conn.execute(query).fetchall()]


def sql_schema(approach="B"):
    """El esquema de las tablas que ve el usuario de solo lectura, con su documentación."""
    user = READERS[approach]
    with psycopg.connect(READER.format(user) % os.environ["PG_DB"]) as conn:
        rows = conn.execute("""
            SELECT c.table_schema, c.table_name, string_agg(c.column_name || ' ' || c.data_type, ', '
                                                          ORDER BY c.ordinal_position)
            FROM information_schema.columns c
            JOIN information_schema.table_privileges p
              ON p.table_schema = c.table_schema AND p.table_name = c.table_name
             AND p.grantee = %s AND p.privilege_type = 'SELECT'
            GROUP BY 1, 2 ORDER BY 1, 2""", (user,)).fetchall()
    tables = "\n".join(f"{s}.{t}({cols})" for s, t, cols in rows)
    notes = (HERE / "sql-notes.md").read_text()
    if approach == "D":
        notes += "\n" + (HERE / "sql-enlaces-notes.md").read_text()
    return f"{notes}\n\nTablas:\n{tables}"


def run_sparql(query):
    r = requests.post(ONTOP, data={"query": query}, timeout=120,
                      headers={"Accept": "application/sparql-results+json"})
    if not r.ok:
        raise RuntimeError(r.text)
    data = r.json()
    var = data["head"]["vars"][0]
    return [b[var]["value"] if var in b else None for b in data["results"]["bindings"]]


APPROACHES = {k: (lambda q, kind, k=k: answer(k, q, kind)) for k in "ABC"}


# --- Preguntas libres para la interfaz -----------------------------

FREE_RULES = """La query puede devolver varias columnas, con nombres de variable claros en \
español (por ejemplo ?farmaco, ?ensayos). Limitá el resultado a 50 filas. No expliques \
nada: devolvé solo la query."""

# De qué fuente viene cada término de la ontología
NS = "https://w3id.org/rastro/ontology#"
TERM_SOURCE = {
    **{t: "aact" for t in ("Trial", "Sponsor", "nctId", "title", "phase", "status", "startDate",
                           "whyStopped", "sponsor", "industry", "condition")},
    **{t: "chembl" for t in ("Drug", "Target", "hasTarget", "gene", "approved", "chemblId")},
    **{t: "openfda" for t in ("YearlyReports", "ReportedReaction", "reports", "seriousReports",
                              "reaction", "year", "drug")},
    "within": "mesh",
    "testsDrug": "rastro",   # enlace de Rastro entre AACT y ChEMBL
    **{t: "rastro" for t in ("DrugLink", "linkTrial", "linkDrug", "interventionText", "matchedText", "linkRule")},
}


def ask_rastro(question):
    """Responde una pregunta libre con SPARQL sobre Rastro. Necesita un LLM configurado."""
    system = system_prompt("C").replace(QUERY_RULES, FREE_RULES)
    schema = output_schema("C", "lista")
    messages = [{"role": "user", "content": question}]
    attempts = []
    for _ in range(MAX_ATTEMPTS):
        assistant, data = ask(system, messages, schema)
        try:
            columns, rows = run_sparql_table(data["query"])
        except Exception as e:  # noqa: BLE001 - el error se le devuelve al modelo tal cual
            attempts.append({"query": data["query"], "error": str(e).strip()[:2000]})
            messages += [{"role": "assistant", "content": assistant},
                         {"role": "user", "content": retry_message(attempts[-1]["error"])}]
            continue
        attempts.append({"query": data["query"], "error": None})
        return {"query": data["query"], "columns": columns, "rows": rows, "attempts": attempts}
    return {"query": None, "columns": [], "rows": [], "attempts": attempts}


def run_sparql_table(query):
    """Ejecuta SPARQL en Ontop y devuelve (columnas, filas)."""
    r = requests.post(ONTOP, data={"query": query}, timeout=120,
                      headers={"Accept": "application/sparql-results+json"})
    if not r.ok:
        raise RuntimeError(r.text)
    data = r.json()
    columns = data["head"]["vars"]
    rows = [[b[c]["value"] if c in b else None for c in columns] for b in data["results"]["bindings"]]
    return columns, rows


def ontop_sql(query):
    """El SQL que Ontop genera y ejecuta en Postgres para una query SPARQL."""
    r = requests.get(ONTOP.replace("/sparql", "/ontop/reformulate"), params={"query": query}, timeout=60)
    r.raise_for_status()
    lines = r.text.splitlines()
    native = next((i for i, line in enumerate(lines) if line.strip().startswith("NATIVE")), None)
    return "\n".join(lines[native + 1:]).strip() if native is not None else r.text.strip()


def column_sources(query):
    """Fuentes de una query: (todas las que usa, las de cada columna del resultado).

    Una columna que es el objeto de un término (?farmaco en ?d :name ?farmaco) toma la
    fuente de ese término, o la de la clase del sujeto si el término es compartido
    (:name). Una columna calculada (COUNT, SUM) toma todas las fuentes de la query.
    """
    from rdflib import URIRef, Variable
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
    types = {s: str(o) for s, p, o in triples if str(p).endswith("#type") and isinstance(o, URIRef)}

    def direct_source(predicate):
        if str(predicate).endswith("rdf-schema#label"):
            return "mesh"
        return TERM_SOURCE.get(str(predicate).replace(NS, ""))

    def source_of(subject, predicate):
        """Fuente del término; si es compartido (:name), la de la clase del sujeto
        o, si la query no la declara, la de los otros términos del mismo sujeto."""
        found = direct_source(predicate)
        if found:
            return found
        cls = TERM_SOURCE.get(types.get(subject, "").replace(NS, ""))
        if cls:
            return cls
        others = {direct_source(p) for s, p, o in triples if s == subject} - {None, "rastro", "mesh"}
        return others.pop() if len(others) == 1 else None

    all_sources = {source_of(s, p) for s, p, o in triples} - {None}
    per_column = {}
    for var in algebra.get("PV", []):
        direct = {source_of(s, p) for s, p, o in triples if o == var} - {None}
        per_column[str(var)] = sorted(direct or all_sources)
    return sorted(all_sources), per_column
