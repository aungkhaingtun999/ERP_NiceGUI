# ==============================================================================
# erp_pages/14_KBZ_Test.py
# ERP ENTERPRISE KBZ QR TEST PAGE
# ==============================================================================


import streamlit as st


from erp_core.payments.kbz_crc_tool import KBZCRCTool

from erp_core.payments.kbz_crc_engine import KBZCRCEngine

from erp_core.payments.kbz_qr_analyzer import KBZQRAnalyzer



# ==============================================================================
# PAGE RUN
# ==============================================================================


def run():


    st.title(
        "🧪 KBZ QR CRC Analyzer"
    )


    st.divider()



    # ==========================================================================
    # SECTION 1
    # QR SAMPLE SPLIT TEST
    # ==========================================================================


    st.subheader(
        "📌 QR Payload / CRC Split Test"
    )


    sample_text = st.text_area(

        "Paste KBZ QR samples (one per line)",

        height=250,

        key="kbz_sample_text"

    )



    if st.button(

        "Analyze CRC Samples",

        key="kbz_sample_analyze_btn"

    ):


        samples = [

            x.strip()

            for x in sample_text.splitlines()

            if x.strip()

        ]



        if not samples:

            st.warning(
                "Please paste KBZ QR samples"
            )

        else:


            result = KBZCRCTool.analyze_samples(

                samples

            )


            st.json(result)



    st.divider()



    # ==========================================================================
    # SECTION 2
    # PAYLOAD CRC VERIFY
    # ==========================================================================


    st.subheader(
        "🔐 CRC Candidate Test"
    )



    payload = st.text_input(

        "KBZ Payload",

        key="kbz_payload_test"

    )


    crc = st.text_input(

        "Expected CRC",

        key="kbz_crc_test"

    )



    if st.button(

        "Run CRC Test",

        key="kbz_crc_run_btn"

    ):


        if not payload or not crc:

            st.warning(
                "Enter Payload and CRC"
            )


        else:


            result = KBZCRCEngine.compare(

                payload,

                crc

            )


            st.json(result)



    st.divider()



    # ==========================================================================
    # SECTION 3
    # DECODED HEX CRC TEST
    # ========================================================================
    st.subheader(
        "🧬 Decoded Hex CRC Test"
    )



    decoded_hex = st.text_area(

        "Decoded HEX",

        height=150,

        key="kbz_decoded_hex"

    )



    if st.button(

        "Analyze Decoded HEX",

        key="kbz_hex_analyze_btn"

    ):


        if not decoded_hex:


            st.warning(
                "Enter decoded hex"
            )


        else:


            try:


                result = KBZCRCEngine.crc16_variants(

                    decoded_hex

                )


                st.json(result)



            except Exception as e:


                st.error(
                    str(e)
                )
                
    st.divider()

    # ==========================================================================
    # SECTION 5
    # CRC RANGE SCANNER
    # ==========================================================================

    st.subheader(
        "🔎 CRC Range Scanner"
    )

    range_hex = st.text_area(
        "HEX For Range Scan",
        height=120,
        key="range_hex_input"
    )

    if st.button(
        "Scan CRC Range",
        key="scan_range_btn"
    ):

        if not range_hex:

            st.warning(
                "Enter HEX value"
            )

        else:

            result = KBZCRCEngine.scan_hex_ranges(
                range_hex
            )

            st.json(result)
    st.divider()

    # ==========================================================================
    # SECTION 6
    # CRC STRING ANALYZER
    # ==========================================================================

    st.subheader(
        "🧩 CRC String Analyzer"
    )

    crc_text = st.text_input(
        "CRC String",
        key="crc_string_input"
    )

    if st.button(
        "Analyze CRC String",
        key="crc_string_btn"
    ):

        result = KBZCRCEngine.analyze_crc_string(
            crc_text
        )

        st.json(result)
        st.divider()

    st.subheader("🔢 CRC Body Integer Test")

    crc_num = st.text_input(
        "CRC For Integer Test",
        key="crc_num_test"
    )

    if st.button(
        "Convert CRC Body",
        key="crc_num_btn"
    ):

        st.json(
            KBZCRCEngine.crc_body_info(crc_num)
        )
        
# ==============================================================================
# DIRECT RUN
# ==============================================================================


if __name__ == "__main__":

    run()
