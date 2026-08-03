# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# ZXING COMPONENT BRIDGE
# ==============================================================================

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


_component = components.declare_component(
    "zxing_barcode",
    path=str(COMPONENT_PATH)
)


def scan_barcode():

    value = _component(
        key="zxing_barcode_test",
        default=""
    )

    st.write(
        "COMPONENT RAW:",
        repr(value)
    )

    return value
