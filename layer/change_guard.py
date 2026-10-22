"""Preserve exact change-test inputs. Recovery data survives an interrupted runner.

Use: python layer/change_guard.py run cambio|correccion|impacto
     python layer/change_guard.py recover
Internal: restore-source restores the source and mapping between cambio acts.
Run only on an isolated development database, with other writers stopped.
"""
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/cache/change-test-guard"
COMPOSE = ["docker", "compose", "-f", str(ROOT / "infra/docker-compose.yml")]
FILES = ["mappings/energia.r2rml.ttl", "linking/energia/participaciones-revisadas.csv", "layer/energia/respuestas"]
TABLES = {
    "cambio": ["capitulo4.produccion"],
    "correccion": [],
    "impacto": ["fractura.fractura", "lab_gas.corrida", "lab_gas.prediccion", "lab_gas.entrada", "lab_gas.aporte"],
}


def sql(query):
    return subprocess.check_output(COMPOSE + ["exec", "-T", "postgres", "psql", "-X", "-U",
                                   os.environ.get("PG_USER", "rastro"), "-d", os.environ.get("PG_DB", "rastro"),
                                   "-v", "ON_ERROR_STOP=1", "-At", "-c", query], text=True).strip()


def tree(path):
    if path.is_symlink():
        raise ValueError(f"Refusing to snapshot symlinks: {path}")
    if not path.exists():
        return None
    if (path.is_dir() and any(p.is_symlink() for p in path.rglob("*"))):
        raise ValueError(f"Refusing to snapshot symlinks: {path}")
    if path.is_file():
        return path.read_bytes()
    return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def save_files(state):
    for index, name in enumerate(FILES):
        source = ROOT / name
        tree(source)  # Reject symlinks before following any path.
        destination = STATE / f"file{index}"
        if source.is_dir():
            shutil.copytree(source, destination)
        elif source.exists():
            shutil.copy2(source, destination)
    state["files"] = FILES


def restore_files(state, only_mapping=False):
    for index, name in enumerate(state["files"]):
        if only_mapping and name != FILES[0]:
            continue
        target, saved = ROOT / name, STATE / f"file{index}"
        if tree(target) == tree(saved):
            continue
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        if saved.is_dir():
            shutil.copytree(saved, target)
        elif saved.exists():
            shutil.copy2(saved, target)
        if tree(target) != tree(saved):
            raise RuntimeError(f"File restoration differs: {name}")


def snapshot(kind):
    if kind == "cambio":
        count = sql("SELECT count(*) FROM information_schema.columns WHERE table_schema='capitulo4' "
                    "AND table_name='produccion' AND column_name='prod_pet'")
        if count != "1":
            raise ValueError("Expected prod_pet column before mutation; recover earlier changes first")
    STATE.mkdir()  # Never overwrite an unfinished recovery.
    state = {"kind": kind, "schema": "rastro_test_" + uuid.uuid4().hex, "tables": TABLES[kind],
             "database": os.environ.get("PG_DB", "rastro"), "user": os.environ.get("PG_USER", "rastro")}
    save_files(state)
    schema = state["schema"]
    statements = [f"CREATE SCHEMA {schema}"]
    for index, table in enumerate(state["tables"]):
        statements.append(f"CREATE TABLE {schema}.t{index} AS TABLE {table}")
    # One transaction: a failed capture cannot leave a partial database snapshot.
    try:
        sql("BEGIN; " + "; ".join(statements) + "; COMMIT;")
    except Exception:
        shutil.rmtree(STATE)  # No source mutation has run; transaction rolled back.
        raise
    (STATE / "state.json").write_text(json.dumps(state))
    return state


