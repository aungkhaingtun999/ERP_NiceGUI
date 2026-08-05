# ==============================================================================
# erp_components/mobile_scanner/scanner.py
# MOBILE BARCODE SCANNER v3.0 STABLE
# Streamlit WebRTC + OpenCV + PyZBar
# Camera stays open until user leaves the page
# ==============================================================================

import time

import streamlit as st
import av

from streamlit_webrtc import (
    webrtc_streamer,
    VideoProcessorBase,
    RTCConfiguration,
)

from .decoder import decode_barcode


# ==============================================================================
# GLOBAL SCAN CONTROL
# ==============================================================================

SCAN_COOLDOWN = 2  # seconds


# ==============================================================================
# BARCODE PROCESSOR
# ==============================================================================

class BarcodeProcessor(VideoProcessorBase):

    def __init__(self):
        self.last_scan = None
        self.last_time = 0

    def recv(self, frame):

        img = frame.to_ndarray(format="bgr24")

        now = time.time()

        # Decode only after cooldown
        if now - self.last_time > SCAN_COOLDOWN:

            result = decode_barcode(img)

            if result:
                self.last_scan = result
                self.last_time = now

        return av.VideoFrame.from_ndarray(
            img,
            format="bgr24"
        )


# ==============================================================================
# WEBRTC CONFIG
# ==============================================================================

RTC_CONFIG = RTCConfiguration(
    {
        "iceServers": [
            {
                "urls": [
                    "stun:stun.l.google.com:19302"
                ]
            }
        ]
    }
)


# ==============================================================================
# PUBLIC FUNCTION
# ==============================================================================

def mobile_scanner():

    if "barcode_value" not in st.session_state:
        st.session_state.barcode_value = ""

    st.subheader("📷 Barcode Scanner")

    webrtc_ctx = webrtc_streamer(
        key="mobile_barcode_scanner_v3",

        video_processor_factory=BarcodeProcessor,

        rtc_configuration=RTC_CONFIG,

        media_stream_constraints={
            "video": {
                "facingMode": {
                    "ideal": "environment"
                }
            },
            "audio": False
        },

        async_processing=True,
    )

    # Get scanned value from processor
    if webrtc_ctx and webrtc_ctx.video_processor:

        scanned = webrtc_ctx.video_processor.last_scan

        if scanned and scanned != st.session_state.barcode_value:
            st.session_state.barcode_value = scanned

    barcode = st.session_state.get("barcode_value", "")

    if barcode:
        st.success(f"✅ Barcode : {barcode}")
        return barcode

    st.info("Waiting for scan...")

    return None
