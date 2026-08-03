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
    get_barcode.__module__
)


def run():

    st.title("📦 Mobile Inventory")
    st.caption("📷 Barcode Inventory")


    if "barcode_value" not in st.session_state:
        st.session_state.barcode_value = ""

    if "product" not in st.session_state:
        st.session_state.product = None


    # ============================
    # SCAN BUTTON
    # ============================

    if st.button(
        "📷 Scan Barcode",
        use_container_width=True
    ):

        scanned = get_barcode()

        st.write(
            "DEBUG VALUE:",
            repr(scanned)
        )

        st.write(
            "DEBUG TYPE:",
            type(scanned).__name__
        )


        if scanned:

            st.session_state.barcode_value = str(scanned).strip()

            st.rerun()



    # ============================
    # BARCODE INPUT
    # ============================

    barcode = st.text_input(
        "📷 Barcode",
        key="barcode_value"
    )


    # ============================
    # SEARCH
    # ============================

    if st.button(
        "🔍 Search Product",
        use_container_width=True
    ):

        if barcode:

            product = search_product(barcode)

            if product:

                st.session_state.product = product

            else:

                st.session_state.product = None

                st.warning(
                    "Barcode not found - Create New Product"
                )



    # ============================
    # RESULT
    # ============================

    if st.session_state.product:

        product = st.session_state.product

        st.success("📦 Product Found")

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


    elif barcode:

        render_new_product_form(barcode)


    else:

        st.info(
            "Scan barcode or enter manually"
        )


if __name__ == "__main__":
    run()
