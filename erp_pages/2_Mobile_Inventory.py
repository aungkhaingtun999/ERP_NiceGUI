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

    if "mobile_product" not in st.session_state:
        st.session_state.mobile_product = None

    barcode = scan_barcode()

    if barcode:

        st.success(f"Barcode: {barcode}")

        product = search_product(barcode)

        if product:

            st.session_state.mobile_product = product

        else:

            st.warning("Barcode not found")

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

    else:

        st.info("Scan a barcode")


if __name__ == "__main__":
    run()
