"""Tres formas de que un LLM responda una pregunta de negocio.

  A. solo:   el LLM responde con lo que sabe, sin acceso a datos
  B. sql:    el LLM escribe SQL sobre las tablas de las fuentes tal como se cargaron
  C. rastro: el LLM escribe SPARQL sobre la ontología de Rastro (Ontop)
  D. sql + enlaces: el LLM escribe SQL sobre las mismas tablas, más las tablas de enlaces
             de Rastro, documentadas. Es la línea de base justa: los mismos datos que C,
             sin la capa semántica

Las tres usan el mismo modelo, las mismas instrucciones de base y, para B y C, los
mismos reintentos: si la query falla, el LLM ve el error y tiene dos intentos más.

Lo propio de cada dominio (oncología, proveedores) está en dominios.yaml; cada función
recibe el dominio y, si no se dice, usa oncología.

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
import yaml

PROVIDER = os.environ.get("RASTRO_PROVIDER") or "anthropic"
MODEL = os.environ.get("RASTRO_MODEL") or {"anthropic": "claude-opus-5-5",
                                           "ollama": "qwen2.5-coder:7b"}[PROVIDER]
OLLAMA = os.environ.get("OLLAMA_URL") or "http://host.docker.internal:11434"
MAX_ATTEMPTS = 3
ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).parent
DOMAINS = yaml.safe_load((HERE / "dominios.yaml").read_text())

# Cuando los datos no alcanzan, el LLM lo dice en lugar de inventar una query
SIN_DATOS = "SIN DATOS:"
NO_DATA_RULE = """Si los datos no alcanzan para responder (falta el período, la medida o el tema), no \
inventes una query: devolvé en su lugar una sola línea que empiece con «SIN DATOS:» y diga qué falta."""

QUERY_RULES = """La query tiene que devolver una sola columna: los nombres si la respuesta \
es una lista, o una sola fila con el número si la respuesta es un número. No expliques \
nada: devolvé solo la query. """ + NO_DATA_RULE


# --- Qué recibe el LLM en cada enfoque ----------------------------

def system_prompt(approach, domain="oncologia"):
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

def answer(approach, question, kind, domain="oncologia"):
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


def explain_query(query, sql, domain="oncologia"):
    """Explica en palabras simples una consulta SPARQL y el SQL que generó Ontop, para alguien que
    sabe SQL pero no tecnologías semánticas. Devuelve viñetas en Markdown."""
    system = ("Explicás consultas a una persona de negocio que sabe SQL pero no conoce tecnologías "
              "semánticas. En español, en 3 a 5 viñetas cortas: qué busca, qué une o filtra, qué "
              "devuelve, y qué habría que hacer a mano en SQL que acá ya resuelve el diccionario de "
              "negocio. Sin jerga: no digas RDF, tripletas ni IRI.\n\n" + (ROOT / DOMAINS[domain]["sparql_notes"]).read_text())
    content = f"Consulta SPARQL:\n{query}" + (f"\n\nSQL que generó Ontop:\n{sql}" if sql else "")
    _, data = ask(system, [{"role": "user", "content": content}],
                  {"type": "object", "properties": {"explicacion": {"type": "string"}},
                   "required": ["explicacion"], "additionalProperties": False})
    return data["explicacion"]


def retry_message(error):
    return f"La query falló con este error:\n{error}\n\nCorregila."


def try_query(approach, query, kind, domain="oncologia"):
    """Ejecuta la query de B (SQL) o C (SPARQL) y devuelve la respuesta o el error."""
    if sin_datos(query):
        return {"answer": None, "attempt": {"query": query, "error": None}}
    try:
        column = run_sparql(query, domain) if approach == "C" else run_sql(query, approach, domain)
    except Exception as e:  # noqa: BLE001 - el error se le devuelve al modelo tal cual
        return {"answer": None, "attempt": {"query": query, "error": str(e).strip()[:2000]}}
    return {"answer": to_answer(column, kind), "attempt": {"query": query, "error": None}}


def sin_datos(query):
    """El LLM dijo que los datos no alcanzan (devuelve el motivo) o escribió una query (None)."""
    text = (query or "").strip()
    return text[len(SIN_DATOS):].strip() or "los datos no alcanzan" if text.upper().startswith(SIN_DATOS) else None


def to_answer(column, kind):
    if kind == "número":
        return float(column[0]) if column and column[0] is not None else None
    return [str(v) for v in column if v is not None]


# --- Dónde corren las queries --------------------------------------

# B ve las fuentes tal como se cargaron; D, además, las tablas de enlaces de Rastro
# (los usuarios de cada dominio están en dominios.yaml)
READER = "host=postgres port=5432 dbname=%s user={0} password={0}"


def run_sql(query, approach="B", domain="oncologia"):
    user = DOMAINS[domain]["readers"][approach]
    with psycopg.connect(READER.format(user) % os.environ["PG_DB"]) as conn:
        return [row[0] for row in conn.execute(query).fetchall()]


def sql_schema(approach="B", domain="oncologia"):
    """El esquema de las tablas que ve el usuario de solo lectura, con su documentación."""
    d = DOMAINS[domain]
    user = d["readers"][approach]
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
    notes = (ROOT / d["sql_notes"]).read_text()
    if approach == "D":
        notes += "\n" + (ROOT / d["links_notes"]).read_text()
    return f"{notes}\n\nTablas:\n{tables}"


def run_sparql(query, domain="oncologia"):
    r = requests.post(DOMAINS[domain]["ontop"], data={"query": query}, timeout=120,
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
nada: devolvé solo la query. """ + NO_DATA_RULE

