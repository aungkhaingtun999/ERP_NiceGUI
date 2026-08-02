# ==============================================================================
# erp_pages/inventory/scanner.py
# MOBILE INVENTORY v2
# Barcode Scanner Engine
# ==============================================================================


import streamlit as st


# ==============================================================================
# MANUAL BARCODE INPUT
# Future:
# Camera Scanner → ဒီ function ကိုပဲ value ပို့မယ်
# ==============================================================================


def barcode_input():

    barcode = st.text_input(
        "📷 Barcode / SKU",
        placeholder="Scan or enter barcode..."
    )

    return barcode.strip()



# ==============================================================================
# CAMERA READY INTERFACE
# ==============================================================================


def decode_barcode(image):

    """
    Future camera scanner handler

    image
        Camera captured image

    return:
        barcode string
    """

    return None
