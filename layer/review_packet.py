"""The packet for the independent review of a domain's reference answers, and the record of what the person found.

The references of the evaluation come from Rastro (SPARQL written by an AI assistant), so they stay provisional until
someone outside checks them against the sources (CLAUDE.md, measurement rules). This script prepares that work and
turns its result into the files the publication gate reads (layer/method.py publication):

    build    writes <folder>/revision/paquete.md (what to check, per question: Rastro's answer, how the three approaches
             answered, the differences already adjudicated, the sources with the loaded version, and a SQL query over
             the sources as they come to start from) and formulario.csv (one row per question, to fill in)
    record   reads the filled formulario.csv; when every question is reviewed it writes eval/referencias.json (the
             person's answers replace Rastro's as the references), scores again and writes reference-evidence.yaml

    docker compose run --rm -T layer-eval python /layer/review_packet.py energia build|record

It never fills in a reviewer, a date or an answer: a row without them stays pending.
"""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from answer import DOMAINS  # noqa: E402

LAYER = Path(__file__).resolve().parent
FORM_COLUMNS = ["pregunta", "respuesta_rastro", "respuesta_revisada", "fuentes_y_version", "como_lo_verifique",
                "revisor", "fecha", "estado"]
NAMES = {"B": "Sin Rastro (SQL)", "D": "SQL + enlaces de Rastro", "C": "Con Rastro"}


def folder(domain):
    return LAYER / Path(DOMAINS[domain]["method"]["evaluation"]["folder"]).relative_to("layer")


