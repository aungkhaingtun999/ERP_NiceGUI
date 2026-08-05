# ==============================================================================
# erp_components/mobile_scanner/scanner.py
# MOBILE BARCODE SCANNER v2.0
# Streamlit WebRTC + OpenCV + PyZBar
# ==============================================================================


import time
import threading

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

SCAN_COOLDOWN = 2



# ==============================================================================
# BARCODE PROCESSOR
# ==============================================================================


class BarcodeProcessor(VideoProcessorBase):


    def __init__(self):

        self.last_scan = None

        self.last_time = 0



    def recv(self, frame):


        img = frame.to_ndarray(
            format="bgr24"
        )


        now = time.time()



        # ----------------------------------------------------------
        # Decode only after cooldown
        # ----------------------------------------------------------

        if now - self.last_time > SCAN_COOLDOWN:


            result = decode_barcode(
                img
            )


            if result:


                self.last_scan = result

                self.last_time = now



                # Safe callback
                threading.Thread(

                    target=
                    self.save_result,

                    args=(result,)

                ).start()



        return av.VideoFrame.from_ndarray(

            img,

            format="bgr24"

        )




    def save_result(self, value):


        st.session_state[
            "barcode_value"
        ] = value





# ==============================================================================
# WEBRTC CONFIG
# ==============================================================================


RTC_CONFIG = RTCConfiguration(

    {

        "iceServers":

        [

            {

                "urls":

                [

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



    st.subheader(
        "📷 Barcode Scanner"
    )



    webrtc_ctx = webrtc_streamer(

        key=
        "mobile_barcode_scanner_v2",


        video_processor_factory=
        BarcodeProcessor,


        rtc_configuration=
        RTC_CONFIG,


        media_stream_constraints=

        {

            "video":

            {

                "facingMode":
                {

                    "ideal":
                    "environment"

                }

            },


            "audio":
            False

        },


        async_processing=True

    )



    barcode = st.session_state.get(

        "barcode_value",

        ""

    )



    if barcode:


        st.success(

            f"✅ Barcode : {barcode}"

        )


        return barcode



    else:


        st.info(

            "Waiting for scan..."

        )



    return None
