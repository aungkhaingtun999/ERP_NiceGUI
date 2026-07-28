# ==============================================================================
# erp_pages/pos/product.py
# ERP ENTERPRISE POS PRODUCT MODULE v12.3 FINAL
#
# RESPONSIBILITY
# - Product loading
# - Search
# - Barcode / SKU lookup
# - Product selection
# - Stock validation
# - Add to cart
# ==============================================================================

from typing import List, Dict, Any

import streamlit as st

from erp_core.loaders.product_loader import get_pos_products

from .cart import (
    add_to_cart,
    check_available_stock,
)

from .engine import get_final_price


# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def money(value):

    try:
        return f"{float(value):,.0f} MMK"

    except Exception:
        return "0 MMK"


# ==============================================================================
# LOAD PRODUCTS
# ==============================================================================

def load_pos_products(warehouse_id=None) -> List[Dict[str, Any]]:

    try:
        return get_pos_products(
            warehouse_id=warehouse_id
        ) or []

    except Exception as e:

        st.error(
            f"Product Load Error : {e}"
        )

        return []


# ==============================================================================
# SEARCH
# ==============================================================================

def search_products(products, keyword=""):

    if not keyword:
        return products

    keyword = str(keyword).lower().strip()

    return [

        p

        for p in products

        if (

            keyword in str(
                p.get("name", "")
            ).lower()

            or

            keyword in str(
                p.get("sku", "")
            ).lower()

            or

            keyword in str(
                p.get("barcode", "")
            ).lower()

        )

    ]


# ==============================================================================
# STOCK CHECK
# ==============================================================================

def check_stock(product, qty):

    return check_available_stock(

        st.session_state.get(
            "cart",
            []
        ),

        product.get("id"),

        product.get(
            "available_qty",
            0
        ),

        qty,

    )


# ==============================================================================
# PRODUCT LABEL
# ==============================================================================

def product_label(product):

    price = get_final_price(product)

    return (

        f"{product.get('sku','')} | "
        f"{product.get('name','')} | "
        f"Stock:{product.get('available_qty',0)} | "
        f"{money(price['price'])}"

    )


# ==============================================================================
# FIND PRODUCT
# ==============================================================================

def get_product_by_id(products, product_id):

    for product in products:

        if int(product.get("id")) == int(product_id):
            return product

    return None


# ==============================================================================
# PRODUCT UI
# ==============================================================================

def render_products(warehouse_id):

    products = load_pos_products(warehouse_id)

    if not products:

        st.warning("No products found")

        return []


    # --------------------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------------------

    st.subheader("🔍 Product Search")

    keyword = st.text_input(
        "Name / SKU / Barcode",
        key="pos_product_search"
    )

    filtered = search_products(products, keyword)

    if not filtered:

        st.warning("Product not found")

        return products


    # --------------------------------------------------------------------------
    # SELECT PRODUCT
    # --------------------------------------------------------------------------

    selected = st.selectbox(
        "Select Product",
        filtered,
        format_func=product_label,
        key="pos_product_selectbox"
    )


    # --------------------------------------------------------------------------
    # QTY
    #