# De qué fuente viene cada término de la ontología (dominios.yaml)
def term_sources(domain="oncologia"):
    return {term: source for source, terms in DOMAINS[domain]["term_sources"].items() for term in terms}



def ask_rastro(question, domain="oncologia"):
    """Responde una pregunta libre con SPARQL sobre Rastro. Necesita un LLM configurado."""
    system = system_prompt("C", domain).replace(QUERY_RULES, FREE_RULES)
    schema = output_schema("C", "lista")
    messages = [{"role": "user", "content": question}]
    attempts = []
    for _ in range(MAX_ATTEMPTS):
        assistant, data = ask(system, messages, schema)
        if sin_datos(data["query"]):
            return {"query": None, "columns": [], "rows": [], "attempts": attempts, "sin_datos": sin_datos(data["query"])}
        try:
            columns, rows = run_sparql_table(data["query"], domain)
        except Exception as e:  # noqa: BLE001 - el error se le devuelve al modelo tal cual
            attempts.append({"query": data["query"], "error": str(e).strip()[:2000]})
            messages += [{"role": "assistant", "content": assistant},
                         {"role": "user", "content": retry_message(attempts[-1]["error"])}]
            continue
        attempts.append({"query": data["query"], "error": None})
        return {"query": data["query"], "columns": columns, "rows": rows, "attempts": attempts}
    return {"query": None, "columns": [], "rows": [], "attempts": attempts}


def run_sparql_table(query, domain="oncologia"):
    """Ejecuta SPARQL en Ontop y devuelve (columnas, filas)."""
    r = requests.post(DOMAINS[domain]["ontop"], data={"query": query}, timeout=120,
                      headers={"Accept": "application/sparql-results+json"})
    if not r.ok:
        raise RuntimeError(r.text)
    data = r.json()
    columns = data["head"]["vars"]
    rows = [[b[c]["value"] if c in b else None for c in columns] for b in data["results"]["bindings"]]
    return columns, rows


def ontop_sql(query, domain="oncologia"):
    """El SQL que Ontop genera y ejecuta en Postgres para una query SPARQL."""
    r = requests.get(DOMAINS[domain]["ontop"].replace("/sparql", "/ontop/reformulate"),
                     params={"query": query}, timeout=60)
    r.raise_for_status()
    lines = r.text.splitlines()
    native = next((i for i, line in enumerate(lines) if line.strip().startswith("NATIVE")), None)
    return "\n".join(lines[native + 1:]).strip() if native is not None else r.text.strip()


def column_sources(query, domain="oncologia"):
    """Fuentes de una query: (todas las que usa, las de cada columna del resultado).

    Una columna que es el objeto de un término (?farmaco en ?d :name ?farmaco) toma la
    fuente de ese término, o la de la clase del sujeto si el término es compartido
    (:name). Una columna calculada (COUNT, SUM) toma todas las fuentes de la query.
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
    link_from = {}   # término de un enlace de Rastro → las fuentes de las que sale
    for source, terms in DOMAINS[domain].get("link_sources", {}).items():
        for term in terms:
            link_from.setdefault(term, set()).add(source)
    types = {s: str(o) for s, p, o in triples if str(p).endswith("#type") and isinstance(o, URIRef)}

    def direct_source(predicate):
        if str(predicate).endswith("rdf-schema#label"):
            return "mesh"
        return sources_of_term.get(str(predicate).replace(ns, ""))

    def source_of(subject, predicate):
        """Fuente del término; si es compartido (:name), la de la clase del sujeto
        o, si la query no la declara, la de los otros términos del mismo sujeto."""
        found = direct_source(predicate)
        if found:
            return found
        cls = sources_of_term.get(types.get(subject, "").replace(ns, ""))
        if cls:
            return cls
        others = {direct_source(p) for s, p, o in triples if s == subject} - {None, "rastro", "mesh"}
        return others.pop() if len(others) == 1 else None

    def steps(predicate):
        """Los términos de un camino (:supplier/:group) o el término solo."""
        return [x for a in predicate.args for x in steps(a)] if hasattr(predicate, "args") else [predicate]

    def sources_for(subject, predicate):
        """La fuente del término y, si es un enlace de Rastro, también las fuentes de las que sale el enlace."""
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
