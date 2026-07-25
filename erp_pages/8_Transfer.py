import streamlit as st
from datetime import datetime

from erp_core.base_repo import db, log_error
from erp_core.loaders.warehouse_loader import (
    get_warehouses,
    get_default_warehouse_id
)
from erp_core.loaders.product_loader import (
    get_active_products
)
from erp_core.repositories import RepositoryCoordinator


def run():
    st.title("🔁 Enterprise Warehouse Transfer")

    # Load Warehouses & Products
    warehouses = get_warehouses()
    products = get_active_products()

    # (သင့်ရဲ့ warehouse_options, product_options dict တည်ဆောက်သည့် logic များ ဤနေရာတွင် ရှိပါမည်)
    # ဥပမာ -
    warehouse_options = {w["id"]: w["name"] for w in warehouses}
    product_options = {p["id"]: p["name"] for p in products}

    # ==================================================
    # WAREHOUSE & PRODUCT SELECTION (Inside run())
    # ==================================================

    source_warehouse_id = st.selectbox(
        "Source Warehouse",
        options=list(warehouse_options.keys()),
        format_func=lambda x: warehouse_options[x],
        key="transfer_source_wh"
    )

    dest_warehouse_id = st.selectbox(
        "Destination Warehouse",
        options=list(warehouse_options.keys()),
        format_func=lambda x: warehouse_options[x],
        key="transfer_dest_wh"
    )

    selected_product_id = st.selectbox(
        "Select Product",
        options=list(product_options.keys()),
        format_func=lambda x: product_options[x],
        key="transfer_product"
    )

    # ==================================================
    # STOCK INFORMATION (Real-time Fetching)
    # ==================================================

    source_stock_qty = 0
    source_available_qty = 0
    dest_stock_qty = 0
    dest_available_qty = 0

    try:
        supabase = db()

        # Source Stock Query
        source_stock = (
            supabase
            .table("warehouse_stock")
            .select("*")
            .eq("warehouse_id", source_warehouse_id)
            .eq("product_id", selected_product_id)
            .execute()
            .data
            or []
        )

        if source_stock:
            source_stock_qty = source_stock[0].get("qty", 0)
            source_available_qty = source_stock[0].get("available_qty", source_stock_qty)

        # Destination Stock Query
        dest_stock = (
            supabase
            .table("warehouse_stock")
            .select("*")
            .eq("warehouse_id", dest_warehouse_id)
            .eq("product_id", selected_product_id)
            .execute()
            .data
            or []
        )

        if dest_stock:
            dest_stock_qty = dest_stock[0].get("qty", 0)
            dest_available_qty = dest_stock[0].get("available_qty", dest_stock_qty)

    except Exception as e:
        st.warning(f"Stock loading error: {e}")

    # ==================================================
    # DISPLAY STOCK
    # ==================================================

    stock_col1, stock_col2 = st.columns(2)

    with stock_col1:
        st.info(
            f"""
📤 **Source Stock**

Warehouse:
{warehouse_options.get(source_warehouse_id, '')}

Product:
{product_options.get(selected_product_id, '')}

Current Qty:
{source_stock_qty}

Available Qty:
{source_available_qty}
"""
        )

    with stock_col2:
        st.success(
            f"""
📥 **Destination Stock**

Warehouse:
{warehouse_options.get(dest_warehouse_id, '')}

Product:
{product_options.get(selected_product_id, '')}

Current Qty:
{dest_stock_qty}

Available Qty:
{dest_available_qty}
"""
        )

    # ==================================================
    # VALIDATION & TRANSFER INPUT
    # ==================================================

    if source_available_qty <= 0:
        st.error("Source warehouse has no available stock to transfer.")
    else:
        transfer_qty = st.number_input(
            "Transfer Quantity",
            min_value=1,
            max_value=int(source_available_qty),
            value=1,
            step=1
        )

        if st.button("Confirm & Transfer", type="primary"):
            # Transfer execution logic goes here
            st.success("Transfer process executed successfully!")


if __name__ == "__main__":
    run()
