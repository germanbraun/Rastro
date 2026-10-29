"""A conversation with the data, through Rastro's business dictionary (app: Preguntar → «Conversar con los datos»).

The context is the semantic layer itself: the query step reads the domain's ontology and its SPARQL notes (the same
system prompt as answer.ask_rastro, cached after the first question), so the model can only ask in the dictionary's
terms; the answer step reads only the query's result.

Each turn has three steps, as everything else in Rastro: narrow down, decide, test.
1. The model writes one SPARQL query over the domain's ontology, reading the conversation so far, so a follow-up
   («¿y Tecpetrol?») resolves against the earlier questions. If the data is not enough it says what is missing.
2. Rastro runs the query; an error goes back to the model, as in answer.ask_rastro.
3. The model answers in words from the result alone, and code checks every number of the answer against the result
   (unsupported_numbers): a number that is not there is flagged, never shown as if it were.
"""
import json
import math
import re

import answer

ANSWER_RULES = """Respondé la pregunta en una a tres oraciones, en {language}, usando solo el resultado de la \
consulta que sigue. Cada número que digas tiene que estar en el resultado (podés redondearlo o pasarlo a \
millones, como en «12,6 millones»). Si el resultado está vacío, decilo. No agregues datos que no estén en el \
resultado ni opiniones."""
FOLLOW_UP = """Es una conversación: la pregunta nueva puede referirse a las anteriores («¿y Tecpetrol?», «¿y en \
2024?»). Resolvé a qué se refiere con lo que se preguntó antes y escribí una consulta completa."""
LANGUAGES = {"es": "español", "en": "inglés"}
MAX_ROWS = 50          # the answer step reads at most this many rows
NUMBER = re.compile(r"(?<![\w.,])\d[\d.,]*")


def history_messages(history):
    """Earlier turns as the conversation the query step reads: each question, and the query and answer it got."""
    messages = []
    for turn in history:
        said = turn.get("answer") or f"SIN DATOS: {turn.get('sin_datos')}"
        messages += [{"role": "user", "content": turn["question"]},
                     {"role": "assistant", "content": json.dumps({"query": turn.get("query") or said}, ensure_ascii=False)
                      + f"\nRespuesta dada: {said}"}]
    return messages


def write_query(question, history, domain):
    """Step 1 and 2: the query for the new question, run over Rastro, with retries. Returns the turn so far."""
    system = answer.system_prompt("C", domain).replace(answer.QUERY_RULES, answer.FREE_RULES) + "\n\n" + FOLLOW_UP
    schema = answer.output_schema("C", "lista")
    messages = history_messages(history) + [{"role": "user", "content": question}]
    attempts = []
    for _ in range(answer.MAX_ATTEMPTS):
        assistant, data = answer.ask(system, messages, schema)
        reason = answer.sin_datos(data["query"])
        if reason:
            return {"question": question, "query": None, "sin_datos": reason, "attempts": attempts}
        try:
            columns, rows = answer.run_sparql_table(data["query"], domain)
        except Exception as error:  # noqa: BLE001 - the error is returned to the model as is
            attempts.append({"query": data["query"], "error": str(error).strip()[:2000]})
            messages += [{"role": "assistant", "content": json.dumps(data, ensure_ascii=False)},
                         {"role": "user", "content": answer.retry_message(attempts[-1]["error"])}]
            continue
        attempts.append({"query": data["query"], "error": None})
        return {"question": question, "query": data["query"], "columns": columns, "rows": rows, "attempts": attempts}
    return {"question": question, "query": None, "attempts": attempts, "failed": True}


def write_answer(turn, domain, language):
    """Step 3: the answer in words, from the result rows only."""
    system = answer.DOMAINS[domain]["base"] + "\n\n" + ANSWER_RULES.format(language=LANGUAGES[language])
    table = json.dumps({"columnas": turn["columns"], "filas": turn["rows"][:MAX_ROWS]}, ensure_ascii=False, default=str)
    messages = [{"role": "user", "content": f"Pregunta: {turn['question']}\n\nResultado de la consulta:\n{table}"}]
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"],
              "additionalProperties": False}
    _, data = answer.ask(system, messages, schema)
    return data["answer"].strip()


def parse_number(text):
    """A number as written in Spanish (12.345,6) or English (12,345.6); None if it is not one."""
    text = text.rstrip(".,")
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
    elif "," in text:   # 12,6 (decimal) or 12,345 (thousands)
        text = text.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", text) else text.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def decimals(text):
    """How many decimals a written number shows (12,6 → 1)."""
    match = re.search(r"[.,](\d{1,2})$", text.rstrip(".,"))
    return len(match.group(1)) if match and not re.fullmatch(r"\d{1,3}([.,]\d{3})+", text.rstrip(".,")) else 0


def supported(value, places, sources):
    """True if a written number is one of the sources, as is, rounded, or in thousands, millions or billions."""
    for source in sources:
        for scale in (1, 1e3, 1e6, 1e9, 0.01):   # 0.01: a share written as a percentage
            if math.isclose(value, round(source / scale, places), rel_tol=1e-9, abs_tol=0.5 * 10 ** -places):
                return True
    return False


def unsupported_numbers(text, turn, history=()):
    """The numbers of an answer that do not come from its result (a value, or a number inside a text cell such as a
    date or an id), nor from the questions (a year), nor the row count. Empty: every number is backed by the data."""
    cells = [v for row in turn.get("rows", []) for v in row]
    sources = [float(v) for v in cells if _numeric(v)]
    sources += [n for v in cells if isinstance(v, str) for n in map(parse_number, NUMBER.findall(v)) if n is not None]
    sources += [len(turn.get("rows", []))]
    asked = " ".join([turn["question"], *(t["question"] for t in history)])
    sources += [n for n in (parse_number(m) for m in NUMBER.findall(asked)) if n is not None]
    unsupported = []
    for written in NUMBER.findall(text):
        value = parse_number(written)
        if value is not None and not supported(value, decimals(written), sources):
            unsupported.append(written.rstrip(".,"))
    return unsupported


def _numeric(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def turn(question, history, domain, language="es"):
    """One turn of the conversation: the query, its result, the answer in words and the numbers it could not back."""
    result = write_query(question, history, domain)
    if result.get("query"):
        result["answer"] = write_answer(result, domain, language)
        result["unsupported"] = unsupported_numbers(result["answer"], result, history)
    return result
