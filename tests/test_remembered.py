"""When the database stops answering, what was already read keeps showing (app/dominio/common.py remembered)."""
import sys
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "layer"))
from dominio import common  # noqa: E402


def down():
    raise psycopg.OperationalError("the database is not answering")


def test_the_last_value_is_served_when_the_database_stops():
    assert common.remembered(("test", 1), lambda: "v1") == "v1"
    assert common.remembered(("test", 1), down) == "v1"
    assert common.remembered(("test", 1), lambda: "v2") == "v2"   # back up: the new value


def test_nothing_read_before_still_fails():
    with pytest.raises(psycopg.OperationalError):
        common.remembered(("test", "never read"), down)
