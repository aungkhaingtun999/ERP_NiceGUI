# ==============================================================================
# erp_components/mobile_scanner/scanner.py
# MOBILE BARCODE SCANNER v4.0
# STREAMLIT CUSTOM COMPONENT + ZXING JS
# ==============================================================================

import os
import streamlit as st
import streamlit.components.v1 as components


# ------------------------------------------------------------------------------
# Component Setup
# ------------------------------------------------------------------------------

COMPONENT_PATH = os.path.join(
    os.path.dirname(__file__),
    "frontend"
)


_mobile_scanner = components.declare_component(
    "mobile_scanner",
    path=COMPONENT_PATH
)



# ------------------------------------------------------------------------------
# Public Function
# ------------------------------------------------------------------------------

def mobile_scanner():

    st.subheader(
        "📷 Barcode Scanner"
    )


    barcode = _mobile_scanner(
        key="mobile_barcode_scanner",
        default=""
    )


    if barcode:

        st.session_state["barcode_value"] = barcode


        st.success(
            f"✅ Barcode : {barcode}"
        )


        return barcode



    st.info(
        "Waiting scan..."
    )


    return None
