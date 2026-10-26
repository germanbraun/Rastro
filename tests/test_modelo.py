"""Rastro Lab: the model and the texts of its explanations, with made-up data."""
import numpy as np
import pandas as pd

import modelo


def pozos():
    """Six wells in two concessions: the 2024 ones train, the 2025 ones are tested."""
    return pd.DataFrame({
        "idpozo": ["1", "2", "3", "4", "5", "6"],
        "inicio": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2025-01-01", "2025-02-01"]),
        "grupo": ["YPF", "YPF", "TOTAL", "TOTAL", "YPF", "TOTAL"],
        "area": ["A", "A", "B", "B", "A", "B"],
        "pct": [50.0, 50.0, 55.0, 55.0, 50.0, np.nan],
        "gas": [40.0, 44.0, 60.0, 64.0, 42.0, 61.0],
    })


def test_los_aportes_suman_la_prediccion():
    df = pozos()
    r = modelo.entrenar(df, ["grupo", "area"], ["pct"])
    suma = r["base"] + r["aportes"].sum(axis=1).values
    assert np.allclose(suma, r["pred"])


def test_un_dato_que_falta_no_suma_ni_resta():
    df = pozos()
    r = modelo.entrenar(df, ["grupo", "area"], ["pct"])
    assert abs(r["aportes"].loc[5, "pct"]) < 1e-9   # well 6 has no stake: the average is used


def test_el_modelo_aprende_la_concesion():
    r = modelo.entrenar(pozos(), ["grupo", "area"], ["pct"])
    assert r["pred"][5] > r["pred"][4]               # B gave more gas than A in training
    assert r["error"] < 10


def test_porcentaje_del_mapa_busca_el_nombre_tal_cual():
    texto = "<br> PAN AMERICAN ENERGY SL: 18.18 %<br> TOTAL AUSTRAL S.A.: 27.27 %"
    assert modelo.porcentaje_del_mapa(texto, "TOTAL AUSTRAL S.A.") == 27.27
    assert np.isnan(modelo.porcentaje_del_mapa(texto, "PLUSPETROL S.A."))


def test_nombres_para_leer():
    assert modelo.nombre("YPF S.A.") == "YPF S.A."
    assert modelo.nombre("PAN AMERICAN ENERGY SL") == "Pan American Energy SL"
    assert modelo.concesion("LAS TACANAS II") == "Las Tacanas II"


def test_numeros_en_castellano():
    assert modelo.num(12345.67) == "12.345,7"
    assert modelo.signo(3.94) == "+3,9"
    assert modelo.signo(-4.9) == "−4,9"


def test_marca_de_datos_que_no_salen_tal_cual():
    assert modelo.marca("mismo nombre normalizado") == ""
    assert modelo.marca("corrección revisada con documento") == "dato corregido con documento"
    assert "revisada por IA" in modelo.marca("corrección revisada")
    assert modelo.marca(float("nan")) == ""


def test_meses_tarde():
    fila = pd.Series({"inicio": pd.Timestamp("2025-03-01"), "fracCargada": pd.Timestamp("2025-06-24")})
    assert modelo.meses_tarde(fila) == 3
    fila["fracCargada"] = pd.Timestamp("2025-02-10")
    assert modelo.meses_tarde(fila) == 0
