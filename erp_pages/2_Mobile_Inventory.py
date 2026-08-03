# ==============================================================================
# MOBILE INVENTORY v3
# LIVE BARCODE INVENTORY
# MOBILE OPTIMIZED
# ==============================================================================

import streamlit as st

from erp_pages.inventory.zxing_scanner import (
    scan_barcode
)

from erp_pages.inventory.product_search import (
    search_product
)

from erp_pages.inventory.product_form import (
    render_new_product_form
)


def run():

    st.title(
        "📦 Mobile Inventory"
    )

    st.caption(
        "📷 Live Barcode Scanner"
    )


    # --------------------------------------------------
    # SESSION
    # --------------------------------------------------

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False


    if "scanned_barcode" not in st.session_state:
        st.session_state.scanned_barcode = ""


    if "mobile_product" not in st.session_state:
        st.session_state.mobile_product = None


    if "new_product_barcode" not in st.session_state:
        st.session_state.new_product_barcode = ""



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

            st.session_state.mobile_product = None

            st.session_state.scanned_barcode = ""

            st.session_state.new_product_barcode = ""

            st.rerun()



    with col2:

        if st.button(
            "🛑 Stop Scanner",
            use_container_width=True
        ):

            st.session_state.scanner_on = False

            st.rerun()



    # --------------------------------------------------
    # SCANNER
    # --------------------------------------------------

    if st.session_state.scanner_on:

        barcode = scan_barcode()

        if barcode:

            st.session_state.scanned_barcode = (
                barcode.strip()
            )

            st.session_state.scanner_on = False

            st.success(
                f"Barcode : {barcode}"
            )

            st.rerun()



    # --------------------------------------------------
    # PRODUCT SEARCH & FLOW CONTROL
    # --------------------------------------------------

    barcode = (
        st.session_state.scanned_barcode
    )


    if barcode:

        st.divider()

        st.success(
            f"📷 Barcode : {barcode}"
        )


        if st.button(
            "🔍 Search Product",
            use_container_width=True
        ):

            product = search_product(
                barcode
            )


            if product:

                st.session_state.mobile_product = product

                st.session_state.new_product_barcode = ""

            else:

                st.session_state.mobile_product = None

                st.session_state.new_product_barcode = barcode

                st.warning(
                    "Barcode not found - Create New Product"
                )



    # --------------------------------------------------
    # RESULT: PRODUCT FOUND
    # --------------------------------------------------

    product = (
        st.session_state.mobile_product
    )


    if product:

        st.subheader(
            "📦 Product Found"
        )

        st.write(
            f"Name : {product.get('name','-')}"
        )

        st.write(
            f"Barcode : {product.get('barcode','-')}"
        )

        st.write(
            f"SKU : {product.get('sku','-')}"
        )

        st.write(
            f"Purchase Price : {product.get('purchase_price',0)}"
        )

        st.write(
            f"Selling Price : {product.get('selling_price',0)}"
        )

        st.write(
            f"Stock : {product.get('stock',0)}"
        )



    # --------------------------------------------------
    # NEW PRODUCT FORM
    # --------------------------------------------------

    elif (
        st.session_state.new_product_barcode
    ):

        render_new_product_form(
            st.session_state.new_product_barcode
        )



    # --------------------------------------------------
    # DEFAULT INFO
    # --------------------------------------------------

    elif not st.session_state.scanner_on:

        st.info(
            "Press 📷 Start Scanner"
        )



if __name__ == "__main__":

    run()