def repo_path(path):
    """A path as the publication gate reads it: relative to the repository root."""
    return "layer/" + path.relative_to(LAYER).as_posix()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect():
    return psycopg.connect(f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                           f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")


def sources():
    """The last load of every table, with its source: what the reviewer checks against."""
    with connect() as conn:
        registered = dict((i, (n, h)) for i, n, h in conn.execute("select id, name, homepage from rastro_meta.source"))
        loads = conn.execute("""select distinct on (table_name) source_id, table_name, version, sha256,
                                       loaded_at::date from rastro_meta.load_run
                                order by table_name, loaded_at desc""").fetchall()
    return {table: (registered[sid], version, sha, day) for sid, table, version, sha, day in loads}


def tables_in(query, known):
    return sorted(set(re.findall(r"\b([a-z_0-9]+\.[a-z_0-9]+)\b", query or "")) & set(known))


def source_lines(tables, known):
    """One line per source, with each table it reads, its version, load date and file fingerprint."""
    by_source = {}
    for table in tables:
        (name, homepage), version, sha, day = known[table]
        by_source.setdefault((name, homepage), []).append(
            f"`{table}` ({version or 's/v'}, cargada el {day}{', archivo sha256 ' + sha[:12] if sha else ''})")
    return [f"- {name} ({homepage}): " + "; ".join(loads) for (name, homepage), loads in by_source.items()]


def shown(value):
    if isinstance(value, list):
        return "; ".join(map(str, value))
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return "—" if value is None else str(value)


def last_query(answer):
    """The query whose result was taken as the answer (the last attempt)."""
    attempts = (answer or {}).get("attempts") or []
    return attempts[-1].get("query") if attempts else None


def adjudications(path):
    """The rows of adjudicacion.md, by question id: «| e05 (gasoductos) | difference | found | result |»."""
    rows = {}
    for line in path.read_text().splitlines() if path.exists() else []:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        match = re.match(r"(e|p)\d+", cells[0]) if len(cells) == 4 else None
        if match:
            rows.setdefault(match.group(0), []).append(cells)
    return rows


def build(domain):
    here = folder(domain)
    results = json.loads((here / "resultados.json").read_text())
    known = sources()
    adjudicated = adjudications(here / "adjudicacion.md")
    out = here / "revision"
    out.mkdir(exist_ok=True)
    lines = [
        f"# Revisión independiente de las referencias: {DOMAINS[domain]['method']['evaluation']['title']}", "",
        f"Las respuestas de referencia de las {len(results['questions'])} preguntas de la evaluación salieron de "
        "Rastro y las escribió un asistente de IA. Hasta que una persona las confirme con las fuentes, todo número de "
        "precisión es provisional. Este paquete es para esa persona.", "",
        "## Qué se pide", "",
        "1. Para cada pregunta, obtener la respuesta **con las fuentes, sin usar Rastro**: ni la app, ni sus "
        "consultas SPARQL, ni sus tablas de enlaces. Sirven las tablas de las fuentes tal como se cargaron "
        "(acceso de solo lectura) o los archivos originales de cada organismo, en la versión indicada.",
        "2. La consulta SQL de cada pregunta es la que escribió el evaluador sin Rastro: un punto de partida, "
        "no la respuesta. Revísela, corríjala o use otra forma.",
        "3. Anotar en `formulario.csv` (una fila por pregunta): `respuesta_revisada` (un número sin separador de "
        "miles y con punto decimal, o una lista separada por «;»), `fuentes_y_version`, `como_lo_verifique` "
        "(una o dos frases; si su respuesta difiere de la de Rastro, por qué), `revisor`, `fecha` (AAAA-MM-DD) y "
        "`estado` = `revisada`.",
        "4. Si una pregunta admite más de una lectura, anote la suya en `como_lo_verifique`; no la cambie.", "",
        "Para saber qué cambia: una respuesta cuenta como correcta si está a menos de 5 % de la referencia "
        "(números) o si sus nombres coinciden en un 80 % o más (listas).", "",
        "El revisor no puede ser quien aprobó las preguntas como requisito de negocio. Tiempo estimado: una o dos "
        "horas con acceso a las tablas.", ""]
    every_table = sorted({t for e in results["questions"].values() for t in tables_in(last_query(e.get("B")), known)})
    form = []
    for qid, entry in results["questions"].items():
        lines += [f"## {qid}", "", f"> {entry['question']}", "",
                  f"**Respuesta de Rastro, a confirmar:** {shown(entry['reference'])}", "",
                  "**Cómo respondieron las tres formas** (el evaluador, un asistente de IA que solo vio la pregunta):", ""]
        lines += [f"- {NAMES[k]}: {'✅' if entry[k].get('ok') else '❌'} {shown(entry[k].get('answer'))}"
                  for k in NAMES if k in entry]
        for cells in adjudicated.get(qid, []):
            lines += ["", f"**Diferencia ya revisada por el asistente ({cells[0]}):** {cells[1]}. {cells[2]} "
                          f"Resultado: {cells[3]}."]
        query = last_query(entry.get("B"))
        used = tables_in(query, known)
        lines += ["", "**Fuentes**" + (" (las tablas que lee la consulta sin Rastro):" if used else
                                       " (las del dominio; la consulta sin Rastro no llegó a una):"), ""]
        lines += source_lines(used or every_table, known)
        if query:
            ended = entry["B"].get("answer") is not None
            lines += ["", "**Consulta de partida sobre las fuentes tal como vienen**"
                      + ("" if ended else " (no llegó a una respuesta: se agotó el tiempo o falló)") + ":", "",
                      "```sql", query.strip(), "```"]
        lines.append("")
        form.append({"pregunta": qid, "respuesta_rastro": shown(entry["reference"]), "estado": "pendiente",
                     "fuentes_y_version": "; ".join(sorted({known[t][0][0] for t in used}))})
    (out / "paquete.md").write_text("\n".join(lines))
    target = out / "formulario.csv"
    if target.exists():
        print(f"{repo_path(target)} already exists: left as it is (it may hold a review in progress)")
    else:
        with target.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, FORM_COLUMNS)
            writer.writeheader()
            writer.writerows({c: row.get(c, "") for c in FORM_COLUMNS} for row in form)
    print(f"Wrote {repo_path(out / 'paquete.md')} ({len(form)} questions) and the form {repo_path(target)}")


def parse(text, kind):
    if kind == "lista":
        return [item.strip() for item in text.split(";") if item.strip()]
    return float(text.replace(" ", ""))


def differs(checked, rastro):
    """A first look only (the score decides): numbers more than 0.1 % apart, lists with other names."""
    if isinstance(checked, list):
        return {v.upper() for v in checked} != {v.upper() for v in rastro}
    return abs(checked - rastro) > 0.001 * max(abs(rastro), 1)


