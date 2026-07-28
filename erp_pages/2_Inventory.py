# ==============================================================================
# pages/2_Inventory.py
# ERP ENTERPRISE PRODUCT MASTER v4.3 - PRODUCTION HARDENED
# ==============================================================================

import time

import pandas as pd
import streamlit as st
from database import (
    db,
    get_inventory_view,
    get_warehouses,
    stock_adjustment_rpc,
    update_product_rpc,
)
from utils.ui import show_table


def run():
    st.title("🏭 Enterprise Product Master v4.3")

    # Warehouse Selection
    warehouses = get_warehouses()
    if not warehouses:
        st.error("No active warehouses found. Please check database.")
        st.stop()

    wh_map = {w["name"]: w["id"] for w in warehouses}
    selected_wh_name = st.selectbox("📍 Select Warehouse", list(wh_map.keys()))
    selected_wh_id = wh_map[selected_wh_name]

    # Tab ၅ ခု
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Product Master",
        "➕ Add Product",
        "✏️ Edit Product",
        "🔧 Stock Adjustment",
        "📊 Enterprise Dashboard",
    ])

    with tab1:
        search = st.text_input(
            "🔍 Search Products (Name, SKU, Barcode)", key="search_bar"
        )
        products = get_inventory_view(warehouse_id=selected_wh_id, search=search)

        if products:
            show_table(products)
        else:
            st.info("No products found in this warehouse.")

    with tab2:
        with st.form("add_product_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            data = {
                "name": c1.text_input("Product Name*"),
                "sku": c1.text_input("SKU*"),
                "barcode": c2.text_input("Barcode"),
                "purchase_price": c1.number_input("Purchase Price", value=0.0),
                "selling_price": c2.number_input("Selling Price", value=0.0),
                "category_id": 1,
                "unit": c2.selectbox("Unit", ["pcs", "kg", "box"]),
                "minimum_stock": c1.number_input("Minimum Stock", value=5),
            }
            init_qty = st.number_input("Initial Stock", min_value=0)

            if st.form_submit_button("Save Product", use_container_width=True):
                try:
                    res = (
                        db()
                        .rpc(
                            "create_product_full",
                            {
                                "p_data": data,
                                "p_warehouse_id": int(selected_wh_id),
                                "p_initial_qty": int(init_qty),
                            },
                        )
                        .execute()
                    )

                    result = res.data
                    if isinstance(result, list):
                        result = result[0]

                    if result and result.get("status") == "success":
                        st.success("Product created successfully!")
                    else:
                        st.error(
                            f"Error: {result.get('message', 'Unknown Error')}"
                        )
                except Exception as e:
                    st.error(f"Transaction failed: {str(e)}")

    with tab3:
        st.subheader("✏️ Edit Product Master")
        products = get_inventory_view(warehouse_id=selected_wh_id)

        if not products:
            st.info("No products available")
        else:
            product_map = {
                f"{p.get('sku','')} | {p.get('name','')}": p for p in products
            }
            selected_name = st.selectbox(
                "Select Product", list(product_map.keys())
            )
            selected_product = product_map[selected_name]

            st.divider()

            with st.form(f"edit_product_form_{selected_product['id']}"):
                c1, c2 = st.columns(2)
                name = c1.text_input(
                    "Product Name", value=selected_product.get("name", "")
                )
                sku = c1.text_input(
                    "SKU", value=selected_product.get("sku", "")
                )
                barcode = c2.text_input(
                    "Barcode", value=selected_product.get("barcode", "")
                )
                purchase_price = c1.number_input(
                    "Purchase Price",
                    value=float(selected_product.get("purchase_price", 0)),
                )
                selling_price = c2.number_input(
                    "Selling Price",
                    value=float(selected_product.get("selling_price", 0)),
                )
                minimum_stock = c1.number_input(
                    "Minimum Stock",
                    value=int(selected_product.get("minimum_stock", 0)),
                )

                unit_options = ["pcs", "kg", "box"]
                unit_val = selected_product.get("unit", "pcs")
                unit = c2.selectbox(
                    "Unit",
                    unit_options,
                    index=unit_options.index(unit_val)
                    if unit_val in unit_options
                    else 0,
                )

                notes = st.text_area(
                    "Notes", value=selected_product.get("notes", "")
                )
                is_active = st.checkbox(
                    "Active Product",
                    value=selected_product.get("is_active", True),
                )

                if st.form_submit_button(
                    "💾 Update Product", use_container_width=True
                ):
                    result = update_product_rpc(
                        product_id=selected_product["id"],
                        name=name,
                        sku=sku,
                        barcode=barcode,
                        purchase_price=purchase_price,
                        selling_price=selling_price,
                        minimum_stock=minimum_stock,
                        unit=unit,
                        notes=notes,
                        is_active=is_active,
                    )

                    if result.get("success"):
                        st.success(
                            f"✅ '{name}' ကို အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ။"
                        )
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result.get("message", "Update failed"))

    # =========================================================
    # 🔧 STOCK ADJUSTMENT
    # =========================================================
    with tab4:
        st.subheader("🔧 Stock Adjustment")
        products = get_inventory_view(warehouse_id=selected_wh_id)

        if not products:
            st.warning("No products found")
        else:
            product_map = {f"{p['id']} | {p['name']}": p for p in products}
            selected = st.selectbox("Select Product", list(product_map.keys()))
            product = product_map[selected]
            product_id = product["id"]
            current_stock = product.get("stock", product.get("qty", 0))

            st.info(
                f"📦 Product : {product['name']}\n🆔 ID : {product_id}\n📊 Current Stock : {current_stock}"
            )

            adjustment_qty = st.number_input(
                "Adjustment Quantity (+/-)", value=0, step=1
            )
            reason = st.text_input("Reason", "Stock Adjustment")

            if st.button("💾 Apply Adjustment", use_container_width=True):
                result = stock_adjustment_rpc(
                    product_id=product_id,
                    warehouse_id=selected_wh_id,
                    quantity=int(adjustment_qty),
                    reason=reason,
                    created_by=st.session_state.get("user_id"),
                )

                if result.get("success"):
                    st.success("✅ Stock Updated Successfully")
                    st.json(result.get("data"))

                    # Clear Streamlit cache
                    st.cache_data.clear()

                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result.get("message", "Adjustment Failed"))

    with tab5:
        st.caption(f"Current Warehouse : {selected_wh_name}")

        products = get_inventory_view(warehouse_id=selected_wh_id)
        if products:
            df = pd.DataFrame(products)
            for col in [
                "purchase_price",
                "minimum_stock",
                "qty",
                "selling_price",
            ]:
                if col not in df.columns:
                    df[col] = 0

            # Numeric conversion to prevent type errors
            df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
            df["purchase_price"] = pd.to_numeric(
                df["purchase_price"], errors="coerce"
            ).fillna(0)
            df["selling_price"] = pd.to_numeric(
                df["selling_price"], errors="coerce"
            ).fillna(0)

            # Calculate stock value per item with rounding
            df["stock_value"] = (df["qty"] * df["purchase_price"]).round(2)

            # Enterprise Inventory KPI
            inventory_cost = df["stock_value"].sum()
            inventory_value = (df["qty"] * df["selling_price"]).sum()
            potential_profit = inventory_value - inventory_cost

            m1, m2, m3, m4, m5 = st.columns(5)

            m1.metric("📦 Total Products", len(df))
            m2.metric("📊 Stock Qty", int(df["qty"].sum()))
            m3.metric("💰 Stock Value", f"{inventory_cost:,.0f} MMK")
            m4.metric("💵 Selling Value", f"{inventory_value:,.0f} MMK")
            m5.metric("📈 Potential Profit", f"{potential_profit:,.0f} MMK")

            st.divider()
            st.subheader("📋 Inventory Summary")
            summary = df.reindex(
                columns=[
                    "sku",
                    "name",
                    "qty",
                    "purchase_price",
                    "selling_price",
                    "stock_value",
                ]
            )
            show_table(summary)

            st.divider()
            st.subheader("⚠️ Low Stock Alert")
            low_stock = df[df["qty"] <= df["minimum_stock"]]
            if not low_stock.empty:
                low_stock_summary = low_stock.reindex(
                    columns=[
                        "sku",
                        "name",
                        "qty",
                        "minimum_stock",
                        "purchase_price",
                    ]
                )
                show_table(low_stock_summary)
            else:
                st.success("No Low Stock Products found in this warehouse.")
        else:
            st.write("No data available for dashboard.")


if __name__ == "__main__":
    run()
