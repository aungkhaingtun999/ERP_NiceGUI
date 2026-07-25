# ==============================================================================
# erp_pages/8_Transfer.py
# ERP ENTERPRISE WAREHOUSE TRANSFER v30 RLS & STOCK DEBUG
# ==============================================================================

import streamlit as st

from erp_core.base_repo import db, log_error
from erp_core.loaders.warehouse_loader import get_warehouses


def run():

    st.title("🔁 Enterprise Warehouse Transfer")

    # ==================================================
    # RESET OLD SELECTBOX STATE
    # ==================================================
    if "source_wh" in st.session_state:
        del st.session_state["source_wh"]

    if "dest_wh" in st.session_state:
        del st.session_state["dest_wh"]

    supabase = db()

    # ==================================================
    # RLS & STOCK DEBUG SECTION
    # ==================================================
    st.markdown("### 🔍 RLS & Warehouse Stock Debug")

    try:
        all_stock = (
            supabase
            .table("warehouse_stock")
            .select("*")
            .execute()
            .data
            or []
        )
        st.write("DEBUG ALL WAREHOUSE STOCK:", all_stock)
    except Exception as e:
        st.error(f"Failed to fetch warehouse stock: {e}")

    st.markdown("---")

    # ==================================================
    # LOAD WAREHOUSES
    # ==================================================

    warehouses = get_warehouses()

    if not warehouses:
        st.error("No warehouses found.")
        return

    warehouse_options = {
        w["id"]: w["name"]
        for w in warehouses
    }

    st.subheader("Transfer Details")

    col1, col2 = st.columns(2)

    warehouse_ids = list(warehouse_options.keys())
    source_default = 0

    for i, wid in enumerate(warehouse_ids):
        if warehouse_options[wid] == "Main Warehouse":
            source_default = i

    with col1:
        source_warehouse_id = st.selectbox(
            "Source Warehouse",
            options=warehouse_ids,
            index=source_default,
            format_func=lambda x: warehouse_options[x]
        )
        source_warehouse_id = int(source_warehouse_id)

    with col2:
        dest_list = [
            x for x in warehouse_options.keys()
            if x != source_warehouse_id
        ]

        dest_warehouse_id = st.selectbox(
            "Destination Warehouse",
            options=dest_list,
            index=0,
            format_func=lambda x: warehouse_options[x]
        )
        dest_warehouse_id = int(dest_warehouse_id)

    # ==================================================
    # LOAD PRODUCTS WITH STOCK
    # ==================================================

    try:
        stock_rows = (
            supabase
            .table("warehouse_stock")
            .select(
                """
                product_id,
                qty,
                available_qty
                """
            )
            .eq(
                "warehouse_id",
                int(source_warehouse_id)
            )
            .execute()
            .data
            or []
        )

    except Exception as e:
        st.error(f"Stock loading error: {e}")
        return

    st.write("DEBUG SOURCE ID:", source_warehouse_id)
    st.write("DEBUG STOCK:", stock_rows)

    if not stock_rows:
        st.warning("Source warehouse has no stock records.")
        return

    product_options = {}

    for row in stock_rows:
        try:
            product = (
                supabase
                .table("products")
                .select("name")
                .eq(
                    "id",
                    row["product_id"]
                )
                .execute()
                .data
            )

            if product:
                product_options[row["product_id"]] = product[0]["name"]
        except Exception:
            continue

    if not product_options:
        st.warning("No products with stock found.")
        return

    selected_product_id = st.selectbox(
        "Select Product",
        options=list(product_options.keys()),
        format_func=lambda x: product_options[x]
    )

    # ==================================================
    # STOCK DETAIL
    # ==================================================

    source_stock = next(
        (
            x for x in stock_rows
            if x["product_id"] == selected_product_id
        ),
        None
    )

    source_qty = source_stock.get("qty", 0) if source_stock else 0
    source_available = source_stock.get("available_qty", source_qty) if source_stock else 0

    # Destination stock
    try:
        dest_stock = (
            supabase
            .table("warehouse_stock")
            .select("qty, available_qty")
            .eq("warehouse_id", dest_warehouse_id)
            .eq("product_id", selected_product_id)
            .execute()
            .data
            or []
        )

        if dest_stock:
            dest_qty = dest_stock[0].get("qty", 0)
            dest_available = dest_stock[0].get("available_qty", dest_qty)
        else:
            dest_qty = 0
            dest_available = 0

    except Exception:
        dest_qty = 0
        dest_available = 0

    # ==================================================
    # DISPLAY STOCK
    # ==================================================

    c1, c2 = st.columns(2)

    with c1:
        st.info(
            f"""
📤 SOURCE STOCK

Warehouse:
{warehouse_options.get(source_warehouse_id, '')}

Product:
{product_options.get(selected_product_id, '')}

Current Qty:
{source_qty}

Available Qty:
{source_available}
"""
        )

    with c2:
        st.success(
            f"""
📥 DESTINATION STOCK

Warehouse:
{warehouse_options.get(dest_warehouse_id, '')}

Product:
{product_options.get(selected_product_id, '')}

Current Qty:
{dest_qty}

Available Qty:
{dest_available}
"""
        )

    # ==================================================
    # TRANSFER & PREVIEW
    # ==================================================

    if source_available <= 0:
        st.error("No available stock.")
        return

    qty = st.number_input(
        "Transfer Quantity",
        min_value=1,
        max_value=int(source_available),
        value=1
    )

    # 📊 After Transfer Preview Section
    st.subheader("📊 After Transfer Preview")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown(f"**{warehouse_options.get(source_warehouse_id, '')}**")
        st.metric(
            label="Source Stock Change",
            value=source_qty - qty,
            delta=f"-{qty}"
        )

    with col_p2:
        st.markdown(f"**{warehouse_options.get(dest_warehouse_id, '')}**")
        st.metric(
            label="Destination Stock Change",
            value=dest_qty + qty,
            delta=f"+{qty}"
        )

    st.markdown("---")

    if st.button(
        "🚚 Execute Transfer",
        type="primary"
    ):
        try:
            # Reduce source stock
            supabase.table(
                "warehouse_stock"
            ).update(
                {
                    "qty": source_qty - qty,
                    "available_qty": source_available - qty
                }
            ).eq(
                "warehouse_id",
                source_warehouse_id
            ).eq(
                "product_id",
                selected_product_id
            ).execute()

            # Increase or Insert destination stock
            if dest_stock:
                supabase.table(
                    "warehouse_stock"
                ).update(
                    {
                        "qty": dest_qty + qty,
                        "available_qty": dest_available + qty
                    }
                ).eq(
                    "warehouse_id",
                    dest_warehouse_id
                ).eq(
                    "product_id",
                    selected_product_id
                ).execute()
            else:
                supabase.table(
                    "warehouse_stock"
                ).insert(
                    {
                        "warehouse_id": dest_warehouse_id,
                        "product_id": selected_product_id,
                        "qty": qty,
                        "available_qty": qty
                    }
                ).execute()

            st.success("Transfer completed successfully.")
            st.rerun()

        except Exception as e:
            log_error(f"Transfer failed: {e}")
            st.error(str(e))


if __name__ == "__main__":
    run()
