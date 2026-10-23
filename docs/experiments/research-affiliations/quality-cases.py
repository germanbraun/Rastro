"""Extra cases for the afiliaciones quality rules, with the severity each must report.

The shared runner checks one good and one broken example per rule and keeps no severity (process note 34). These
cases come from GPT's review of 6f3e970: a withdrawn record must be a warning, not a violation; a missing status must
not pass as active; free text must not pass as a person's confirmation; blank evidence must fail. Each case runs one
rule, without inference, and asserts the set of severities in the report. Writes quality-cases.json.

Run on the machine (Python with pyshacl): python3 docs/experiments/research-affiliations/quality-cases.py
"""

import hashlib
import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import RDF, Namespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ontology"))
import calidad  # noqa: E402

SH = Namespace("http://www.w3.org/ns/shacl#")
IDENT = ('e:id a afiliaciones:Identification ; afiliaciones:ofMention e:m ; afiliaciones:identifies <https://ror.org/1> ; '
         'prov:wasDerivedFrom fuente:crossref, fuente:ror ; ')
DOUBT = ('e:d a afiliaciones:DoubtfulCandidate ; afiliaciones:reviewDecision "reject" ; '
         'afiliaciones:decisionReason "Lugar fuera de Argentina." ; ')
CASES = [
    ("RegistroActivo", "active record", 'e:i afiliaciones:identifies e:o . e:o afiliaciones:status "active" .', []),
    ("RegistroActivo", "withdrawn record is a warning",
     'e:i afiliaciones:identifies e:o . e:o afiliaciones:status "withdrawn" .', ["Warning"]),
    ("RegistroActivo", "missing status is not active", "e:i afiliaciones:identifies e:o . e:o afiliaciones:country \"AR\" .",
     ["Violation"]),
    ("ConfirmadaPorPersona", "pending is informational", DOUBT + 'afiliaciones:humanConfirmation "pending" .', ["Info"]),
    ("DudosaDecidida", "pending is the only valid state", DOUBT + 'afiliaciones:humanConfirmation "pending" .', []),
    ("DudosaDecidida", "empty confirmation", DOUBT + 'afiliaciones:humanConfirmation "" .', ["Violation"]),
    ("DudosaDecidida", "«no» as confirmation", DOUBT + 'afiliaciones:humanConfirmation "no" .', ["Violation"]),
    ("DudosaDecidida", "free text as confirmation", DOUBT + 'afiliaciones:humanConfirmation "banana" .', ["Violation"]),
    ("DudosaDecidida", "«confirmed» without a record", DOUBT + 'afiliaciones:humanConfirmation "confirmed" .', ["Violation"]),
    ("DudosaDecidida", "missing confirmation state", DOUBT.rstrip("; ") + " .", ["Violation"]),
    ("DudosaDecidida", "blank decision reason",
     'e:d a afiliaciones:DoubtfulCandidate ; afiliaciones:reviewDecision "reject" ; afiliaciones:decisionReason "  " ; '
     'afiliaciones:humanConfirmation "pending" .', ["Violation"]),
    ("IdentificacionCompleta", "complete", IDENT + 'afiliaciones:rule "R1" ; afiliaciones:sourceText "Nombre y Argentina." .', []),
    ("IdentificacionCompleta", "blank evidence", IDENT + 'afiliaciones:rule "R1" ; afiliaciones:sourceText "   " .',
     ["Violation"]),
    ("IdentificacionCompleta", "blank rule", IDENT + 'afiliaciones:rule " " ; afiliaciones:sourceText "Nombre y Argentina." .',
     ["Violation"]),
    ("OrganizacionEnArgentina", "typed Argentine but only GB",
     'e:i afiliaciones:identifies e:o . e:o a afiliaciones:ArgentineOrganization ; afiliaciones:country "GB" .',
     ["Violation"]),
    ("MencionCompleta", "blank text",
     'e:m a afiliaciones:AffiliationMention ; afiliaciones:inPublication e:p ; afiliaciones:affiliationText " " .',
     ["Violation"]),
]


def main():
    config = calidad.QualityConfig.load("afiliaciones")
    shapes = {str(shape).rsplit("#", 1)[-1]: graph for shape, graph in calidad.bloques(config)}
    results, failures = [], 0
    for rule, label, data, expected in CASES:
        _, report, _ = validate(calidad.example_graph(config, data), shacl_graph=shapes[rule], advanced=True, inference="none")
        got = sorted({str(report.value(r, SH.resultSeverity)).rsplit("#", 1)[-1]
                      for r in report.subjects(RDF.type, SH.ValidationResult)})
        ok = got == sorted(expected)
        failures += not ok
        results.append({"rule": rule, "case": label, "expected": expected, "got": got, "passed": ok})
        print(f"{'ok  ' if ok else 'FAIL'} {rule}: {label} -> {got or 'conforms'}")
    (Path(__file__).parent / "quality-cases.json").write_text(
        json.dumps({"rules_sha256": hashlib.sha256(config.rules.read_bytes()).hexdigest(), "cases": results, "passed": not failures},
                   indent=2, ensure_ascii=False) + "\n")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
