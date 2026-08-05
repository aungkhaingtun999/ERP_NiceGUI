# ==============================================================================
# PRODUCT FORM v12 STABLE
# MOBILE INVENTORY NEW PRODUCT REGISTRATION
# SAVE SUCCESS MESSAGE HOLD
# ==============================================================================

import streamlit as st


from database import supabase


# ------------------------------------------------------------------------------
# SHOW SAVE MESSAGE
# ------------------------------------------------------------------------------

def show_saved_message():

    if "product_saved_message" in st.session_state:

        st.success(
            st.session_state.product_saved_message
        )

        del st.session_state.product_saved_message



# ------------------------------------------------------------------------------
# RENDER FORM
# ------------------------------------------------------------------------------

def render_new_product_form(barcode=None):


    show_saved_message()


    st.subheader(
        "🆕 New Product Registration"
    )


    name = st.text_input(
        "Product Name"
    )


    barcode_value = st.text_input(
        "Barcode",
        value=barcode or ""
    )


    sku = st.text_input(
        "SKU"
    )


    purchase_price = st.number_input(
        "Purchase Price",
        min_value=0.0,
        step=100.0
    )


    selling_price = st.number_input(
        "Selling Price",
        min_value=0.0,
        step=100.0
    )


    stock = st.number_input(
        "Opening Stock",
        min_value=0,
        step=1
    )



    if st.button(
        "💾 Save Product",
        use_container_width=True
    ):


        if not name:

            st.warning(
                "Please enter product name"
            )

            return


        data = {

            "name": name,

            "barcode": barcode_value,

            "sku": sku,

            "purchase_price": purchase_price,

            "selling_price": selling_price,

            "stock": stock

        }



        try:


            result = (
                supabase
                .table("products")
                .insert(data)
                .execute()
            )



            if result.data:


                st.session_state.product_saved_message = (
                    "✅ Product saved successfully!"
                )


                st.session_state.barcode_value = barcode_value


                st.rerun()



            else:

                st.error(
                    "❌ Product save failed"
                )


        except Exception as e:


            st.error(
                f"❌ Error: {e}"
            )
