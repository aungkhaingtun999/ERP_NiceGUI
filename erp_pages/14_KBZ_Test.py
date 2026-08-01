import streamlit as st

from erp_core.payments.kbz_qr_analyzer import KBZQRAnalyzer


st.title(
    "🔍 KBZ Pay QR Analyzer"
)


qr_data = st.text_area(
    "Paste KBZ QR Data"
)



if st.button(
    "Analyze"
):

    result = KBZQRAnalyzer.analyze(
        qr_data
    )


    st.json(
        result
    )

def run():

    st.title(
        "🔍 KBZ Pay QR Analyzer"
    )

    qr_data = st.text_area(
        "Paste KBZ QR"
    )


    if st.button("Analyze"):

        result = KBZQRAnalyzer.analyze(
            qr_data
        )

        st.json(result)
