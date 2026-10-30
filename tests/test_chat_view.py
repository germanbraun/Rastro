"""The chat in the app when the model fails: the user sees plain words (and the error only in the technical view), not
a trace, and the failed question is not added to the conversation."""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "layer"))


@pytest.mark.parametrize("technical", [False, True])
def test_a_model_failure_is_said_in_plain_words(technical):
    script = f'''
from unittest.mock import patch
from dominio import chat_view, common
import chat

def fails(*args):
    raise RuntimeError("API error 500")

with patch.object(common, "llm_status", lambda: (True, "test")), patch.object(chat, "turn", fails):
    chat_view.show_chat({{"domain": "energia"}}, {technical!r})
'''
    app = AppTest.from_string(script).run(timeout=15)
    app.chat_input[0].set_value("¿Cuánto gas?").run(timeout=15)
    assert not app.exception, [error.message for error in app.exception]
    warnings = [w.value for w in app.warning]
    assert any("no respondió" in w and "¿Cuánto gas?" in w for w in warnings), warnings
    assert any("API error 500" in c.value for c in app.caption) == technical
    assert app.session_state["energia_chat"] == []   # the failed question is not part of the conversation
