# ==============================================================================
# erp_pages/pos/session.py
# ERP ENTERPRISE POS SESSION MANAGER v12.5 FINAL
#
# - Initialize POS session
# - Load TAX setting
# - Reset transaction
# - Manage checkout state
#
# ==============================================================================


import streamlit as st


from erp_core import get_setting





# ==============================================================================
# LOAD TAX
# ==============================================================================

def load_tax_rate():

    try:

        value = get_setting(

            "DEFAULT_TAX_RATE",

            0

        )


        return float(value)


    except Exception:


        return 0.0





# ==============================================================================
# DEFAULT SESSION FACTORY
# ==============================================================================

def default_pos_state():


    return {


        # Cart

        "cart":

            [],



        # Sale

        "sale_data":

            None,



        # Receipt

        "show_receipt":

            False,



        # Checkout

        "processing":

            False,



        # TAX

        "tax_rate":

            load_tax_rate(),



        # Discount

        "discount_policy":

            "allowed",



        # Product

        "selected_product":

            None,



        # Search

        "product_search":

            "",



        # Payment

        "payment_method":

            "CASH",



        "received_amount":

            0,


    }





# ==============================================================================
# INIT SESSION
# ==============================================================================

def init_pos_session():


    defaults = default_pos_state()


    for key, value in defaults.items():


        if key not in st.session_state:


            st.session_state[key] = value





    # Safety reload TAX if missing

    if "tax_rate" not in st.session_state:


        st.session_state.tax_rate = load_tax_rate()





# ==============================================================================
# RESET SALE
# ==============================================================================

def reset_sale():


    st.session_state.cart = []


    st.session_state.sale_data = None


    st.session_state.show_receipt = False


    st.session_state.processing = False


    st.session_state.selected_product = None


    st.session_state.product_search = ""


    st.session_state.payment_method = "CASH"


    st.session_state.received_amount = 0





    # Keep TAX

    st.session_state.tax_rate = load_tax_rate()





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
