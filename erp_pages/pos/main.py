# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v12.2 FINAL
#
# FLOW
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
# MONEY FORMAT
# ==============================================================================

def money(value):

    try:
        return f"{float(value):,.0f} MMK"

    except Exception:
        return "0 MMK"


# ==============================================================================
# POS ENTRY
# ==============================================================================

def run():


    # --------------------------------------------------------------------------
    # PAGE CONFIG
    # --------------------------------------------------------------------------
    try:
        st.set_page_config(
            page_title="ERP POS",
            page_icon="🛒",
            layout="wide"
        )
    except Exception:
        pass


    # --------------------------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------------------------
    try:
        language_selector()
    except Exception:
        pass


    # --------------------------------------------------------------------------
    # AUTH
    # --------------------------------------------------------------------------
    if not is_authenticated():

        st.warning(
            "Please login first."
        )

        st.stop()


    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------
    try:
        init_pos_session()
    except Exception as e:

        st.error(
            f"POS Session Error : {e}"
        )

        st.stop()


    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------
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


    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------
    st.title("🛒 ERP Enterprise POS")

    st.caption(
        """
OWNER PRICE
↓
PRODUCT MARKUP
↓
CATEGORY MARKUP
↓
SYSTEM PRICE

POS uses FINAL SELLING PRICE
        """
    )


    # --------------------------------------------------------------------------
    # RECEIPT MODE
    # --------------------------------------------------------------------------
    if st.session_state.get("show_receipt", False):

        try:
            render_receipt()
        except Exception as e:
            st.error(f"Receipt Error : {e}")

        return


    # --------------------------------------------------------------------------
    # PRODUCT AREA
    # --------------------------------------------------------------------------
    try:
        render_products(warehouse_id)

    except Exception as e:

        st.error(
            f"Product Module Error : {e}"
        )

        return


    # --------------------------------------------------------------------------
    # CART AREA
    # --------------------------------------------------------------------------
    cart = st.session_state.get("cart", [])


    if not cart:

        st.info("Cart is empty.")

        return


    st.divider()

    st.subheader("🛒 Cart Summary")


    try:
        subtotal = calculate_subtotal(cart)

        total_qty = sum(
            int(item.get("qty", 0))
            for item in cart
        )

        st.info(
            f"""
Items      : {len(cart)}
Total Qty  : {total_qty}
Subtotal   : {money(subtotal)}
            """
        )

    except Exception as e:

        st.error(
            f"Cart Calculation Error : {e}"
        )

        return


    # --------------------------------------------------------------------------
    # PAYMENT AREA
    # --------------------------------------------------------------------------
    try:
        render_payment(warehouse_id)

    except Exception as e:

        st.error(
            f"Payment Module Error : {e}"
        )


# ==============================================================================
# DIRECT RUN
# ==============================================================================

if __name__ == "__main__":

    run()
