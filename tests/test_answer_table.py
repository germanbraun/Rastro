"""An answer table shows numbers in the interface's format even in a column the domain does not declare (the chat's
queries name their own columns), and leaves ids and years as they are."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "layer"))
from dominio import answers  # noqa: E402


def test_an_undeclared_decimal_column_is_formatted(monkeypatch):
    monkeypatch.setattr(answers.idioma, "lang", lambda: "es")
    rows = [["TOTAL AUSTRAL S.A.", "5246629.44413004950000000000", "2025", "164166"]]
    table = answers.as_table(["empresa", "gas_miles_m3", "anio", "idpozo"], rows, {}, False, {})
    assert table.iloc[0].tolist() == ["TOTAL AUSTRAL S.A.", "5.246.629,4", "2025", "164166"]


def test_the_technical_view_keeps_the_exact_value():
    rows = [["5246629.4441300495"]]
    assert answers.as_table(["gas"], rows, {}, True, {}).iloc[0, 0] == "5246629.4441300495"


def test_only_numbers_with_decimals():
    assert answers.decimal_column(["12.5", None, "3"]) and not answers.decimal_column(["2024", "2025"])
    assert not answers.decimal_column(["YPF S.A.", "1.5"]) and not answers.decimal_column([None])
