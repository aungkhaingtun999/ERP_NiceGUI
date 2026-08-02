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


# ==============================================================================
# BARCODE DECODER (Improved)
# ==============================================================================

def decode_barcode(image):
    try:
        import numpy as np
        import cv2
        from PIL import Image

        # Streamlit UploadedFile → PIL
        img_pil = Image.open(image).convert("RGB")

        # PIL → OpenCV
        img = np.array(img_pil)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # -------------------------------------------------
        # 1) OpenCV BarcodeDetector
        # -------------------------------------------------

        detector = cv2.barcode_BarcodeDetector()

        ok, decoded_info, decoded_type, points = detector.detectAndDecode(img)

        if ok and decoded_info:
            value = decoded_info[0]

            if value:
                return value.strip()

        # -------------------------------------------------
        # 2) pyzbar fallback
        # -------------------------------------------------

        from pyzbar.pyzbar import decode

        result = decode(img_pil)

        if result:
            return result[0].data.decode("utf-8").strip()

    except Exception as e:
        print("Barcode decode error:", e)

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
