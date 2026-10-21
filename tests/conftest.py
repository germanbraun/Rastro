"""Las pruebas corren en la máquina, sin Docker ni base de datos (`python3 -m pytest`)."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "lab" / "gas"))
