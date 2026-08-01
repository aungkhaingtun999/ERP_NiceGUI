# ==============================================================================
# erp_pages/14_KBZ_Test.py
# ERP ENTERPRISE KBZ QR TEST PAGE
# ==============================================================================


import streamlit as st

from erp_core.payments.kbz_crc_tool import KBZCRCTool



def run():


    st.title(
        "🧪 KBZ QR CRC Analyzer"
    )


    st.divider()


    sample_text = st.text_area(

        "Paste KBZ QR samples (one per line)",

        height=250,

        key="kbz_crc_input"

    )



    if st.button(

        "Analyze CRC Samples",

        key="kbz_crc_analyze_button"

    ):


        samples = [

            x.strip()

            for x in sample_text.splitlines()

            if x.strip()

        ]


        if not samples:

            st.warning(
                "Please paste QR samples"
            )

            return



        result = KBZCRCTool.analyze_samples(

            samples

        )


        st.json(result)




# direct run support

if __name__ == "__main__":

    run()
