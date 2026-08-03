import streamlit as st

from erp_pages.inventory.zxing_scanner import scan_barcode
from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title("📦 Mobile Inventory")
    st.caption("📷 Live Barcode Scanner")

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False

    if "barcode_input" not in st.session_state:
        st.session_state.barcode_input = ""

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
    # SCANNER
    # --------------------------------------------------

    if st.session_state.scanner_on:

        scanned = scan_barcode()

        if scanned:

            # Auto fill barcode box
            st.session_state.barcode_input = scanned.strip()

            st.success(
                f"Scanned : {scanned}"
            )

            # Stop scanner after successful scan
            st.session_state.scanner_on = False

    # --------------------------------------------------
    # BARCODE INPUT
    # --------------------------------------------------

    barcode = st.text_input(
        "📷 Barcode",
        key="barcode_input"
    )

    if barcode:

        st.success(
            f"Barcode : {barcode}"
        )

        if st.button(
            "🔍 Search Product",
            use_container_width=True
        ):

            product = search_product(barcode)

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

            else:

                st.warning(
                    "Barcode not found - Create New Product"
                )

                # Barcode auto passed into form
                render_new_product_form(barcode)

    else:

        st.info(
            "Press 📷 Start Scanner or enter barcode manually"
        )


if __name__ == "__main__":

    run()
