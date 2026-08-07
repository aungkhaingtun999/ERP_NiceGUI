# ==============================================================================
# erp_pages/inventory/scanner.py
# ERP ENTERPRISE MOBILE BARCODE SCANNER v3.0
#
# Camera + Manual Input
# Barcode + SKU Compatible
#
# ==============================================================================


import streamlit as st



# ------------------------------------------------------------------------------
# MANUAL INPUT
# ------------------------------------------------------------------------------


def manual_barcode_input():


    value = st.text_input(

        "⌨️ Barcode / SKU",

        value=st.session_state.get(
            "inventory_barcode",
            ""
        ),

        placeholder="Scan or enter barcode"

    )



    value = value.strip()



    if value:

        st.session_state.inventory_barcode = value



    return value





# ------------------------------------------------------------------------------
# IMAGE PREPROCESS
# ------------------------------------------------------------------------------


def preprocess_image(img_bgr):


    import cv2
    import numpy as np


    gray = cv2.cvtColor(

        img_bgr,

        cv2.COLOR_BGR2GRAY

    )


    gray = cv2.equalizeHist(
        gray
    )



    kernel = np.array(

        [
            [0,-1,0],
            [-1,5,-1],
            [0,-1,0]
        ]

    )



    return cv2.filter2D(

        gray,

        -1,

        kernel

    )





# ------------------------------------------------------------------------------
# PYZBAR
# ------------------------------------------------------------------------------


def decode_pyzbar(img):


    try:


        from pyzbar.pyzbar import decode



        result = decode(img)



        if result:


            value = (

                result[0]
                .data
                .decode(
                    "utf-8"
                )
                .strip()

            )



            if value:

                return value



    except Exception:


        pass



    return None






# ------------------------------------------------------------------------------
# OPENCV
# ------------------------------------------------------------------------------


def decode_opencv(img):


    try:


        import cv2



        detector = (

            cv2
            .barcode_BarcodeDetector()

        )



        result = detector.detectAndDecode(
            img
        )



        if isinstance(result, tuple):


            decoded = result[0]



            if decoded:


                return decoded.strip()



    except Exception:


        pass



    return None





# ------------------------------------------------------------------------------
# MAIN DECODE
# ------------------------------------------------------------------------------


def decode_barcode(image):


    try:


        import cv2
        import numpy as np

        from PIL import Image



        pil = (

            Image
            .open(image)
            .convert("RGB")

        )



        img = cv2.cvtColor(

            np.array(pil),

            cv2.COLOR_RGB2BGR

        )



        # 1. Original

        value = decode_pyzbar(
            pil
        )


        if value:
            return value




        # 2. Enhanced


        processed = preprocess_image(
            img
        )



        processed_pil = Image.fromarray(
            processed
        )


        value = decode_pyzbar(
            processed_pil
        )


        if value:
            return value





        # 3. OpenCV


        value = decode_opencv(
            img
        )


        if value:
            return value



        return None



    except Exception as e:


        st.error(
            f"Scanner Error : {e}"
        )

        return None






# ------------------------------------------------------------------------------
# CAMERA
# ------------------------------------------------------------------------------


def camera_barcode_scan():


    image = st.camera_input(

        "📷 Scan Barcode"

    )



    if image:


        barcode = decode_barcode(
            image
        )



        if barcode:


            st.session_state.inventory_barcode = barcode


            st.success(
                f"✅ {barcode}"
            )

            return barcode



        else:


            st.warning(
                "Barcode not detected"
            )



    return None





# ------------------------------------------------------------------------------
# MAIN ENTRY
# ------------------------------------------------------------------------------


def get_barcode():


    barcode = camera_barcode_scan()



    if barcode:

        return barcode



    return manual_barcode_input()
