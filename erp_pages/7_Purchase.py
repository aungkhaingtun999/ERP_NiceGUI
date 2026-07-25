import os
import sys
from decimal import Decimal

import streamlit as st

# ==============================================================================
# ROOT PATH
# ==============================================================================

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

# ==============================================================================
# IMPORTS
# ==============================================================================

from auth import is_authenticated

from database import (
    create_audit_log
)

from erp_core import (
    get_products,
    get_suppliers,
    get_warehouses,
    purchase_receive_rpc
)

from utils.ui import show_table

# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="Purchase Receive",
    page_icon="📦",
    layout="wide"
)

# ==============================================================================
# SAFE NAME HELPERS
# ==============================================================================

def supplier_name(data):
    return (
        data.get("company_name") or 
        data.get("name") or 
        data.get("supplier_name") or 
        f"Supplier #{data.get('id')}"
    )

def warehouse_name(data):
    return (
        data.get("name") or 
        data.get("warehouse_name") or 
        data.get("code") or 
        f"Warehouse #{data.get('id')}"
    )

def product_name(data):
    return (
        data.get("name") or 
        data.get("product_name") or 
        f"Product #{data.get('id')}"
    )

# ==============================================================================
# MAIN RUN
# ==============================================================================

def run():
    # --------------------------------------------------------------------------
    # AUTH
    # --------------------------------------------------------------------------
    if not is_authenticated():
        st.error("ကျေးဇူးပြု၍ Login အရင်ဝင်ပါ။")
        st.stop()

    # --------------------------------------------------------------------------
    # TITLE
    # --------------------------------------------------------------------------
    st.title("📦 Purchase Receive")

    # --------------------------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------------------------
    try:
        suppliers = get_suppliers()
        warehouses = get_warehouses()
        products = get_products()
    except Exception as e:
        st.error(f"Data loading error : {e}")
        st.stop()

    if not suppliers:
        st.error("Supplier မရှိပါ")
        st.stop()
    if not warehouses:
        st.error("Warehouse မရှိပါ")
        st.stop()
    if not products:
        st.error("Product မရှိပါ")
        st.stop()

    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------
    if "purchase_cart" not in st.session_state:
        st.session_state.purchase_cart = []
    if "purchase_supplier_id" not in st.session_state:
        st.session_state.purchase_supplier_id = None
    if "purchase_warehouse_id" not in st.session_state:
        st.session_state.purchase_warehouse_id = None

    cart_exists = (len(st.session_state.purchase_cart) > 0)

    # --------------------------------------------------------------------------
    # PURCHASE INFORMATION
    # --------------------------------------------------------------------------
    st.subheader("🏭 Purchase Information")
    
    supplier_ids = [s["id"] for s in suppliers]
    warehouse_ids = [w["id"] for w in warehouses]

    if st.session_state.purchase_supplier_id in supplier_ids:
        supplier_index = supplier_ids.index(st.session_state.purchase_supplier_id)
    else:
        supplier_index = 0

    selected_supplier = st.selectbox(
        "Supplier", 
        suppliers, 
        index=supplier_index, 
        format_func=supplier_name, 
        disabled=cart_exists
    )

    if st.session_state.purchase_warehouse_id in warehouse_ids:
        warehouse_index = warehouse_ids.index(st.session_state.purchase_warehouse_id)
    else:
        warehouse_index = 0

    selected_warehouse = st.selectbox(
        "Warehouse", 
        warehouses, 
        index=warehouse_index, 
        format_func=warehouse_name, 
        disabled=cart_exists
    )

    if not cart_exists:
        st.session_state.purchase_supplier_id = selected_supplier["id"]
        st.session_state.purchase_warehouse_id = selected_warehouse["id"]

    st.divider()

    # --------------------------------------------------------------------------
    # ADD PRODUCT
    # --------------------------------------------------------------------------
    st.subheader("➕ Add Product")
    with st.container(border=True):
        product = st.selectbox(
            "Product", 
            products, 
            format_func=lambda x: f"{product_name(x)} ({x.get('sku', '')})"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("Quantity", min_value=Decimal("0.01"), value=Decimal("1.00"), step=Decimal("1.00"))
        with col2:
            cost_price = st.number_input("Unit Cost", min_value=Decimal("0.00"), value=Decimal("0.00"), step=Decimal("1.00"))

        if st.button("Add to Cart", use_container_width=True):
            cart_item = {
                "product_id": product["id"],
                "product_name": product_name(product),
                "sku": product.get("sku", ""),
                "qty": quantity,
                "cost": cost_price,
                "total": quantity * cost_price
            }
            st.session_state.purchase_cart.append(cart_item)
            st.success("Product added to cart successfully!")
            st.rerun()

    # --------------------------------------------------------------------------
    # PURCHASE CART
    # --------------------------------------------------------------------------
    st.subheader("🛒 Purchase Cart")
    if st.session_state.purchase_cart:
        cart_display = []
        for idx, item in enumerate(st.session_state.purchase_cart):
            cart_display.append({
                "No": idx + 1,
                "Product": item["product_name"],
                "SKU": item["sku"],
                "Quantity": item["qty"],
                "Unit Cost": item["cost"],
                "Total": item["total"]
            })
        
        show_table(cart_display)

        # Remove item section
        remove_idx = st.number_input("Remove Item No", min_value=1, max_value=len(st.session_state.purchase_cart), step=1)
        if st.button("Remove Selected Item"):
            st.session_state.purchase_cart.pop(remove_idx - 1)
            st.rerun()

        if st.button("💾 Complete Purchase", type="primary", use_container_width=True):
            success = []
            errors = []
            
            for item in st.session_state.purchase_cart:
                try:
                    res = purchase_receive_rpc(
                        product_id=item["product_id"],
                        supplier_id=st.session_state.purchase_supplier_id,
                        warehouse_id=st.session_state.purchase_warehouse_id,
                        qty=int(item["qty"]),
                        cost=item["cost"],
                        remarks="Purchase Receive",
                        user_id=st.session_state.get("user_id")
                    )
                    if res and (res.get("success") or res is True):
                        success.append(f"Product #{item['product_id']} received successfully")
                    else:
                        err_msg = res.get("error", "Unknown error") if isinstance(res, dict) else "RPC execution failed"
                        errors.append(f"Product #{item['product_id']}: {err_msg}")
                except Exception as e:
                    errors.append(f"Product #{item['product_id']}: {str(e)}")

            if success:
                create_audit_log(
                    action="PURCHASE_RECEIVE", 
                    details=f"Received purchase items for supplier ID {st.session_state.purchase_supplier_id}"
                )
                st.success("Purchase Completed : " + ", ".join(success))
                st.session_state.purchase_cart = []
                st.session_state.purchase_supplier_id = None
                st.session_state.purchase_warehouse_id = None
                st.rerun()
            if errors:
                st.error("\n".join(errors))
    else:
        st.info("Cart is empty.")

    # --------------------------------------------------------------------------
    # CLEAR CART
    # --------------------------------------------------------------------------
    if st.button("🗑 Clear Cart", use_container_width=True):
        st.session_state.purchase_cart = []
        st.session_state.purchase_supplier_id = None
        st.session_state.purchase_warehouse_id = None
        st.rerun()

# ==============================================================================
# DIRECT RUN SUPPORT
# ==============================================================================

if __name__ == "__main__":
    run()
