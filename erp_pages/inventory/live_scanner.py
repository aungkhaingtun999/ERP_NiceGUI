# ==============================================================================
# erp_pages/inventory/live_scanner.py
# MOBILE INVENTORY v2
# LIVE CAMERA BARCODE SCANNER
# ==============================================================================


import streamlit as st

from streamlit_webrtc import (
    webrtc_streamer,
    VideoProcessorBase,
    WebRtcMode
)

import av
import cv2



class BarcodeProcessor(VideoProcessorBase):


    def __init__(self):

        self.barcode = None

        self.detector = cv2.QRCodeDetector()



    def recv(self, frame):


        img = frame.to_ndarray(
            format="bgr24"
        )


        # Barcode detector
        data, points, _ = self.detector.detectAndDecode(
            img
        )


        if data:

            self.barcode = data



        return av.VideoFrame.from_ndarray(
            img,
            format="bgr24"
        )




def live_barcode_scan():


    st.subheader(
        "📷 Live Barcode Scanner"
    )


    ctx = webrtc_streamer(

        key="barcode-scanner",

        mode=WebRtcMode.SENDRECV,

        video_processor_factory=BarcodeProcessor,

        media_stream_constraints={
            "video": True,
            "audio": False
        },

    )


    if ctx:

        if ctx.video_processor:

            code = ctx.video_processor.barcode

            if code:

                return code


    return None
