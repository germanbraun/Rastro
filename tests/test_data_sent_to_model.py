"""docs/data-sent-to-model.md names every function that calls the language model: a new call fails here until the
page says what it sends."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = [p for folder in ("app", "layer", "lab", "linking", "ontology", "infra") for p in (ROOT / folder).rglob("*.py")]
CALL = re.compile(r"(?<![\w.])(?:answer\.)?ask\(")
DEF = re.compile(r"^\s*def (\w+)\(")


def callers():
    """(file, function) for every function whose body calls ask(…) or answer.ask(…), other than ask itself. Read as
    text, not parsed, so it does not depend on the Python version running the tests."""
    found = set()
    for path in CODE:
        function = None
        for line in path.read_text().splitlines():
            match = DEF.match(line)
            if match:
                function = match.group(1)
            elif CALL.search(line.split("#")[0]) and function not in (None, "ask", "ask_claude", "ask_ollama"):
                found.add((path.relative_to(ROOT).as_posix(), function))
    return found


def test_every_model_call_is_named_in_the_page():
    page = (ROOT / "docs/data-sent-to-model.md").read_text()
    missing = [f"{path} {name}" for path, name in callers() if f"`{path}` `{name}`" not in page]
    assert not missing, f"docs/data-sent-to-model.md does not say what these send: {missing}"


def test_the_known_calls_are_found():
    assert {("layer/chat.py", "write_query"), ("layer/chat.py", "write_answer"),
            ("layer/answer.py", "explain_query"), ("layer/answer.py", "ask_rastro")} <= callers()
