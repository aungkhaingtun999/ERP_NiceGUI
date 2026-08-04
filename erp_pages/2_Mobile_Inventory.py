# ==============================================================================
# MOBILE INVENTORY v7 LIVE SCANNER AUTO FILL
# ==============================================================================

import streamlit as st

from erp_pages.inventory.zxing_scanner import scan_barcode
from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title("📦 Mobile Inventory")
    st.caption("📷 Live Barcode Scanner")


    # --------------------------------------------------
    # SESSION
    # --------------------------------------------------

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False

    if "barcode_value" not in st.session_state:
        st.session_state.barcode_value = ""

    if "last_scanned" not in st.session_state:
        st.session_state.last_scanned = ""

    if "product" not in st.session_state:
        st.session_state.product = None


    # --------------------------------------------------
    # START / STOP BUTTON
    # --------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Start Scanner", use_container_width=True):
            st.session_state.scanner_on = True

    with col2:
        if st.button("🛑 Stop Scanner", use_container_width=True):
            st.session_state.scanner_on = False


    # --------------------------------------------------
    # LIVE SCANNER
    # --------------------------------------------------

    if st.session_state.scanner_on:

        scanned = scan_barcode()

        # Barcode ရလာရင် textbox ထဲ auto ထည့်
        if scanned and scanned != st.session_state.last_scanned:

            st.session_state.last_scanned = scanned
            st.session_state.barcode_value = scanned.strip()

            st.success(f"✅ Scanned: {scanned}")

            # scanner ပိတ်
            st.session_state.scanner_on = False

            # textbox update ပြန်ပြ
            st.rerun()


    # --------------------------------------------------
    # BARCODE BOX
    # --------------------------------------------------

    barcode = st.text_input(
        "📷 Barcode",
        key="barcode_value"
    )


    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------

    if st.button("🔍 Search Product", use_container_width=True):

        if barcode:

            product = search_product(barcode.strip())

            if product:

                st.session_state.product = product

            else:

                st.session_state.product = None

                st.warning(
                    f"Barcode not found: {barcode}"
                )

        else:

            st.warning("Please scan barcode first")


    # --------------------------------------------------
    # PRODUCT RESULT
    # --------------------------------------------------

    product = st.session_state.product

    if product:

        st.divider()
        st.subheader("📦 Product Found")

        st.write("**Name:**", product.get("name", "-"))
        st.write("**Barcode:**", product.get("barcode", "-"))
        st.write("**SKU:**", product.get("sku", "-"))
        st.write("**Purchase Price:**", product.get("purchase_price", 0))
        st.write("**Selling Price:**", product.get("selling_price", 0))
        st.write("**Stock:**", product.get("stock", 0))


    # --------------------------------------------------
    # NEW PRODUCT FORM
    # --------------------------------------------------

    elif barcode:

        st.divider()
        st.subheader("🆕 New Product Registration")

        render_new_product_form(barcode)


    else:

        st.info("Press 📷 Start Scanner")


if __name__ == "__main__":
    run()
