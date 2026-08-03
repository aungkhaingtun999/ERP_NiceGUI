from pathlib import Path
import streamlit.components.v1 as components


_component_func = components.declare_component(
    "zxing_barcode",
    path=str(
        Path(__file__).resolve().parents[2]
        / "erp_components"
        / "zxing_barcode"
        / "frontend"
    ),
)


def scan_barcode():

    barcode = _component_func(
        key="zxing_barcode_scanner",
        default=""
    )

    if barcode is None:
        return ""

    return str(barcode).strip()
