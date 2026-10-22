"""Every configured domain's SHACL examples execute against its own rules and namespace."""
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ontology"))
import calidad

REGISTRY = yaml.safe_load((ROOT / "layer/dominios.yaml").read_text())
DOMAINS = [name for name, cfg in REGISTRY.items() if cfg.get("method", {}).get("quality")]


@pytest.mark.parametrize("domain", DOMAINS)
def test_each_domain_checks_its_own_good_and_bad_examples(domain):
    assert calidad.check_examples(calidad.QualityConfig.load(domain)) > 0
