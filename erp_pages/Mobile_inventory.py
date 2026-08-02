# ==============================================================================
# erp_pages/Mobile_Inventory.py
# MOBILE INVENTORY v2
# Phase 1 - Barcode + Product Search
# ==============================================================================


import streamlit as st


from inventory.scanner import (
    barcode_input
)

from inventory.product_search import (
    search_product,
    product_card
)



# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="Mobile Inventory v2",
    page_icon="📦",
    layout="centered"
)



# ==============================================================================
# TITLE
# ==============================================================================

st.title("📦 Mobile Inventory v2")

st.caption(
    "Barcode • SKU • Product Search"
)



# ==============================================================================
# SESSION
# ==============================================================================

if "mobile_product" not in st.session_state:
    st.session_state.mobile_product = None



# ==============================================================================
# BARCODE INPUT
# ==============================================================================

barcode = barcode_input()



# ==============================================================================
# SEARCH AREA
# ==============================================================================

st.divider()

st.subheader("🔍 Search Product")


search_text = st.text_input(
    "Product Name / SKU",
    placeholder="Example: Coke or SKU001"
)



# ==============================================================================
# SEARCH BUTTON
# ==============================================================================

if st.button("🔎 Find Product"):


    keyword = (
        barcode
        if barcode
        else search_text
    )


    product = search_product(keyword)


    if product:

        st.session_state.mobile_product = (
            product_card(product)
        )

    else:

        st.warning(
            "Product not found"
        )



# ==============================================================================
# PRODUCT CARD
# ==============================================================================


product = st.session_state.mobile_product


if product:


    st.divider()

    st.success(
        "Product Found"
    )


    st.subheader(
        f"📦 {product['name']}"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Purchase Price",
            f"{product['purchase_price']:,.0f}"
        )


        st.metric(
            "Current Stock",
            f"{product['stock']} {product['unit']}"
        )


    with col2:

        st.metric(
            "Selling Price",
            f"{product['selling_price']:,.0f}"
        )


        st.text(
            f"SKU : {product['sku']}"
        )


    st.divider()


    st.info(
        "Next Phase: Stock Update"
    )


else:


    st.info(
        "Scan barcode or search product"
    )