# ==============================================================================
# ZXING BARCODE SCANNER v2 ENTERPRISE
# Streamlit Camera Barcode Integration
# ==============================================================================

import os
import streamlit as st
import streamlit.components.v1 as components



CURRENT = os.path.abspath(__file__)


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../.."
    )
)


FRONTEND = os.path.join(
    PROJECT_ROOT,
    "erp_components",
    "zxing_scanner",
    "frontend"
)



zxing_component = components.declare_component(
    "zxing_scanner",
    path=FRONTEND
)



def zxing_scanner():


    result = zxing_component(
        key="zxing_scanner_v3",
        default="",
        height=450
    )


    if result:


        barcode = str(result).strip()


        if barcode:


            st.session_state.barcode_value = barcode


            return barcode



    return None
