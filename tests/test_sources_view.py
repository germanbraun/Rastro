"""«Las fuentes de datos»: every domain that describes its sources does it completely, in both languages, and
names sources that exist in Rastro's registry."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
# Sources are registered where they are created or loaded: the init schema and each loader that inserts into
# rastro_meta.source («('id', 'name', …»)
REGISTRATIONS = [ROOT / "infra/postgres/init/01-schemas.sql", *(ROOT / "data").glob("*/schema.sql"),
                 *(ROOT / "data").glob("*/load.py")]
REGISTERED = {source for path in REGISTRATIONS if "rastro_meta.source" in path.read_text()
              for source in re.findall(r"\(\s*'([a-z_0-9]+)',\s*'", path.read_text())}
DOMAINS = [p for p in sorted((ROOT / "app/dominios").glob("*.yaml"))
           if not p.name.endswith(".en.yaml") and "fuentes_detalle" in yaml.safe_load(p.read_text())]


def test_each_described_source_is_complete_and_registered():
    assert DOMAINS, "no domain describes its sources"
    for path in DOMAINS:
        entries = yaml.safe_load(path.read_text())["fuentes_detalle"]
        assert len({e["id"] for e in entries}) == len(entries), path.name
        for e in entries:
            assert e["id"] in REGISTERED, f"{path.name}: {e['id']} is not in rastro_meta.source"
            for key in ("nombre", "organismo", "que_es", "que_usa"):
                assert isinstance(e.get(key), str) and e[key].strip(), f"{path.name}: {e['id']} {key}"
            assert all(isinstance(item, str) for item in e.get("cuidado", [])), f"{path.name}: {e['id']} cuidado"


def test_the_english_overlay_covers_every_source():
    for path in DOMAINS:
        english = path.with_name(path.stem + ".en.yaml")
        spanish_ids = [e["id"] for e in yaml.safe_load(path.read_text())["fuentes_detalle"]]
        english_entries = yaml.safe_load(english.read_text()).get("fuentes_detalle", [])
        assert [e["id"] for e in english_entries] == spanish_ids, english.name
        for e in english_entries:
            assert all(isinstance(item, str) for item in e.get("cuidado", [])), f"{english.name}: {e['id']}"
