"""Revisa que la ontología cargue y que cada query use solo términos declarados.

Se corre con: docker compose run --rm ontology-check (los tres dominios)
Un dominio: docker compose run --rm ontology-check python /ontology/check.py /ontology/proveedores
"""

import sys
from pathlib import Path

import rdflib
from rdflib.namespace import OWL, RDF
from rdflib.plugins.sparql import prepareQuery

# Carpetas de los dominios: cada una con su ontología (*.ttl) y sus queries/
AQUI = Path(__file__).parent
DOMINIOS = [Path(a) for a in sys.argv[1:]] or [AQUI, AQUI / "energia", AQUI / "proveedores"]
NS = "https://w3id.org/rastro/oncologia#"


def terms_in(node, found, seen):
    """Recorre el álgebra de una query y junta las IRIs de la ontología."""
    if id(node) in seen:
        return
    seen.add(id(node))
    if isinstance(node, rdflib.URIRef):
        if str(node).startswith(NS):
            found.add(str(node))
    elif isinstance(node, dict) or hasattr(node, "items"):
        for v in node.values():
            terms_in(v, found, seen)
    elif isinstance(node, (list, tuple, set)):
        for v in node:
            terms_in(v, found, seen)
    elif hasattr(node, "__dict__"):
        for v in vars(node).values():
            terms_in(v, found, seen)


def revisar(carpeta):
    global NS
    g = rdflib.Graph().parse(next(carpeta.glob("*.ttl")))
    NS = str(next(g.subjects(RDF.type, OWL.Ontology))) + "#"
    declared = {str(s) for s in g.subjects() if str(s).startswith(NS)}
    print(f"Ontología {carpeta.name}: {len(set(g.subjects(RDF.type, OWL.Class)))} clases, "
          f"{len(set(g.subjects(RDF.type, OWL.ObjectProperty)))} relaciones, "
          f"{len(set(g.subjects(RDF.type, OWL.DatatypeProperty)))} atributos")

    ok = True
    for f in sorted((carpeta / "queries").glob("*.rq")):
        try:
            used = set()
            terms_in(prepareQuery(f.read_text()).algebra, used, set())
        except Exception as e:  # noqa: BLE001 - se informa el error de sintaxis tal cual
            print(f"{f.name}: ERROR de sintaxis: {e}")
            ok = False
            continue
        missing = sorted(u.replace(NS, ":") for u in used - declared)
        if missing:
            print(f"{f.name}: usa términos no declarados: {', '.join(missing)}")
            ok = False
        else:
            print(f"{f.name}: OK")
    return ok


def main():
    ok = all([revisar(c) for c in DOMINIOS])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
