import streamlit as st

from streamlit_webrtc import (
    webrtc_streamer,
    VideoProcessorBase,
    RTCConfiguration
)

import av

from .decoder import decode_barcode



class BarcodeProcessor(
    VideoProcessorBase
):

    def __init__(self):

        self.barcode = None



    def recv(self, frame):

        img = frame.to_ndarray(
            format="bgr24"
        )


        result = decode_barcode(
            img
        )


        if result:

            self.barcode = result


            st.session_state[
                "barcode_value"
            ] = result



        return av.VideoFrame.from_ndarray(
            img,
            format="bgr24"
        )




RTC_CONFIG = RTCConfiguration(
    {
        "iceServers":[
            {
                "urls":[
                    "stun:stun.l.google.com:19302"
                ]
            }
        ]
    }
)




def mobile_scanner():


    if "barcode_value" not in st.session_state:

        st.session_state.barcode_value = ""



    webrtc_ctx = webrtc_streamer(

        key="mobile_barcode_scanner",

        video_processor_factory=
            BarcodeProcessor,

        rtc_configuration=
            RTC_CONFIG,

        media_stream_constraints={

            "video": {
                "facingMode":
                "environment"
            },

            "audio": False
        }

    )


    if st.session_state.barcode_value:


        st.success(
            "Barcode: "
            +
            st.session_state.barcode_value
        )


        return (
            st.session_state.barcode_value
        )


    return None