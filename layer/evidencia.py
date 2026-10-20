"""Cobertura de la evidencia en cada dominio: cuántos enlaces de Rastro guardan su fuente, su regla y su
texto (PROV-O), y cuántas columnas de las respuestas a las preguntas de competencia dicen de qué fuente salen. Lo muestra la
tarjeta «Cada respuesta se puede auditar» de «Por qué confiar».

    docker compose run --rm -T layer-eval python /layer/evidencia.py
"""
import json
import sys
from pathlib import Path


sys.path.insert(0, "/layer")
import answer  # noqa: E402

HERE = Path(__file__).parent
PROV = "PREFIX prov: <http://www.w3.org/ns/prov#>\n"

# Para cada dominio: las clases de enlace, lo que cuenta como evidencia completa y dónde se guarda
DOMINIOS = {
    "energia": {
        "salida": HERE / "energia" / "evidencia.json",
        "consultas": "/ontology/energia/queries",
        "enlaces": ["Stake", "OperatorLink", "CompanyName", "LocationLink", "PipelineLink", "SurroundingsLink",
                    "LeiLink", "StudyLink", "OperatorChange"],
        "evidencia": "?l prov:wasDerivedFrom ?f ; prov:wasGeneratedBy ?g ; energia:sourceText ?t .",
    },
    "proveedores": {
        "salida": HERE / "proveedores" / "evidencia.json",
        "consultas": "/ontology/proveedores/queries",
        "enlaces": ["GroupLink", "LeiLink", "WatchlistLink"],
        "evidencia": "?l prov:wasDerivedFrom ?f ; proveedores:sourceText ?t .",
    },
    "oncologia": {
        "salida": HERE / "eval" / "evidencia.json",
        "consultas": "/ontology/queries",
        "enlaces": ["DrugLink"],
        "evidencia": "?l prov:wasDerivedFrom ?f ; oncologia:interventionText ?t ; oncologia:linkRule ?r .",
    },
}


def links(domain, spec):
    ns = answer.DOMAINS[domain]["namespace"]
    values = " ".join(f"{domain}:{c}" for c in spec["enlaces"])
    query = (f"PREFIX {domain}: <{ns}>\n" + PROV +
             f"SELECT (COUNT(DISTINCT ?l) AS ?n) (COUNT(DISTINCT ?ok) AS ?con) WHERE {{ VALUES ?clase {{ {values} }} "
             f"?l a ?clase . OPTIONAL {{ {spec['evidencia']} BIND(?l AS ?ok) }} }}")
    _, rows = answer.run_sparql_table(query, domain)
    total, ok = (int(float(x)) for x in rows[0])
    return total, ok


def columns(domain, spec):
    total = with_source = 0
    for path in sorted(Path(spec["consultas"]).glob("*.rq")):
        try:
            per_column = answer.column_sources(path.read_text(), domain)[1]
        except ValueError:   # una consulta que el análisis de fuentes no sabe leer: no se cuenta
            print(f"  {domain}: {path.name} no se pudo analizar; queda afuera del conteo de columnas")
            continue
        for sources in per_column.values():
            total += 1
            with_source += bool(sources)
    return total, with_source


def main():
    for domain, spec in DOMINIOS.items():
        n, ok = links(domain, spec)
        cols, cols_ok = columns(domain, spec)
        result = {"enlaces": n, "enlaces_con_evidencia": ok, "columnas": cols, "columnas_con_fuente": cols_ok}
        spec["salida"].write_text(json.dumps(result, indent=1))
        print(domain, result)


if __name__ == "__main__":
    main()
