"""Registry-driven SHACL checks. python ontology/calidad.py [domain] [--examples-only].

Execution failures exit nonzero. Detected source defects remain in the result with their
coverage and affected predictions; they are not silently corrected or treated as runner errors.
"""
import argparse
import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests
import yaml
from pyshacl import validate
from rdflib import BNode, RDF, RDFS, Graph, Namespace

ROOT = Path(__file__).resolve().parents[1]
SH = Namespace("http://www.w3.org/ns/shacl#")


@dataclass
class QualityConfig:
    domain: str
    rules: Path
    examples: Path
    data: Path
    result: Path
    endpoint: str
    namespace: str
    prefix: str
    predictions: Path | None = None

    @property
    def prefixes(self):
        return f"PREFIX {self.prefix}: <{self.namespace}>\nPREFIX prov: <http://www.w3.org/ns/prov#>\n"

    @classmethod
    def load(cls, domain="energia", root=ROOT):
        registry = yaml.safe_load((root / "layer/dominios.yaml").read_text())
        cfg = registry[domain]
        quality = cfg.get("method", {}).get("quality")
        if not quality:
            raise ValueError(f"{domain}: quality coverage is not built")
        paths = {}
        for name in ("rules", "examples", "data", "result", "predictions"):
            if name in quality:
                path = (root / quality[name]).resolve()
                if not path.is_relative_to(root.resolve()):
                    raise ValueError(f"{domain}: quality path escapes root")
                paths[name] = path
        prefix = quality.get("prefix", domain)
        endpoint = os.environ.get(f"ONTOP_{domain.upper()}", cfg["ontop"])
        return cls(domain=domain, endpoint=endpoint, namespace=cfg["namespace"], prefix=prefix, **paths)


def bloques(config):
    """Yield each NodeShape and its complete constraint graph, without layout conventions."""
    graph = Graph().parse(config.rules)
    targets = {SH.targetClass, SH.targetNode, SH.targetSubjectsOf, SH.targetObjectsOf}
    shapes = sorted((shape for shape in set(graph.subjects(RDF.type, SH.NodeShape))
                     if any(predicate in targets for predicate in graph.predicates(shape))), key=str)
    if not shapes:
        raise ValueError(f"{config.domain}: rules contain no NodeShapes")
    for shape in shapes:
        part = Graph()
        for prefix, namespace in graph.namespaces():
            part.bind(prefix, namespace)
        pending, seen = [shape], set()
        while pending:
            node = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            for triple in graph.triples((node, None, None)):
                part.add(triple)
                if isinstance(triple[2], BNode) or triple[1] in {SH.node, SH.property, SH.qualifiedValueShape}:
                    pending.append(triple[2])
        yield shape, part


def blancos(datos, forma, regla):
    """Union of every explicit SHACL target, including multiple target types."""
    nodes = set(forma.objects(regla, SH.targetNode))
    for target in forma.objects(regla, SH.targetClass):
        for subclass in datos.transitive_subjects(RDFS.subClassOf, target):
            nodes.update(datos.subjects(RDF.type, subclass))
    for target in forma.objects(regla, SH.targetSubjectsOf):
        nodes.update(datos.subjects(target, None))
    for target in forma.objects(regla, SH.targetObjectsOf):
        nodes.update(datos.objects(None, target))
    return nodes


def example_graph(config, text):
    graph = Graph()
    graph.bind("e", config.namespace.rstrip("#/") + "/")
    for prefix, namespace in Graph().parse(config.rules).namespaces():
        graph.bind(prefix, namespace)
    # Examples can use the vocabulary's declared prefixes, or declare their own.
    prefixes = "\n".join(f"@prefix {p}: <{n}> ." for p, n in graph.namespaces())
    return graph.parse(data=prefixes + "\n" + text, format="turtle")


