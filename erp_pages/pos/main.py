# ==============================================================================
# erp_pages/pos/main.py
# 
# ERP ENTERPRISE POS MAIN CONTROLLER v13.2 STABLE
# 
# Stable POS Layout
# - Product + Cart Side Layout
# - Existing Payment Engine
# - Existing Pricing Engine
# - Existing Checkout Engine
# ==============================================================================

import pandas as pd
import streamlit as st

from erp_core import get_default_warehouse_id

from .session import init_pos_session
from .product import render_products
from .cart import get_cart_rows
from .cart_ui import render_cart_control
from .payment import render_payment
from .receipt import render_receipt
from .styles import load_pos_style

from auth import is_authenticated
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
# MAIN RUN
# ==============================================================================

def run():
    # --------------------------------------------------------------------------
    # UI STYLE
    # --------------------------------------------------------------------------
    load_pos_style()
    
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
        st.warning("Please login first.")
        st.stop()
        
    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------
    init_pos_session()
    
    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------
    warehouse_id = get_default_warehouse_id()
    if not warehouse_id:
        st.error("Default warehouse not configured.")
        st.stop()
        
    # --------------------------------------------------------------------------
    # RECEIPT MODE
    # --------------------------------------------------------------------------
    if st.session_state.get("show_receipt", False):
        render_receipt()
        return
        
    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------
    st.title("🛒 ERP Enterprise POS")
    st.caption("Fast Compact Sales System")
    
    # --------------------------------------------------------------------------
    # PRODUCT + CART AREA
    # --------------------------------------------------------------------------
    product_area, cart_area = st.columns([6, 4])
    
    # ==========================================================================
    # PRODUCT PANEL
    # ==========================================================================
    with product_area:
        st.subheader("📦 Products")
        render_products(warehouse_id)
        
    # ==========================================================================
    # CART PANEL
    # ==========================================================================
    with cart_area:
        st.subheader("🛒 Cart")
        cart = st.session_state.get("cart", [])
        if not cart:
            st.info("Cart is empty")
        else:
            rows = get_cart_rows(cart)
            if rows:
                cart_df = pd.DataFrame(rows)
                cart_df["Unit Price"] = cart_df["Unit Price"].apply(money)
                cart_df["Amount"] = cart_df["Amount"].apply(money)
                st.dataframe(
                    cart_df,
                    height=220,
                    use_container_width=True,
                    hide_index=True
                )
                render_cart_control(cart)
                
    # --------------------------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------------------------
    cart = st.session_state.get("cart", [])
    if cart:
        render_payment(warehouse_id)
