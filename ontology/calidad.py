"""Comprueba las reglas de calidad (SHACL) de petróleo y gas sobre los datos de Rastro.

Trae de Rastro, con CONSTRUCT, solo lo que miran las reglas, lo valida con cada regla de
ontology/energia/calidad/reglas.ttl y escribe el resultado en layer/energia/calidad.json (lo lee la app).

    docker compose run --rm calidad
"""

import json
import os
import re
from datetime import date
from pathlib import Path

import requests
from pyshacl import validate
from rdflib import RDF, Graph, Namespace

REGLAS = Path(__file__).parent / "energia" / "calidad" / "reglas.ttl"
SALIDA = Path("/layer/energia/calidad.json")
ONTOP = os.environ.get("ONTOP_ENERGIA", "http://ontop-energia:8080/sparql")
SH = Namespace("http://www.w3.org/ns/shacl#")
PREFIJOS = "PREFIX energia: <https://w3id.org/rastro/energia#>\nPREFIX prov: <http://www.w3.org/ns/prov#>\n"

# Lo que miran las reglas, y nada más: cada enlace con su regla, fuente y evidencia; las participaciones;
# las predicciones con lo que usaron; las empresas con LEI
DATOS = [
    """CONSTRUCT { ?s energia:rule ?r ; prov:wasDerivedFrom ?f ; energia:sourceText ?t }
       WHERE { ?s energia:rule ?r . OPTIONAL { ?s prov:wasDerivedFrom ?f } OPTIONAL { ?s energia:sourceText ?t } }""",
    """CONSTRUCT { ?s a energia:Stake ; energia:percent ?p ; energia:partner ?e ; energia:inConcession ?c }
       WHERE { ?s a energia:Stake . OPTIONAL { ?s energia:percent ?p } OPTIONAL { ?s energia:partner ?e }
               OPTIONAL { ?s energia:inConcession ?c } }""",
    """CONSTRUCT { ?p a energia:Prediction ; prov:used ?u ; energia:predictedGas ?g ; energia:predictedLow ?l ;
                  energia:predictedHigh ?h . ?u a ?t }
       WHERE { ?p a energia:Prediction . OPTIONAL { ?p energia:predictedGas ?g } OPTIONAL { ?p energia:predictedLow ?l }
               OPTIONAL { ?p energia:predictedHigh ?h } OPTIONAL { ?p prov:used ?u . ?u a ?t } }""",
    """CONSTRUCT { ?e a energia:Company ; energia:lei ?l } WHERE { ?e a energia:Company ; energia:lei ?l }""",
]


def traer():
    datos = Graph()
    for q in DATOS:
        r = requests.post(ONTOP, data={"query": PREFIJOS + q}, headers={"Accept": "text/turtle"}, timeout=600)
        r.raise_for_status()
        datos.parse(data=r.text, format="turtle")
    return datos


def bloques():
    """Las reglas, cada una con su texto tal cual (los prefijos y un bloque por regla)."""
    texto = REGLAS.read_text()
    prefijos = "\n".join(line for line in texto.splitlines() if line.startswith("@prefix"))
    for bloque in re.split(r"\n\s*\n", texto):
        if bloque.lstrip().startswith("calidad:"):
            yield prefijos, bloque.strip()


def revisados(datos, forma, regla):
    """Cuántos datos mira la regla."""
    for p, o in forma.predicate_objects(regla):
        if p == SH.targetClass:
            return len(set(datos.subjects(RDF.type, o)))
        if p == SH.targetSubjectsOf:
            return len(set(datos.subjects(o, None)))
        if p == SH.targetObjectsOf:
            return len(set(datos.objects(None, o)))
    return 0


def main():
    datos = traer()
    resultado = {"fecha": date.today().isoformat(), "triples": len(datos), "reglas": []}
    for prefijos, bloque in bloques():
        forma = Graph().parse(data=prefijos + "\n" + bloque, format="turtle")
        regla = next(forma.subjects(RDF.type, SH.NodeShape))
        _, informe, _ = validate(datos, shacl_graph=forma, advanced=True)
        fallas = [{"dato": str(informe.value(r, SH.focusNode)), "mensaje": str(informe.value(r, SH.resultMessage))}
                  for r in informe.subjects(RDF.type, SH.ValidationResult)]
        resultado["reglas"].append({
            "id": str(regla).split("#")[-1],
            "nombre": str(forma.value(regla, Namespace("http://www.w3.org/2000/01/rdf-schema#").label)),
            "porque": str(forma.value(regla, Namespace("http://www.w3.org/2000/01/rdf-schema#").comment)),
            "shacl": bloque,
            "revisados": revisados(datos, forma, regla),
            "fallas": len(fallas),
            "ejemplos": sorted(fallas, key=lambda f: f["dato"])[:10],
        })
        print(f"{resultado['reglas'][-1]['nombre']}: {resultado['reglas'][-1]['revisados']} revisados, {len(fallas)} no cumplen")
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
