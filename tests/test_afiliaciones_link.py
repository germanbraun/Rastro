"""The affiliations linker's normalization: a glued footnote letter goes, segments stay as boundaries, and generic
acronyms are found from the organizations' names (the defects the blind reference found)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("afiliaciones_link", ROOT / "linking/afiliaciones/link.py")
link = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(link)


def test_a_glued_footnote_letter_is_dropped_but_not_acronyms():
    assert link.norm("AUniversidad de Buenos Aires, Cátedra") == "universidad de buenos aires catedra"
    assert link.norm("EConsejo Nacional") == "consejo nacional"
    assert link.norm("IBioBA-CONICET") == "ibioba conicet"
    assert link.norm("CONICET, Rosario") == "conicet rosario"


def test_mention_segments_are_boundaries_a_name_cannot_cross():
    text = f" {link.norm('PLAPIQUI (UNS-CONICET), Bahía Blanca 8000', segments=True)} "
    assert " conicet bahia blanca " not in text
    assert " conicet " in text and " bahia blanca " in text


def test_initials_skip_connectors():
    assert link.initials("Centro Científico Tecnológico - La Plata", 3) == "cct"
    assert link.initials("Comisión de Investigaciones Científicas", 3) == "cic"
