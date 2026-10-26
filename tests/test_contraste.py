"""The demo slides' numbers come from the same files and queries as the app (story_numbers), never typed."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import contraste  # noqa: E402


def number(value, decimals):
    return f"{float(value):.{decimals}f}"


def test_story_numbers_reads_each_source(tmp_path):
    quality = {"reglas": [{"id": "Agua", "revisados": 40, "fallas": 2,
                           "ejemplos": [{"dato": "https://x/f/1", "predicciones": ["p1", "p2"]},
                                        {"dato": "https://x/f/2", "predicciones": []}]}]}
    fuera = {"preguntas": {"f1": {"sin_datos": True}, "c1": {"sin_datos": False, "C": {"respuesta": "6910.3"}}}}
    (tmp_path / "calidad.json").write_text(json.dumps(quality))
    (tmp_path / "fuera.json").write_text(json.dumps(fuera))
    (tmp_path / "externo.csv").write_text("empresa,su_parte_m3\nYPF S.A.,12570093.0\n")
    reading = {"divisor": 1000000, "consulta": "ranking"}
    cfg = {"afirmaciones": {"ejemplos": [{"lecturas": [reading, reading]}]},
           "fuera": {"archivo": str(tmp_path / "fuera.json")}, "calidad": {"archivo": str(tmp_path / "calidad.json")},
           "externo": {"guardado": str(tmp_path / "externo.csv")}}
    asked = []

    def sparql(query):
        asked.append(query)
        if query == "ranking":
            return ["empresa", "gas"], [["TOTAL AUSTRAL S.A.", "12335523.9"], ["YPF S.A.", "11728068.7"]]
        return ["n", "m"], [["537184.6", "111515"]] if "VALUES" in query else [["10"]]

    out = contraste.story_numbers(cfg, sparql, number)
    assert out["opera_total"] == "12.3" and out["parte_ypf"] == "11.7"
    assert out["sin_dato"] == "1" and out["control"] == "6910"
    assert out["Agua_fallas"] == "2" and out["Agua_revisados"] == "40" and out["predicciones_afectadas"] == "2"
    assert "<https://x/f/1>" in next(q for q in asked if "VALUES" in q)       # only the data a prediction used
    assert out["agua_afectada"] == "537185" and out["externo_con_lei"] == "1"
    assert "error_b" not in out                                              # Lab only when asked
