# ==============================================================================
# erp_pages/2_Mobile_Inventory.py
# MOBILE INVENTORY v2
# Phase 1 + Camera Scanner Ready
# Barcode + SKU + Product Search
# ==============================================================================


import streamlit as st


from erp_pages.inventory.scanner import (
    get_barcode
)


from erp_pages.inventory.product_search import (
    search_product,
    product_card
)



# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run():


    # ==========================================================================
    # TITLE
    # ==========================================================================

    st.title("📦 Mobile Inventory v2")

    st.caption(
        "📷 Barcode • 🔍 SKU • Product Search"
    )


    # ==========================================================================
    # SESSION
    # ==========================================================================

    if "mobile_product" not in st.session_state:

        st.session_state.mobile_product = None



    # ==========================================================================
    # SCANNER
    # ==========================================================================

    barcode = get_barcode()



    # ==========================================================================
    # SEARCH
    # ==========================================================================

    st.divider()

    st.subheader(
        "🔍 Search Product"
    )


    search_text = st.text_input(
        "Product Name / SKU",
        placeholder="Example: Coke or SKU001"
    )



    # ==========================================================================
    # FIND BUTTON
    # ==========================================================================

    if st.button(
        "🔎 Find Product"
    ):


        keyword = (

            barcode
            if barcode
            else search_text

        )


        if keyword:


            product = search_product(
                keyword
            )


            if product:


                st.session_state.mobile_product = (
                    product_card(product)
                )


            else:

                st.session_state.mobile_product = None

                st.warning(
                    "Product not found"
                )


        else:

            st.warning(
                "Enter barcode or product name"
            )



    # ==========================================================================
    # PRODUCT CARD
    # ==========================================================================

    product = st.session_state.mobile_product



    if product:


        st.divider()


        st.success(
            "✅ Product Found"
        )


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
            "Next Phase: Opening Stock / Stock In / Adjustment"
        )



    else:


        st.info(
            "📷 Scan barcode or search product"
        )



# ==============================================================================
# DIRECT RUN TEST
# ==============================================================================

if __name__ == "__main__":

    run()
