# ==============================================================================
# erp_pages/pos/session.py
# ERP ENTERPRISE POS SESSION MANAGER v12.0
#
# Responsibilities:
# - Initialize POS session state
# - Reset POS transaction
# - Manage checkout status
#
# ==============================================================================


import streamlit as st




# ==============================================================================
# DEFAULT POS STATE
# ==============================================================================


POS_DEFAULTS = {


    # Cart

    "cart":

        [],



    # Sale

    "sale_data":

        None,



    # Receipt

    "show_receipt":

        False,



    # Checkout lock

    "processing":

        False,



    # Tax

    "tax_rate":

        0,



    # Discount

    "discount_policy":

        "allowed",



    # Selected product

    "selected_product":

        None,



    # Search

    "product_search":

        "",



}





# ==============================================================================
# INIT POS SESSION
# ==============================================================================


def init_pos_session():


    """
    Initialize POS session_state

    Called once when POS opens

    """


    for key, value in POS_DEFAULTS.items():


        if key not in st.session_state:


            st.session_state[key] = value





# ==============================================================================
# RESET CURRENT SALE
# ==============================================================================


def reset_sale():


    """
    Clear current transaction

    Keep login session

    """


    st.session_state.cart = []


    st.session_state.sale_data = None


    st.session_state.show_receipt = False


    st.session_state.processing = False


    st.session_state.selected_product = None


    st.session_state.product_search = ""





# ==============================================================================
# CART STATUS
# ==============================================================================


def has_cart():


    return bool(

        st.session_state.get(

            "cart",

            []

        )

    )





# ==============================================================================
# RECEIPT STATUS
# ==============================================================================


def is_receipt_mode():


    return st.session_state.get(

        "show_receipt",

        False

    )





# ==============================================================================
# PROCESS LOCK
# ==============================================================================


def start_processing():


    st.session_state.processing = True





def stop_processing():


    st.session_state.processing = False





def is_processing():


    return st.session_state.get(

        "processing",

        False

    )
