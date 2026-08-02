# ==============================================================================
# erp_pages/2_Mobile_Inventory.py
# MOBILE INVENTORY v2
# Camera Auto Scan + Search
# ==============================================================================

import streamlit as st

from erp_pages.inventory.scanner import get_barcode
from erp_pages.inventory.product_search import (
    search_product,
    product_card
)


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run():

    st.title("📦 Mobile Inventory v2")

    st.caption("📷 Camera Scan • 🔍 SKU • Product Search")

    st.info(
        "📌 Barcode ကို မျက်နှာပြင်အလယ်ထားပြီး 10–15 cm အကွာမှ ရိုက်ပါ။ "
        "အလင်းရောင်ကောင်းကောင်းရှိပြီး reflection မထိစေပါနှင့်။"
    )

    # ------------------------------------------------------------------
    # SESSION
    # ------------------------------------------------------------------

    if "mobile_product" not in st.session_state:
        st.session_state.mobile_product = None

    if "last_scanned_barcode" not in st.session_state:
        st.session_state.last_scanned_barcode = ""

    # ------------------------------------------------------------------
    # SCANNER
    # ------------------------------------------------------------------

    barcode = get_barcode()

    # ------------------------------------------------------------------
    # AUTO SEARCH (Camera success)
    # ------------------------------------------------------------------

    if barcode and barcode != st.session_state.last_scanned_barcode:

        st.session_state.last_scanned_barcode = barcode

        product = search_product(barcode)

        if product:

            st.session_state.mobile_product = product_card(product)

            st.success(f"📷 Scanned: {barcode}")

        else:

            st.warning(f"Barcode not found: {barcode}")

    # ------------------------------------------------------------------
    # MANUAL SEARCH
    # ------------------------------------------------------------------

    st.divider()

    st.subheader("🔍 Search Product")

    search_text = st.text_input(
        "Product Name / SKU",
        placeholder="Example: Coke or SKU001"
    )

    if st.button("🔎 Find Product"):

        keyword = barcode if barcode else search_text

        if keyword:

            product = search_product(keyword)

            if product:

                st.session_state.mobile_product = product_card(product)

            else:

                st.session_state.mobile_product = None

                st.warning("Product not found")

        else:

            st.warning("Enter barcode or product name")

    # ------------------------------------------------------------------
    # PRODUCT CARD
    # ------------------------------------------------------------------

    product = st.session_state.mobile_product

    if product:

        st.divider()

        st.success("✅ Product Found")

        st.subheader(f"📦 {product.get('name', 'Unknown')}")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Purchase Price",
                f"{float(product.get('purchase_price', 0)):,.0f}"
            )

            st.metric(
                "Current Stock",
                f"{product.get('stock', 0)} {product.get('unit', 'pcs')}"
            )

        with col2:

            st.metric(
                "Selling Price",
                f"{float(product.get('selling_price', 0)):,.0f}"
            )

            st.write(f"SKU : {product.get('sku', '-')}")

            st.write(f"Barcode : {product.get('barcode', '-')}")

        st.divider()

        st.info("Next Phase: Opening Stock / Stock In / Adjustment")

    else:

        st.info("📷 Scan barcode or search product")


# ==============================================================================
# DIRECT RUN
# ==============================================================================

if __name__ == "__main__":

    run()
