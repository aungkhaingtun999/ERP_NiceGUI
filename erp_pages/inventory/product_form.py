# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v5
# ERP ENTERPRISE PRODUCT REGISTRATION FORM
# ==============================================================================

import streamlit as st



# ------------------------------------------------------------------------------
# Clear Product Form
# ------------------------------------------------------------------------------

def clear_product_form():

    if "product_form_version" not in st.session_state:

        st.session_state["product_form_version"] = 0

    else:

        st.session_state["product_form_version"] += 1



# ------------------------------------------------------------------------------
# Product Registration Form
# ------------------------------------------------------------------------------

def render_new_product_form(barcode=""):


    # Initialize form version

    if "product_form_version" not in st.session_state:

        st.session_state["product_form_version"] = 0



    form_key = (
        f"new_product_form_"
        f"{st.session_state['product_form_version']}"
    )


    st.divider()

    st.subheader(
        "🆕 New Product Registration"
    )


    barcode = barcode.strip()



    if barcode:

        st.success(
            f"📷 Barcode: {barcode}"
        )

    else:

        st.warning(
            "Please scan or enter barcode first."
        )



    # --------------------------------------------------------------------------
    # Product Form
    # --------------------------------------------------------------------------

    with st.form(
        form_key,
        clear_on_submit=False
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
            step=100.0,
            value=0.0
        )


        selling_price = st.number_input(
            "Selling Price",
            min_value=0.0,
            step=100.0,
            value=0.0
        )


        stock = st.number_input(
            "Opening Stock",
            min_value=0,
            step=1,
            value=0
        )



        save_btn = st.form_submit_button(
            "💾 Save Product",
            use_container_width=True
        )



    # --------------------------------------------------------------------------
    # Clear Button
    # --------------------------------------------------------------------------

    clear_btn = st.button(
        "🧹 Clear Form",
        use_container_width=True
    )



    if clear_btn:

        clear_product_form()

        st.rerun()



    # --------------------------------------------------------------------------
    # Save Processing
    # --------------------------------------------------------------------------

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


            "barcode": barcode,


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


        st.json(
            product_data
        )


        return product_data



    return None
