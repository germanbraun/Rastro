"""«Método» (app/dominio/method_view.py): each step's status, read from the repository's evidence and given loads."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "layer"))
from dominio import method_view  # noqa: E402

ENERGY_SOURCES = ["ambiental", "capitulo4", "enargas", "fractura", "gleif", "ign", "sig_energia", "trayectorias",
                  "wikidata"]


def status(domain, loads):
    return {key: mark for key, mark, _ in method_view.steps(domain, None, loads, root=ROOT)}


def test_every_step_of_the_method_has_a_row():
    keys = [key for key, _, _ in method_view.steps("energia", None, {}, root=ROOT)]
    assert keys == ["questions", "sources", "dictionary", "mapping", "links", "quality", "evaluate", "show", "maintain"]


def test_sources_count_only_the_registered_ones():
    loaded = status("energia", {s: "2026-10-21" for s in ENERGY_SOURCES})
    assert loaded["sources"] == method_view.DONE   # «lab» and «rastro» are not sources Rastro loads
    half = status("energia", {**{s: "2026-10-21" for s in ENERGY_SOURCES[:-1]}, ENERGY_SOURCES[-1]: None})
    assert half["sources"] == method_view.WAITING


def test_what_waits_for_a_person_is_never_done():
    assert status("energia", {})["links"] == method_view.WAITING        # AI-reviewed corrections with a «motivo»
    assert status("afiliaciones", {})["links"] == method_view.WAITING   # its own human_confirmation column
    assert status("energia", {})["evaluate"] == method_view.WAITING     # independent references still missing


def test_a_piece_not_built_says_so():
    assert status("proveedores", {})["quality"] == method_view.MISSING
