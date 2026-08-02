# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v3
# ERP ENTERPRISE PRODUCT REGISTRATION
# ==============================================================================
import streamlit as st

from database import db

def render_new_product_form(barcode):

st.subheader("🆕 New Product")

with st.form("new_product_form"):

    st.text_input(
        "Barcode",
        value=barcode,
        disabled=True
    )

    name = st.text_input("Product Name")
    sku = st.text_input("SKU")

    purchase_price = st.number_input(
        "Purchase Price",
        min_value=0.0
    )

    selling_price = st.number_input(
        "Selling Price",
        min_value=0.0
    )

    stock = st.number_input(
        "Opening Stock",
        min_value=0
    )

    save = st.form_submit_button("Save Product")

    if save:

        if not name:

            st.error("Product name required")

            return

        result = (
            db()
            .table("products")
            .insert(
                {
                    "name": name,
                    "barcode": barcode,
                    "sku": sku,
                    "purchase_price": purchase_price,
                    "selling_price": selling_price,
                    "stock": stock,
                    "unit": "pcs",
                    "is_active": True
                }
            )
            .execute()
        )

        st.success("Product saved")

        st.session_state.mobile_product = result.data[0]

        st.rerun()
