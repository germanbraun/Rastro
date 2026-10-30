"""infra/customer/restore.sh, with a stand-in for docker: when the restore fails, the services it stopped (the proxy
included, from the customer compose file on an installation) start again, so a failed restore does not leave the customer without Rastro."""
import hashlib
import os
import subprocess
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FAKE_DOCKER = """#!/bin/sh
echo "$@" >> "$DOCKER_LOG"
case "$*" in
  *" ps "*) printf 'app\\nontop-energia\\nproxy\\npostgres\\n' ;;
  *pg_restore*) exit 1 ;;
esac
"""


@pytest.mark.parametrize("installed", [True, False])
def test_a_failed_restore_starts_the_services_again(tmp_path, installed):
    backup = tmp_path / "backup-1"
    backup.mkdir()
    (backup / "database.dump").write_bytes(b"not a dump")
    with tarfile.open(backup / "state.tar.gz", "w:gz"):
        pass
    sums = "".join(f"{hashlib.sha256((backup / f).read_bytes()).hexdigest()}  {f}\n"
                   for f in ("database.dump", "state.tar.gz"))
    (backup / "SHA256SUMS").write_text(sums)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text(FAKE_DOCKER)
    (bin_dir / "docker").chmod(0o755)
    # A customer installation has its passwords in .env; the demo machine does not
    (tmp_path / ".env").write_text("PG_USER=rastro\n" + ("RASTRO_READONLY_PASSWORD=set\n" if installed else ""))
    log = tmp_path / "docker.log"
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "DOCKER_LOG": str(log),
           "RASTRO_ENV_FILE": str(tmp_path / ".env")}
    run = subprocess.run(["bash", str(ROOT / "infra/customer/restore.sh"), str(backup)], input="backup-1\n",
                         env=env, capture_output=True, text=True, timeout=60)
    calls = log.read_text().splitlines()
    assert run.returncode != 0                                      # the restore failed …
    assert any("docker-compose.customer.yml" in c for c in calls) == installed   # … with the customer file if installed …
    stop = next(c for c in calls if " stop " in c)
    start = next(c for c in calls if " start " in c)                # … and what it stopped started again
    assert stop.split(" stop ")[1] == start.split(" start ")[1] == "app ontop-energia proxy"
