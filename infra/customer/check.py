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
    listed = subprocess.run(COMPOSE + ["ps", "-q"], capture_output=True, text=True)
    if listed.returncode != 0:   # e.g. a machine without the customer setup: .env lacks its passwords
        sys.exit("docker compose cannot read the customer setup: " + (listed.stderr.strip().splitlines() or ["?"])[-1])
    ids = listed.stdout.split()
    if not ids:   # nothing running: docker inspect with no ids would fail
        return {}
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
    except (urllib.error.URLError, OSError):   # the proxy does not answer: a failed check, not a trace
        return None


def readers():
    """The read-only users of every domain (`readers: {B: …, D: …}` in layer/dominios.yaml), read as text: this
    script runs with the standard library only."""
    found = set()
    for line in (ROOT / "layer/dominios.yaml").read_text().splitlines():
        if "readers: {B: " in line:
            inner = line.split("readers: {", 1)[1].split("}", 1)[0]
            found |= {part.split(":", 1)[1].strip() for part in inner.split(",")}
    return sorted(found)


def main():
    e, running = env(), containers()
    if not running:
        sys.exit("No service is running: start them first (infra/customer/install.sh <domain>).")
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
            # Which language model the app can call (docs/data-sent-to-model.md); with RASTRO_NO_MODEL=1, none
            provider = variables.get("RASTRO_PROVIDER") or ("anthropic" if variables.get("ANTHROPIC_API_KEY") else "")
            model = {"anthropic": "Claude API", "openai": "OpenAI API",
                     "ollama": "a local model (Ollama)"}.get(provider, "none")
            if e.get("RASTRO_NO_MODEL") == "1":
                check(model == "none", f"app: calls no language model (configured: {model})")
            else:
                print(f"ℹ️  app: language model configured: {model} (RASTRO_NO_MODEL=1 makes this a check)")
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
    users = readers()
    check(bool(users), f"read-only users found in layer/dominios.yaml ({len(users)})")
    for reader in users:
        new, old = psql(reader, e.get("RASTRO_READER_PASSWORD", ""), "SELECT 1"), psql(reader, reader, "SELECT 1")
        if new or old:   # neither: the domain is not loaded here, so its reader does not exist
            check(new and not old, f"{reader}: logs in with the password of .env, not its own name")
    if "proxy" in running:
        status = https("/")
        check(status == 401, f"proxy: asks for a login (status {status or 'no answer'})")
        if os.environ.get("RASTRO_LOGIN_PASSWORD"):
            status = https("/", e.get("RASTRO_LOGIN_USER"), os.environ["RASTRO_LOGIN_PASSWORD"])
            check(status == 200, f"proxy: the login opens the app (status {status})")
    print(f"\n{sum(results)} of {len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
