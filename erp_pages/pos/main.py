# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v12.0
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
# POS ENTRY POINT
# ==============================================================================


def run():


    # ==============================================================
    # LANGUAGE
    # ==============================================================

    language_selector()



    # ==============================================================
    # AUTH CHECK
    # ==============================================================

    if not is_authenticated():


        st.warning(

            "Please login first."

        )

        st.stop()





    # ==============================================================
    # SESSION INIT
    # ==============================================================

    init_pos_session()





    # ==============================================================
    # WAREHOUSE
    # ==============================================================

    warehouse_id = get_default_warehouse_id()



    if not warehouse_id:


        st.error(

            "Default warehouse not configured."

        )

        st.stop()





    # ==============================================================
    # TITLE
    # ==============================================================

    st.title(

        "🛒 ERP Enterprise POS"

    )


    st.caption(

        """

OWNER PRICE
↓
PRODUCT MARKUP
↓
CATEGORY MARKUP
↓
SYSTEM PRICE


POS uses ERP Product Loader

        """

    )





    # ==============================================================
    # RECEIPT MODE
    # ==============================================================


    if st.session_state.get(

        "show_receipt",

        False

    ):


        render_receipt()

        return





    # ==============================================================
    # PRODUCT AREA
    # ==============================================================


    products = render_products(

        warehouse_id

    )





    # ==============================================================
    # CART SUMMARY
    # ==============================================================


    cart = st.session_state.get(

        "cart",

        []

    )



    if cart:


        st.divider()


        subtotal = calculate_subtotal(

            cart

        )


        st.info(

            f"Subtotal : {subtotal:,.0f} MMK"

        )





    # ==============================================================
    # PAYMENT
    # ==============================================================


    if cart:


        render_payment(

            warehouse_id

        )
