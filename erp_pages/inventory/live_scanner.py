# ==============================================================================
# erp_pages/inventory/live_scanner.py
# MOBILE INVENTORY v2
# LIVE CAMERA BARCODE SCANNER
# ==============================================================================


import streamlit as st
import av
import cv2


from streamlit_webrtc import (
    webrtc_streamer,
    VideoProcessorBase
)



# ==============================================================================
# BARCODE PROCESSOR
# ==============================================================================


class BarcodeProcessor(VideoProcessorBase):


    def __init__(self):

        self.barcode = None


        try:

            self.detector = cv2.barcode.BarcodeDetector()

        except Exception:

            self.detector = None



    def recv(self, frame):


        img = frame.to_ndarray(
            format="bgr24"
        )


        # ==============================================================
        # OpenCV 1D Barcode Detector
        # ==============================================================

        if self.detector:


            try:

                result = self.detector.detectAndDecode(
                    img
                )


                if isinstance(result, tuple):

                    if len(result) == 3:

                        ok, decoded, points = result


                        if ok and decoded:

                            self.barcode = decoded



                    elif len(result) == 2:

                        decoded, points = result


                        if decoded:

                            self.barcode = decoded



            except Exception:

                pass



        return av.VideoFrame.from_ndarray(
            img,
            format="bgr24"
        )



# ==============================================================================
# LIVE SCANNER
# ==============================================================================


def live_barcode_scanner():


    st.subheader(
        "📷 Live Barcode Scanner"
    )


    ctx = webrtc_streamer(

        key="mobile-inventory-scanner",

        video_processor_factory=BarcodeProcessor,

        media_stream_constraints={

            "video": {

                "facingMode": "environment"

            },

            "audio": False

        }

    )



    if ctx is not None:


        if ctx.video_processor:


            code = ctx.video_processor.barcode


            if code:

                return code



    return None
