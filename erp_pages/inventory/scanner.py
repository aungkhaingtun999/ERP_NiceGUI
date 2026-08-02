# ==============================================================================
# erp_pages/inventory/scanner.py
# MOBILE INVENTORY v2
# Camera + Manual Barcode Scanner Engine
# ==============================================================================


import streamlit as st



# ==============================================================================
# MANUAL BARCODE INPUT
# ==============================================================================


def manual_barcode_input():

    barcode = st.text_input(
        "⌨️ Manual Barcode / SKU",
        placeholder="Enter barcode or SKU..."
    )

    return barcode.strip()



# ==============================================================================
# CAMERA BARCODE SCANNER
# ==============================================================================


def camera_barcode_scan():

    image = st.camera_input(
        "📷 Scan Barcode"
    )


    if image is None:
        return None


    barcode = decode_barcode(image)


    return barcode



# ==============================================================================
# BARCODE DECODER
# ==============================================================================


def decode_barcode(image):

    """
    Barcode decoder engine

    Future:
        pyzbar
        OpenCV
        Bluetooth scanner

    """

    try:

        from PIL import Image
        from pyzbar.pyzbar import decode


        img = Image.open(image)


        result = decode(img)


        if result:

            return result[0].data.decode(
                "utf-8"
            )


    except Exception:

        return None



    return None



# ==============================================================================
# UNIFIED SCANNER
# ==============================================================================


def get_barcode():

    """
    Priority:

    1. Camera Scan
    2. Manual Input

    """

    barcode = camera_barcode_scan()


    if barcode:

        return barcode


    return manual_barcode_input()
