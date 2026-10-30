"""The ways layer/answer.py reaches a model besides the Claude API: the OpenAI API (the request it sends, a refusal)
and files (a call written to a file, answered by an assistant without a key, and read back)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))
import answer  # noqa: E402

SCHEMA = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"],
          "additionalProperties": False}


class Reply:
    def __init__(self, message):
        self.message = message

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": self.message}]}


def test_openai_sends_the_schema_and_reads_the_json(monkeypatch):
    sent = {}

    def post(url, **kwargs):
        sent.update(url=url, **kwargs)
        return Reply({"content": '{"query": "SELECT 1"}'})
    monkeypatch.setattr(answer, "PROVIDER", "openai")
    monkeypatch.setattr(answer, "MODEL", "some-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setattr(answer.requests, "post", post)
    _, data = answer.ask("sistema", [{"role": "user", "content": "¿cuántas?"}], SCHEMA)
    assert data == {"query": "SELECT 1"}
    assert sent["url"] == "https://api.openai.com/v1/chat/completions"
    assert sent["json"]["messages"][0] == {"role": "system", "content": "sistema"}
    assert sent["json"]["response_format"]["json_schema"]["schema"] == SCHEMA


def test_openai_needs_a_model_and_says_a_refusal(monkeypatch):
    monkeypatch.setattr(answer, "PROVIDER", "openai")
    monkeypatch.setattr(answer, "MODEL", "")
    with pytest.raises(RuntimeError, match="RASTRO_MODEL"):
        answer.ask("s", [], SCHEMA)
    monkeypatch.setattr(answer, "MODEL", "some-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(answer.requests, "post", lambda url, **kw: Reply({"content": None, "refusal": "no"}))
    with pytest.raises(RuntimeError, match="rechazó"):
        answer.ask("s", [], SCHEMA)


def test_files_waits_for_the_reply_then_reads_it(monkeypatch, tmp_path):
    monkeypatch.setattr(answer, "PROVIDER", "files")
    monkeypatch.setenv("RASTRO_FILES", str(tmp_path))
    messages = [{"role": "user", "content": "¿cuántas concesiones?"}]
    with pytest.raises(answer.Pending) as pending:
        answer.ask("sistema", messages, SCHEMA)
    key = str(pending.value)
    prompt = (tmp_path / f"{key}.txt").read_text()
    assert "[system]\nsistema" in prompt and "¿cuántas concesiones?" in prompt and '"query"' in prompt
    (tmp_path / f"{key}.json").write_text(json.dumps({"query": "SELECT 2"}))
    assert answer.ask("sistema", messages, SCHEMA)[1] == {"query": "SELECT 2"}
    with pytest.raises(answer.Pending):   # another call is another file
        answer.ask("sistema", messages + [{"role": "user", "content": "¿y en 2024?"}], SCHEMA)


def test_a_recorded_call_is_made_once(monkeypatch, tmp_path):
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        return Reply({"content": '{"query": "SELECT 3"}'})
    monkeypatch.setattr(answer, "PROVIDER", "openai")
    monkeypatch.setattr(answer, "MODEL", "some-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("RASTRO_RECORD", str(tmp_path))
    monkeypatch.setattr(answer.requests, "post", post)
    for _ in range(2):
        assert answer.ask("s", [{"role": "user", "content": "q"}], SCHEMA)[1] == {"query": "SELECT 3"}
    assert len(calls) == 1 and len(list(tmp_path.glob("*.txt"))) == 1 and len(list(tmp_path.glob("*.json"))) == 1


def test_an_unknown_provider_says_so_at_once():
    import os
    import subprocess
    run = subprocess.run([sys.executable, "-c", "import answer"], cwd=ROOT / "layer", capture_output=True, text=True,
                         env={**os.environ, "RASTRO_PROVIDER": "claude"}, timeout=60)
    assert run.returncode != 0 and "RASTRO_PROVIDER=claude: use one of anthropic" in run.stderr


def test_a_text_where_a_number_was_asked_goes_back_to_the_model(monkeypatch):
    monkeypatch.setattr(answer, "run_sparql", lambda query, domain: ["YPF S.A."])
    result = answer.try_query("C", "SELECT ?x WHERE {}", "número", "energia")
    assert result["answer"] is None and "could not convert" in result["attempt"]["error"]
