# ==============================================================================
# MOBILE INVENTORY v13 CLEAN ENTERPRISE
# CAMERA + SEARCH + PRODUCT REGISTRATION
# ==============================================================================

import io
import streamlit as st
from PIL import Image


# ------------------------------------------------------------------------------
# Barcode Decoder
# ------------------------------------------------------------------------------

try:
    from pyzbar.pyzbar import decode
    PYZBAR_OK = True

except Exception:
    PYZBAR_OK = False



# ------------------------------------------------------------------------------
# ERP Imports
# ------------------------------------------------------------------------------

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form

from database import (
    get_warehouses,
)



# ------------------------------------------------------------------------------
# CAMERA SCANNER
# ------------------------------------------------------------------------------

def scan_barcode_from_camera():

    if not PYZBAR_OK:

        st.error(
            "❌ Barcode scanner library not available"
        )

        return None


    photo = st.camera_input(
        "📷 Scan Barcode"
    )


    if photo is None:

        return None


    try:

        image = Image.open(
            io.BytesIO(
                photo.getvalue()
            )
        )


        codes = decode(image)


        if codes:

            return codes[0].data.decode(
                "utf-8"
            ).strip()


        st.warning(
            "❌ Barcode not detected"
        )


    except Exception as e:

        st.error(
            f"Scanner error : {e}"
        )


    return None




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


        st.session_state.barcode_value = barcode

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
        "📷 Camera Scan + Barcode Search + Product Registration"
    )



    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------

    defaults = {

        "camera_on": False,

        "barcode_value": "",

        "product": None,

        "warehouse_id": 1,

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

        st.error(
            f"Warehouse loading error : {e}"
        )



    st.divider()



    # --------------------------------------------------------------------------
    # CAMERA BUTTON
    # --------------------------------------------------------------------------

    c1,c2,c3 = st.columns(3)


    with c1:

        if st.button(
            "📷 Camera ON",
            use_container_width=True
        ):

            st.session_state.camera_on = True

            st.rerun()



    with c2:

        if st.button(
            "🛑 OFF",
            use_container_width=True
        ):

            st.session_state.camera_on = False

            st.rerun()



    with c3:

        if st.button(
            "🧹 Clear",
            use_container_width=True
        ):

            clear_inventory()

            st.rerun()




    # --------------------------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------------------------

    if st.session_state.camera_on:


        st.success(
            "📷 Camera Ready"
        )


        scanned = scan_barcode_from_camera()


        if scanned:


            st.success(
                f"✅ Scanned : {scanned}"
            )


            load_product(
                scanned
            )



    else:

        st.info(
            "Camera OFF"
        )



    st.divider()



    # --------------------------------------------------------------------------
    # MANUAL BARCODE
    # --------------------------------------------------------------------------

    barcode = st.text_input(

        "📷 Barcode / SKU",

        value=st.session_state.barcode_value

    )



    if barcode != st.session_state.barcode_value:


        if barcode:

            load_product(
                barcode
            )



    barcode = st.session_state.barcode_value

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


        render_new_product_form(
            barcode
        )




if __name__ == "__main__":

    run()
