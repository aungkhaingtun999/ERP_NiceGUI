# ==============================================================================
# erp_pages/14_KBZ_Test.py
# ERP KBZ QR ANALYZER TEST PAGE
# ==============================================================================

import streamlit as st

from erp_core.payments.kbz_qr_analyzer import KBZQRAnalyzer



def run():


    st.title(
        "🔍 KBZ Pay QR Test"
    )


    qr_text = st.text_area(

        "Paste KBZ QR Data",

        height=150,

        key="kbz_qr_input"

    )



    if st.button(

        "Analyze QR",

        key="kbz_analyze_button"

    ):


        if not qr_text:


            st.warning(
                "Please paste QR data"
            )

            return



        result = KBZQRAnalyzer.analyze(

            qr_text

        )


        st.subheader(
            "Result"
        )


        st.json(
            result
        )



if __name__ == "__main__":

    run()
