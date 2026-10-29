"""Checks that the customer setup took effect (docs/customer-deployment.md, section 2.2), on the running services.

    python3 infra/customer/check.py

Each point prints ✅ or ❌ with what it found; it exits with an error if any fails. With RASTRO_LOGIN_PASSWORD in the
environment (never in .env), it also logs in through the proxy.
"""
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = Path(os.environ.get("RASTRO_ENV_FILE") or ROOT / ".env")   # another file only to try the setup
COMPOSE = ["docker", "compose", "--env-file", str(ENV_FILE), "-f", str(ROOT / "infra/docker-compose.yml"),
           "-f", str(ROOT / "infra/docker-compose.customer.yml")]
DEFAULTS = {"PG_PASSWORD": "rastro"}


def env():
    """.env as a dictionary (quotes removed); the process environment wins."""
    values = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return {**values, **{k: v for k, v in os.environ.items() if k.startswith(("RASTRO_", "PG_"))}}


def containers():
    """Each running service and its inspection (environment and published ports)."""
    ids = subprocess.run(COMPOSE + ["ps", "-q"], capture_output=True, text=True, check=True).stdout.split()
    found = json.loads(subprocess.run(["docker", "inspect", *ids], capture_output=True, text=True, check=True).stdout)
    return {c["Config"]["Labels"]["com.docker.compose.service"]: c for c in found}


def psql(user, password, sql):
    """Runs sql as user over the Docker network, as the other services connect: inside the container, 127.0.0.1 is
    trusted without a password (pg_hba.conf), so it would prove nothing. True if it worked."""
    cmd = COMPOSE + ["exec", "-T", "-e", f"PGPASSWORD={password}", "postgres", "psql", "-h", "postgres",
                     "-U", user, "-d", env().get("PG_DB", "rastro"), "-v", "ON_ERROR_STOP=1", "-qc", sql]
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


def https(path, user=None, password=None):
    """The proxy's HTTP status for path (Caddy's own certificate is accepted: it is checked by the browser)."""
    port = env().get("RASTRO_HTTPS_PORT", "8443")
    request = urllib.request.Request(f"https://localhost:{port}{path}")
    if user:
        import base64
        request.add_header("Authorization", "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode())
    try:
        return urllib.request.urlopen(request, context=ssl._create_unverified_context(), timeout=10).status
    except urllib.error.HTTPError as error:
        return error.code


def main():
    e, running = env(), containers()
    results = []

    def check(ok, what):
        results.append(ok)
        print(("✅ " if ok else "❌ ") + what)

    for key, default in DEFAULTS.items():
        check(e.get(key, default) != default, f"{key} is not the demo default")
    for name, c in sorted(running.items()):
        variables = dict(v.split("=", 1) for v in c["Config"]["Env"])
        if name.startswith("ontop"):
            check(variables.get("ONTOP_DEV_MODE") == "false", f"{name}: dev mode off")
            check(variables.get("ONTOP_DB_USER") == "rastro_readonly", f"{name}: reads as rastro_readonly")
        if name == "app":
            check(variables.get("PG_USER") == "rastro_readonly", "app: reads as rastro_readonly")
        open_ports = [f"{b['HostIp'] or '0.0.0.0'}:{b['HostPort']}" for bindings in c["NetworkSettings"]["Ports"].values()
                      for b in bindings or [] if b["HostIp"] not in ("127.0.0.1", "::1")]
        if name == "proxy":
            check(bool(open_ports), f"proxy: reachable from the network ({', '.join(open_ports) or 'not published'})")
        else:
            check(not open_ports, f"{name}: only reachable from this machine"
                  + (f" (open: {', '.join(open_ports)})" if open_ports else ""))
    check(psql("rastro_readonly", e.get("RASTRO_READONLY_PASSWORD", ""), "SELECT count(*) FROM rastro_meta.source"),
          "rastro_readonly logs in and reads")
    check(not psql("rastro_readonly", e.get("RASTRO_READONLY_PASSWORD", ""),
                   "BEGIN; CREATE TABLE rastro_meta.check_write (x int); ROLLBACK;"), "rastro_readonly cannot write")
    readers = subprocess.run(["grep", "-o", r"readers: {B: [a-z_]*, D: [a-z_]*}", str(ROOT / "layer/dominios.yaml")],
                             capture_output=True, text=True).stdout
    for reader in sorted({r for line in readers.splitlines() for r in line[13:-1].replace("D: ", "").split(", ")}):
        new, old = psql(reader, e.get("RASTRO_READER_PASSWORD", ""), "SELECT 1"), psql(reader, reader, "SELECT 1")
        if new or old:   # neither: the domain is not loaded here, so its reader does not exist
            check(new and not old, f"{reader}: logs in with the password of .env, not its own name")
    if "proxy" in running:
        check(https("/") == 401, f"proxy: asks for a login (status {https('/')})")
        if os.environ.get("RASTRO_LOGIN_PASSWORD"):
            status = https("/", e.get("RASTRO_LOGIN_USER"), os.environ["RASTRO_LOGIN_PASSWORD"])
            check(status == 200, f"proxy: the login opens the app (status {status})")
    print(f"\n{sum(results)} of {len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
