"""The chat over the semantic layer (layer/chat.py), with the model and Ontop replaced: the flow and the number check."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))
import chat  # noqa: E402

TURN = {"question": "¿Cuánto petróleo de 2025 le corresponde a YPF?", "rows": [["YPF S.A.", 12570093.35, 0.55]]}


def test_numbers_backed_by_the_result_rounded_or_scaled():
    assert chat.unsupported_numbers("A YPF le corresponden 12,6 millones de m³ en 2025, el 55 %.", TURN) == []
    assert chat.unsupported_numbers("YPF has 12.57 million m³ (12,570,093 m³).", TURN) == []


def test_a_number_not_in_the_result_is_flagged():
    assert chat.unsupported_numbers("A YPF le corresponden 14,2 millones de m³.", TURN) == ["14,2"]


def test_the_query_step_reads_the_ontology_and_the_conversation(monkeypatch):
    seen = {}

    def ask(system, messages, schema):
        seen.update(system=system, messages=messages)
        return None, {"query": "SELECT ?x WHERE {}"}
    monkeypatch.setattr(chat.answer, "ask", ask)
    monkeypatch.setattr(chat.answer, "run_sparql_table", lambda query, domain: (["x"], [["1"]]))
    earlier = [{**TURN, "query": "SELECT 1", "answer": "12,6 millones de m³."}]
    chat.write_query("¿y Tecpetrol?", earlier, "energia")
    assert (ROOT / "ontology/energia/energia.ttl").read_text()[:200] in seen["system"]
    assert [m["role"] for m in seen["messages"]] == ["user", "assistant", "user"]
    assert seen["messages"][0]["content"] == TURN["question"] and seen["messages"][-1]["content"] == "¿y Tecpetrol?"


def test_a_failing_query_goes_back_to_the_model(monkeypatch):
    queries = iter(["BAD", "SELECT ?x WHERE {}"])
    monkeypatch.setattr(chat.answer, "ask", lambda system, messages, schema: (None, {"query": next(queries)}))

    def run(query, domain):
        if query == "BAD":
            raise RuntimeError("syntax error")
        return ["x"], [["1"]]
    monkeypatch.setattr(chat.answer, "run_sparql_table", run)
    turn = chat.write_query("¿Cuántas concesiones hay?", [], "energia")
    assert turn["query"] == "SELECT ?x WHERE {}" and [a["error"] for a in turn["attempts"]] == ["syntax error", None]


def test_without_data_it_says_what_is_missing(monkeypatch):
    monkeypatch.setattr(chat.answer, "ask", lambda *a: (None, {"query": "SIN DATOS: no hay precios"}))
    turn = chat.turn("¿Cuánto vale el barril?", [], "energia")
    assert turn["query"] is None and turn["sin_datos"] == "no hay precios" and "answer" not in turn


def test_a_turn_answers_in_words_and_checks_them(monkeypatch):
    replies = iter([{"query": "SELECT ?e ?p WHERE {}"}, {"answer": "A YPF le corresponden 14,2 millones de m³."}])
    monkeypatch.setattr(chat.answer, "ask", lambda system, messages, schema: (None, next(replies)))
    monkeypatch.setattr(chat.answer, "run_sparql_table", lambda q, d: (["e", "p"], TURN["rows"]))
    turn = chat.turn(TURN["question"], [], "energia")
    assert turn["answer"].startswith("A YPF") and turn["unsupported"] == ["14,2"]
    assert json.loads(chat.history_messages([turn])[1]["content"].split("\n")[0])["query"] == "SELECT ?e ?p WHERE {}"
