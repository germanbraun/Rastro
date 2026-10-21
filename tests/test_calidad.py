"""Las reglas de calidad (SHACL): cada una deja pasar un dato bueno y marca uno malo."""
import sys
from pathlib import Path

import pytest
import yaml
from pyshacl import validate
from rdflib import Graph

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ontology"))
import calidad  # noqa: E402

PREFIJOS = """@prefix energia: <https://w3id.org/rastro/energia#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix e: <https://w3id.org/rastro/energia/> .
"""

CASOS = {regla: (e["bueno"], e["malo"]) for regla, e in yaml.safe_load(calidad.EJEMPLOS.read_text()).items()}
REGLAS = {bloque.split()[0].split(":")[1]: (prefijos, bloque) for prefijos, bloque in calidad.bloques()}


def test_cada_regla_tiene_su_caso():
    assert set(REGLAS) == set(CASOS)


@pytest.mark.parametrize("regla", sorted(CASOS))
def test_la_regla_deja_pasar_lo_bueno_y_marca_lo_malo(regla):
    prefijos, bloque = REGLAS[regla]
    forma = Graph().parse(data=prefijos + "\n" + bloque, format="turtle")
    bueno, malo = CASOS[regla]
    assert validate(Graph().parse(data=PREFIJOS + bueno, format="turtle"), shacl_graph=forma, advanced=True)[0]
    assert not validate(Graph().parse(data=PREFIJOS + malo, format="turtle"), shacl_graph=forma, advanced=True)[0]
