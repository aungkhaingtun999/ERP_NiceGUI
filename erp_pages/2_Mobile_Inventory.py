import streamlit as st

from erp_pages.inventory.zxing_scanner import scan_barcode
from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title("📦 Mobile Inventory")
    st.caption("📷 Live Barcode Scanner")


    # ==========================
    # SESSION
    # ==========================

    if "scanner_on" not in st.session_state:
        st.session_state.scanner_on = False

    if "barcode_input" not in st.session_state:
        st.session_state.barcode_input = ""

    if "last_scanned" not in st.session_state:
        st.session_state.last_scanned = ""


    # ==========================
    # CAMERA BUTTON
    # ==========================

    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "📷 Start Scanner",
            use_container_width=True
        ):

            st.session_state.scanner_on = True
            st.rerun()



    with col2:

        if st.button(
            "🛑 Stop Scanner",
            use_container_width=True
        ):

            st.session_state.scanner_on = False
            st.rerun()



    # ==========================
    # CAMERA SCANNER
    # ==========================

    if st.session_state.scanner_on:


        scanned = scan_barcode()


        if scanned:


            scanned = str(scanned).strip()


            if scanned != st.session_state.last_scanned:


                st.session_state.last_scanned = scanned

                st.session_state.barcode_input = scanned

                st.session_state.scanner_on = False


                st.success(
                    f"✅ Scanned : {scanned}"
                )


                st.rerun()



    # ==========================
    # BARCODE BOX
    # ==========================

    barcode = st.text_input(
        "📷 Barcode",
        key="barcode_input"
    )



    # ==========================
    # SEARCH BUTTON
    # ==========================

    if barcode:


        st.success(
            f"Barcode : {barcode}"
        )


        if st.button(
            "🔍 Search Product",
            use_container_width=True
        ):


            product = search_product(
                barcode
            )


            if product:


                st.success(
                    "Product Found"
                )


                st.write(
                    product
                )


            else:


                st.warning(
                    "Barcode not found"
                )


                render_new_product_form(
                    barcode
                )



    else:


        st.info(
            "Press 📷 Start Scanner"
        )
