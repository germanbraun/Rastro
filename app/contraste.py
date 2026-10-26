"""The numbers of a contrast card («antes_despues» in app/dominios/<domain>.yaml), read now: «valores» are one-row
queries (SQL over the sources as they come, or SPARQL over Rastro), «calculos» simple arithmetic over them, and the
card's texts name them in braces. The app and the slides read the same numbers through this module.

From the command line, the Spanish numbers of every card of a domain, as JSON (docs/slides/build.py reads them):
docker compose exec -T app python /app/contraste.py energia > docs/slides/numeros/energia.json
"""
import json
import os
import sys

TEXTS = ("sin", "con", "impacto")


def values(card, sql, sparql):
    """sql(query) and sparql(query) return (columns, rows)."""
    found = {}
    for query in card.get("valores", []):
        columns, rows = sql(query["sql"]) if query.get("sql") else sparql(query["sparql"])
        found.update({c: float(v) for c, v in zip(columns, rows[0])})
    for name, formula in card.get("calculos", {}).items():
        found[name] = eval(str(formula), {"__builtins__": {}, "round": round}, dict(found))   # noqa: S307 - our own YAML
    return found


def shown(card, found, number):
    """Each value as text: number(value, decimals); whole numbers without decimals, others with one."""
    return {name: number(v, card.get("decimales", {}).get(name, 0 if float(v).is_integer() else 1))
            for name, v in found.items()}


def fill(card, texts):
    """The card with its texts filled in."""
    return {key: ({k: v.format(**texts) for k, v in part.items()} if isinstance(part, dict) else part.format(**texts))
            if key in TEXTS else part for key, part in card.items()}


def main(domain):
    sys.path[:0] = ["/app", "/layer"]
    import psycopg
    import yaml

    import answer
    from idioma import format_number

    ns = answer.DOMAINS[domain]["namespace"]

    def sql(query):
        user = answer.DOMAINS[domain]["readers"]["B"]
        with psycopg.connect(answer.READER.format(user) % os.environ["PG_DB"]) as conn:
            cur = conn.execute(query)
            return [c.name for c in cur.description], cur.fetchall()

    def sparql(query):
        return answer.run_sparql_table(f"PREFIX {domain}: <{ns}>\n" + query, domain)

    cfg = yaml.safe_load(open(f"/app/dominios/{domain}.yaml"))
    numbers = {}
    for item in cfg.get("preguntas", []):
        card = item.get("antes_despues") or {}
        if card.get("valores"):
            numbers[item["id"]] = shown(card, values(card, sql, sparql),
                                        lambda value, decimals: format_number(value, decimals, "es"))
    print(json.dumps(numbers, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
