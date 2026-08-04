import streamlit.components.v1 as components
from pathlib import Path

COMPONENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "erp_components"
    / "zxing_scanner"
    / "frontend"
)

_component = components.declare_component(
    "zxing_scanner",
    path=str(COMPONENT_PATH)
)

def scan_barcode():
    value = _component(key="live_barcode_scanner", default="")
    return value or ""
