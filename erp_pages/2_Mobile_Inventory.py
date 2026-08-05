# ==============================================================================
# 2_Mobile_Inventory.py
# MOBILE INVENTORY v15 ENTERPRISE
# WEBRTC BARCODE SCANNER + SEARCH + PRODUCT REGISTRATION
# ==============================================================================


import streamlit as st


# ==============================================================================
# MOBILE SCANNER
# ==============================================================================

from erp_components.mobile_scanner.scanner import (
    mobile_scanner
)


# ==============================================================================
# PRODUCT MODULES
# ==============================================================================

from erp_pages.inventory.product_search import (
    search_product
)

import erp_pages.inventory.product_form as product_form


# ==============================================================================
# DATABASE
# ==============================================================================

from database import (
    get_warehouses
)



# ==============================================================================
# SESSION INITIALIZATION
# ==============================================================================


def initialize_session_state():

    defaults = {

        "barcode_value": "",

        "product": None,

        "camera_on": False,

        "warehouse_id": None,

    }


    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value





# ==============================================================================
# PRODUCT SEARCH
# ==============================================================================


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
            f"Product Search Error : {e}"
        )


        st.session_state.product = None





# ==============================================================================
# CLEAR
# ==============================================================================


def clear_inventory():


    st.session_state.barcode_value = ""

    st.session_state.product = None

    st.session_state.camera_on = False





# ==============================================================================
# WAREHOUSE
# ==============================================================================


def render_warehouse_selector():


    st.subheader(
        "🏭 Warehouse"
    )


    try:


        warehouses = get_warehouses()



        if warehouses:


            warehouse_map = {


                w.get("name"):
                w.get("id")


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



        else:


            st.warning(
                "No warehouse found"
            )



    except Exception as e:


        st.warning(
            f"Warehouse Error : {e}"
        )





# ==============================================================================
# SCANNER
# ==============================================================================


def handle_scanner():


    if st.session_state.camera_on:


        st.success(
            "📷 Scanner Ready"
        )


        scanned = mobile_scanner()



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





# ==============================================================================
# MAIN APP
# ==============================================================================


def run():


    st.title(
        "📦 Mobile Inventory v15"
    )


    st.caption(
        "📷 WebRTC Barcode Scanner + Product Management"
    )



    initialize_session_state()



    # Warehouse

    render_warehouse_selector()


    st.divider()



    # Buttons


    col1, col2 = st.columns(2)



    with col1:


        if st.button(

            "📷 Start Scanner",

            use_container_width=True

        ):


            st.session_state.camera_on = True

            st.rerun()



    with col2:


        if st.button(

            "🧹 Clear",

            use_container_width=True

        ):


            clear_inventory()

            st.rerun()



    st.divider()



    # Scanner

    handle_scanner()



    st.divider()



    # Manual Input


    barcode_input = st.text_input(

        "📷 Barcode / SKU",

        value=
        st.session_state.barcode_value,

        key="mobile_barcode_input"

    )



    if barcode_input != st.session_state.barcode_value:


        st.session_state.barcode_value = barcode_input



        if barcode_input:

            load_product(
                barcode_input
            )

        else:

            st.session_state.product = None



        st.rerun()

    # ==========================================================================
    # PRODUCT VIEW
    # ==========================================================================


def render_product_view():


    product = st.session_state.product

    barcode = st.session_state.barcode_value



    if product:


        st.divider()


        st.subheader(
            "📦 Product Found"
        )


        st.write(
            f"**Name:** {product.get('name','N/A')}"
        )


        st.write(
            f"**Barcode:** {product.get('barcode','N/A')}"
        )


        st.write(
            f"**SKU:** {product.get('sku','N/A')}"
        )


        st.write(
            f"**Stock:** {product.get('stock',0)}"
        )


        st.write(
            f"**Selling Price:** {product.get('selling_price',0)} MMK"
        )



    elif barcode:


        st.divider()


        st.subheader(
            "🆕 New Product Registration"
        )


        product_form.render_new_product_form(

            barcode

        )



    else:


        st.info(
            "Scan barcode or enter SKU"
        )





# ==============================================================================
# COMPLETE RUNNER
# ==============================================================================


def run():


    st.title(
        "📦 Mobile Inventory v15"
    )


    st.caption(
        "📷 WebRTC Barcode Scanner + Search + Product Registration"
    )



    initialize_session_state()



    render_warehouse_selector()



    st.divider()



    # --------------------------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------------------------


    col1, col2 = st.columns(2)



    with col1:


        if st.button(

            "📷 Start Scanner",

            use_container_width=True,

            key="start_mobile_scanner"

        ):


            st.session_state.camera_on = True

            st.rerun()



    with col2:


        if st.button(

            "🧹 Clear",

            use_container_width=True,

            key="clear_mobile_inventory"

        ):


            clear_inventory()

            st.rerun()



    st.divider()



    # --------------------------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------------------------


    handle_scanner()



    st.divider()



    # --------------------------------------------------------------------------
    # MANUAL SEARCH
    # --------------------------------------------------------------------------


    barcode_input = st.text_input(

        "📷 Barcode / SKU",

        value=st.session_state.barcode_value,

        key="manual_barcode_input"

    )



    if barcode_input != st.session_state.barcode_value:


        st.session_state.barcode_value = barcode_input



        if barcode_input:


            load_product(
                barcode_input
            )


        else:


            st.session_state.product = None



        st.rerun()



    # --------------------------------------------------------------------------
    # PRODUCT RESULT
    # --------------------------------------------------------------------------


    render_product_view()





# ==============================================================================
# ENTRY POINT
# ==============================================================================


if __name__ == "__main__":

    run()
