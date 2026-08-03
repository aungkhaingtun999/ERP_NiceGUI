# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# DEBUG CLEAN VERSION
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


    # DEBUG
    st.write(
        "INNER VALUE:",
        repr(barcode)
    )

    st.write(
        "INNER TYPE:",
        type(barcode).__name__
    )


    if barcode:

        return barcode.strip()


    return ""
