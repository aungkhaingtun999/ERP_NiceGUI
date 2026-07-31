# ==============================================================================
# erp_pages/pos/styles.py
# ERP ENTERPRISE POS UI STYLE ENGINE v1.1 SAFE
# ==============================================================================

import streamlit as st


def load_pos_style():

    st.markdown(
        """
        <style>

        /* Keep default Streamlit layout */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }

        /* Small POS buttons only */
        div.stButton > button {
            border-radius: 6px;
            font-size: 0.9rem;
        }

        </style>
        """,
        unsafe_allow_html=True
    )
