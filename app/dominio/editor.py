"""The two editors of «Bajo el capó»: a SPARQL query and a domain's R2RML mapping, each in a code editor (Ace) and
checked before it runs or is saved. Each check returns problems as (line, column, text), so the editor marks the line.

A mapping is saved to the domain's real file only when it passes its checks; the file it replaces is kept in
mappings/.backup/ (not versioned), so a save can be undone, and Ontop, which watches the file, reloads it.
"""
import difflib
import importlib.util
import time
from datetime import datetime, timezone

import rdflib
import streamlit as st
from rdflib.namespace import RDF
from rdflib.plugins.sparql import prepareQuery

import answer
import idioma

RR = rdflib.Namespace("http://www.w3.org/ns/r2rml#")


def code_editor(value, language, key, problems=(), height=18):
    """A code editor with line numbers and colors; each problem (line, column, text) is marked on its line.
    Returns the text after «Apply» (or Ctrl+Enter)."""
    from streamlit_ace import st_ace
    annotations = [{"row": max(line - 1, 0), "column": max(column - 1, 0), "text": text, "type": "error"}
                   for line, column, text in problems]
    return st_ace(value=value, language=language, theme="chrome", key=key, min_lines=height, max_lines=height * 3,
                  font_size=15, tab_size=2, wrap=True, annotations=annotations, auto_update=False)


def show_problems(problems, warnings, ok_text):
    """The check's verdict under the editor: errors stop, warnings only inform."""
    for line, column, text in problems:
        st.error(idioma.t("dominio.editor.problem", line=line, column=column, text=text))
    for text in warnings:
        st.warning(text)
    if not problems and not warnings:
        st.success(ok_text)


def declared_terms(domain):
    """The IRIs the domain's ontology declares, and its namespace."""
    spec = answer.DOMAINS[domain]
    ontology = rdflib.Graph().parse(answer.ROOT / spec["ontology"])
    namespace = spec["namespace"]
    return namespace, {str(s) for s in ontology.subjects() if str(s).startswith(namespace)}, ontology


def sparql_check(query, domain):
    """(problems, warnings): a syntax error with its line and column, or the terms the dictionary does not declare."""
    try:
        algebra = prepareQuery(query).algebra
    except Exception as error:   # noqa: BLE001 - pyparsing and rdflib raise several kinds; all are syntax
        line, column = getattr(error, "lineno", 1), getattr(error, "col", 1)
        return [(line, column, str(error).split(" (at char")[0])], []
    namespace, declared, _ = declared_terms(domain)
    used = set()
    _iris(algebra, used, set())
    missing = sorted(u.replace(namespace, f"{domain}:") for u in used if u.startswith(namespace) and u not in declared)
    return [], [idioma.t("dominio.editor.unknown_terms", terms=", ".join(missing))] if missing else []


def _iris(node, found, seen):
    """Every IRI in a query's algebra."""
    if id(node) in seen:
        return
    seen.add(id(node))
    if isinstance(node, rdflib.URIRef):
        found.add(str(node))
    elif hasattr(node, "items"):
        for value in node.values():
            _iris(value, found, seen)
    elif isinstance(node, (list, tuple, set)):
        for value in node:
            _iris(value, found, seen)
    elif hasattr(node, "__dict__"):
        for value in vars(node).values():
            _iris(value, found, seen)


def mapping_check(text, domain):
    """(problems, warnings, triples maps): Turtle syntax, R2RML structure (each triples map with a logical table and a
    subject map, each predicate-object map with a predicate and an object), every class and property of the domain
    declared in its ontology, and no shared property with a domain (ontology/check.py)."""
    try:
        mapping = rdflib.Graph().parse(data=text, format="turtle")
    except Exception as error:   # noqa: BLE001 - BadSyntax and others: the parser's message says where
        line = (getattr(error, "lines", 0) or 0) + 1
        return [(line, 1, str(error).splitlines()[-1][:300] if str(error) else type(error).__name__)], [], 0
    lines = text.splitlines()

    def line_of(node):   # the first line that names a triples map (<#Name>), for the editor's mark
        name = str(node).rsplit("#", 1)[-1]
        return next((n for n, line in enumerate(lines, 1) if f"<#{name}>" in line), 1)

    problems = []
    maps = list(mapping.subjects(RDF.type, RR.TriplesMap))
    if not maps:
        problems.append((1, 1, idioma.t("dominio.editor.no_maps")))
    for tm in maps:
        table = mapping.value(tm, RR.logicalTable)
        if table is None or not (mapping.value(table, RR.tableName) or mapping.value(table, RR.sqlQuery)):
            problems.append((line_of(tm), 1, idioma.t("dominio.editor.no_table", map=line_of_name(tm))))
        if mapping.value(tm, RR.subjectMap) is None:
            problems.append((line_of(tm), 1, idioma.t("dominio.editor.no_subject", map=line_of_name(tm))))
        for pom in mapping.objects(tm, RR.predicateObjectMap):
            if not (mapping.value(pom, RR.predicate) or mapping.value(pom, RR.predicateMap)):
                problems.append((line_of(tm), 1, idioma.t("dominio.editor.no_predicate", map=line_of_name(tm))))
            if not (mapping.value(pom, RR.objectMap) or mapping.value(pom, RR.object)):
                problems.append((line_of(tm), 1, idioma.t("dominio.editor.no_object", map=line_of_name(tm))))
    namespace, declared, ontology = declared_terms(domain)
    used = {str(o) for o in mapping.objects(None, RR["class"])} | {str(o) for o in mapping.objects(None, RR.predicate)}
    missing = sorted(u.replace(namespace, f"{domain}:") for u in used if u.startswith(namespace) and u not in declared)
    if missing:
        problems.append((1, 1, idioma.t("dominio.editor.unknown_terms", terms=", ".join(missing))))
    problems += [(1, 1, error) for error in _ontology_check().shared_domain_errors(ontology, mapping)]
    return problems, [], len(maps)


def line_of_name(node):
    return "<#" + str(node).rsplit("#", 1)[-1] + ">"


def _ontology_check():
    """ontology/check.py, which the CI and the ontology-check service also run."""
    path = answer.ROOT / "ontology" / "check.py"
    spec = importlib.util.spec_from_file_location("ontology_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mapping_path(domain):
    return answer.ROOT / answer.DOMAINS[domain]["method"]["mapping"]


def diff(old, new, name):
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                        fromfile=idioma.t("dominio.mapping_editor.diff_now", file=name),
                                        tofile=idioma.t("dominio.mapping_editor.diff_edited", file=name)))


def save_mapping(domain, text):
    """Keeps the current file in mappings/.backup/ and writes the new one. Returns the backup's path."""
    path = mapping_path(domain)
    backups = path.parent / ".backup"
    backups.mkdir(exist_ok=True)
    backup = backups / f"{path.stem}.{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.ttl"
    backup.write_text(path.read_text())
    path.write_text(text)
    return backup


def ontop_answers(domain, seconds=40):
    """Whether the domain's Ontop answers after reloading its mapping: it watches the file and takes a few seconds to
    notice the change, so the first check waits."""
    time.sleep(8)
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            answer.run_sparql_table("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1", domain)
            return True
        except Exception:   # noqa: BLE001 - while it reloads, Ontop refuses or errs
            time.sleep(2)
    return False
