# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v3
# ERP ENTERPRISE PRODUCT REGISTRATION
# ==============================================================================
import streamlit as st


def render_product_form(barcode=""):

    st.subheader("🆕 New Product Registration")

    name = st.text_input(
        "Product Name"
    )

    sku = st.text_input(
        "SKU"
    )

    barcode_value = st.text_input(
        "Barcode",
        value=barcode
    )

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


    if st.button("💾 Save Product"):

        if not name:

            st.warning(
                "Product name required"
            )

            return None


        product = {

            "name": name,

            "sku": sku,

            "barcode": barcode_value,

            "purchase_price": purchase_price,

            "selling_price": selling_price,

            "stock": stock

        }


        st.success(
            "Product data ready"
        )


        return product


    return None
