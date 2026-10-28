"""The app's frame and the shared template know no domain: what is specific to a domain is in its YAML
(app/dominios/<domain>.yaml), in the registry (layer/dominios.yaml) or in its extension (app/extensions/<name>/).

The check reads the code itself, not its comments or docstrings (an example there is fine): no domain, no data source
and no word of one domain's business may appear in a name or a string of the shared code.
"""
import ast
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SHARED = [ROOT / "app/app.py", ROOT / "app/idioma.py", ROOT / "app/contraste.py", ROOT / "app/enlaces.py",
          ROOT / "app/grafo.py", ROOT / "app/check_domain.py", ROOT / "layer/answer.py",
          *sorted((ROOT / "app/dominio").glob("*.py"))]
# Words of one domain's business that slipped into shared code before (units, records)
BUSINESS = ["pozo", "wells?", "concesi[oó]n", "m³", "m3", "ypf"]


def forbidden():
    """Every domain and every source the registry knows, and the business words above."""
    registry = yaml.safe_load((ROOT / "layer/dominios.yaml").read_text())
    words = set(registry)
    for spec in registry.values():
        words |= set(spec.get("term_sources") or {}) | set(spec.get("link_sources") or {})
        words |= {spec["label_source"]} if spec.get("label_source") else set()
    words -= {"rastro"}   # Rastro's own links are not a domain's
    return re.compile(r"\b(" + "|".join(sorted({re.escape(w) for w in words} | set(BUSINESS))) + r")\b", re.I)


def code_texts(path):
    """(line, text) of every name, attribute and string of the code, without its docstrings."""
    tree = ast.parse(path.read_text())
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body
                  and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.lineno, node.value
        elif isinstance(node, ast.Name):
            yield node.lineno, node.id
        elif isinstance(node, ast.Attribute):
            yield node.lineno, node.attr


def test_the_shared_code_names_no_domain():
    pattern = forbidden()
    found = [f"{path.relative_to(ROOT)}:{line}: {text[:60]!r}"
             for path in SHARED for line, text in code_texts(path) if pattern.search(text)]
    assert not found, "domain words in shared code (move them to the domain's YAML or extension):\n" + "\n".join(found)


def test_the_shared_code_imports_no_extension():
    """The template reaches a domain's code only through dominio/extension.py, by the name in the domain's YAML."""
    for path in SHARED:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [node.module or ""] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
                assert not any(n.split(".")[0] == "extensions" for n in names), f"{path.name} imports {names}"


def test_the_guard_catches_a_domain_word(tmp_path):
    """The check itself works: a source name in a string is caught, the same name in a docstring is not."""
    sample = tmp_path / "sample.py"
    sample.write_text('"""Reads usaspending."""\nSOURCE = "usaspending"\n')
    assert [line for line, text in code_texts(sample) if forbidden().search(text)] == [2]
