# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v4
# ERP ENTERPRISE PRODUCT REGISTRATION FORM
# ==============================================================================

import streamlit as st


def clear_product_form():

    keys = [
        "product_name",
        "product_sku",
        "purchase_price",
        "selling_price",
        "opening_stock"
    ]

    for key in keys:
        st.session_state.pop(key, None)



def render_new_product_form(barcode=""):

    st.divider()

    st.subheader("🆕 New Product Registration")

    if barcode:

        st.success(
            f"📷 Barcode: {barcode}"
        )

    else:

        st.warning(
            "Please enter or scan a barcode first."
        )


    with st.form(
        "new_product_form",
        clear_on_submit=False
    ):


        name = st.text_input(
            "Product Name",
            key="product_name"
        )


        sku = st.text_input(
            "SKU",
            key="product_sku"
        )


        purchase_price = st.number_input(
            "Purchase Price",
            min_value=0.0,
            step=100.0,
            key="purchase_price"
        )


        selling_price = st.number_input(
            "Selling Price",
            min_value=0.0,
            step=100.0,
            key="selling_price"
        )


        stock = st.number_input(
            "Opening Stock",
            min_value=0,
            step=1,
            key="opening_stock"
        )


        # Form အတွင်းမှာ Save Product ခလုတ် တစ်ခုတည်းသာ ထားရှိပါသည်
        save_btn = st.form_submit_button(
            "💾 Save Product",
            use_container_width=True
        )


    # Clear Button ကို form အပြင်ဘက်သို့ ရွှေ့ပြောင်းထားပါသည်
    clear_btn = st.button(
        "🧹 Clear Form",
        use_container_width=True
    )


    if clear_btn:

        clear_product_form()

        st.rerun()



    if save_btn:


        if not barcode:

            st.error(
                "❌ Barcode required"
            )

            return None



        if not name.strip():

            st.error(
                "❌ Enter product name"
            )

            return None



        product_data = {

            "name": name.strip(),

            "barcode": barcode.strip(),

            "sku": sku.strip(),

            "purchase_price": float(
                purchase_price
            ),

            "selling_price": float(
                selling_price
            ),

            "stock": int(
                stock
            )

        }



        st.success(
            "✅ Product data ready"
        )


        return product_data



    return None
