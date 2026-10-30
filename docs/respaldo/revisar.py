"""Before a demo: is everything ready, or what is missing? One line per check, and the command that fixes it.

It checks what the demo leans on, from outside, like the person who gives it: the app and the oil and gas Rastro
answer, the slides were built with the current numbers, the backup screenshots are newer than those numbers, and the
chat has a model (an API key, a local model, or the recorded conversations). It changes nothing.

    python3 docs/respaldo/revisar.py [--url http://localhost:8501]
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLIDES = ROOT / "docs/slides"
NUMBERS = SLIDES / "numeros/energia.json"


def env():
    path = ROOT / ".env"
    pairs = (line.split("=", 1) for line in path.read_text().splitlines() if "=" in line and not line.startswith("#"))
    return {k.strip(): v.strip() for k, v in pairs} if path.exists() else {}


def answers(url, data=None, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, headers or {}), timeout=20) as reply:
            return reply.read().decode()
    except OSError:
        return None


def app(base):
    ok = answers(f"{base}/_stcore/health") == "ok"
    return ok, "the app answers" if ok else f"the app does not answer at {base}: docker compose up -d"


def rastro():
    query = "PREFIX energia: <https://w3id.org/rastro/energia#> SELECT (COUNT(*) AS ?n) WHERE { ?c a energia:Concession }"
    reply = answers("http://localhost:8082/sparql", urllib.parse.urlencode({"query": query}).encode(),
                    {"Accept": "text/csv"})
    count = int(reply.splitlines()[1]) if reply and len(reply.splitlines()) > 1 else 0
    return count > 0, (f"Rastro answers: {count} concessions" if count else
                       "the oil and gas Rastro does not answer on :8082: docker compose up -d")


def deck():
    built = SLIDES / "energia.html"
    sources = [NUMBERS, SLIDES / "mazos/energia.json", *(SLIDES / "slides").glob("*.html")]
    stale = [p.name for p in sources if p.stat().st_mtime > built.stat().st_mtime] if built.exists() else ["all"]
    return not stale, ("the deck is built with the current slides and numbers" if not stale else
                       f"the deck is older than {', '.join(stale[:3])}: python3 docs/slides/build.py")


def backup():
    shots = sorted((ROOT / "docs/respaldo/es").glob("momento-*.png"))
    old = [p.name for p in shots if p.stat().st_mtime < NUMBERS.stat().st_mtime]
    ok = len(shots) >= 4 and not old
    return ok, (f"the backup has {len(shots)} screenshots, newer than the numbers" if ok else
                "the backup screenshots are missing or older than the numbers: python3 docs/respaldo/capturar.py")


def chat(e):
    provider = e.get("RASTRO_PROVIDER") or "anthropic"
    if provider == "replay":
        folder = ROOT / (e.get("RASTRO_RECORD") or "missing").replace("/layer/", "layer/", 1)
        ok = any(folder.glob("*.json"))
        return ok, (f"the chat answers the recorded conversations ({folder.name}): ask them as written in "
                    "layer/energia/chat/conversaciones.yaml, in Spanish" if ok else
                    f"RASTRO_RECORD has no recorded conversations: {e.get('RASTRO_RECORD') or 'empty'}")
    needs = {"anthropic": ["ANTHROPIC_API_KEY"], "openai": ["OPENAI_API_KEY", "RASTRO_MODEL"], "ollama": []}
    missing = [k for k in needs.get(provider, []) if not e.get(k)]
    if not missing:
        return True, f"the chat has a model ({provider}); each answer takes 20 to 40 seconds"
    return False, (f"the chat has no model ({provider} needs {', '.join(missing)} in .env); without a key, "
                   "RASTRO_PROVIDER=replay and RASTRO_RECORD=/layer/energia/chat/llamadas-gpt-5.5, then "
                   "docker compose up -d app")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://localhost:8501")
    base = parser.parse_args().url.rstrip("/")
    checks = [app(base), rastro(), deck(), backup(), chat(env())]
    for ok, text in checks:
        print(("✅ " if ok else "❌ ") + text)
    ready = all(ok for ok, _ in checks)
    print("Ready for the demo." if ready else "Not ready: fix the lines with ❌. The deck and the backup work without "
          "the services.")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
