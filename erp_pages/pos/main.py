# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v12.1
#
# POS FLOW
#
# AUTH
#   ↓
# SESSION
#   ↓
# WAREHOUSE
#   ↓
# PRODUCT
#   ↓
# CART
#   ↓
# PAYMENT
#   ↓
# RECEIPT
#
# ==============================================================================


import streamlit as st



# ==============================================================================
# ERP CORE
# ==============================================================================

from erp_core import (
    get_default_warehouse_id
)



# ==============================================================================
# POS MODULES
# ==============================================================================

from .session import (
    init_pos_session
)


from .product import (
    render_products
)


from .cart import (
    calculate_subtotal
)


from .payment import (
    render_payment
)


from .receipt import (
    render_receipt
)



# ==============================================================================
# AUTH
# ==============================================================================

from auth import (
    is_authenticated
)



# ==============================================================================
# LANGUAGE
# ==============================================================================

from language import (
    language_selector
)





# ==============================================================================
# SAFE MONEY FORMAT
# ==============================================================================

def money(value):

    try:

        return f"{float(value):,.0f} MMK"

    except Exception:

        return "0 MMK"





# ==============================================================================
# POS ENTRY POINT
# ==============================================================================


def run():



    # ==========================================================================
    # LANGUAGE
    # ==========================================================================

    try:

        language_selector()

    except Exception as e:

        st.warning(
            f"Language module unavailable : {e}"
        )





    # ==========================================================================
    # AUTH CHECK
    # ==========================================================================

    if not is_authenticated():

        st.warning(
            "Please login first."
        )

        st.stop()





    # ==========================================================================
    # SESSION INITIALIZE
    # ==========================================================================

    try:

        init_pos_session()

    except Exception as e:

        st.error(
            f"POS Session Error : {e}"
        )

        st.stop()





    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================

    try:

        warehouse_id = get_default_warehouse_id()

    except Exception as e:

        st.error(
            f"Warehouse Load Error : {e}"
        )

        st.stop()





    if not warehouse_id:

        st.error(
            "Default warehouse not configured."
        )

        st.stop()





    # ==========================================================================
    # TITLE
    # ==========================================================================

    st.title(
        "🛒 ERP Enterprise POS"
    )



    st.caption(
        """
ERP Pricing Engine

OWNER PRICE
↓
PRODUCT MARKUP
↓
CATEGORY MARKUP
↓
SYSTEM PRICE


Inventory controlled by ERP Core

        """
    )





    # ==========================================================================
    # RECEIPT MODE
    # ==========================================================================

    if st.session_state.get(
        "show_receipt",
        False
    ):


        render_receipt()

        return





    # ==========================================================================
    # PRODUCT SECTION
    # ==========================================================================

    try:

        render_products(
            warehouse_id
        )


    except Exception as e:

        st.error(
            f"Product Module Error : {e}"
        )

        return





    # ==========================================================================
    # CART SECTION
    # ==========================================================================


    cart = st.session_state.get(
        "cart",
        []
    )



    if not cart:

        return





    st.divider()


    st.subheader(
        "🛒 Cart Summary"
    )



    try:

        subtotal = calculate_subtotal(
            cart
        )


        st.info(

            f"""
Items :

{len(cart)}


Subtotal :

{money(subtotal)}

            """

        )


    except Exception as e:

        st.error(
            f"Cart Calculation Error : {e}"
        )

        return





    # ==========================================================================
    # PAYMENT SECTION
    # ==========================================================================

    try:

        render_payment(
            warehouse_id
        )


    except Exception as e:

        st.error(
            f"Payment Module Error : {e}"
        )





# ==============================================================================
# END
# ==============================================================================
