"""The customer setup (infra/docker-compose.customer.yml): what can be checked without running Docker. Running it is
checked by infra/customer/check.py."""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))


class ComposeLoader(yaml.SafeLoader):
    """Reads Compose's own tags (!override, !reset) as plain values."""


ComposeLoader.add_multi_constructor("!", lambda loader, tag, node: loader.construct_sequence(node)
                                    if isinstance(node, yaml.SequenceNode) else loader.construct_scalar(node))


def compose(name):
    return yaml.load((ROOT / "infra" / name).read_text(), Loader=ComposeLoader)


def test_reader_password_comes_from_env_or_is_the_name(monkeypatch):
    import answer
    monkeypatch.setenv("PG_DB", "rastro")
    monkeypatch.delenv("RASTRO_READER_PASSWORD", raising=False)
    assert answer.reader_dsn("energia_reader").endswith("user=energia_reader password=energia_reader")
    monkeypatch.setenv("RASTRO_READER_PASSWORD", "s3cret")
    assert answer.reader_dsn("energia_reader").endswith("user=energia_reader password=s3cret")


def test_override_names_only_existing_services_and_hardens_every_ontop():
    base, customer = compose("docker-compose.yml")["services"], compose("docker-compose.customer.yml")["services"]
    assert set(customer) - {"proxy"} <= set(base)
    ontops = {name for name in base if name.startswith("ontop")}
    assert ontops <= set(customer), "every Ontop service needs the customer settings"
    for name in ontops:
        assert customer[name]["environment"]["ONTOP_DEV_MODE"] == "false"
        assert all(port.startswith("127.0.0.1:") for port in customer[name]["ports"])


def test_only_the_proxy_is_open_to_the_network():
    customer = compose("docker-compose.customer.yml")["services"]
    for name, service in customer.items():
        if name != "proxy" and "ports" in service:
            assert all(port.startswith("127.0.0.1:") for port in service["ports"]), name
