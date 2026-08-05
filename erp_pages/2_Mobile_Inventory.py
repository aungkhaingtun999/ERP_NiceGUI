# ==============================================================================
# MOBILE INVENTORY v14 ENTERPRISE
# ZXING LIVE BARCODE SCANNER
# CAMERA + SEARCH + PRODUCT REGISTRATION
# ==============================================================================


import streamlit as st


from erp_pages.inventory.zxing_scanner import (
    zxing_scanner
)


from erp_pages.inventory.product_search import (
    search_product
)


import erp_pages.inventory.product_form as product_form


from database import (
    get_warehouses,
)



# ------------------------------------------------------------------------------
# PRODUCT SEARCH
# ------------------------------------------------------------------------------

def load_product(barcode):


    barcode = str(barcode).strip()


    if not barcode:
        return



    try:


        product = search_product(
            barcode
        )


        st.session_state.product = product



    except Exception as e:


        st.error(
            f"Search error : {e}"
        )




# ------------------------------------------------------------------------------
# RESET
# ------------------------------------------------------------------------------

def clear_inventory():


    st.session_state.barcode_value = ""

    st.session_state.product = None



# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

def run():


    st.title(
        "📦 Mobile Inventory"
    )


    st.caption(
        "📷 Live Barcode Scanner + Product Registration"
    )



    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------

    defaults = {


        "barcode_value": "",


        "product": None,


        "camera_on": False,


        "warehouse_id": None,


    }



    for key,value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value




    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    st.subheader(
        "🏭 Warehouse"
    )


    try:


        warehouses = get_warehouses()



        if warehouses:


            warehouse_map = {

                w["name"]: w["id"]

                for w in warehouses

            }



            selected = st.selectbox(

                "Select Warehouse",

                list(
                    warehouse_map.keys()
                )

            )



            st.session_state.warehouse_id = (
                warehouse_map[selected]
            )



    except Exception as e:


        st.warning(
            f"Warehouse error : {e}"
        )




    st.divider()



    # --------------------------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------------------------

    c1,c2 = st.columns(2)



    with c1:


        if st.button(

            "📷 Start Scanner",

            use_container_width=True

        ):


            st.session_state.camera_on = True



    with c2:


        if st.button(

            "🧹 Clear",

            use_container_width=True

        ):


            clear_inventory()

            st.rerun()



    # --------------------------------------------------------------------------
    # ZXING SCANNER
    # --------------------------------------------------------------------------

    if st.session_state.camera_on:


        st.success(
            "📷 Scanner Ready"
        )


        scanned = zxing_scanner()



        if scanned:


            if scanned != st.session_state.barcode_value:


                st.session_state.barcode_value = scanned


                load_product(
                    scanned
                )


                st.rerun()



    else:


        st.info(
            "Scanner OFF"
        )



    st.divider()



    # --------------------------------------------------------------------------
    # BARCODE INPUT
    # --------------------------------------------------------------------------

    barcode = st.text_input(

        "📷 Barcode / SKU",

        key="barcode_value"

    )



    if barcode:


        if (

            st.session_state.product is None

        ):


            load_product(
                barcode
            )




    product = st.session_state.product




    # --------------------------------------------------------------------------
    # PRODUCT FOUND
    # --------------------------------------------------------------------------

    if product:


        st.divider()


        st.subheader(
            "📦 Product Found"
        )


        st.write(
            "Name:",
            product.get("name")
        )


        st.write(
            "Barcode:",
            product.get("barcode")
        )


        st.write(
            "SKU:",
            product.get("sku")
        )


        st.write(
            "Stock:",
            product.get("stock",0)
        )



    # --------------------------------------------------------------------------
    # NEW PRODUCT
    # --------------------------------------------------------------------------

    elif barcode:


        st.divider()


        st.subheader(
            "🆕 New Product Registration"
        )


        product_form.render_new_product_form(
            barcode
        )




if __name__ == "__main__":

    run()
