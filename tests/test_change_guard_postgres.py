"""Optional integration checks against a disposable database, never application data.

RASTRO_TEST_POSTGRES=1 python -m pytest tests/test_change_guard_postgres.py
Requires the repository's Postgres compose service to be running.
"""
import importlib.util
import os
import subprocess
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("postgres_guard", ROOT / "layer/change_guard.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
pytestmark = pytest.mark.skipif(os.environ.get("RASTRO_TEST_POSTGRES") != "1", reason="Requires local Postgres")


@pytest.fixture
def database(tmp_path, monkeypatch):
    name = "rastro_guard_test_" + uuid.uuid4().hex
    subprocess.run(guard.COMPOSE + ["exec", "-T", "postgres", "createdb", "-U", "rastro", name], check=True)
    monkeypatch.setenv("PG_DB", name)
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "STATE", tmp_path / "state")
    monkeypatch.setattr(guard, "FILES", [])
    try:
        guard.sql("""CREATE SCHEMA capitulo4; CREATE TABLE capitulo4.produccion (id text, prod_pet numeric);
INSERT INTO capitulo4.produccion VALUES ('a', 1.23456789012345), ('a', 1.23456789012345), ('b', NULL);
CREATE SCHEMA fractura; CREATE TABLE fractura.fractura (id text, cantidad_fracturas numeric);
INSERT INTO fractura.fractura VALUES ('4703', 18);
CREATE SCHEMA lab_gas;
CREATE TABLE lab_gas.corrida (id text, vigente boolean);
INSERT INTO lab_gas.corrida VALUES ('original', true), ('old', false);
CREATE TABLE lab_gas.prediccion (corrida text); INSERT INTO lab_gas.prediccion VALUES ('original');
CREATE TABLE lab_gas.entrada (corrida text); INSERT INTO lab_gas.entrada VALUES ('original');
CREATE TABLE lab_gas.aporte (corrida text); INSERT INTO lab_gas.aporte VALUES ('original');""")
        yield
    finally:
        subprocess.run(guard.COMPOSE + ["exec", "-T", "postgres", "dropdb", "-U", "rastro", name], check=True)


def test_exact_source_restoration_after_rename_and_unit_change(database):
    before = guard.sql("TABLE capitulo4.produccion")
    state = guard.snapshot("cambio")
    guard.sql("ALTER TABLE capitulo4.produccion RENAME COLUMN prod_pet TO petroleo; "
              "UPDATE capitulo4.produccion SET petroleo = petroleo * 6.2898")
    guard.restore_tables(state)
    assert guard.sql("TABLE capitulo4.produccion") == before
    guard.restore_tables(state)  # Crash recovery can be retried safely.
    assert guard.sql("TABLE capitulo4.produccion") == before


def test_impact_restores_original_run_flags_and_removes_test_runs(database):
    state = guard.snapshot("impacto")
    guard.sql("UPDATE fractura.fractura SET cantidad_fracturas = 30; "
              "UPDATE lab_gas.corrida SET vigente = false; "
              "INSERT INTO lab_gas.corrida VALUES ('test', true); "
              "INSERT INTO lab_gas.prediccion VALUES ('test'); "
              "INSERT INTO lab_gas.entrada VALUES ('test'); INSERT INTO lab_gas.aporte VALUES ('test')")
    guard.restore_tables(state)
    assert guard.sql("SELECT cantidad_fracturas FROM fractura.fractura") == "18"
    assert guard.sql("SELECT id FROM lab_gas.corrida WHERE vigente") == "original"
    for table in ("prediccion", "entrada", "aporte"):
        assert guard.sql(f"SELECT corrida FROM lab_gas.{table}") == "original"
    assert guard.sql("SELECT count(*) FROM lab_gas.corrida") == "2"


def test_failed_capture_never_leaves_partial_backup_or_mutates_source(database, monkeypatch):
    monkeypatch.setitem(guard.TABLES, "cambio", ["capitulo4.produccion", "missing.table"])
    before = guard.sql("TABLE capitulo4.produccion")
    with pytest.raises(subprocess.CalledProcessError):
        guard.snapshot("cambio")
    assert guard.sql("TABLE capitulo4.produccion") == before
    assert not guard.STATE.exists()
    assert guard.sql("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'rastro_test_%'") == "0"


def test_model_helpers_use_the_same_selected_database(database):
    import modelo
    selected = modelo.sql_local("SELECT current_database() AS name")
    assert selected.name.iloc[0] == os.environ["PG_DB"]
    modelo.sql_ejecutar("CREATE TABLE helper_probe (value int); INSERT INTO helper_probe VALUES (42);")
    assert guard.sql("SELECT value FROM helper_probe") == "42"


def test_recovery_refuses_a_different_database_configuration(database, monkeypatch):
    state = guard.snapshot("cambio")
    monkeypatch.setenv("PG_DB", "different_database")
    with pytest.raises(ValueError, match="configuration changed"):
        guard.restore_tables(state)
    assert guard.STATE.exists()
