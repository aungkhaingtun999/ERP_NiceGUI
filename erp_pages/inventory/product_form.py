# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v3
# ERP ENTERPRISE PRODUCT REGISTRATION
# ==============================================================================
import streamlit as st


def render_new_product_form(barcode=""):

    st.divider()

    st.subheader("🆕 New Product Registration")

    st.info(
        f"Barcode : {barcode}"
    )

    with st.form(
        "new_product_form"
    ):

        name = st.text_input(
            "Product Name"
        )

        sku = st.text_input(
            "SKU"
        )

        purchase_price = st.number_input(
            "Purchase Price",
            min_value=0.0,
            value=0.0
        )

        selling_price = st.number_input(
            "Selling Price",
            min_value=0.0,
            value=0.0
        )

        stock = st.number_input(
            "Opening Stock",
            min_value=0,
            value=0
        )

        save_btn = st.form_submit_button(
            "💾 Save Product",
            use_container_width=True
        )

    if save_btn:

        if not name:

            st.error(
                "Enter product name"
            )

            return None

        product_data = {
            "name": name,
            "barcode": barcode,
            "sku": sku,
            "purchase_price": purchase_price,
            "selling_price": selling_price,
            "stock": stock
        }

        st.success(
            "✅ Product form completed"
        )

        st.json(product_data)

        return product_data

    return None
