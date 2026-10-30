"""The numbers of a contrast card («antes_despues» in app/dominios/<domain>.yaml), read now: «valores» are one-row
queries (SQL over the sources as they come, or SPARQL over Rastro), «calculos» simple arithmetic over them, and the
card's texts name them in braces. The app and the slides read the same numbers through this module.

From the command line, the Spanish numbers of every card of a domain, of «Por qué confiar» and of the other demo
slides (story_numbers), as JSON (docs/slides/build.py reads them; Rastro Lab trains its two models, ~1 min):
docker compose exec -T app python /app/contraste.py energia > docs/slides/numeros/energia.json
"""
import json
import os
import sys
from pathlib import Path

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


def trust_numbers(cfg, evaluation, changes, evidence, number):
    """The measured numbers of «Por qué confiar»: the evaluation, the consistency test, the change test (the scenario
    where the most queries broke without Rastro: how many broke, how many questions it ran and how many of them had
    a query without Rastro, «—» being a question SQL over the sources could not answer) and the evidence coverage.
    number(value) formats a count."""
    totals, consistency = evaluation.get("totals", {}), evaluation.get("consistency", {})
    scenarios = [changes.get(c["antes"], {}) for c in cfg.get("cambios", [])]
    worst = max(scenarios, key=lambda r: sum(n for s, n in r.get("totals", {}).get("B", {}).items()
                                             if s not in ("✅", "—")), default={})
    without = worst.get("totals", {}).get("B", {})
    broken = sum(n for s, n in without.items() if s not in ("✅", "—"))
    numbers = {"c_consistent": totals.get("C", {}).get("consistent", "—"),
               "b_consistent": totals.get("B", {}).get("consistent", "—"),
               "n_consistency": len(consistency), "b_broken": broken,
               "change_questions": len(worst.get("cells", {})),
               "b_answerable": sum(n for s, n in without.items() if s != "—"),
               "c_correct": totals.get("C", {}).get("correct", "—"), "b_correct": totals.get("B", {}).get("correct", "—"),
               "d_correct": totals.get("D", {}).get("correct", "—"),
               "n_questions": len(evaluation.get("questions", {}))}
    if evidence:
        numbers.update(pct_evidencia=f"{100 * evidence['enlaces_con_evidencia'] / evidence['enlaces']:.0f} %",
                       n_enlaces=number(evidence["enlaces"]), cols=evidence["columnas"],
                       cols_ok=evidence["columnas_con_fuente"])
    return numbers


def change_numbers(cfg, changes, number):
    """The change scenario the demo tells with one answer («valor» in cambios): that answer before the change, right
    after it without and with Rastro, and after the one-line fix, as the change test recorded them."""
    change = next((c for c in cfg.get("cambios", []) if c.get("valor")), None)
    if not change:
        return {}
    valor = change["valor"]

    def at(step, path):
        v = (changes.get(step, {}).get("values") or {}).get(valor["pregunta"], {}).get(path)
        return number(v / valor.get("escala", 1), valor.get("decimales", 1)) if v is not None else "—"

    return {"antes": at("antes", "C"), "sin": at(change["antes"], "B"), "con": at(change["antes"], "C"),
            "arreglado": at(change["despues"], "C")}


def key(name):
    """A company's token key: the first word of its name, in lower case («TOTAL AUSTRAL S.A.» → total)."""
    return name.split()[0].lower()


