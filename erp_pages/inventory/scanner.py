# ==============================================================================
# erp_pages/inventory/scanner.py
# MOBILE INVENTORY v2
# Enterprise Barcode Scanner Engine
# OpenCV + pyzbar + Image Enhancement
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
# IMAGE PREPROCESS
# ------------------------------------------------------------------------------

def preprocess_image(img_bgr):

    import cv2
    import numpy as np

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Contrast improve
    gray = cv2.equalizeHist(gray)

    # Sharpen
    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    sharp = cv2.filter2D(gray, -1, kernel)

    return sharp


# ------------------------------------------------------------------------------
# OPENCV DECODER
# ------------------------------------------------------------------------------

def decode_opencv(img_bgr):

    import cv2

    detector = cv2.barcode_BarcodeDetector()

    result = detector.detectAndDecode(img_bgr)

    # OpenCV version compatibility
    if len(result) == 4:
        ok, decoded_info, decoded_type, points = result

    elif len(result) == 3:
        decoded_info, decoded_type, points = result
        ok = bool(decoded_info)

    else:
        return None

    if ok and decoded_info:

        value = decoded_info[0].strip()

        # Reject invalid short reads like "8"
        if len(value) < 8:
            return None

        return value

    return None


# ------------------------------------------------------------------------------
# PYZBAR DECODER
# ------------------------------------------------------------------------------

def decode_pyzbar(img_pil):

    try:

        from pyzbar.pyzbar import decode

        result = decode(img_pil)

        if result:

            value = result[0].data.decode("utf-8").strip()

            if len(value) >= 8:
                return value

    except Exception:
        return None

    return None


# ------------------------------------------------------------------------------
# MAIN DECODER
# ------------------------------------------------------------------------------

def decode_barcode(image):

    try:

        import cv2
        import numpy as np
        from PIL import Image

        # Streamlit image → PIL
        img_pil = Image.open(image).convert("RGB")

        # PIL → OpenCV
        img_bgr = cv2.cvtColor(
            np.array(img_pil),
            cv2.COLOR_RGB2BGR
        )

        # Enhanced image
        processed = preprocess_image(img_bgr)

        # -------------------------------------------------
        # 1. pyzbar original (best for EAN13)
        # -------------------------------------------------

        value = decode_pyzbar(img_pil)

        if value:
            return value

        # -------------------------------------------------
        # 2. pyzbar processed
        # -------------------------------------------------

        processed_pil = Image.fromarray(processed)

        value = decode_pyzbar(processed_pil)

        if value:
            return value

        # -------------------------------------------------
        # 3. OpenCV original
        # -------------------------------------------------

        value = decode_opencv(img_bgr)

        if value:
            return value

        # -------------------------------------------------
        # 4. OpenCV processed
        # -------------------------------------------------

        value = decode_opencv(
            cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        )

        if value:
            return value

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

        st.warning(
            "❌ Barcode not detected. Try again with better light."
        )

    return barcode


# ------------------------------------------------------------------------------
# MAIN ENTRY
# ------------------------------------------------------------------------------

def get_barcode():

    barcode = camera_barcode_scan()

    if barcode:
        return barcode

    return manual_barcode_input()
