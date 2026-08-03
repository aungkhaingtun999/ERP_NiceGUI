# ==============================================================================
# MOBILE INVENTORY v3
# LIVE BARCODE INVENTORY
# ==============================================================================
import streamlit as st

from erp_pages.inventory.zxing_scanner import scan_barcode
from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title("📦 Mobile Inventory")
    st.caption("📷 Barcode Scanner")

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False

    if "scanned_barcode" not in st.session_state:
        st.session_state.scanned_barcode = ""

    if "mobile_product" not in st.session_state:
        st.session_state.mobile_product = None

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Start Scanner"):
            st.session_state.scanner_on = True
            st.session_state.mobile_product = None

    with col2:
        if st.button("🛑 Stop Scanner"):
            st.session_state.scanner_on = False

    if st.session_state.scanner_on:

        barcode = scan_barcode()

        if barcode:

            st.session_state.scanned_barcode = barcode
            st.session_state.scanner_on = False
            st.rerun()

    barcode = st.session_state.scanned_barcode

    if barcode:

        st.success(f"Barcode: {barcode}")

        product = search_product(barcode)

        if product:

            st.session_state.mobile_product = product

        else:

            st.session_state.mobile_product = None

            st.warning(
                f"Barcode not found: {barcode}"
            )

            st.divider()

            st.write("### 🆕 New Product Registration")

            render_new_product_form(barcode)

    product = st.session_state.mobile_product

    if product:

        st.divider()

        st.subheader(product.get("name", "Unknown Product"))

        st.write(f"Barcode: {product.get('barcode', '-')}")
        st.write(f"SKU: {product.get('sku', '-')}")
        st.write(f"Purchase Price: {product.get('purchase_price', 0)}")
        st.write(f"Selling Price: {product.get('selling_price', 0)}")
        st.write(f"Stock: {product.get('stock', 0)}")

    if not barcode and not st.session_state.scanner_on:

        st.info("Press 📷 Start Scanner to scan a barcode")


if __name__ == "__main__":
    run()
