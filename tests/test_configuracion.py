"""The app and repo configuration: that it is read and that what it names exists."""
import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]


def cargar(ruta):
    return yaml.safe_load((RAIZ / ruta).read_text())


def ruta_local(ruta):
    """Configuration paths are the container's (/layer/..., /app/...): they are looked up in the repo."""
    return RAIZ / str(ruta).lstrip("/")


def test_los_yaml_de_la_app_se_leen():
    for f in list((RAIZ / "app").glob("*.yaml")) + list((RAIZ / "app" / "dominios").glob("*.yaml")):
        assert yaml.safe_load(f.read_text()) is not None, f


def test_las_preguntas_de_la_app_tienen_su_consulta():
    for f in (RAIZ / "app" / "dominios").glob("*.yaml"):
        cfg = yaml.safe_load(f.read_text())
        for q in cfg.get("preguntas", []):
            assert ruta_local(q["query"]).exists(), (f.name, q["query"])


def test_la_demo_de_petroleo_y_gas():
    cfg = cargar("app/dominios/energia.yaml")
    pasos = cfg["demo"]
    assert [p["paso"] for p in pasos] == ["Preguntar", "La base cambia", "Predecir", "Una corrección"]
    ids = {q["id"] for q in cfg["preguntas"]}
    for p in pasos:
        assert p.get("tipo", "pregunta") in {"pregunta", "cambio", "lab", "correccion"}
        if p.get("tipo", "pregunta") == "pregunta":
            assert p["pregunta"] in ids
    assert ruta_local(cfg["cambio"]).exists() and ruta_local(cfg["correccion"]).exists()


def test_petroleo_y_gas_abre_primero():
    assert cargar("app/dominios.yaml")[0]["id"] == "energia"


def test_las_skills_de_claude_md_existen():
    """Every skill listed in CLAUDE.md exists, and every skill folder is listed."""
    texto = (RAIZ / "CLAUDE.md").read_text()
    nombradas = set(re.findall(r"^- `([a-z-]+)`:", texto.split("## Repo skills")[1], re.M))
    existentes = {p.parent.name for p in (RAIZ / ".claude" / "skills").glob("*/SKILL.md")}
    assert nombradas == existentes


def test_env_example_sin_claves():
    for linea in (RAIZ / ".env.example").read_text().splitlines():
        if re.match(r"^[A-Z_]*(KEY|TOKEN)=", linea):
            assert linea.split("=", 1)[1].strip() == "", linea
