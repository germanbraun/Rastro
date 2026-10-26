"""Checks that the ontology loads and that each query uses only declared terms.

Run with: docker compose run --rm ontology-check (all three domains)
One domain: docker compose run --rm ontology-check python /ontology/check.py /ontology/proveedores
"""

import sys
from pathlib import Path

import rdflib
from rdflib.namespace import OWL, RDF, RDFS

import yaml
from rdflib.plugins.sparql import prepareQuery

# Domain folders: each one with its ontology (*.ttl) and its queries/
AQUI = Path(__file__).parent
ROOT = AQUI.parent
NS = "https://w3id.org/rastro/oncologia#"


def terms_in(node, found, seen):
    """Walks the algebra of a query and collects the ontology IRIs."""
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


def shared_domain_errors(ontology, mapping):
    """Find shared predicates from explicit R2RML subject classes, not inferred domain types."""
    rr = rdflib.Namespace("http://www.w3.org/ns/r2rml#")
    uses = {}
    for triples_map, subject_map in mapping.subject_objects(rr.subjectMap):
        classes = set(mapping.objects(subject_map, rr["class"]))
        for pom in mapping.objects(triples_map, rr.predicateObjectMap):
            predicates = set(mapping.objects(pom, rr.predicate))
            for predicate_map in mapping.objects(pom, rr.predicateMap):
                predicates.update(mapping.objects(predicate_map, rr.constant))
            for predicate in predicates:
                uses.setdefault(predicate, set()).update(classes)
    # Also check explicit typed examples supplied in the ontology itself.
    for subject, predicate, _ in ontology:
        uses.setdefault(predicate, set()).update(ontology.objects(subject, RDF.type))
    return [f"Shared property {predicate} has rdfs:domain but is used by {sorted(map(str, classes))}"
            for predicate, classes in uses.items() if len(classes) > 1 and (predicate, RDFS.domain, None) in ontology]


def registered_targets(root=ROOT):
    registry = yaml.safe_load((root / "layer/dominios.yaml").read_text())
    targets = {}
    for cfg in registry.values():
        method = cfg.get("method", {})
        if cfg.get("ontology") and method.get("mapping") and method.get("queries"):
            key = (root / cfg["ontology"], root / method["mapping"], root / method["queries"])
            targets[key] = key
    return list(targets.values())


def revisar(carpeta, mapping=None, queries=None):
    global NS
    ontology = carpeta if carpeta.is_file() else next(carpeta.glob("*.ttl"))
    g = rdflib.Graph().parse(ontology)
    NS = str(next(g.subjects(RDF.type, OWL.Ontology))) + "#"
    declared = {str(s) for s in g.subjects() if str(s).startswith(NS)}
    print(f"Ontología {carpeta.name}: {len(set(g.subjects(RDF.type, OWL.Class)))} clases, "
          f"{len(set(g.subjects(RDF.type, OWL.ObjectProperty)))} relaciones, "
          f"{len(set(g.subjects(RDF.type, OWL.DatatypeProperty)))} atributos")

    errors = shared_domain_errors(g, rdflib.Graph().parse(mapping) if mapping else rdflib.Graph())
    for error in errors:
        print(error)
    ok = not errors
    folder = queries or (ontology.parent / "queries")
    for f in sorted(folder.glob("*.rq")):
        try:
            used = set()
            terms_in(prepareQuery(f.read_text()).algebra, used, set())
        except Exception as e:  # noqa: BLE001 - the syntax error is reported as is
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
    targets = registered_targets()
    if sys.argv[1:]:
        folders = {Path(arg).resolve() for arg in sys.argv[1:]}
        selected = [target for target in targets if target[0].parent.resolve() in folders or target[0].resolve() in folders]
        if not selected:
            raise ValueError("No registered ontology matches the requested paths")
        targets = selected
    if not targets:
        raise ValueError("No registered ontologies to check")
    ok = all([revisar(ontology, mapping, queries) for ontology, mapping, queries in targets])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
