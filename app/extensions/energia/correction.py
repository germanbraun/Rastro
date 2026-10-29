"""One correction, every result: the oil and gas correction test as the demo shows it (layer/energia/cambio/)."""
import pandas as pd
import streamlit as st

import idioma
from dominio import common


def show_correction(result, tech, part=None):
    """One correction, every result: what changes in Rastro Layer and in Rastro Lab when a concession's corrected
    share is set, without touching anything else. part="layer" or "lab" shows only that half (the demo tells the
    correction in Rastro Layer and comes back to it in Rastro Lab)."""
    con, sin = result.get("con"), result.get("sin")
    if not (con and sin):
        st.info(idioma.t("energia.correction.missing"))
        return

    def m3(v):
        return f"{idioma.number(v / 1e6, 2)} M m³"

    def pct(v):
        return f"{v:g} %" if idioma.lang() == "en" else f"{v:g} %".replace(".", ",")

    layer = [   # (where, without the correction, with the correction)
        (idioma.t("energia.correction.row_rastro"), m3(sin["layer_C"]), m3(con["layer_C"])),
        (idioma.t("energia.correction.row_sql_rastro"), m3(sin["layer_D"]), m3(con["layer_D"])),
        (idioma.t("energia.correction.row_without"), m3(sin["layer_B"]), m3(con["layer_B"])),
    ]
    lab = [
        (idioma.t("energia.correction.row_input_with"), pct(sin["lab_B_pct"]), pct(con["lab_B_pct"])),
        (idioma.t("energia.correction.row_input_without"), pct(sin["lab_A_pct"]), pct(con["lab_A_pct"])),
        (idioma.t("energia.correction.row_explanation"), idioma.t("energia.correction.unmarked"),
         idioma.t("energia.correction.marked") if con["lab_B_marca"] else idioma.t("energia.correction.unmarked")),
    ]
    filas = {"layer": layer, "lab": lab}.get(part, layer + lab)
    yes, no = idioma.t("energia.correction.yes"), idioma.t("energia.correction.no")
    headers = [idioma.t(f"energia.correction.col_{c}") for c in ("where", "before", "after", "changed")]
    df = pd.DataFrame([dict(zip(headers, (a, b, c, yes if b != c else no))) for a, b, c in filas])
    st.caption(idioma.t(f"energia.correction.what_{part}" if part else "energia.correction.what"))
    common.tabla(df, key=f"demo_correccion_{part or 'todo'}")
    if part != "lab":
        st.markdown(common.md(idioma.t("energia.correction.where_fixed", places=result["lugares_sin_rastro"])))
    if tech:
        st.caption(idioma.t("energia.correction.measured"))
