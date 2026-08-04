# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# ZXING LIVE BARCODE SCANNER BRIDGE
# ==============================================================================

import streamlit.components.v1 as components
from pathlib import Path


COMPONENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "erp_components"
    / "zxing_scanner"   # ← ဒီနေရာပြောင်းထားတယ်
    / "frontend"
)


scanner_component = components.declare_component(
    "zxing_scanner",
    path=str(COMPONENT_PATH)
)


def scan_barcode():

    barcode = scanner_component(
        key="live_barcode_scanner",
        default=""
    )

    if barcode:
        return str(barcode).strip()

    return ""
