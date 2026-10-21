"""Lo que comparten los cargadores: la huella de un archivo cambia si cambia su contenido."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import comun  # noqa: E402


def test_la_huella_cambia_con_el_contenido(tmp_path):
    f = tmp_path / "fuente.csv"
    f.write_text("idpozo,etapas\n166133,18\n")
    antes = comun.huella(f)
    assert antes == comun.huella(f) and len(antes) == 64
    f.write_text("idpozo,etapas\n166133,30\n")
    assert comun.huella(f) != antes
