import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


COMPONENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "erp_components"
    / "zxing_barcode"
    / "frontend"
)

st.write("PATH:", COMPONENT_PATH)
st.write("EXISTS:", COMPONENT_PATH.exists())


_component = components.declare_component(
    "zxing_test",
    path=str(COMPONENT_PATH)
)


def scan_barcode():

    value = _component(
        key="zxing_test",
        default=""
    )

    return value
