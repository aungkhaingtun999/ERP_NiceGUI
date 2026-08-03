# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# DEBUG
# ==============================================================================

import streamlit as st


def scan_barcode():

    st.subheader(
        "📷 Barcode Scanner Test"
    )


    barcode = st.text_input(
        "Scan Barcode Here",
        key="debug_barcode"
    )


    return barcode
