# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v12.3 FINAL
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
# DUPLICATE RENDER GUARD
# ==============================================================================

# Prevent Streamlit from rendering POS twice in the same request cycle.
if st.session_state.get("_pos_rendering"):
    st.stop()

st.session_state["_pos_rendering"] = True


# ==============================================================================
# ERP CORE
# ==============================================================================

from erp_core import get_default_warehouse_id


# ==============================================================================
# POS MODULES
# ==============================================================================

from .session import init_pos_session
from .product import render_products
from .cart import calculate_subtotal
from .payment import render_payment
from .receipt import render_receipt


# ==============================================================================
# AUTH
# ==============================================================================

from auth import is_authenticated


# ==============================================================================
# LANGUAGE
# ==============================================================================

from language import language_selector


# ==============================================================================
# MONEY FORMAT
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

    try:

        # ----------------------------------------------------------------------
        # LANGUAGE
        # ----------------------------------------------------------------------
        try:
            language_selector()
        except Exception:
            pass


        # ----------------------------------------------------------------------
        # AUTH
        # ----------------------------------------------------------------------
        if not is_authenticated():
            st.warning("Please login first.")
            st.stop()


        # ----------------------------------------------------------------------
        # SESSION
        # ----------------------------------------------------------------------
        init_pos_session()


        # ----------------------------------------------------------------------
        # WAREHOUSE
        # ----------------------------------------------------------------------
        warehouse_id = get_default_warehouse_id()

        if not warehouse_id:
            st.error("Default warehouse not configured.")
            st.stop()


        # ----------------------------------------------------------------------
        # HEADER
        # ----------------------------------------------------------------------
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


        # ----------------------------------------------------------------------
        # RECEIPT MODE
        # ----------------------------------------------------------------------
        if st.session_state.get("show_receipt", False):
            render_receipt()
            return


        # ----------------------------------------------------------------------
        # PRODUCT AREA
        # ----------------------------------------------------------------------
        render_products(warehouse_id)


        # ----------------------------------------------------------------------
        # CART AREA
        # ----------------------------------------------------------------------
        cart = st.session_state.get("cart", [])

        if not cart:
            st.info("Cart is empty.")
            return


        st.divider()
        st.subheader("🛒 Cart Summary")

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


        # ----------------------------------------------------------------------
        # PAYMENT
        # ----------------------------------------------------------------------
        render_payment(warehouse_id)


    finally:

        # Always release render guard after page finishes rendering.
        st.session_state["_pos_rendering"] = False


# ==============================================================================
# DIRECT RUN
# ==============================================================================

if __name__ == "__main__":
    run()
