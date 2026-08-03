import streamlit as st

from erp_pages.inventory.zxing_scanner import scan_barcode
from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title("📦 Mobile Inventory")
    st.caption("📷 Live Barcode Scanner")

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False

    if "scanned_barcode" not in st.session_state:
        st.session_state.scanned_barcode = ""

    if "mobile_product" not in st.session_state:
        st.session_state.mobile_product = None

    if "new_product_barcode" not in st.session_state:
        st.session_state.new_product_barcode = ""

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Start Scanner"):
            st.session_state.scanner_on = True
            st.session_state.mobile_product = None
            st.session_state.scanned_barcode = ""
            st.session_state.new_product_barcode = ""

    with col2:
        if st.button("🛑 Stop Scanner"):
            st.session_state.scanner_on = False

    # --------------------------------------------------
    # SCANNER
    # --------------------------------------------------

    if st.session_state.scanner_on:

        barcode = scan_barcode()

        if barcode:

            st.session_state.scanned_barcode = barcode.strip()
            st.session_state.scanner_on = False

            st.success(
                f"Barcode : {barcode}"
            )

    # --------------------------------------------------
    # BARCODE DISPLAY
    # --------------------------------------------------

    barcode = st.session_state.scanned_barcode

    if barcode:

        st.divider()

        st.success(
            f"📷 Barcode : {barcode}"
        )

        if st.button(
            "🔍 Search Product",
            use_container_width=True
        ):

            product = search_product(barcode)

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
    # PRODUCT RESULT
    # --------------------------------------------------

    product = st.session_state.mobile_product

    if product:

        st.divider()

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

    elif st.session_state.new_product_barcode:

        st.divider()

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
