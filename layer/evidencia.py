"""Evidence coverage in each domain: how many Rastro links keep their source, their rule and their
text (PROV-O), and how many columns of the competency-question answers say which source they come from. Shown by the
card «Cada respuesta se puede auditar» in «Por qué confiar».

    docker compose run --rm -T layer-eval python /layer/evidencia.py [<domain> ...]   # every domain by default
"""
import json
import sys
from pathlib import Path


sys.path.insert(0, "/layer")
import answer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]          # the repo root (/ in Docker, where ontology/ and layer/ are mounted)
PROV = "PREFIX prov: <http://www.w3.org/ns/prov#>\n"


def domains():
    """Each domain with a `method.evidence` block in layer/dominios.yaml: its link classes, what counts as complete
    evidence, where the result goes and its competency queries. A domain that shares another one's result (energia_lab
    reuses energia's block) is measured once."""
    seen = set()
    for domain, d in answer.DOMAINS.items():
        spec = d.get("method", {}).get("evidence")
        if spec and spec["result"] not in seen:
            seen.add(spec["result"])
            yield domain, {**spec, "queries": d["method"]["queries"]}


def links(domain, spec):
    ns = answer.DOMAINS[domain]["namespace"]
    values = " ".join(f"{domain}:{c}" for c in spec["link_classes"])
    query = (f"PREFIX {domain}: <{ns}>\n" + PROV +
             f"SELECT (COUNT(DISTINCT ?l) AS ?n) (COUNT(DISTINCT ?ok) AS ?con) WHERE {{ VALUES ?clase {{ {values} }} "
             f"?l a ?clase . OPTIONAL {{ {spec['pattern']} BIND(?l AS ?ok) }} }}")
    _, rows = answer.run_sparql_table(query, domain)
    total, ok = (int(float(x)) for x in rows[0])
    return total, ok


def columns(domain, spec):
    total = with_source = 0
    for path in sorted((ROOT / spec["queries"]).glob("*.rq")):
        try:
            per_column = answer.column_sources(path.read_text(), domain)[1]
        except ValueError:   # a query the source analysis cannot read: not counted
            print(f"  {domain}: {path.name} no se pudo analizar; queda afuera del conteo de columnas")
            continue
        for sources in per_column.values():
            total += 1
            with_source += bool(sources)
    return total, with_source


def main():
    only = set(sys.argv[1:])                        # measure only these domains (their Ontop must be up)
    for domain, spec in domains():
        if only and domain not in only:
            continue
        n, ok = links(domain, spec)
        cols, cols_ok = columns(domain, spec)
        result = {"enlaces": n, "enlaces_con_evidencia": ok, "columnas": cols, "columnas_con_fuente": cols_ok}
        (ROOT / spec["result"]).write_text(json.dumps(result, indent=1))
        print(domain, result)


if __name__ == "__main__":
    main()
