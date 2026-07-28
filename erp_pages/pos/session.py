# ==============================================================================
# erp_pages/pos/session.py
# ERP ENTERPRISE POS SESSION MANAGER v12.1
#
# Responsibilities:
# - Initialize POS session
# - Reset transaction
# - Manage checkout state
#
# ==============================================================================


import streamlit as st





# ==============================================================================
# DEFAULT SESSION FACTORY
# ==============================================================================


def default_pos_state():

    return {

        # Cart

        "cart": [],



        # Sale result

        "sale_data": None,



        # Receipt

        "show_receipt": False,



        # Checkout lock

        "processing": False,



        # Tax

        "tax_rate": 0,



        # Discount

        "discount_policy": "allowed",



        # Product

        "selected_product": None,



        # Search

        "product_search": "",



        # Payment

        "payment_method": "CASH",



        "received_amount": 0,



    }







# ==============================================================================
# INIT SESSION
# ==============================================================================


def init_pos_session():

    """
    Initialize POS session state
    """

    defaults = default_pos_state()


    for key, value in defaults.items():


        if key not in st.session_state:


            st.session_state[key] = value







# ==============================================================================
# RESET SALE
# ==============================================================================


def reset_sale():

    """
    Reset current transaction only.

    Login session remains.
    """


    reset_keys = [

        "cart",

        "sale_data",

        "show_receipt",

        "processing",

        "selected_product",

        "product_search",

        "payment_method",

        "received_amount",

    ]



    for key in reset_keys:


        if key == "cart":


            st.session_state[key] = []



        elif key == "processing":


            st.session_state[key] = False



        elif key == "show_receipt":


            st.session_state[key] = False



        elif key == "sale_data":


            st.session_state[key] = None



        elif key == "received_amount":


            st.session_state[key] = 0



        else:


            st.session_state[key] = None







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
