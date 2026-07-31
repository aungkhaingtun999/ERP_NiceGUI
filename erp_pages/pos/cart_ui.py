# ==============================================================================
# erp_pages/pos/cart_ui.py
# ERP ENTERPRISE POS CART UI v1.0
# ==============================================================================

import streamlit as st

from .cart import (
    increase_quantity,
    decrease_quantity,
    remove_from_cart
)


# ==============================================================================
# CART CONTROL RENDER
# ==============================================================================

def render_cart_control(cart):

    if not cart:
        return

    st.caption("Qty Control")

    for index, item in enumerate(cart):

        col1, col2, col3, col4 = st.columns([5,1,1,1])

        # Product name
        with col1:
            st.write(
                f"{item.get('name','')} x {item.get('qty',0)}"
            )

        # Plus
        with col2:
            if st.button("➕", key=f"cart_plus_{index}"):
                increase_quantity(cart, index)
                st.session_state.cart = cart
                st.rerun()

        # Minus
        with col3:
            if st.button("➖", key=f"cart_minus_{index}"):
                decrease_quantity(cart, index)
                st.session_state.cart = cart
                st.rerun()

        # Delete
        with col4:
            if st.button("🗑", key=f"cart_delete_{index}"):
                remove_from_cart(cart, index)
                st.session_state.cart = cart
                st.rerun()