def story_numbers(cfg, sparql, number, ext=None):
    """The other numbers the demo slides show, each from where the app reads it: the two readings of the first
    «Comprobar una afirmación», the «sin dato» test, the quality rules, the saved Wikidata enrichment and, when
    the domain has an extension (ext), its own numbers (Rastro Lab's, for oil and gas). number(value, decimals)
    formats; values by company are keyed by key()."""
    out = {}
    claims = (cfg.get("afirmaciones") or {}).get("ejemplos") or []
    if claims:
        first, share = claims[0]["lecturas"][:2]
        for prefix, reading in (("opera", first), ("parte", share)):
            out.update({f"{prefix}_{key(n)}": number(float(v) / reading["divisor"], 1)
                        for n, v in sparql(reading["consulta"])[1][:3]})
    fuera = json.loads(Path(cfg["fuera"]["archivo"]).read_text()) if cfg.get("fuera") else {}
    if fuera:
        asked = fuera["preguntas"].values()
        out["sin_dato"] = number(sum(q["sin_datos"] for q in asked), 0)
        control = next(q for q in asked if not q["sin_datos"])
        out["control"] = number(float(control["C"]["respuesta"]), 0)
    # A second evaluation, over a model's predictions (Rastro Lab): correct answers of each approach
    if cfg.get("evaluacion_predicciones"):
        predictions = json.loads(Path(cfg["evaluacion_predicciones"]).read_text())
        out["pred_n"] = number(len(predictions["questions"]), 0)
        out.update({f"pred_{k.lower()}": number(predictions["totals"][k]["correct"], 0) for k in ("B", "D", "C")})
    quality = json.loads(Path(cfg["calidad"]["archivo"]).read_text()) if cfg.get("calidad") else {}
    failing = set()
    if quality:
        out["reglas"] = number(len(quality["reglas"]), 0)
        for rule in quality["reglas"]:
            out[f"{rule['id']}_revisados"] = number(rule["revisados"], 0)
            out[f"{rule['id']}_fallas"] = number(rule["fallas"], 0)
        failing = {e["dato"] for r in quality["reglas"] for e in r["ejemplos"] if e["predicciones"]}
        out["predicciones_afectadas"] = number(len({p for r in quality["reglas"] for e in r["ejemplos"]
                                                    for p in e["predicciones"]}), 0)
    # The domain's own slide numbers: one-row queries and arithmetic, like a contrast card. {fallas} in a query is
    # the list of data that fail a quality rule and that a prediction used; without any, that query is skipped
    own = cfg.get("numeros_demo")
    if own:
        fallas = " ".join(f"<{d}>" for d in sorted(failing))
        card = {**own, "valores": [{"sparql": v["sparql"].replace("{fallas}", fallas)} for v in own["valores"]
                                   if fallas or "{fallas}" not in v["sparql"]]}
        found = values(card, None, sparql)
        out.update({k: v for k, v in shown(card, found, number).items() if k in own["mostrar"]})
    saved = (cfg.get("externo") or {}).get("guardado")
    if saved and os.path.exists(saved):
        import csv
        from idioma import scaled
        spec = cfg["externo"]["numeros"]   # which columns of the saved file are the name and the number
        scale = cfg["unidades"][spec["unidad"]]["escala"]
        import io
        rows = list(csv.DictReader(io.StringIO(Path(saved).read_text(), newline='')))
        out.update({f"externo_{key(r[spec['nombre']])}": scaled(r[spec["valor"]], scale, "es") for r in rows})
        out["externo_con_lei"] = number(len(rows), 0)
    if ext:
        out.update(ext.story_numbers(number))
    return out


def main(domain):
    sys.path[:0] = ["/app", "/layer"]
    import psycopg
    import yaml

    import answer
    from idioma import format_number

    ns = answer.DOMAINS[domain]["namespace"]

    def sql(query):
        user = answer.DOMAINS[domain]["readers"]["B"]
        with psycopg.connect(answer.reader_dsn(user)) as conn:
            cur = conn.execute(query)
            return [c.name for c in cur.description], cur.fetchall()

    def sparql(query):
        return answer.run_sparql_table(f"PREFIX {domain}: <{ns}>\n" + query, domain)

    cfg = yaml.safe_load(Path(f"/app/dominios/{domain}.yaml").read_text())

    def read(key):
        return json.loads(Path(cfg[key]).read_text()) if cfg.get(key) and os.path.exists(cfg[key]) else {}

    numbers = {"confiar": {k: str(v) for k, v in trust_numbers(cfg, read("evaluacion"), read("cambio"), read("evidencia"),
                                                                lambda v: format_number(v, 0, "es")).items()}}
    for item in cfg.get("preguntas", []):
        card = item.get("antes_despues") or {}
        if card.get("valores"):
            numbers[item["id"]] = shown(card, values(card, sql, sparql),
                                        lambda value, decimals: format_number(value, decimals, "es"))
    numbers["cambio"] = change_numbers(cfg, read("cambio"), lambda value, decimals: format_number(value, decimals, "es"))
    from dominio import extension
    numbers["demo"] = story_numbers(cfg, sparql, lambda value, decimals: format_number(value, decimals, "es"),
                                    extension.load(cfg))
    print(json.dumps(numbers, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
