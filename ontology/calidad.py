"""Checks a domain's quality rules (SHACL) over Rastro's data.

Fetches from Rastro, with CONSTRUCT, only what the rules look at, validates it with each rule and writes the result
(the app reads it). Everything domain-specific comes from the domain's `method.quality` block in layer/dominios.yaml:
the rules, their examples, the CONSTRUCT queries, the result path and, if the domain has predictions, the query
for the predictions that inherit the failures.

    docker compose run --rm calidad [<domain>]        # energia by default
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
import yaml
from pyshacl import validate
from rdflib import RDF, Graph, Namespace

ROOT = Path(__file__).resolve().parents[1]          # the repo root (/ in Docker, where ontology/ and layer/ are mounted)
REGISTRY = yaml.safe_load((ROOT / "layer" / "dominios.yaml").read_text())
SH = Namespace("http://www.w3.org/ns/shacl#")
PROV = Namespace("http://www.w3.org/ns/prov#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")


def config(domain):
    """The domain's quality paths (absolute), its Ontop URL and its prefix (name, namespace, instance base)."""
    d = REGISTRY[domain]
    q = {k: ROOT / v if isinstance(v, str) else v for k, v in d["method"]["quality"].items() if k != "run"}
    ns = d["namespace"]
    name = ns.rstrip("#/").rsplit("/", 1)[-1]                 # https://w3id.org/rastro/energia# -> energia
    return q, d["ontop"], (name, ns, ns.rstrip("#/") + "/")


QUALITY, ONTOP, (PREFIX, NS, BASE) = config("energia")      # defaults (the tests use the oil and gas rules)
REGLAS, EJEMPLOS = QUALITY["rules"], QUALITY["examples"]


def prefixes():
    return f"PREFIX {PREFIX}: <{NS}>\nPREFIX prov: <http://www.w3.org/ns/prov#>\n"


def prefixes_ttl():
    return f"@prefix {PREFIX}: <{NS}> .\n@prefix prov: <http://www.w3.org/ns/prov#> .\n@prefix e: <{BASE}> .\n"


def sparql(query, accept):
    r = requests.post(ONTOP, data={"query": prefixes() + query}, headers={"Accept": accept}, timeout=600)
    r.raise_for_status()
    return r


def traer():
    """What the rules look at: the result of each of the domain's CONSTRUCT queries."""
    datos = Graph()
    for q in yaml.safe_load(QUALITY["data"].read_text()):
        datos.parse(data=sparql(q, "text/turtle").text, format="turtle")
    return datos


def predicciones_vigentes():
    """The predictions of the current model run (the ones that can inherit a failure), or None without predictions."""
    if "predictions" not in QUALITY:
        return None
    filas = sparql(QUALITY["predictions"].read_text(), "application/sparql-results+json").json()["results"]["bindings"]
    return {f["p"]["value"] for f in filas}


def bloques(reglas=None):
    """The rules, each with its text as is (the prefixes and one block per rule)."""
    texto = (reglas or REGLAS).read_text()
    prefijos = "\n".join(line for line in texto.splitlines() if line.startswith("@prefix"))
    for bloque in re.split(r"\n\s*\n", texto):
        if bloque.lstrip().startswith("calidad:"):
            yield prefijos, bloque.strip()


def blancos(datos, forma, regla):
    """The data the rule looks at."""
    for p, o in forma.predicate_objects(regla):
        if p == SH.targetClass:
            return set(datos.subjects(RDF.type, o))
        if p == SH.targetSubjectsOf:
            return set(datos.subjects(o, None))
        if p == SH.targetObjectsOf:
            return set(datos.objects(None, o))
    return set()


def en_turtle(datos, nodo, entrantes):
    """A Rastro datum in Turtle: what it says and, if the rule looks at what points to it (a concession), that too."""
    g = Graph()
    for n in [nodo] + (sorted(datos.subjects(None, nodo))[:4] if entrantes else []):
        for t in datos.triples((n, None, None)):
            g.add(t)
    g.bind(PREFIX, NS)
    g.bind("prov", "http://www.w3.org/ns/prov#")
    g.bind("e", BASE)
    texto = g.serialize(format="turtle")
    return "\n".join(line for line in texto.splitlines() if not line.startswith("@prefix")).strip()


def ejemplo_roto(forma, malo):
    """What SHACL says about the broken example."""
    _, informe, _ = validate(Graph().parse(data=prefixes_ttl() + malo, format="turtle"), shacl_graph=forma, advanced=True)
    return sorted({str(informe.value(r, SH.resultMessage)) for r in informe.subjects(RDF.type, SH.ValidationResult)})


def main():
    global QUALITY, ONTOP, PREFIX, NS, BASE
    QUALITY, ONTOP, (PREFIX, NS, BASE) = config(sys.argv[1] if len(sys.argv) > 1 else "energia")
    datos = traer()
    vigentes = predicciones_vigentes()
    ejemplos = yaml.safe_load(QUALITY["examples"].read_text())
    resultado = {"fecha": date.today().isoformat(), "triples": len(datos), "reglas": []}
    for prefijos, bloque in bloques(QUALITY["rules"]):
        forma = Graph().parse(data=prefijos + "\n" + bloque, format="turtle")
        regla = next(forma.subjects(RDF.type, SH.NodeShape))
        _, informe, _ = validate(datos, shacl_graph=forma, advanced=True)
        # each failing datum and, if the domain has predictions, the current ones that used it (prov:used):
        # the ones that inherit the error
        fallas = []
        for r in informe.subjects(RDF.type, SH.ValidationResult):
            nodo = informe.value(r, SH.focusNode)
            fallas.append({"dato": str(nodo), "mensaje": str(informe.value(r, SH.resultMessage))})
            if vigentes is not None:
                fallas[-1]["predicciones"] = sorted(str(p) for p in datos.subjects(PROV.used, nodo) if str(p) in vigentes)
        fallidos = {f["dato"] for f in fallas}
        nodos = sorted(n for n in blancos(datos, forma, regla) if str(n) not in fallidos)
        ejemplo = ejemplos[str(regla).split("#")[-1]]
        resultado["reglas"].append({
            "id": str(regla).split("#")[-1],
            "nombre": str(forma.value(regla, RDFS.label)),
            "porque": str(forma.value(regla, RDFS.comment)),
            "shacl": bloque,
            "revisados": len(blancos(datos, forma, regla)),
            "un_dato": en_turtle(datos, nodos[0], (regla, SH.targetObjectsOf, None) in forma) if nodos else None,
            "roto": ejemplo["malo"],
            "roto_dice": ejemplo_roto(forma, ejemplo["malo"]),
            "fallas": len(fallas),
            "ejemplos": sorted(fallas, key=lambda f: f["dato"])[:10],
        })
        if vigentes is not None:
            resultado["reglas"][-1]["predicciones_afectadas"] = sorted({p for f in fallas for p in f["predicciones"]})
        print(f"{resultado['reglas'][-1]['nombre']}: {resultado['reglas'][-1]['revisados']} revisados, {len(fallas)} no cumplen")
    QUALITY["result"].write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
