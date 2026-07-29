# ==============================================================================
# erp_pages/pos/product.py
# ERP ENTERPRISE POS PRODUCT MODULE v12.7 FINAL
# TWO SEARCH BOX VERSION
# ==============================================================================

from typing import List, Dict, Any

import streamlit as st

from erp_core.loaders.product_loader import get_pos_products
from .cart import add_to_cart, check_available_stock
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
        return get_pos_products(warehouse_id=warehouse_id) or []
    except Exception as e:
        st.error(f"Product Load Error : {e}")
        return []


# ==============================================================================
# STOCK CHECK
# ==============================================================================

def check_stock(product, qty):
    return check_available_stock(
        st.session_state.get("cart", []),
        product.get("id"),
        product.get("available_qty", 0),
        qty,
    )


# ==============================================================================
# PRODUCT LABEL
# ==============================================================================

def product_label(product):
    price = get_final_price(product)
    sku = product.get("sku") or "NO-SKU"

    return (
        f"{sku} | "
        f"{product.get('name','')} | "
        f"Stock:{product.get('available_qty',0)} | "
        f"{money(price['price'])}"
    )


# ==============================================================================
# PRODUCT UI
# ==============================================================================

def render_products(warehouse_id):

    products = load_pos_products(warehouse_id)

    if not products:
        st.warning("No products found")
        return []


    # --------------------------------------------------------------------------
    # SEARCH AREA (TWO BOXES)
    # --------------------------------------------------------------------------
    st.subheader("🔍 Product Search")

    col1, col2 = st.columns(2)

    with col1:
        name_search = st.text_input(
            "🔍 Product Name",
            key=f"pos_name_search_{warehouse_id}"
        )

    with col2:
        barcode_search = st.text_input(
            "📦 SKU / Barcode",
            key=f"pos_barcode_search_{warehouse_id}"
        )


    # --------------------------------------------------------------------------
    # FILTER
    # --------------------------------------------------------------------------
    matches = []

    for product in products:

        name = str(product.get("name", ""))
        sku = str(product.get("sku", ""))
        barcode = str(product.get("barcode", ""))

        name_ok = True
        code_ok = True

        if name_search:
            name_ok = name_search.lower() in name.lower()

        if barcode_search:
            search = barcode_search.lower()

            code_ok = (
                search in sku.lower()
                or
                search in barcode.lower()
            )

        if name_ok and code_ok:
            matches.append(product)


    if not matches:
        st.warning("Product not found")
        return products


    # --------------------------------------------------------------------------
    # SELECT PRODUCT
    # --------------------------------------------------------------------------
    selected = st.selectbox(
        "Select Product",
        matches,
        format_func=product_label,
        key=f"pos_product_selectbox_{warehouse_id}"
    )


    # --------------------------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------------------------
    qty = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1,
        key=f"pos_product_qty_{warehouse_id}"
    )


    # --------------------------------------------------------------------------
    # PRODUCT INFO
    # --------------------------------------------------------------------------
    if selected:

        price_data = get_final_price(selected)

        st.info(
            f"""
**Product:** {selected.get('name')}

**Price:** {money(price_data['price'])}

**Price Source:** {price_data['source']}

**Available Stock:** {selected.get('available_qty',0)}
"""
        )


        # ----------------------------------------------------------------------
        # ADD TO CART
        # ----------------------------------------------------------------------
        if st.button(
            "➕ Add To Cart",
            use_container_width=True,
            key=f"pos_add_to_cart_{warehouse_id}_{selected.get('id')}"
        ):

            if not check_stock(selected, qty):
                st.error("Insufficient stock")
                return products

            add_to_cart(
                st.session_state.cart,
                selected,
                qty,
                price_data["price"],
                price_data["source"]
            )

            st.success("Added to cart")
            st.rerun()


    return products