def record(domain):
    here = folder(domain)
    form = here / "revision" / "formulario.csv"
    questions = {q["id"]: q for q in yaml.safe_load((here / "eval" / "questions.yaml").read_text())["questions"]}
    rows = {r["pregunta"]: r for r in csv.DictReader(form.open(encoding="utf-8"))}
    required = ["respuesta_revisada", "fuentes_y_version", "como_lo_verifique", "revisor", "fecha"]
    pending = [qid for qid in questions
               if rows.get(qid, {}).get("estado") != "revisada" or any(not rows[qid].get(c, "").strip() for c in required)]
    if pending:
        print(f"{len(questions) - len(pending)} of {len(questions)} reviewed; pending: {', '.join(pending)}. "
              "Nothing written: the references change only when every question is reviewed.")
        return 1
    answers = {qid: parse(rows[qid]["respuesta_revisada"], q["kind"]) for qid, q in questions.items()}
    reviewers = sorted({rows[qid]["revisor"].strip() for qid in questions})
    dates = sorted({rows[qid]["fecha"].strip() for qid in questions})
    (here / "eval" / "referencias.json").write_text(json.dumps({
        "nota": f"Referencias revisadas con las fuentes, sin Rastro, por {', '.join(reviewers)} "
                f"({dates[0]}{' a ' + dates[-1] if len(dates) > 1 else ''}).",
        "answers": answers}, ensure_ascii=False, indent=1))
    subprocess.run([sys.executable, str(LAYER / "evaluar.py"), domain, "puntaje"], check=True,
                   stdout=subprocess.DEVNULL)
    manifest = here / "reference-evidence.yaml"
    data = yaml.safe_load(manifest.read_text()) if manifest.exists() else {}
    data["questions_sha256"] = digest(here / "eval" / "questions.yaml")
    run = data.setdefault("run", {})
    run["result_artifact"] = {"path": repo_path(here / "resultados.json"), "sha256": digest(here / "resultados.json")}
    run["attempt_artifacts"] = [{"path": repo_path(p), "sha256": digest(p)}
                                for p in sorted((here / "respuestas").glob("*-0-*.json"))]
    scored = json.loads((here / "resultados.json").read_text())["questions"]
    known = sources()
    read = sorted({t for e in scored.values() for t in tables_in(last_query(e.get("B")), known)})
    run["source_versions"] = {t: f"{known[t][1] or 's/v'}, cargada el {known[t][3]}"
                                 + (f", sha256 {known[t][2]}" if known[t][2] else "") for t in read}
    data["references"] = {qid: {
        "source": rows[qid]["fuentes_y_version"].strip(), "source_version": rows[qid]["fuentes_y_version"].strip(),
        "checked_answer": answers[qid], "reviewer": rows[qid]["revisor"].strip(),
        "reviewed_on": rows[qid]["fecha"].strip(), "adjudication": rows[qid]["como_lo_verifique"].strip(),
        "independent": True, "status": "approved", "artifact": repo_path(form), "sha256": digest(form)}
        for qid in questions}
    manifest.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    changed = [qid for qid in questions if differs(answers[qid], parse(rows[qid]["respuesta_rastro"], questions[qid]["kind"]))]
    print(f"Recorded {len(questions)} reviewed references and scored again: {repo_path(here / 'resultados.md')}.")
    print("Answers written differently from Rastro's (check them against the new score): "
          + (", ".join(changed) if changed else "none"))
    for k, totals in json.loads((here / "resultados.json").read_text())["totals"].items():
        print(f"  {NAMES[k]}: {totals['correct']} of {len(scored)} correct")
    print(f"Then: python layer/method.py publication {domain} (the evaluation run's model and prompts are the "
          "evaluator's to record, not the reviewer's)")
    return 0


if __name__ == "__main__":
    command_domain = sys.argv[1:3]
    if len(command_domain) != 2 or command_domain[1] not in {"build", "record"}:
        sys.exit(__doc__)
    sys.exit(build(command_domain[0]) if command_domain[1] == "build" else record(command_domain[0]))
