# ==============================================================================
# erp_pages/2_Mobile_Inventory.py
# MOBILE INVENTORY v3
# BARCODE + PRODUCT SEARCH + NEW PRODUCT
# ==============================================================================

import streamlit as st
from erp_pages.inventory.scanner import get_barcode
from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


st.write(
    "DEBUG FUNCTION:",
    scan_barcode.__module__
)


def run():

    st.title(
        "📦 Mobile Inventory"
    )

    st.caption(
        "📷 Barcode Inventory"
    )


    # ==================================================
    # SESSION
    # ==================================================

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False


    if "barcode_value" not in st.session_state:
        st.session_state.barcode_value = ""


    if "product" not in st.session_state:
        st.session_state.product = None



    # ==================================================
    # CAMERA BUTTON
    # ==================================================

    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "📷 Start Scanner",
            use_container_width=True
        ):

            st.session_state.scanner_on = True
            st.session_state.product = None



    with col2:

        if st.button(
            "🛑 Stop Scanner",
            use_container_width=True
        ):

            st.session_state.scanner_on = False



    # ==================================================
    # SCANNER
    # ==================================================

    if st.session_state.scanner_on:


        scanned = get_barcode()


        st.write(
            "VALUE:",
            repr(scanned)
        )


        st.write(
            "TYPE:",
            type(scanned).__name__
        )


        if scanned and isinstance(scanned, str):


            barcode = scanned.strip()


            st.session_state.barcode_value = barcode


            st.session_state.scanner_on = False


            st.success(
                f"Scanned : {barcode}"
            )



    # ==================================================
    # BARCODE INPUT
    # ==================================================

    barcode = st.text_input(
        "📷 Barcode",
        key="barcode_value"
    )



    # ==================================================
    # SEARCH
    # ==================================================

    if barcode:


        if st.button(
            "🔍 Search Product",
            use_container_width=True
        ):


            product = search_product(
                barcode
            )


            if product:


                st.session_state.product = product


            else:


                st.session_state.product = None


                st.warning(
                    "Barcode not found"
                )



    # ==================================================
    # PRODUCT FOUND
    # ==================================================

    if st.session_state.product:


        product = st.session_state.product


        st.divider()


        st.subheader(
            "📦 Product Found"
        )


        st.write(
            "Name:",
            product.get(
                "name",
                "-"
            )
        )


        st.write(
            "Barcode:",
            product.get(
                "barcode",
                "-"
            )
        )


        st.write(
            "SKU:",
            product.get(
                "sku",
                "-"
            )
        )


        st.write(
            "Purchase Price:",
            product.get(
                "purchase_price",
                0
            )
        )


        st.write(
            "Selling Price:",
            product.get(
                "selling_price",
                0
            )
        )


        st.write(
            "Stock:",
            product.get(
                "stock",
                0
            )
        )



    # ==================================================
    # NEW PRODUCT
    # ==================================================

    elif barcode:


        st.divider()


        render_new_product_form(
            barcode
        )



    else:


        st.info(
            "Press 📷 Start Scanner"
        )



if __name__ == "__main__":

    run()
