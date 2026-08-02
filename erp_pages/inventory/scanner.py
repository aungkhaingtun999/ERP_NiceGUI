# ==============================================================================
# erp_pages/inventory/scanner.py
# MOBILE INVENTORY v2
# Barcode Scanner Engine
# ==============================================================================


import streamlit as st



def manual_barcode_input():

    return st.text_input(
        "⌨️ Manual Barcode / SKU",
        placeholder="Enter barcode..."
    ).strip()



def decode_barcode(image):

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



def camera_barcode_scan():

    image = st.camera_input(
        "📷 Scan Barcode"
    )


    if image:

        return decode_barcode(image)


    return None



# ==========================================================
# MAIN SCANNER FUNCTION
# ==========================================================

def get_barcode():

    """
    Scanner priority

    1. Camera
    2. Manual Input
    """

    barcode = camera_barcode_scan()


    if barcode:

        return barcode


    return manual_barcode_input()
