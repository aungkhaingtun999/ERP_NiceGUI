# ==============================================================================
# erp_pages/inventory/scanner.py
# MOBILE INVENTORY v2
# OpenCV Barcode Scanner (Cloud Friendly)
# ==============================================================================

import streamlit as st


# ------------------------------------------------------------------------------
# MANUAL INPUT
# ------------------------------------------------------------------------------

def manual_barcode_input():

    return st.text_input(
        "⌨️ Manual Barcode / SKU",
        placeholder="Enter barcode..."
    ).strip()


# ------------------------------------------------------------------------------
# BARCODE DECODER (OpenCV only)
# ------------------------------------------------------------------------------

def decode_barcode(image):

    try:

        import cv2
        import numpy as np
        from PIL import Image

        # Streamlit UploadedFile → PIL
        img_pil = Image.open(image).convert("RGB")

        # PIL → OpenCV
        img = np.array(img_pil)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Barcode detector
        detector = cv2.barcode_BarcodeDetector()

        ok, decoded_info, decoded_type, points = detector.detectAndDecode(img)

        if ok and decoded_info:

            value = decoded_info[0]

            if value:
                return value.strip()

    except Exception as e:

        st.error(f"SCAN ERROR: {e}")

    return None


# ------------------------------------------------------------------------------
# CAMERA SCAN
# ------------------------------------------------------------------------------

def camera_barcode_scan():

    image = st.camera_input("📷 Scan Barcode")

    if image is None:
        return None

    barcode = decode_barcode(image)

    if barcode:
        st.success(f"📷 Barcode: {barcode}")
    else:
        st.warning("❌ Barcode not detected. Try again.")

    return barcode


# ------------------------------------------------------------------------------
# MAIN ENTRY
# ------------------------------------------------------------------------------

def get_barcode():

    barcode = camera_barcode_scan()

    if barcode:
        return barcode

    return manual_barcode_input()
