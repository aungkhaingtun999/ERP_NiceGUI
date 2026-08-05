# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v5
# ERP ENTERPRISE PRODUCT REGISTRATION
# create_product_full RPC VERSION
# ==============================================================================

import streamlit as st

from database import db


# ------------------------------------------------------------------------------
# CLEAR FORM
# ------------------------------------------------------------------------------

def clear_product_form():

    keys = [
        "product_name",
        "product_sku",
        "purchase_price",
        "selling_price",
        "opening_stock"
    ]

    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


# ------------------------------------------------------------------------------
# CREATE PRODUCT RPC
# ------------------------------------------------------------------------------

def create_product(
    product_data,
    warehouse_id
):

    try:

        response = (
            db()
            .rpc(
                "create_product_full",
                {
                    "p_data": product_data,
                    "p_warehouse_id": int(warehouse_id),
                    "p_initial_qty": int(
                        product_data.get("stock", 0)
                    )
                }
            )
            .execute()
        )


        result = response.data


        if isinstance(result, list):
            result = result[0]


        return result


    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }



# ------------------------------------------------------------------------------
# PRODUCT FORM
# ------------------------------------------------------------------------------

def render_new_product_form(
    barcode="",
    warehouse_id=1
):

    st.divider()

    st.subheader(
        "🆕 New Product Registration"
    )


    if barcode:

        st.success(
            f"📷 Barcode : {barcode}"
        )

    else:

        st.warning(
            "Barcode required"
        )



    with st.form(
        "mobile_new_product_form",
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


        save = st.form_submit_button(
            "💾 Save Product",
            use_container_width=True
        )



    clear = st.button(
        "🧹 Clear Form",
        use_container_width=True
    )


    # --------------------------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------------------------

    if clear:

        clear_product_form()

        st.success(
            "🧹 Form Cleared"
        )

        st.rerun()



    # --------------------------------------------------------------------------
    # SAVE
    # --------------------------------------------------------------------------

    if save:


        if not barcode:

            st.error(
                "❌ Barcode required"
            )

            return



        if not name.strip():

            st.error(
                "❌ Product name required"
            )

            return



        product_data = {

            "name": name.strip(),

            "barcode": str(
                barcode
            ).strip(),

            "sku": sku.strip(),

            "purchase_price": float(
                purchase_price
            ),

            "selling_price": float(
                selling_price
            ),

            "stock": int(
                stock
            ),

            "category_id": 1,

            "unit": "PCS",

            "minimum_stock": 5

        }



        with st.spinner(
            "Saving product..."
        ):


            result = create_product(
                product_data,
                warehouse_id
            )



        if result.get("status") == "success":


            st.success(
                "✅ Product Created Successfully"
            )


            st.json(result)


            clear_product_form()


            st.session_state.product = None


            st.session_state.barcode_value = ""


            st.rerun()



        else:


            message = result.get(
                "message",
                "Unknown error"
            )


            if "duplicate" in message.lower():

                st.error(
                    "⚠️ Barcode already exists"
                )

            else:

                st.error(
                    f"❌ Create Failed : {message}"
                )
