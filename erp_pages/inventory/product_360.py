# ==============================================================================
# erp_pages/inventory/product_360.py
#
# ERP ENTERPRISE PRODUCT 360°
# CLEAN & OPTIMIZED BUILD
# ------------------------------------------------------------------------------
# Product Master
# Warehouse Stock
# Batch / FEFO
# FIFO Cost Layers
# Pricing Intelligence
# Sales / Purchases / Adjustments / Transfers / Refunds
# Unified History & Audit
# Integrity & Entry Points
#
# Compatibility:
#     render_product_360_page(client, product_id)
#     render_product_360(client, product_id)
#     render_page(client, product_id)
#
# IMPORTANT: READ ONLY MODULE
# ==============================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import streamlit as st


# ==============================================================================
# TIMEZONE
# ==============================================================================

MMT = ZoneInfo("Asia/Yangon")
UTC = ZoneInfo("UTC")


def format_myanmar_time(value: Any) -> str:
    """
    Convert database timestamp to Myanmar Standard Time.
    """
    if value is None or value == "":
        return "-"

    try:
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return "-"
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            dt = datetime.fromisoformat(text)
        elif isinstance(value, datetime):
            dt = value
        else:
            return str(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        dt = dt.astimezone(MMT)
        return dt.strftime("%Y-%m-%d %H:%M:%S MMT")

    except Exception:
        return str(value)


# ==============================================================================
# DECIMAL HELPERS
# ==============================================================================

def to_decimal(
    value: Any,
    default: Decimal = Decimal("0"),
) -> Decimal:
    """
    Safe Decimal conversion.
    """
    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def money(value: Any) -> str:
    """
    Format money. Example: 1500 -> 1,500.00
    """
    return f"{to_decimal(value):,.2f}"


def qty(value: Any) -> str:
    """
    Format quantity.
    """
    amount = to_decimal(value)
    try:
        if amount == amount.to_integral_value():
            return f"{int(amount):,}"
    except Exception:
        pass
    return f"{amount:,.3f}"


# ==============================================================================
# SAFE DATABASE EXECUTION
# ==============================================================================

def _execute(query: Any) -> Any:
    """
    Execute Supabase query safely.
    """
    try:
        result = query.execute()
        data = getattr(result, "data", None)
        return data or []
    except Exception as exc:
        return {"__error__": str(exc)}


def _is_error(data: Any) -> bool:
    return isinstance(data, dict) and "__error__" in data


# ==============================================================================
# EMPTY STATE
# ==============================================================================

def empty_history(
    title: str,
    message: str = "No historical record available.",
):
    st.info(f"**{title}**\n\n{message}")


# ==============================================================================
# DATA LOADERS (PRODUCT, STOCK, BATCHES, FIFO)
# ==============================================================================

def get_product(client: Any, product_id: int) -> Optional[Dict]:
    try:
        result = (
            client.table("products")
            .select("*")
            .eq("id", int(product_id))
            .limit(1)
            .execute()
        )
        rows = getattr(result, "data", None) or []
        if isinstance(rows, list) and rows:
            return rows[0]
        if isinstance(rows, dict):
            return rows
        return None
    except Exception:
        return None


def get_warehouse_stock(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("warehouse_stock")
        .select("*")
        .eq("product_id", int(product_id))
        .order("warehouse_id", desc=False)
    )
    return [] if _is_error(data) else data


def get_batches(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("inventory_batches")
        .select("*")
        .eq("product_id", int(product_id))
        .order("created_at", desc=False)
    )
    return [] if _is_error(data) else data


def get_fifo_layers(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("inventory_cost_layers")
        .select("*")
        .eq("product_id", int(product_id))
        .order("created_at", desc=False)
    )
    return [] if _is_error(data) else data


# ==============================================================================
# HISTORY DATA LOADERS
# ==============================================================================

def get_sales(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("sale_items")
        .select("*")
        .eq("product_id", int(product_id))
        .order("created_at", desc=True)
    )
    return [] if _is_error(data) else data


def get_purchases(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("purchase_items")
        .select("*")
        .eq("product_id", int(product_id))
        .order("created_at", desc=True)
    )
    return [] if _is_error(data) else data


def get_adjustments(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("stock_adjustments")
        .select("*")
        .eq("product_id", int(product_id))
        .order("created_at", desc=True)
    )
    return [] if _is_error(data) else data


def get_transfers(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("stock_transfers")
        .select("*")
        .eq("product_id", int(product_id))
        .order("created_at", desc=True)
    )
    return [] if _is_error(data) else data


def get_refunds(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("refunds")
        .select("*")
        .eq("product_id", int(product_id))
        .order("refund_date", desc=True)
    )
    return [] if _is_error(data) else data


def get_unified_history(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("product_inventory_history")
        .select("*")
        .eq("product_id", int(product_id))
        .order("transaction_time", desc=True)
    )
    if not _is_error(data):
        return data

    data = _execute(
        client.table("inventory_movements")
        .select("*")
        .eq("product_id", int(product_id))
        .order("created_at", desc=True)
    )
    return [] if _is_error(data) else data


def get_audit_history(client: Any, product_id: int) -> List[Dict]:
    data = _execute(
        client.table("product_audit_logs")
        .select("*")
        .eq("product_id", int(product_id))
        .order("changed_at", desc=True)
    )
    if not _is_error(data):
        return data

    data = _execute(
        client.table("inventory_audit_logs")
        .select("*")
        .eq("product_id", int(product_id))
        .order("changed_at", desc=True)
    )
    return [] if _is_error(data) else data


# ==============================================================================
# INVENTORY INTEGRITY & CALCULATIONS
# ==============================================================================

def get_integrity(
    product: Dict,
    warehouse_rows: List[Dict],
    batch_rows: List[Dict],
    fifo_rows: List[Dict],
) -> Dict:
    master_stock = to_decimal(product.get("stock"))

    warehouse_stock = sum(
        to_decimal(row.get("qty") if row.get("qty") is not None else row.get("quantity"))
        for row in warehouse_rows
    )

    batch_remaining = sum(
        to_decimal(row.get("qty_remaining") if row.get("qty_remaining") is not None else row.get("remaining_qty"))
        for row in batch_rows
    )

    fifo_remaining = sum(
        to_decimal(row.get("qty_remaining") if row.get("qty_remaining") is not None else row.get("remaining_qty"))
        for row in fifo_rows
    )

    warnings: List[str] = []
    passed: List[str] = []

    if warehouse_stock == fifo_remaining:
        passed.append("Warehouse stock matches FIFO remaining.")
    else:
        warnings.append("Warehouse stock differs from FIFO remaining.")

    if master_stock == warehouse_stock:
        passed.append("Master stock matches warehouse stock.")
    else:
        warnings.append("Master stock differs from warehouse stock.")

    if batch_remaining == fifo_remaining:
        passed.append("Batch remaining matches FIFO remaining.")
    else:
        warnings.append("Batch remaining differs from FIFO remaining.")

    return {
        "master_stock": master_stock,
        "warehouse_stock": warehouse_stock,
        "batch_remaining": batch_remaining,
        "fifo_remaining": fifo_remaining,
        "warnings": warnings,
        "passed": passed,
    }


def calculate_stock_summary(
    product: Dict,
    warehouse_rows: List[Dict],
    batch_rows: List[Dict],
    fifo_rows: List[Dict],
) -> Dict:
    integrity = get_integrity(product, warehouse_rows, batch_rows, fifo_rows)
    return {
        "master_stock": integrity["master_stock"],
        "warehouse_stock": integrity["warehouse_stock"],
        "batch_remaining": integrity["batch_remaining"],
        "fifo_remaining": integrity["fifo_remaining"],
    }


def calculate_price_info(product: Dict) -> Dict:
    purchase_price = to_decimal(product.get("purchase_price"))
    selling_price = to_decimal(product.get("selling_price"))
    markup_percent = to_decimal(product.get("markup_percent"))

    if markup_percent == Decimal("0"):
        markup_percent = to_decimal(product.get("global_markup_percent", product.get("default_markup_percent", 0)))

    global_markup_price = purchase_price * (Decimal("1") + markup_percent / Decimal("100"))

    owner_selling_price = to_decimal(product.get("owner_selling_price"))
    owner_price_locked = bool(product.get("owner_price_locked", False))

    final_selling_price = to_decimal(product.get("final_selling_price"))
    if final_selling_price == 0:
        if owner_price_locked and owner_selling_price > 0:
            final_selling_price = owner_selling_price
        elif selling_price > 0:
            final_selling_price = selling_price
        else:
            final_selling_price = global_markup_price

    if purchase_price > 0:
        actual_markup_percent = ((final_selling_price - purchase_price) / purchase_price) * Decimal("100")
    else:
        actual_markup_percent = Decimal("0")

    profit_per_unit = final_selling_price - purchase_price
    price_source = product.get("price_source") or "PRODUCT"

    return {
        "purchase_price": purchase_price,
        "selling_price": selling_price,
        "global_markup_percent": markup_percent,
        "global_markup_price": global_markup_price,
        "actual_markup_percent": actual_markup_percent,
        "owner_selling_price": owner_selling_price,
        "final_selling_price": final_selling_price,
        "owner_price_locked": owner_price_locked,
        "price_source": price_source,
        "profit_per_unit": profit_per_unit,
    }


# ==============================================================================
# UI RENDERERS
# ==============================================================================

def render_product_header(product: Dict):
    name = product.get("name") or "Unknown Product"
    sku = product.get("sku") or "-"
    barcode = product.get("barcode") or "-"
    status = "ACTIVE" if product.get("is_active", True) else "INACTIVE"

    st.title(f"Product 360° — {name}")
    st.caption(f"SKU: {sku}  |  Barcode: {barcode}  |  Status: {status}")


def render_current_status(product: Dict, integrity: Dict):
    st.subheader("Current Inventory Status")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Master Stock", qty(integrity.get("master_stock")))
    c2.metric("Warehouse Stock", qty(integrity.get("warehouse_stock")))
    c3.metric("FIFO Remaining", qty(integrity.get("fifo_remaining")))
    c4.metric("Batch Remaining", qty(integrity.get("batch_remaining")))

    warnings = integrity.get("warnings", [])
    if warnings:
        for warning in warnings:
            st.warning(f"⚠️ {warning}")
    else:
        st.success("Inventory integrity checks passed.")


def render_warehouse(rows: List[Dict]):
    st.subheader("Warehouse Stock")
    if not rows:
        empty_history("Warehouse Stock")
        return

    display = []
    for row in rows:
        qty_value = row.get("qty") if row.get("qty") is not None else row.get("quantity")
        display.append({
            "Warehouse": row.get("warehouse_id") or "-",
            "Qty": qty(qty_value),
            "Reserved": qty(row.get("reserved_qty")),
            "Available": qty(row.get("available_qty")),
            "Minimum": qty(row.get("minimum_stock")),
            "Reorder": qty(row.get("reorder_level")),
            "Location": row.get("location") or "-",
            "Batch No": row.get("batch_no") or "-",
            "Updated": format_myanmar_time(row.get("updated_at")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_batches(rows: List[Dict]):
    st.subheader("Batch / FEFO")
    if not rows:
        empty_history("Batch / FEFO")
        return

    display = []
    for index, row in enumerate(rows, start=1):
        q_val = row.get("quantity") if row.get("quantity") is not None else row.get("qty_in")
        r_val = row.get("qty_remaining") if row.get("qty_remaining") is not None else row.get("remaining_qty")
        display.append({
            "FEFO Rank": index,
            "Batch": row.get("batch_no") or "-",
            "Qty In": qty(q_val),
            "Remaining": qty(r_val),
            "Unit Cost": money(row.get("unit_cost")),
            "MFG Date": row.get("mfg_date") or "-",
            "Expiry": row.get("expiry_date") or "-",
            "Supplier": row.get("supplier_code") or "-",
            "Created": format_myanmar_time(row.get("created_at")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_fifo(rows: List[Dict]):
    st.subheader("FIFO Cost Layers")
    if not rows:
        empty_history("FIFO Cost Layers")
        return

    display = []
    for index, row in enumerate(rows, start=1):
        q_in = row.get("qty_in") if row.get("qty_in") is not None else row.get("quantity")
        r_val = row.get("qty_remaining") if row.get("qty_remaining") is not None else row.get("remaining_qty")
        display.append({
            "FIFO Rank": index,
            "Layer ID": row.get("id") or "-",
            "Qty In": qty(q_in),
            "Remaining": qty(r_val),
            "Unit Cost": money(row.get("unit_cost")),
            "Reference": row.get("reference_type") or "-",
            "Reference ID": row.get("reference_id") or "-",
            "Batch": row.get("batch_no") or "-",
            "Expiry": row.get("expiry_date") or "-",
            "Created": format_myanmar_time(row.get("created_at")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_pricing(product: Dict):
    st.subheader("Pricing Intelligence")
    info = calculate_price_info(product)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Purchase Price", money(info["purchase_price"]))
    c2.metric("Global Markup", f"{info['global_markup_percent']}%")
    c3.metric("Selling Price", money(info["selling_price"]))
    c4.metric("Profit / Unit", money(info["profit_per_unit"]))

    st.markdown(
        f"""
**Price Source:** `{info["price_source"]}`  
**Global Markup Price:** `{money(info["global_markup_price"])}`  
**Actual Markup:** `{info["actual_markup_percent"]:.2f}%`  
**Owner Selling Price:** `{money(info["owner_selling_price"])}`  
**Final Selling Price:** `{money(info["final_selling_price"])}`  
**Owner Price Locked:** `{info["owner_price_locked"]}`
"""
    )


def render_sales(rows: List[Dict]):
    st.subheader("Sales History")
    if not rows:
        empty_history("Sales History")
        return

    display = []
    for row in rows:
        display.append({
            "Invoice": row.get("invoice_no") or row.get("sale_id") or "-",
            "Warehouse": row.get("warehouse_id") or "-",
            "Qty": qty(row.get("quantity") if row.get("quantity") is not None else row.get("qty")),
            "Unit Price": money(row.get("unit_price") or row.get("selling_price")),
            "Discount": money(row.get("discount")),
            "Total": money(row.get("total") or row.get("line_total")),
            "Status": row.get("sale_status") or row.get("status") or "-",
            "Payment": row.get("payment_method") or "-",
            "Time": format_myanmar_time(row.get("created_at")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_purchases(rows: List[Dict]):
    st.subheader("Purchase History")
    if not rows:
        empty_history("Purchase History")
        return

    display = []
    for row in rows:
        q_val = row.get("qty") if row.get("qty") is not None else row.get("quantity")
        p_val = row.get("price") if row.get("price") is not None else row.get("unit_cost")
        t_val = row.get("total") if row.get("total") is not None else (to_decimal(q_val) * to_decimal(p_val))
        display.append({
            "Purchase No": row.get("purchase_no") or row.get("purchase_id") or "-",
            "Warehouse": row.get("warehouse_id") or "-",
            "Qty": qty(q_val),
            "Unit Cost": money(p_val),
            "Total": money(t_val),
            "Status": row.get("status") or "-",
            "Payment": row.get("payment_method") or "-",
            "Reference": row.get("reference_no") or "-",
            "Time": format_myanmar_time(row.get("created_at")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_adjustments(rows: List[Dict]):
    st.subheader("Stock Adjustment History")
    if not rows:
        empty_history("Adjustment History")
        return

    display = []
    for row in rows:
        display.append({
            "ID": row.get("id"),
            "Warehouse": row.get("warehouse_id") or "-",
            "Type": row.get("adjustment_type") or "-",
            "Qty": qty(row.get("qty")),
            "Unit Cost": money(row.get("unit_cost")),
            "Reason": row.get("reason") or "-",
            "Status": row.get("status") or "-",
            "Requested By": row.get("requested_by") or "-",
            "Approved By": row.get("approved_by") or "-",
            "Created": format_myanmar_time(row.get("created_at")),
            "Approved": format_myanmar_time(row.get("approved_at")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_transfers(rows: List[Dict]):
    st.subheader("Stock Transfer History")
    if not rows:
        empty_history("Transfer History")
        return

    display = []
    for row in rows:
        display.append({
            "Transfer No": row.get("transfer_no") or row.get("id") or "-",
            "From Warehouse": row.get("from_warehouse_id") or "-",
            "To Warehouse": row.get("to_warehouse_id") or "-",
            "Qty": qty(row.get("qty") if row.get("qty") is not None else row.get("quantity")),
            "Status": row.get("status") or "-",
            "Remarks": row.get("remarks") or "-",
            "Requested By": row.get("requested_by") or "-",
            "Approved By": row.get("approved_by") or "-",
            "Created": format_myanmar_time(row.get("created_at")),
            "Approved": format_myanmar_time(row.get("approved_at")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_refunds(rows: List[Dict]):
    st.subheader("Refund History")
    if not rows:
        empty_history("Refund History")
        return

    display = []
    for row in rows:
        display.append({
            "Refund ID": row.get("refund_id") or row.get("id"),
            "Sale ID": row.get("sale_id"),
            "Qty": qty(row.get("quantity")),
            "Unit Price": money(row.get("unit_price")),
            "Total": money(row.get("total")),
            "Refund Amount": money(row.get("refund_amount")),
            "Reason": row.get("reason") or "-",
            "Status": row.get("status") or "-",
            "Date": format_myanmar_time(row.get("refund_date")),
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_unified_history(rows: List[Dict]):
    st.subheader("Unified Product Transaction History")
    if not rows:
        empty_history("Unified Transaction History")
        return

    display = []
    for row in rows:
        balance = row.get("balance_after")
        display.append({
            "Time (MMT)": format_myanmar_time(row.get("transaction_time") or row.get("created_at")),
            "Source": row.get("transaction_source") or row.get("source") or "-",
            "Type": row.get("transaction_type") or row.get("movement_type") or "-",
            "Reference": row.get("reference_id") or "-",
            "Transaction": row.get("transaction_id") or row.get("id") or "-",
            "Warehouse": row.get("warehouse_id") or "-",
            "Qty": qty(row.get("quantity") if row.get("quantity") is not None else row.get("qty")),
            "Balance": qty(balance) if balance is not None else "-",
            "Remarks": row.get("remarks") or row.get("reason") or "-",
        })
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_audit(rows: List[Dict]):
    st.subheader("Product Audit History")
    if not rows:
        empty_history("Audit History", "No historical audit record available.")
        return

    for row in rows:
        operation = row.get("operation") or row.get("action") or "UNKNOWN"
        changed_at = format_myanmar_time(row.get("changed_at"))
        with st.expander(f"{operation} — {changed_at}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### Before")
                st.json({
                    "purchase_price": row.get("old_purchase_price"),
                    "selling_price": row.get("old_selling_price"),
                    "markup_percent": row.get("old_markup_percent"),
                    "price_source": row.get("old_price_source"),
                    "owner_selling_price": row.get("old_owner_selling_price"),
                    "final_selling_price": row.get("old_final_selling_price"),
                })
            with c2:
                st.markdown("### After")
                st.json({
                    "purchase_price": row.get("new_purchase_price"),
                    "selling_price": row.get("new_selling_price"),
                    "markup_percent": row.get("new_markup_percent"),
                    "price_source": row.get("new_price_source"),
                    "owner_selling_price": row.get("new_owner_selling_price"),
                    "final_selling_price": row.get("new_final_selling_price"),
                })
            st.caption(f"Changed By: {row.get('changed_by') or 'SYSTEM'}")


def render_integrity(integrity: Dict):
    st.subheader("Inventory Integrity")
    passed = integrity.get("passed", [])
    warnings = integrity.get("warnings", [])

    for item in passed:
        st.success(f"✓ {item}")
    for item in warnings:
        st.warning(f"⚠ {item}")

    if not passed and not warnings:
        st.info("No inventory integrity result available.")


# ==============================================================================
# ENTRY POINTS
# ==============================================================================

def render_product_360(client: Any, product_id: int):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        st.error("Invalid Product ID.")
        return

    if product_id <= 0:
        st.error("Invalid Product ID.")
        return

    product = get_product(client, product_id)
    if not product:
        st.error(f"Product ID {product_id} was not found.")
        return

    warehouse_rows = get_warehouse_stock(client, product_id)
    batch_rows = get_batches(client, product_id)
    fifo_rows = get_fifo_layers(client, product_id)

    sales_rows = get_sales(client, product_id)
    purchase_rows = get_purchases(client, product_id)
    adjustment_rows = get_adjustments(client, product_id)
    transfer_rows = get_transfers(client, product_id)
    refund_rows = get_refunds(client, product_id)
    unified_rows = get_unified_history(client, product_id)
    audit_rows = get_audit_history(client, product_id)

    integrity = get_integrity(product, warehouse_rows, batch_rows, fifo_rows)

    render_product_header(product)
    st.divider()
    render_current_status(product, integrity)
    st.divider()

    st.subheader("Product Information")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Product ID", str(product.get("id") or product_id))
    c2.metric("SKU", str(product.get("sku") or "-"))
    c3.metric("Barcode", str(product.get("barcode") or "-"))
    c4.metric("Category", str(product.get("category_id") or "-"))

    tabs = st.tabs([
        "Overview", "Warehouse", "Batch / FEFO", "FIFO", "Pricing",
        "Sales", "Purchases", "Adjustments", "Transfers", "Refunds",
        "History", "Audit", "Integrity"
    ])

    with tabs[0]:
        st.subheader("Product Overview")
        overview = {
            "Product ID": product.get("id"),
            "Name": product.get("name"),
            "SKU": product.get("sku"),
            "Barcode": product.get("barcode"),
            "Category ID": product.get("category_id"),
            "Brand ID": product.get("brand_id"),
            "Purchase Price": money(product.get("purchase_price")),
            "Selling Price": money(product.get("selling_price")),
            "Stock": qty(product.get("stock")),
            "Active": product.get("is_active", True),
            "Created": format_myanmar_time(product.get("created_at")),
            "Updated": format_myanmar_time(product.get("updated_at")),
        }
        st.dataframe(
            [{"Field": k, "Value": v} for k, v in overview.items()],
            use_container_width=True,
            hide_index=True,
        )

    with tabs[1]:
        render_warehouse(warehouse_rows)
    with tabs[2]:
        render_batches(batch_rows)
    with tabs[3]:
        render_fifo(fifo_rows)
    with tabs[4]:
        render_pricing(product)
    with tabs[5]:
        render_sales(sales_rows)
    with tabs[6]:
        render_purchases(purchase_rows)
    with tabs[7]:
        render_adjustments(adjustment_rows)
    with tabs[8]:
        render_transfers(transfer_rows)
    with tabs[9]:
        render_refunds(refund_rows)
    with tabs[10]:
        render_unified_history(unified_rows)
    with tabs[11]:
        render_audit(audit_rows)
    with tabs[12]:
        render_integrity(integrity)


def render_product_360_page(client: Any, product_id: int):
    return render_product_360(client, product_id)


def render_page(client: Any, product_id: int):
    return render_product_360(client, product_id)


# ==============================================================================
# PUBLIC API
# ==============================================================================

__all__ = [
    "render_product_360",
    "render_product_360_page",
    "render_page",
    "get_product",
    "get_warehouse_stock",
    "get_batches",
    "get_fifo_layers",
    "get_sales",
    "get_purchases",
    "get_adjustments",
    "get_transfers",
    "get_refunds",
    "get_unified_history",
    "get_audit_history",
    "get_integrity",
    "calculate_stock_summary",
    "calculate_price_info",
    "format_myanmar_time",
    "to_decimal",
    "money",
    "qty",
]
