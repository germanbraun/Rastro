"""The tests run on the machine, without Docker or a database (`python3 -m pytest`)."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "lab" / "gas"))
