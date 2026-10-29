"""`method.py new-domain`: the scaffold, on copies of the registry and the compose files (never the real ones)."""
import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))
import method  # noqa: E402
import new_domain  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    for path in ("layer/dominios.yaml", "app/dominios.yaml", "infra/docker-compose.yml", "infra/docker-compose.customer.yml"):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / path, tmp_path / path)
    return tmp_path


def test_scaffold_passes_the_registry_check(repo):
    written, port = new_domain.scaffold("ensayo", "un dominio de prueba", root=repo)
    registry = yaml.safe_load((repo / "layer/dominios.yaml").read_text())
    assert method.registry_errors({"ensayo": registry["ensayo"]}, root=repo) == []
    assert port == new_domain.next_port((ROOT / "infra/docker-compose.yml").read_text())
    compose = yaml.safe_load((repo / "infra/docker-compose.yml").read_text())["services"]
    assert compose["ontop-ensayo"]["ports"] == [f"${{ONTOP_ENSAYO_PORT:-{port}}}:8080"]
    assert "ontop-ensayo:\n    environment: *ontop-customer" in (repo / "infra/docker-compose.customer.yml").read_text()
    # The mapping's one map reads the sources, so Ontop starts; its terms are in the ontology
    assert "rastro_meta.source WHERE false" in (repo / "mappings/ensayo.r2rml.ttl").read_text()
    assert "ensayo:DataSource a owl:Class" in (repo / "ontology/ensayo/ensayo.ttl").read_text()
    # The app lists it from the start and hides it until it has a question (app.py)
    assert registry["ensayo"]["method"]["app"] == "app/dominios/ensayo.yaml"
    assert yaml.safe_load((repo / "app/dominios.yaml").read_text())[-1]["id"] == "ensayo"
    assert yaml.safe_load((repo / "app/dominios/ensayo.yaml").read_text())["preguntas"] == []


def test_scaffold_refuses_to_overwrite(repo):
    new_domain.scaffold("ensayo", "un dominio de prueba", root=repo)
    before = (repo / "layer/dominios.yaml").read_text()
    with pytest.raises(ValueError, match="already"):
        new_domain.scaffold("ensayo", "otra vez", root=repo)
    with pytest.raises(ValueError, match="already"):
        new_domain.scaffold("energia", "ya existe", root=repo)
    assert (repo / "layer/dominios.yaml").read_text() == before


def test_scaffold_refuses_a_bad_name(repo):
    with pytest.raises(ValueError, match="lowercase"):
        new_domain.scaffold("Mi-Dominio", "x", root=repo)