def restore_tables(state, source_only=False):
    if (state["database"] != os.environ.get("PG_DB", "rastro")
            or state["user"] != os.environ.get("PG_USER", "rastro")):
        raise ValueError("Database configuration changed since snapshot; restore the original settings first")
    tables = state["tables"]
    if source_only:
        tables = [t for t in tables if t == "capitulo4.produccion"]
    if not tables:
        return
    schema = state["schema"]
    statements = []
    if "capitulo4.produccion" in tables:
        statements.append("""DO $$ BEGIN
IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='capitulo4'
AND table_name='produccion' AND column_name='petroleo') THEN
ALTER TABLE capitulo4.produccion RENAME COLUMN petroleo TO prod_pet;
END IF; END $$""")
    statements.append("TRUNCATE " + ", ".join(tables))
    for table in tables:
        index = state["tables"].index(table)
        statements.append(f"INSERT INTO {table} SELECT * FROM {schema}.t{index}")
        statements.append(f"""DO $$ BEGIN IF EXISTS (
(TABLE {table} EXCEPT ALL TABLE {schema}.t{index}) UNION ALL
(TABLE {schema}.t{index} EXCEPT ALL TABLE {table})) THEN
RAISE EXCEPTION 'Restoration differs: {table}'; END IF; END $$""")
    sql("BEGIN; " + "; ".join(statements) + "; COMMIT;")


def rebuild():
    subprocess.run(COMPOSE + ["run", "--rm", "energia-linker"], check=True)
    subprocess.run(COMPOSE + ["restart", "ontop-energia"], check=True)
    container = subprocess.check_output(COMPOSE + ["ps", "-aq", "ontop-energia"], text=True).strip()
    for _ in range(90):
        status = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Health.Status}}", container], text=True).strip()
        if status == "healthy":
            return
        time.sleep(2)
    raise RuntimeError("Restored inputs but Ontop did not become healthy; recovery data retained")


def recover(state):
    restore_files(state)
    restore_tables(state)
    rebuild()
    sql(f"DROP SCHEMA {state['schema']} CASCADE")
    shutil.rmtree(STATE)
    print("Original inputs and model runs restored; rebuilt layer is healthy")


def configure_database():
    # Read only required runtime metadata; never log compose configuration or credentials.
    config = json.loads(subprocess.check_output(COMPOSE + ["config", "--format", "json"], text=True))
    postgres = config["services"]["postgres"]["environment"]
    os.environ["PG_DB"] = str(postgres["POSTGRES_DB"])
    os.environ["PG_USER"] = str(postgres["POSTGRES_USER"])
    ports = config["services"]["ontop-energia"].get("ports", [])
    if ports:
        os.environ["ONTOP_ENERGIA_PORT"] = str(ports[0]["published"])


def main():
    args = sys.argv[1:]
    if args == ["restore-source"]:
        if not os.environ.get("RASTRO_CHANGE_GUARD"):
            raise ValueError("restore-source requires a guarded run")
        state = json.loads((STATE / "state.json").read_text())
        restore_files(state, only_mapping=True)
        restore_tables(state, source_only=True)
        return
    lock_path = STATE.parent / "change-test.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        configure_database()
        if args == ["recover"]:
            recover(json.loads((STATE / "state.json").read_text()))
            return
        if len(args) != 2 or args[0] != "run" or args[1] not in TABLES:
            raise ValueError(__doc__)
        if STATE.exists():
            raise ValueError("Unfinished recovery exists; inspect it and run change_guard.py recover first")
        kind = args[1]
        state = snapshot(kind)
        child_env = {**os.environ, "RASTRO_CHANGE_GUARD": str(STATE)}
        process = None

        def interrupted(signum, _frame):
            if process is not None:
                os.killpg(process.pid, signum)
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        code = 1
        try:
            process = subprocess.Popen(["bash", str(ROOT / f"layer/energia/cambio/{kind}.sh"), "registrar"],
                                       env=child_env, start_new_session=True)
            code = process.wait()
        finally:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            # Do not let a second terminal signal interrupt restoration.
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                recover(state)
            except Exception:
                print(f"RESTORATION FAILED. Keep {STATE}; run: python3 layer/change_guard.py recover", file=sys.stderr)
                raise
        raise SystemExit(code)


if __name__ == "__main__":
    main()
