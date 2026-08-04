# ==============================================================================
# MOBILE INVENTORY v9 STABLE
# SCANNER GUN / PHONE KEYBOARD MODE
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.zxing_scanner import zxing_scanner

from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title("📦 Mobile Inventory")
    st.caption("📷 Barcode Scanner / Manual Input")


    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False

    if "barcode_value" not in st.session_state:
        st.session_state.barcode_value = ""

    if "product" not in st.session_state:
        st.session_state.product = None
    if st.session_state.scanner_on:

    scanned_code = zxing_scanner()

    if scanned_code:
        st.session_state.barcode_value = scanned_code
        st.success(f"Scanned: {scanned_code}")

    # --------------------------------------------------
    # ON / OFF BUTTONS
    # --------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Start Scanner", use_container_width=True):
            st.session_state.scanner_on = True

    with col2:
        if st.button("🛑 Stop Scanner", use_container_width=True):
            st.session_state.scanner_on = False


    # --------------------------------------------------
    # BARCODE INPUT
    # --------------------------------------------------

    barcode = st.text_input(
        "📷 Barcode",
        key="barcode_value",
        placeholder="Scan barcode here or type manually"
    )


    # --------------------------------------------------
    # AUTO FOCUS WHEN SCANNER ON
    # --------------------------------------------------

    if st.session_state.scanner_on:

        components.html(
            """
            <script>
            const doc = window.parent.document;

            const input = doc.querySelector(
                'input[aria-label="📷 Barcode"]'
            );

            if(input){

                input.focus();
                input.select();

                input.addEventListener(
                    'blur',
                    () => setTimeout(() => input.focus(), 100)
                );
            }
            </script>
            """,
            height=0
        )

        st.success("📷 Scanner ON - scan barcode now")

    else:

        st.info("Scanner OFF")


    # --------------------------------------------------
    # SEARCH PRODUCT
    # --------------------------------------------------

    if st.button("🔍 Search Product", use_container_width=True):

        if barcode:

            product = search_product(barcode.strip())

            if product:

                st.session_state.product = product

            else:

                st.session_state.product = None
                st.warning(f"Barcode not found: {barcode}")

        else:

            st.warning("Please scan or enter barcode first")


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


if __name__ == "__main__":
    run()
