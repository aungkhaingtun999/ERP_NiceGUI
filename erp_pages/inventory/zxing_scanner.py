import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


COMPONENT_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "erp_components"
    / "zxing_barcode"
    / "frontend"
)


zxing_component = components.declare_component(
    "zxing_barcode",
    path=str(COMPONENT_PATH)
)


def scan_barcode():

    st.subheader("📷 Live Barcode Scanner")

    barcode = zxing_component(
        key="barcode_scanner",
        default=""
    )

    if barcode:
        return str(barcode).strip()

    return ""
