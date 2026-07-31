# ==============================================================================
# erp_pages/pos/styles.py
# ERP ENTERPRISE POS UI STYLE ENGINE v1.0
#
# Responsibilities:
# - Global POS CSS
# - Compact Layout
# - Button Style
# - Spacing Control
#
# ==============================================================================


import streamlit as st





# ==============================================================================
# LOAD POS STYLE
# ==============================================================================


def load_pos_style():


    st.markdown(

        """

        <style>


        /* ==========================================================
           MAIN CONTAINER
        ========================================================== */


        .block-container {

            padding-top: 0.8rem;

            padding-bottom: 0.8rem;

        }



        /* ==========================================================
           VERTICAL SPACING
        ========================================================== */


        div[data-testid="stVerticalBlock"] {

            gap: 0.25rem;

        }



        div[data-testid="stHorizontalBlock"] {

            gap: 0.4rem;

        }




        /* ==========================================================
           HEADINGS
        ========================================================== */


        h1 {

            margin-bottom:0.2rem;

            font-size:1.8rem;

        }



        h2 {

            margin-bottom:0.15rem;

            font-size:1.35rem;

        }



        h3 {

            margin-bottom:0.1rem;

            font-size:1.1rem;

        }





        /* ==========================================================
           BUTTON BASE
        ========================================================== */


        div.stButton > button {


            min-height:1.8rem;

            height:1.8rem;

            padding:

            0.1rem 0.4rem;


            font-size:0.85rem;


            border-radius:6px;


        }





        /* ==========================================================
           DATAFRAME
        ========================================================== */


        div[data-testid="stDataFrame"] {

            margin-top:0.2rem;

        }



        </style>

        """,

        unsafe_allow_html=True

    )