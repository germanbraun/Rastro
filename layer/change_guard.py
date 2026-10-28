"""Preserve exact change-test inputs. Recovery data survives an interrupted runner.

Use: python layer/change_guard.py run cambio|correccion|impacto [domain]   (domain defaults to energia)
     python layer/change_guard.py recover
Internal: restore-source restores the source and mapping between cambio acts.
Run only on an isolated development database, with other writers stopped.
What each test may change comes from the domain's method.change_guard entry in layer/dominios.yaml (files, and
tables per test, and the column the cambio test renames); the linker and Ontop to rebuild, and the folder with the
test scripts, from the same method block.
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

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/cache/change-test-guard"
COMPOSE = ["docker", "compose", "-f", str(ROOT / "infra/docker-compose.yml")]
DOMAIN, FILES, TABLES, RENAMED, LINKER, ONTOP, SCRIPTS = None, [], {}, None, None, None, None


def configure(domain):
    """Read what the domain's change tests may change, and what to rebuild, from the registry."""
    global DOMAIN, FILES, TABLES, RENAMED, LINKER, ONTOP, SCRIPTS
    method = yaml.safe_load((ROOT / "layer/dominios.yaml").read_text())[domain]["method"]
    guard = method["change_guard"]
    DOMAIN, FILES, TABLES, RENAMED = domain, guard["files"], guard["tables"], guard.get("renamed")
    LINKER, ONTOP = method["linker"]["service"], method["ontop"]["service"]
    SCRIPTS = method["change_tests"]


configure("energia")


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
        if only_mapping and name != state["files"][0]:
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


def has_column(table, column):
    schema, name = table.split(".")
    return sql(f"SELECT count(*) FROM information_schema.columns WHERE table_schema='{schema}' "
               f"AND table_name='{name}' AND column_name='{column}'") == "1"


def snapshot(kind):
    if kind == "cambio" and RENAMED and not has_column(RENAMED["table"], RENAMED["column"]):
        raise ValueError(f"Expected {RENAMED['column']} column before mutation; recover earlier changes first")
    STATE.mkdir()  # Never overwrite an unfinished recovery.
    state = {"kind": kind, "domain": DOMAIN, "renamed": RENAMED if kind == "cambio" else None,
             "schema": "rastro_test_" + uuid.uuid4().hex, "tables": TABLES[kind],
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
    renamed = state.get("renamed")
    tables = state["tables"]
    if source_only:
        tables = [t for t in tables if renamed and t == renamed["table"]]
    if not tables:
        return
    schema = state["schema"]
    statements = []
    if renamed and renamed["table"] in tables:
        table_schema, table_name = renamed["table"].split(".")
        statements.append(f"""DO $$ BEGIN
IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{table_schema}'
AND table_name='{table_name}' AND column_name='{renamed["to"]}') THEN
ALTER TABLE {renamed["table"]} RENAME COLUMN {renamed["to"]} TO {renamed["column"]};
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
    subprocess.run(COMPOSE + ["run", "--rm", LINKER], check=True)
    subprocess.run(COMPOSE + ["restart", ONTOP], check=True)
    container = subprocess.check_output(COMPOSE + ["ps", "-aq", ONTOP], text=True).strip()
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
    ports = config["services"].get(ONTOP, {}).get("ports", [])   # services behind a profile are not listed
    if ports:
        os.environ[f"ONTOP_{DOMAIN.upper()}_PORT"] = str(ports[0]["published"])


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
        if args == ["recover"]:
            state = json.loads((STATE / "state.json").read_text())
            configure(state.get("domain", "energia"))
            configure_database()
            recover(state)
            return
        if len(args) not in (2, 3) or args[0] != "run":
            raise ValueError(__doc__)
        configure(args[2] if len(args) == 3 else "energia")
        if args[1] not in TABLES:
            raise ValueError(__doc__)
        configure_database()
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
            process = subprocess.Popen(["bash", str(ROOT / SCRIPTS / f"{kind}.sh"), "registrar"],
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
