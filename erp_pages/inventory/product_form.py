# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v3
# NEW PRODUCT REGISTRATION
# ==============================================================================


import streamlit as st


from database import db



def render_new_product_form(barcode):


    st.divider()

    st.subheader(
        "🆕 New Product Registration"
    )


    with st.form(
        "new_product_form"
    ):


        product_barcode = st.text_input(
            "📷 Barcode",
            value=barcode
        )


        name = st.text_input(
            "📝 Product Name"
        )


        sku = st.text_input(
            "🏷 SKU"
        )


        purchase_price = st.number_input(
            "💰 Purchase Price",
            min_value=0.0
        )


        selling_price = st.number_input(
            "💵 Selling Price",
            min_value=0.0
        )


        stock = st.number_input(
            "📦 Opening Stock",
            min_value=0
        )


        unit = st.selectbox(
            "Unit",
            [
                "pcs",
                "box",
                "kg",
                "liter"
            ]
        )


        save = st.form_submit_button(
            "💾 Save Product"
        )



        if save:


            if not name:

                st.error(
                    "Product name required"
                )

                return



            try:


                result = (
                    db()
                    .table("products")
                    .insert(
                        {

                        "name": name,

                        "barcode": product_barcode,

                        "sku": sku,

                        "purchase_price":
                            purchase_price,

                        "selling_price":
                            selling_price,

                        "stock":
                            stock,

                        "unit":
                            unit

                        }
                    )
                    .execute()
                )



                st.success(
                    "✅ Product Saved"
                )


                st.session_state.mobile_product = (
                    result.data[0]
                )



            except Exception as e:


                st.error(
                    f"Save Error: {e}"
                )