def check_examples(config):
    examples = yaml.safe_load(config.examples.read_text()) or {}
    shapes = list(bloques(config))
    ids = {str(shape).rsplit("#", 1)[-1].rsplit("/", 1)[-1].rsplit(":", 1)[-1] for shape, _ in shapes}
    if set(examples) != ids:
        raise ValueError(f"{config.domain}: examples must cover exactly every shape")
    for shape, graph in shapes:
        name = str(shape).rsplit("#", 1)[-1].rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        for key, expected in (("bueno", True), ("malo", False)):
            sample = example_graph(config, examples[name][key])
            if not blancos(sample, graph, shape):
                raise ValueError(f"{name}: {key} example has no target nodes")
            conforms, _, _ = validate(sample, shacl_graph=graph, advanced=True)
            if conforms != expected:
                raise ValueError(f"{name}: {key} example did not produce expected conformance")
    return len(shapes)


def traer(config):
    queries = yaml.safe_load(config.data.read_text())
    if not isinstance(queries, list) or not queries:
        raise ValueError("Quality data must contain nonempty CONSTRUCT queries")
    graph = Graph()
    for query in queries:
        response = requests.post(config.endpoint, data={"query": config.prefixes + query},
                                 headers={"Accept": "text/turtle"}, timeout=600)
        response.raise_for_status()
        graph.parse(data=response.text, format="turtle")
    return graph


def prediction_links(config):
    if config.predictions is None:
        return {}
    response = requests.post(config.endpoint, data={"query": config.predictions.read_text()},
                             headers={"Accept": "application/sparql-results+json"}, timeout=60)
    response.raise_for_status()
    links = {}
    for row in response.json()["results"]["bindings"]:
        links.setdefault(row["record"]["value"], set()).add(row["prediction"]["value"])
    return links


def en_turtle(datos, nodo, entrantes):
    graph = Graph()
    for prefix, namespace in datos.namespaces():
        graph.bind(prefix, namespace)
    for node in [nodo] + (sorted(datos.subjects(None, nodo), key=str)[:4] if entrantes else []):
        for triple in datos.triples((node, None, None)):
            graph.add(triple)
    return graph.serialize(format="turtle")


def evaluate(config, data, predictions=None):
    examples = yaml.safe_load(config.examples.read_text())
    predictions = predictions or {}
    result = {"fecha": date.today().isoformat(), "domain": config.domain, "triples": len(data), "reglas": []}
    for shape, graph in bloques(config):
        _, report, _ = validate(data, shacl_graph=graph, advanced=True)
        failures = [{"dato": str(report.value(node, SH.focusNode)), "mensaje": str(report.value(node, SH.resultMessage)),
                     "predicciones": sorted(predictions.get(str(report.value(node, SH.focusNode)), []))}
                    for node in report.subjects(RDF.type, SH.ValidationResult)]
        bad = {failure["dato"] for failure in failures}
        targets = blancos(data, graph, shape)
        passing = sorted((node for node in targets if str(node) not in bad), key=str)
        name = str(shape).rsplit("#", 1)[-1].rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        broken = examples[name]["malo"]
        _, broken_report, _ = validate(example_graph(config, broken), shacl_graph=graph, advanced=True)
        result["reglas"].append({
            "id": name, "nombre": str(graph.value(shape, RDFS.label) or name),
            "porque": str(graph.value(shape, RDFS.comment) or ""), "shacl": graph.serialize(format="turtle"),
            "revisados": len(targets), "coverage": "checked" if targets else "no_targets",
            "un_dato": en_turtle(data, passing[0], bool(list(graph.objects(shape, SH.targetObjectsOf)))) if passing else None,
            "roto": broken, "roto_dice": sorted({str(message) for message in broken_report.objects(None, SH.resultMessage)}),
            "fallas": len(failures), "ejemplos": sorted(failures, key=lambda item: item["dato"])[:10],
            "predicciones_afectadas": sorted({p for failure in failures for p in failure["predicciones"]}),
        })
    result["status"] = "coverage_pending" if any(not row["revisados"] for row in result["reglas"]) else (
        "defects_detected" if any(row["fallas"] for row in result["reglas"]) else "checked")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", nargs="?", default="energia")
    parser.add_argument("--examples-only", action="store_true")
    args = parser.parse_args()
    config = QualityConfig.load(args.domain)
    count = check_examples(config)
    if args.examples_only:
        print(f"{args.domain}: {count} good/bad pairs passed")
        return
    result = evaluate(config, traer(config), prediction_links(config))
    config.result.parent.mkdir(parents=True, exist_ok=True)
    config.result.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(f"{args.domain}: {result['status']}")
    if result["status"] == "coverage_pending":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
