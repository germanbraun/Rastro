"""The oil and gas dictionary: every term the mappings and the queries use is declared in the
ontology. An undeclared term makes Ontop fail to start or a query return nothing."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def terminos(texto):
    return set(re.findall(r"\benergia:([A-Za-z][A-Za-z0-9]*)", texto))


def declarados():
    texto = (RAIZ / "ontology" / "energia" / "energia.ttl").read_text()
    return set(re.findall(r"^energia:([A-Za-z][A-Za-z0-9]*)\s+a\s", texto, re.M))


def test_los_mapeos_usan_terminos_declarados():
    usados = terminos((RAIZ / "mappings" / "energia.r2rml.ttl").read_text())
    assert usados - declarados() == set()


def test_las_consultas_usan_terminos_declarados():
    usados = set()
    for f in [*(RAIZ / "ontology" / "energia" / "queries").glob("*.rq"), RAIZ / "lab" / "gas" / "modelo.py"]:
        usados |= terminos(f.read_text())
    assert usados - declarados() == set()


def test_los_terminos_de_cada_fuente_existen():
    import yaml
    dom = yaml.safe_load((RAIZ / "layer" / "dominios.yaml").read_text())["energia"]
    listados = {t for terms in dom["term_sources"].values() for t in terms}
    assert listados - declarados() == set()
