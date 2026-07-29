# ==============================================================================
# erp_pages/pos/session.py
# ERP ENTERPRISE POS SESSION MANAGER v12.9 FINAL
#
# Responsibilities:
# - Initialize POS session
# - Load system settings
# - Manage checkout state
# - Reset transaction safely
#
# Flow:
#
# ERP Settings
#      |
#      ↓
# POS Session
#      |
#      ↓
# Checkout
#      |
#      ↓
# Receipt
#
# ==============================================================================


import streamlit as st



from erp_core.loaders.settings_loader import (
    get_setting
)





# ==============================================================================
# DEFAULT STATE
# ==============================================================================


def default_pos_state():


    return {


        # --------------------------------------------------
        # CART
        # --------------------------------------------------

        "cart":

            [],



        # --------------------------------------------------
        # SALE
        # --------------------------------------------------

        "sale_data":

            None,


        "show_receipt":

            False,



        # --------------------------------------------------
        # PROCESS LOCK
        # --------------------------------------------------

        "processing":

            False,



        # --------------------------------------------------
        # TAX
        # --------------------------------------------------

        "tax_rate":

            0.0,



        # --------------------------------------------------
        # DISCOUNT
        # --------------------------------------------------

        "discount":

            0.0,


        "discount_policy":

            "allowed",



        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        "selected_product":

            None,


        "product_search":

            "",



        # --------------------------------------------------
        # PAYMENT
        # --------------------------------------------------

        "payment_method":

            "CASH",


        "received_amount":

            0.0,



    }





# ==============================================================================
# LOAD SYSTEM SETTINGS
# ==============================================================================


def load_pos_settings():


    try:


        tax_rate = float(

            get_setting(

                "DEFAULT_TAX_RATE",

                0

            )

        )



    except Exception:


        tax_rate = 0.0




    try:


        discount_policy = str(

            get_setting(

                "DISCOUNT_POLICY",

                "allowed"

            )

        )



    except Exception:


        discount_policy = "allowed"





    return {


        "tax_rate":

            tax_rate,


        "discount_policy":

            discount_policy

    }





# ==============================================================================
# INIT SESSION
# ==============================================================================


def init_pos_session():

    defaults = {

        "cart": [],

        "show_receipt": False,

        "processing": False,

        "products_cache": None

    }


    for key,value in defaults.items():

        if key not in st.session_state:

            st.session_state[key]=value


    # --------------------------------------------------
    # Load ERP Settings
    # --------------------------------------------------


    if not st.session_state.get(

        "_pos_settings_loaded",

        False

    ):



        settings = load_pos_settings()



        st.session_state.tax_rate = settings.get(

            "tax_rate",

            0

        )



        st.session_state.discount_policy = settings.get(

            "discount_policy",

            "allowed"

        )



        st.session_state._pos_settings_loaded = True





# ==============================================================================
# RESET SALE
# ==============================================================================


def reset_sale():


    reset_values = {


        "cart":

            [],



        "sale_data":

            None,



        "show_receipt":

            False,



        "processing":

            False,



        "selected_product":

            None,



        "product_search":

            "",



        "payment_method":

            "CASH",



        "received_amount":

            0.0,



        "discount":

            0.0,


    }





    for key, value in reset_values.items():


        st.session_state[key] = value





# ==============================================================================
# CART CHECK
# ==============================================================================


def has_cart():


    return bool(

        st.session_state.get(

            "cart",

            []

        )

    )





# ==============================================================================
# RECEIPT MODE
# ==============================================================================


def is_receipt_mode():


    return bool(

        st.session_state.get(

            "show_receipt",

            False

        )

    )





# ==============================================================================
# PROCESS LOCK
# ==============================================================================


def start_processing():


    st.session_state.processing = True





def stop_processing():


    st.session_state.processing = False





def is_processing():


    return bool(

        st.session_state.get(

            "processing",

            False

        )

    )





# ==============================================================================
# TAX HELPER
# ==============================================================================


def get_tax_rate():


    return float(

        st.session_state.get(

            "tax_rate",

            0

        )

    )





# ==============================================================================
# DISCOUNT HELPER
# ==============================================================================


def get_discount_policy():


    return st.session_state.get(

        "discount_policy",

        "allowed"

    )
