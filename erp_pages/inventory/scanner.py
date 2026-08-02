# ==============================================================================
# erp_pages/inventory/live_scanner.py
# REAL-TIME MOBILE BARCODE SCANNER
# Compatible with latest streamlit-webrtc
# ==============================================================================

import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import av


# Shared scan result
SCAN_RESULT = {"code": ""}


class BarcodeTransformer(VideoTransformerBase):

    def transform(self, frame):

        img = frame.to_ndarray(format="bgr24")

        detector = cv2.barcode_BarcodeDetector()

        result = detector.detectAndDecode(img)

        try:

            if len(result) == 4:
                ok, decoded_info, decoded_type, points = result

            elif len(result) == 3:
                decoded_info, decoded_type, points = result
                ok = bool(decoded_info)

            else:
                ok = False
                decoded_info = []

            if ok and decoded_info:

                value = decoded_info[0].strip()

                if len(value) >= 8:

                    SCAN_RESULT["code"] = value

                    cv2.putText(
                        img,
                        value,
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )

        except Exception:
            pass

        return av.VideoFrame.from_ndarray(img, format="bgr24")


def live_barcode_scanner():

    st.subheader("📷 Live Barcode Scanner")

    webrtc_streamer(
        key="barcode-scanner",
        video_transformer_factory=BarcodeTransformer,
        media_stream_constraints={
            "video": {
                "facingMode": "environment"
            },
            "audio": False,
        },
        async_processing=True,
    )

    code = SCAN_RESULT.get("code", "")

    if code:

        st.success(f"📦 Scanned: {code}")

        return code

    return None
