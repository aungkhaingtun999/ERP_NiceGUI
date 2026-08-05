# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v5
# ERP ENTERPRISE PRODUCT REGISTRATION ENGINE
# ==============================================================================

import time
import streamlit as st

from database import (
    db,
    get_warehouses,
)


# ------------------------------------------------------------------------------
# CLEAR FORM
# ------------------------------------------------------------------------------

def clear_product_form():

    keys = [
        "product_name",
        "product_sku",
        "purchase_price",
        "selling_price",
        "opening_stock",
        "selected_warehouse"
    ]

    for key in keys:
        st.session_state.pop(key, None)



# ------------------------------------------------------------------------------
# BARCODE DUPLICATE CHECK
# ------------------------------------------------------------------------------

def check_barcode_exists(barcode):

    try:

        result = (
            db()
            .table("products")
            .select(
                "id,name,barcode,sku"
            )
            .eq(
                "barcode",
                barcode
            )
            .execute()
        )

        if result.data:

            return result.data[0]

        return None


    except Exception:

        return None



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
                        product_data.get(
                            "stock",
                            0
                        )
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
            "status":"error",
            "message":str(e)
        }




# ------------------------------------------------------------------------------
# MAIN FORM
# ------------------------------------------------------------------------------

def render_new_product_form(
    barcode=""
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


    # --------------------------------------------------
    # WAREHOUSE LOAD
    # --------------------------------------------------

    warehouses = get_warehouses()


    if not warehouses:

        st.error(
            "No warehouse found"
        )

        return None



    warehouse_map = {

        w.get("name"):
        w.get("id")

        for w in warehouses

    }



    with st.form(
        "mobile_product_registration",
        clear_on_submit=False
    ):


        warehouse_name = st.selectbox(

            "🏭 Warehouse",

            list(
                warehouse_map.keys()
            ),

            key="selected_warehouse"

        )


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



    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    if save:


        if not barcode:

            st.error(
                "❌ Barcode missing"
            )

            return None



        if not name.strip():

            st.error(
                "❌ Product name required"
            )

            return None



        # Duplicate check

        duplicate = check_barcode_exists(
            barcode
        )


        if duplicate:


            st.error(
                "❌ Barcode already exists"
            )


            st.json(
                duplicate
            )

            return None



        payload = {


            "name":
                name.strip(),


            "barcode":
                barcode.strip(),


            "sku":
                sku.strip(),


            "purchase_price":
                float(
                    purchase_price
                ),


            "selling_price":
                float(
                    selling_price
                ),


            "category_id":
                1,


            "unit":
                "PCS",


            "minimum_stock":
                5


        }



        result = create_product(

            payload,

            warehouse_map[
                warehouse_name
            ]

        )



        if result.get("status") == "success":


            st.success(
                "✅ Product Created Successfully"
            )


            st.info(
                f"""
                Product ID :
                {result.get('product_id')}

                Warehouse :
                {warehouse_name}

                Opening Stock :
                {stock}
                """
            )


            time.sleep(1)


            clear_product_form()


            st.rerun()



        else:


            st.error(
                "❌ Product Create Failed"
            )


            st.code(
                result.get(
                    "message",
                    "Unknown error"
                )
            )


    return None
