# ==============================================================================
# erp_pages/2_Mobile_Inventory.py
# MOBILE INVENTORY v3
# REAL-TIME LIVE BARCODE SCANNER
# ==============================================================================

import streamlit as st

from erp_pages.inventory.zxing_scanner import (
    scan_barcode
)

from erp_pages.inventory.product_search import (
    search_product
)



# ==============================================================================
# MAIN
# ==============================================================================


def run():


    st.title(
        "📦 Mobile Inventory v3"
    )


    st.caption(
        "📷 Live Barcode Scanner • Mobile Optimized"
    )


    # ------------------------------------------------------------------
    # SESSION
    # ------------------------------------------------------------------

    if "mobile_product" not in st.session_state:

        st.session_state.mobile_product = None


    if "last_code" not in st.session_state:

        st.session_state.last_code = ""



    # ------------------------------------------------------------------
    # LIVE SCANNER
    # ------------------------------------------------------------------

    barcode = scan_barcode()



    if barcode:


        st.success(
            f"Barcode: {barcode}"
        )



        # Prevent duplicate search

        if barcode != st.session_state.last_code:


            st.session_state.last_code = barcode



            product = search_product(
                barcode
            )


            if product:


                st.session_state.mobile_product = product


                st.success(
                    "✅ Product loaded automatically"
                )


            else:


                st.warning(
                    f"Barcode not found: {barcode}"
                )



    # ------------------------------------------------------------------
    # PRODUCT CARD
    # ------------------------------------------------------------------

    product = st.session_state.mobile_product



    if product:


        st.divider()


        st.subheader(
            f"📦 {product.get('name','Unknown')}"
        )



        col1, col2 = st.columns(2)



        with col1:


            st.metric(

                "Purchase Price",

                f"{float(product.get('purchase_price',0)):,.0f}"

            )


            st.metric(

                "Current Stock",

                f"{product.get('stock',0)} {product.get('unit','pcs')}"

            )



        with col2:


            st.metric(

                "Selling Price",

                f"{float(product.get('selling_price',0)):,.0f}"

            )


            st.write(
                f"SKU : {product.get('sku','-')}"
            )


            st.write(
                f"Barcode : {product.get('barcode','-')}"
            )



        st.divider()


        st.info(
            "Next Phase: Stock Update"
        )



    else:


        st.info(
            "📷 Point the camera at a barcode"
        )



# ==============================================================================
# STREAMLIT ENTRY
# ==============================================================================


if __name__ == "__main__":

    run()
