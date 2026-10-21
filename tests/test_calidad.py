"""Las reglas de calidad (SHACL): cada una deja pasar un dato bueno y marca uno malo."""
import sys
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ontology"))
import calidad  # noqa: E402

PREFIJOS = """@prefix energia: <https://w3id.org/rastro/energia#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix e: <https://w3id.org/rastro/energia/> .
"""

# Por regla: un dato que la cumple y uno que no
CASOS = {
    "EnlaceConEvidencia": (
        'e:enlace energia:rule "punto dentro del contorno" ; prov:wasDerivedFrom e:fuente ; energia:sourceText "El punto cae en X." .',
        'e:enlace energia:rule "punto dentro del contorno" ; prov:wasDerivedFrom e:fuente .',
    ),
    "Participacion": (
        "e:p a energia:Stake ; energia:percent 55 ; energia:partner e:ypf ; energia:inConcession e:c .",
        "e:p a energia:Stake ; energia:percent 120 ; energia:partner e:ypf ; energia:inConcession e:c .",
    ),
    "ConcesionHasta100": (
        "e:a energia:inConcession e:c ; energia:percent 60 . e:b energia:inConcession e:c ; energia:percent 40 .",
        "e:a energia:inConcession e:c ; energia:percent 70 . e:b energia:inConcession e:c ; energia:percent 40 .",
    ),
    "Prediccion": (
        "e:p a energia:Prediction ; prov:used e:i ; energia:predictedLow 10 ; energia:predictedGas 20 ; energia:predictedHigh 30 ."
        " e:i a energia:WellStart .",
        "e:p a energia:Prediction ; energia:predictedLow 25 ; energia:predictedGas 20 ; energia:predictedHigh 30 .",
    ),
    "EmpresaUnLei": (
        'e:ypf a energia:Company ; energia:lei "549300BS2ZHDWDKUGX28" .',
        'e:ypf a energia:Company ; energia:lei "549300BS2ZHDWDKUGX28", "ABC" .',
    ),
}
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
