# ==============================================================================
# MOBILE INVENTORY v10
# CAMERA SCAN AUTO SEARCH + MANUAL BARCODE INPUT
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.zxing_scanner import zxing_scanner
from erp_pages.inventory.product_form import render_new_product_form


def load_product(barcode):

    if not barcode:
        return

    product = search_product(barcode.strip())

    if product:

        st.session_state.product = product
        st.session_state.barcode_value = barcode

    else:

        st.session_state.product = None

        st.warning(
            f"❌ Barcode not found: {barcode}"
        )



def run():

    st.title("📦 Mobile Inventory")

    st.caption(
        "📷 Camera Scanner + Manual Barcode"
    )


    # --------------------------------------------------
    # SESSION
    # --------------------------------------------------

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False


    if "barcode_value" not in st.session_state:
        st.session_state.barcode_value = ""


    if "product" not in st.session_state:
        st.session_state.product = None



    # --------------------------------------------------
    # BUTTON
    # --------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "📷 Start Scanner",
            use_container_width=True
        ):

            st.session_state.scanner_on = True



    with col2:

        if st.button(
            "🛑 Stop Scanner",
            use_container_width=True
        ):

            st.session_state.scanner_on = False



    # --------------------------------------------------
    # CAMERA SCANNER
    # --------------------------------------------------

    if st.session_state.scanner_on:


        st.success(
            "📷 Point camera to barcode"
        )


        scanned_code = zxing_scanner()


        # AUTO SEARCH
        if scanned_code:


            st.success(
                f"✅ Scanned: {scanned_code}"
            )


            load_product(
                scanned_code
            )



    else:

        st.info(
            "Scanner OFF"
        )



    # --------------------------------------------------
    # MANUAL BARCODE
    # --------------------------------------------------

    st.divider()


    barcode = st.text_input(

        "📷 Manual Barcode / SKU",

        value=st.session_state.barcode_value,

        placeholder="Type barcode manually"

    )


    if barcode:

        if st.button(
            "🔍 Search Product",
            use_container_width=True
        ):

            load_product(
                barcode
            )



    # --------------------------------------------------
    # PRODUCT
    # --------------------------------------------------

    product = st.session_state.product


    if product:


        st.divider()


        st.subheader(
            "📦 Product Found"
        )


        st.write(
            "Name:",
            product.get("name","-")
        )


        st.write(
            "Barcode:",
            product.get("barcode","-")
        )


        st.write(
            "SKU:",
            product.get("sku","-")
        )


        st.write(
            "Purchase:",
            product.get("purchase_price",0)
        )


        st.write(
            "Selling:",
            product.get("selling_price",0)
        )


        st.write(
            "Stock:",
            product.get("stock",0)
        )


    # --------------------------------------------------
    # NEW PRODUCT
    # --------------------------------------------------

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
