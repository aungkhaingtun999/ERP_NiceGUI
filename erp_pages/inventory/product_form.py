# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v3
# ERP ENTERPRISE PRODUCT REGISTRATION
# ==============================================================================

import streamlit as st

from database import (
    get_inventory_service,
    get_categories,
    get_suppliers,
    get_warehouses,
)


def render_new_product_form(barcode: str):

    st.divider()
    st.subheader("🆕 New Product Registration")

    categories = get_categories() or []
    suppliers = get_suppliers() or []
    warehouses = get_warehouses() or []

    category_options = {c["id"]: c["name"] for c in categories}
    supplier_options = {s["id"]: s["name"] for s in suppliers}
    warehouse_options = {w["id"]: w["name"] for w in warehouses}

    with st.form("mobile_inventory_new_product"):

        st.text_input(
            "📷 Barcode",
            value=barcode,
            disabled=True
        )

        name = st.text_input("📝 Product Name")
        short_name = st.text_input("🔤 Short Name")
        sku = st.text_input("🏷 SKU")

        category_id = None
        if category_options:
            category_id = st.selectbox(
                "📂 Category",
                options=list(category_options.keys()),
                format_func=lambda x: category_options[x]
            )

        supplier_id = None
        if supplier_options:
            supplier_id = st.selectbox(
                "🏭 Supplier",
                options=list(supplier_options.keys()),
                format_func=lambda x: supplier_options[x]
            )

        warehouse_id = None
        if warehouse_options:
            warehouse_id = st.selectbox(
                "🏬 Warehouse",
                options=list(warehouse_options.keys()),
                format_func=lambda x: warehouse_options[x]
            )

        unit = st.selectbox(
            "📏 Unit",
            ["pcs", "box", "kg", "liter"]
        )

        col1, col2 = st.columns(2)

        with col1:
            purchase_price = st.number_input(
                "💰 Purchase Price",
                min_value=0.0,
                step=100.0
            )

            markup_percent = st.number_input(
                "📈 Markup %",
                min_value=0.0,
                value=20.0,
                step=1.0
            )

        with col2:
            selling_price = st.number_input(
                "💵 Selling Price",
                min_value=0.0,
                step=100.0
            )

            opening_stock = st.number_input(
                "📦 Opening Stock",
                min_value=0,
                step=1
            )

        minimum_stock = st.number_input(
            "⚠️ Minimum Stock",
            min_value=0,
            value=5
        )

        reorder_level = st.number_input(
            "🔁 Reorder Level",
            min_value=0,
            value=10
        )

        notes = st.text_area("📝 Notes")

        save_btn = st.form_submit_button(
            "💾 Save Product"
        )

        if save_btn:

            if not name.strip():
                st.error("Product name is required")
                return

            product_data = {
                "name": name.strip(),
                "short_name": short_name.strip() or None,
                "barcode": barcode,
                "sku": sku.strip() or None,
                "category_id": category_id,
                "supplier_id": supplier_id,
                "unit": unit,
                "purchase_price": purchase_price,
                "selling_price": selling_price,
                "final_selling_price": selling_price,
                "markup_percent": markup_percent,
                "minimum_stock": minimum_stock,
                "reorder_level": reorder_level,
                "notes": notes.strip() or None,
                "is_active": True,
            }

            try:

                service = get_inventory_service()

                result = service.create_product_with_stock(
                    product_data=product_data,
                    opening_stock=int(opening_stock),
                    warehouse_id=warehouse_id,
                    created_by=None,
                )

                if result.get("success"):

                    st.success("✅ Product created successfully")

                    st.session_state.mobile_product = result["data"]

                    st.rerun()

                else:

                    st.error(result.get("message", "Save failed"))

            except Exception as e:

                st.error(f"Save error: {e}")
                
