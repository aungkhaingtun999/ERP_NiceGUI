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

    name = st.text_input(
        "Product Name"
    )

    sku = st.text_input(
        "SKU"
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


    if st.button(
        "💾 Save Product"
    ):

        if not name:

            st.error(
                "Enter product name"
            )

            return


        st.success(
            "Product ready"
        )

        st.json(
            {
                "name": name,
                "barcode": barcode,
                "sku": sku,
                "purchase_price": purchase_price,
                "selling_price": selling_price,
                "stock": stock
            }
        )
