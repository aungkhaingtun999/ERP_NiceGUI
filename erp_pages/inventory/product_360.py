# ==============================================================================
# erp_pages/inventory/product_360.py
#
# ERP ENTERPRISE PRODUCT 360°
# ------------------------------------------------------------------------------
# Product Master
# Current Stock
# Warehouse
# FIFO / Cost Layers
# Batch / FEFO
# Pricing Intelligence
# Sales
# Purchases
# Stock Adjustments
# Transfers
# Refunds
# Unified Movement History
# Audit History
# Integrity Checks
#
# Timezone:
#   Database -> timestamptz
#   UI       -> Asia/Yangon (MMT / UTC+06:30)
# ==============================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional

import streamlit as st


# ==============================================================================
# TIMEZONE
# ==============================================================================

MMT = ZoneInfo("Asia/Yangon")


def format_myanmar_time(value: Any) -> str:
    """
    Convert database timestamp to Myanmar Standard Time.

    PostgreSQL timestamptz normally arrives as an aware datetime
    or ISO formatted string.
    """

    if not value:
        return "-"

    try:

        if isinstance(value, str):

            text = value.strip()

            if text.endswith("Z"):
                text = text[:-1] + "+00:00"

            dt = datetime.fromisoformat(text)

        elif isinstance(value, datetime):

            dt = value

        else:

            return str(value)

        if dt.tzinfo is None:

            # Database should normally provide timezone.
            # Assume UTC if a naive timestamp somehow arrives.
            dt = dt.replace(
                tzinfo=ZoneInfo("UTC")
            )

        dt = dt.astimezone(MMT)

        return dt.strftime(
            "%Y-%m-%d %H:%M:%S MMT"
        )

    except Exception:

        return str(value)


# ==============================================================================
# NUMBER HELPERS
# ==============================================================================

def to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:

    if value is None:
        return default

    try:
        return Decimal(str(value))

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):

        return default


def money(value: Any) -> str:

    amount = to_decimal(value)

    return f"{amount:,.2f}"


def qty(value: Any) -> str:

    amount = to_decimal(value)

    if amount == amount.to_integral_value():
        return f"{int(amount):,}"

    return f"{amount:,.3f}"


# ==============================================================================
# SAFE QUERY
# ==============================================================================

def _execute(query):

    try:

        result = query.execute()

        return result.data or []

    except Exception as e:

        return {
            "__error__": str(e)
        }


def _is_error(data) -> bool:

    return (
        isinstance(data, dict)
        and "__error__" in data
    )


# ==============================================================================
# PRODUCT MASTER
# ==============================================================================

def get_product(
    client,
    product_id: int,
) -> Optional[Dict]:

    try:

        result = (
            client
            .table("products")
            .select("*")
            .eq(
                "id",
                int(product_id)
            )
            .single()
            .execute()
        )

        data = result.data

        if isinstance(data, list):

            return data[0] if data else None

        if isinstance(data, dict):

            return data

        return None

    except Exception:

        return None


# ==============================================================================
# WAREHOUSE STOCK
# ==============================================================================

def get_warehouse_stock(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("warehouse_stock")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "warehouse_id"
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# INVENTORY BATCHES
# ==============================================================================

def get_batches(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("inventory_batches")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "created_at",
            desc=False
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# FIFO COST LAYERS
# ==============================================================================

def get_fifo_layers(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("inventory_cost_layers")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "created_at",
            desc=False
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# SALES
# ==============================================================================

def get_sales(
    client,
    product_id: int,
) -> List[Dict]:

    try:

        result = (
            client
            .table("sale_items")
            .select(
                """
                id,
                sale_id,
                product_id,
                quantity,
                unit_price,
                discount,
                total,
                product_name
                """
            )
            .eq(
                "product_id",
                int(product_id)
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        items = result.data or []

        if not items:
            return []

        sale_ids = list(
            {
                int(row["sale_id"])
                for row in items
                if row.get("sale_id") is not None
            }
        )

        if not sale_ids:
            return items

        sales_result = (
            client
            .table("sales")
            .select(
                """
                id,
                invoice_no,
                warehouse_id,
                cashier_id,
                sale_status,
                status,
                payment_method,
                created_at,
                total_amount,
                total
                """
            )
            .in_(
                "id",
                sale_ids
            )
            .execute()
        )

        sales_map = {
            int(row["id"]): row
            for row in (
                sales_result.data or []
            )
        }

        output = []

        for item in items:

            sale = sales_map.get(
                int(item["sale_id"])
            )

            row = dict(item)

            if sale:

                row.update(
                    {
                        "invoice_no":
                            sale.get("invoice_no"),

                        "warehouse_id":
                            sale.get("warehouse_id"),

                        "cashier_id":
                            sale.get("cashier_id"),

                        "sale_status":
                            sale.get("sale_status"),

                        "sale_status2":
                            sale.get("status"),

                        "payment_method":
                            sale.get("payment_method"),

                        "created_at":
                            sale.get("created_at"),
                    }
                )

            output.append(row)

        return output

    except Exception:

        return []


# ==============================================================================
# PURCHASES
# ==============================================================================

def get_purchases(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("purchases")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "created_at",
            desc=True
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# STOCK ADJUSTMENTS
# ==============================================================================

def get_adjustments(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("stock_adjustments")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "created_at",
            desc=True
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# TRANSFERS
# ==============================================================================

def get_transfers(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("stock_transfers")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "created_at",
            desc=True
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# TRANSFER COSTS
# ==============================================================================

def get_transfer_costs(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("stock_transfer_costs")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "created_at",
            desc=True
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# REFUNDS
# ==============================================================================

def get_refunds(
    client,
    product_id: int,
) -> List[Dict]:

    try:

        result = (
            client
            .table("refund_items")
            .select("*")
            .eq(
                "product_id",
                int(product_id)
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        items = result.data or []

        if not items:
            return []

        refund_ids = list(
            {
                int(row["refund_id"])
                for row in items
                if row.get("refund_id") is not None
            }
        )

        if not refund_ids:
            return items

        refunds_result = (
            client
            .table("refunds")
            .select("*")
            .in_(
                "id",
                refund_ids
            )
            .execute()
        )

        refunds_map = {
            int(row["id"]): row
            for row in (
                refunds_result.data or []
            )
        }

        output = []

        for item in items:

            row = dict(item)

            refund = refunds_map.get(
                int(item["refund_id"])
            )

            if refund:

                row.update(
                    {
                        "sale_id":
                            refund.get("sale_id"),

                        "refund_date":
                            refund.get("refund_date"),

                        "reason":
                            refund.get("reason"),

                        "refund_amount":
                            refund.get("refund_amount"),

                        "status":
                            refund.get("status"),
                    }
                )

            output.append(row)

        return output

    except Exception:

        return []


# ==============================================================================
# UNIFIED MOVEMENT HISTORY
# ==============================================================================

def get_unified_history(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("product_360_movement_history")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "transaction_time",
            desc=False
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# AUDIT HISTORY
# ==============================================================================

def get_audit_history(
    client,
    product_id: int,
) -> List[Dict]:

    data = _execute(
        client
        .table("product_360_audit_history")
        .select("*")
        .eq(
            "product_id",
            int(product_id)
        )
        .order(
            "changed_at",
            desc=False
        )
    )

    return [] if _is_error(data) else data


# ==============================================================================
# PRICE INTELLIGENCE
# ==============================================================================

def calculate_price_info(
    product: Dict,
    global_markup: Decimal = Decimal("10"),
) -> Dict:

    purchase_price = to_decimal(
        product.get("purchase_price")
    )

    selling_price = to_decimal(
        product.get("selling_price")
    )

    markup_percent = product.get(
        "markup_percent"
    )

    owner_price = product.get(
        "owner_selling_price"
    )

    final_price = product.get(
        "final_selling_price"
    )

    price_source = product.get(
        "price_source"
    ) or "UNKNOWN"

    global_price = (
        purchase_price
        * (
            Decimal("1")
            + global_markup / Decimal("100")
        )
    ).quantize(
        Decimal("0.01")
    )

    profit = (
        selling_price
        - purchase_price
    )

    if purchase_price > 0:

        actual_markup = (
            profit
            / purchase_price
            * Decimal("100")
        )

    else:

        actual_markup = Decimal("0")

    return {
        "purchase_price":
            purchase_price,

        "selling_price":
            selling_price,

        "markup_percent":
            markup_percent,

        "owner_selling_price":
            owner_price,

        "final_selling_price":
            final_price,

        "price_source":
            price_source,

        "owner_price_locked":
            bool(
                product.get(
                    "owner_price_locked",
                    False
                )
            ),

        "global_markup_percent":
            global_markup,

        "global_markup_price":
            global_price,

        "profit_per_unit":
            profit,

        "actual_markup_percent":
            actual_markup,
    }


# ==============================================================================
# INTEGRITY CHECK
# ==============================================================================

def get_integrity(
    product: Dict,
    warehouse_rows: List[Dict],
    batch_rows: List[Dict],
    fifo_rows: List[Dict],
) -> Dict:

    master_stock = to_decimal(
        product.get("stock")
    )

    warehouse_stock = sum(
        (
            to_decimal(
                row.get("qty")
            )
            for row in warehouse_rows
        ),
        Decimal("0")
    )

    batch_remaining = sum(
        (
            to_decimal(
                row.get("qty_remaining")
            )
            for row in batch_rows
        ),
        Decimal("0")
    )

    fifo_remaining = sum(
        (
            to_decimal(
                row.get("qty_remaining")
            )
            for row in fifo_rows
        ),
        Decimal("0")
    )

    warnings = []
    passed = []

    if warehouse_stock == fifo_remaining:

        passed.append(
            "Warehouse stock matches FIFO remaining."
        )

    else:

        warnings.append(
            "Warehouse stock differs from FIFO remaining."
        )

    if (
        master_stock == warehouse_stock
    ):

        passed.append(
            "Master stock matches warehouse stock."
        )

    else:

        warnings.append(
            "Master stock differs from warehouse stock."
        )

    if (
        batch_remaining == fifo_remaining
    ):

        passed.append(
            "Batch remaining matches FIFO remaining."
        )

    else:

        warnings.append(
            "Batch remaining differs from FIFO remaining."
        )

    purchase_price = to_decimal(
        product.get("purchase_price")
    )

    selling_price = to_decimal(
        product.get("selling_price")
    )

    if purchase_price > 0:

        actual_markup = (
            (
                selling_price
                - purchase_price
            )
            / purchase_price
            * Decimal("100")
        )

        if actual_markup == Decimal("10"):

            passed.append(
                "Selling price matches 10% global markup."
            )

        else:

            warnings.append(
                "Selling price does not match 10% global markup."
            )

    return {
        "master_stock":
            master_stock,

        "warehouse_stock":
            warehouse_stock,

        "batch_remaining":
            batch_remaining,

        "fifo_remaining":
            fifo_remaining,

        "warnings":
            warnings,

        "passed":
            passed,
    }


# ==============================================================================
# EMPTY STATE
# ==============================================================================

def empty_history(
    title: str,
    message: str = "No historical record available.",
):

    st.info(
        f"**{title}**\n\n{message}"
    )


# ==============================================================================
# RENDER PRODUCT HEADER
# ==============================================================================

def render_product_header(
    product: Dict,
):

    name = product.get(
        "name",
        "Unknown Product"
    )

    sku = product.get(
        "sku"
    ) or "-"

    barcode = product.get(
        "barcode"
    ) or "-"

    active = product.get(
        "is_active",
        True
    )

    status = (
        "ACTIVE"
        if active
        else "INACTIVE"
    )

    st.title(
        f"Product 360° — {name}"
    )

    st.caption(
        f"SKU: {sku}  |  "
        f"Barcode: {barcode}  |  "
        f"Status: {status}"
    )


# ==============================================================================
# CURRENT STATUS
# ==============================================================================

def render_current_status(
    product: Dict,
    integrity: Dict,
):

    st.subheader(
        "Current Inventory Status"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Master Stock",
        qty(
            integrity["master_stock"]
        )
    )

    c2.metric(
        "Warehouse Stock",
        qty(
            integrity["warehouse_stock"]
        )
    )

    c3.metric(
        "FIFO Remaining",
        qty(
            integrity["fifo_remaining"]
        )
    )

    c4.metric(
        "Batch Remaining",
        qty(
            integrity["batch_remaining"]
        )
    )

    if integrity["warnings"]:

        for warning in integrity["warnings"]:

            st.warning(
                f"⚠️ {warning}"
            )

    else:

        st.success(
            "Inventory integrity checks passed."
        )


# ==============================================================================
# PRICING
# ==============================================================================

def render_pricing(
    product: Dict,
):

    st.subheader(
        "Pricing Intelligence"
    )

    info = calculate_price_info(
        product
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Purchase Price",
        money(
            info["purchase_price"]
        )
    )

    c2.metric(
        "Global Markup",
        f"{info['global_markup_percent']}%"
    )

    c3.metric(
        "Selling Price",
        money(
            info["selling_price"]
        )
    )

    c4.metric(
        "Profit / Unit",
        money(
            info["profit_per_unit"]
        )
    )

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


# ==============================================================================
# WAREHOUSE
# ==============================================================================

def render_warehouse(
    rows: List[Dict],
):

    st.subheader(
        "Warehouse Stock"
    )

    if not rows:

        empty_history(
            "Warehouse Stock"
        )

        return

    display = []

    for row in rows:

        display.append(
            {
                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ),

                "Qty":
                    qty(
                        row.get("qty")
                    ),

                "Reserved":
                    qty(
                        row.get("reserved_qty")
                    ),

                "Available":
                    qty(
                        row.get("available_qty")
                    ),

                "Minimum":
                    row.get(
                        "minimum_stock"
                    ),

                "Reorder":
                    row.get(
                        "reorder_level"
                    ),

                "Location":
                    row.get(
                        "location"
                    ) or "-",

                "Batch No":
                    row.get(
                        "batch_no"
                    ) or "-",

                "Updated":
                    format_myanmar_time(
                        row.get(
                            "updated_at"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# BATCH
# ==============================================================================

def render_batches(
    rows: List[Dict],
):

    st.subheader(
        "Batch / FEFO"
    )

    if not rows:

        empty_history(
            "Batch History"
        )

        return

    display = []

    for index, row in enumerate(
        rows,
        start=1
    ):

        display.append(
            {
                "FEFO Rank":
                    index,

                "Batch":
                    row.get(
                        "batch_no"
                    ) or "-",

                "Qty":
                    qty(
                        row.get(
                            "quantity"
                        )
                    ),

                "Remaining":
                    qty(
                        row.get(
                            "qty_remaining"
                        )
                    ),

                "Unit Cost":
                    money(
                        row.get(
                            "unit_cost"
                        )
                    ),

                "MFG Date":
                    row.get(
                        "mfg_date"
                    ) or "-",

                "Expiry":
                    row.get(
                        "expiry_date"
                    ) or "-",

                "Supplier":
                    row.get(
                        "supplier_code"
                    ) or "-",

                "Created":
                    format_myanmar_time(
                        row.get(
                            "created_at"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# FIFO
# ==============================================================================

def render_fifo(
    rows: List[Dict],
):

    st.subheader(
        "FIFO Cost Layers"
    )

    if not rows:

        empty_history(
            "FIFO Cost Layers"
        )

        return

    display = []

    for index, row in enumerate(
        rows,
        start=1
    ):

        display.append(
            {
                "FIFO Rank":
                    index,

                "Layer ID":
                    row.get("id"),

                "Qty In":
                    qty(
                        row.get(
                            "qty_in"
                        )
                    ),

                "Remaining":
                    qty(
                        row.get(
                            "qty_remaining"
                        )
                    ),

                "Unit Cost":
                    money(
                        row.get(
                            "unit_cost"
                        )
                    ),

                "Reference":
                    row.get(
                        "reference_type"
                    ) or "-",

                "Reference ID":
                    row.get(
                        "reference_id"
                    ) or "-",

                "Batch":
                    row.get(
                        "batch_no"
                    ) or "-",

                "Expiry":
                    row.get(
                        "expiry_date"
                    ) or "-",

                "Created":
                    format_myanmar_time(
                        row.get(
                            "created_at"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# SALES
# ==============================================================================

def render_sales(
    rows: List[Dict],
):

    st.subheader(
        "Sales History"
    )

    if not rows:

        empty_history(
            "Sales History"
        )

        return

    display = []

    for row in rows:

        display.append(
            {
                "Invoice":
                    row.get(
                        "invoice_no"
                    ) or "-",

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ) or "-",

                "Qty":
                    qty(
                        row.get(
                            "quantity"
                        )
                    ),

                "Unit Price":
                    money(
                        row.get(
                            "unit_price"
                        )
                    ),

                "Discount":
                    money(
                        row.get(
                            "discount"
                        )
                    ),

                "Total":
                    money(
                        row.get(
                            "total"
                        )
                    ),

                "Status":
                    row.get(
                        "sale_status"
                    ) or "-",

                "Payment":
                    row.get(
                        "payment_method"
                    ) or "-",

                "Time":
                    format_myanmar_time(
                        row.get(
                            "created_at"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# PURCHASES
# ==============================================================================

def render_purchases(
    rows: List[Dict],
):

    st.subheader(
        "Purchase History"
    )

    if not rows:

        empty_history(
            "Purchase History"
        )

        return

    display = []

    for row in rows:

        display.append(
            {
                "Purchase No":
                    row.get(
                        "purchase_no"
                    ) or "-",

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ) or "-",

                "Qty":
                    qty(
                        row.get(
                            "qty"
                        )
                    ),

                "Unit Cost":
                    money(
                        row.get(
                            "price"
                        )
                    ),

                "Total":
                    money(
                        row.get(
                            "total"
                        )
                    ),

                "Status":
                    row.get(
                        "status"
                    ) or "-",

                "Payment":
                    row.get(
                        "payment_method"
                    ) or "-",

                "Reference":
                    row.get(
                        "reference_no"
                    ) or "-",

                "Time":
                    format_myanmar_time(
                        row.get(
                            "created_at"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# ADJUSTMENTS
# ==============================================================================

def render_adjustments(
    rows: List[Dict],
):

    st.subheader(
        "Stock Adjustment History"
    )

    if not rows:

        empty_history(
            "Adjustment History"
        )

        return

    display = []

    for row in rows:

        display.append(
            {
                "ID":
                    row.get("id"),

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ),

                "Type":
                    row.get(
                        "adjustment_type"
                    ) or "-",

                "Qty":
                    qty(
                        row.get("qty")
                    ),

                "Unit Cost":
                    money(
                        row.get(
                            "unit_cost"
                        )
                    ),

                "Reason":
                    row.get(
                        "reason"
                    ) or "-",

                "Status":
                    row.get(
                        "status"
                    ) or "-",

                "Requested By":
                    row.get(
                        "requested_by"
                    ) or "-",

                "Approved By":
                    row.get(
                        "approved_by"
                    ) or "-",

                "Created":
                    format_myanmar_time(
                        row.get(
                            "created_at"
                        )
                    ),

                "Approved":
                    format_myanmar_time(
                        row.get(
                            "approved_at"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# TRANSFERS
# ==============================================================================

def render_transfers(
    rows: List[Dict],
):

    st.subheader(
        "Stock Transfer History"
    )

    if not rows:

        empty_history(
            "Transfer History"
        )

        return

    display = []

    for row in rows:

        display.append(
            {
                "Transfer No":
                    row.get(
                        "transfer_no"
                    ) or "-",

                "From Warehouse":
                    row.get(
                        "from_warehouse_id"
                    ),

                "To Warehouse":
                    row.get(
                        "to_warehouse_id"
                    ),

                "Qty":
                    qty(
                        row.get("qty")
                    ),

                "Status":
                    row.get(
                        "status"
                    ) or "-",

                "Remarks":
                    row.get(
                        "remarks"
                    ) or "-",

                "Requested By":
                    row.get(
                        "requested_by"
                    ) or "-",

                "Approved By":
                    row.get(
                        "approved_by"
                    ) or "-",

                "Created":
                    format_myanmar_time(
                        row.get(
                            "created_at"
                        )
                    ),

                "Approved":
                    format_myanmar_time(
                        row.get(
                            "approved_at"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# REFUNDS
# ==============================================================================

def render_refunds(
    rows: List[Dict],
):

    st.subheader(
        "Refund History"
    )

    if not rows:

        empty_history(
            "Refund History"
        )

        return

    display = []

    for row in rows:

        display.append(
            {
                "Refund ID":
                    row.get(
                        "refund_id"
                    ),

                "Sale ID":
                    row.get(
                        "sale_id"
                    ),

                "Qty":
                    qty(
                        row.get(
                            "quantity"
                        )
                    ),

                "Unit Price":
                    money(
                        row.get(
                            "unit_price"
                        )
                    ),

                "Total":
                    money(
                        row.get(
                            "total"
                        )
                    ),

                "Refund Amount":
                    money(
                        row.get(
                            "refund_amount"
                        )
                    ),

                "Reason":
                    row.get(
                        "reason"
                    ) or "-",

                "Status":
                    row.get(
                        "status"
                    ) or "-",

                "Date":
                    format_myanmar_time(
                        row.get(
                            "refund_date"
                        )
                    ),
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# UNIFIED HISTORY
# ==============================================================================

def render_unified_history(
    rows: List[Dict],
):

    st.subheader(
        "Unified Product Transaction History"
    )

    if not rows:

        empty_history(
            "Unified Transaction History"
        )

        return

    display = []

    for row in rows:

        display.append(
            {
                "Time (MMT)":
                    format_myanmar_time(
                        row.get(
                            "transaction_time"
                        )
                    ),

                "Source":
                    row.get(
                        "transaction_source"
                    ) or "-",

                "Type":
                    row.get(
                        "transaction_type"
                    ) or "-",

                "Reference":
                    row.get(
                        "reference_id"
                    ) or "-",

                "Transaction":
                    row.get(
                        "transaction_id"
                    ) or "-",

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ) or "-",

                "Qty":
                    qty(
                        row.get(
                            "quantity"
                        )
                    ),

                "Balance":
                    (
                        qty(
                            row.get(
                                "balance_after"
                            )
                        )
                        if row.get(
                            "balance_after"
                        ) is not None
                        else "-"
                    ),

                "Remarks":
                    row.get(
                        "remarks"
                    ) or "-",
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# AUDIT
# ==============================================================================

def render_audit(
    rows: List[Dict],
):

    st.subheader(
        "Product Audit History"
    )

    if not rows:

        empty_history(
            "Audit History",
            "No historical audit record available.",
        )

        return

    for row in rows:

        operation = (
            row.get(
                "operation"
            ) or "UNKNOWN"
        )

        changed_at = format_myanmar_time(
            row.get(
                "changed_at"
            )
        )

        with st.expander(
            f"{operation} — {changed_at}"
        ):

            c1, c2 = st.columns(2)

            with c1:

                st.markdown(
                    "### Before"
                )

                st.json(
                    {
                        "purchase_price":
                            row.get(
                                "old_purchase_price"
                            ),

                        "selling_price":
                            row.get(
                                "old_selling_price"
                            ),

                        "markup_percent":
                            row.get(
                                "old_markup_percent"
                            ),

                        "price_source":
                            row.get(
                                "old_price_source"
                            ),

                        "owner_selling_price":
                            row.get(
                                "old_owner_selling_price"
                            ),

                        "final_selling_price":
                            row.get(
                                "old_final_selling_price"
                            ),
                    }
                )

            with c2:

                st.markdown(
                    "### After"
                )

                st.json(
                    {
                        "purchase_price":
                            row.get(
                                "new_purchase_price"
                            ),

                        "selling_price":
                            row.get(
                                "new_selling_price"
                            ),

                        "markup_percent":
                            row.get(
                                "new_markup_percent"
                            ),

                        "price_source":
                            row.get(
                                "new_price_source"
                            ),

                        "owner_selling_price":
                            row.get(
                                "new_owner_selling_price"
                            ),

                        "final_selling_price":
                            row.get(
                                "new_final_selling_price"
                            ),
                    }
                )

            st.caption(
                f"Changed By: "
                f"{row.get('changed_by') or 'SYSTEM'}"
            )


# ==============================================================================
# INTEGRITY PANEL
# ==============================================================================

def render_integrity(
    integrity: Dict,
):

    st.subheader(
        "Inventory Integrity"
    )

    if integrity["passed"]:

        for item in integrity["passed"]:

            st.success(
                f"✓ {item}"
            )

    if integrity["warnings"]:

        for item in integrity["warnings"]:

            st.warning(
                f"⚠ {item}"
            )

    else:

        st.success(
            "✓ No inventory integrity warning detected."
        )


# ==============================================================================
# MAIN RENDER
# ==============================================================================

def render_product_360(
    client,
    product_id: int,
):

    product = get_product(
        client,
        product_id
    )

    if not product:

        st.error(
            f"Product ID {product_id} not found."
        )

        return

    warehouse_rows = get_warehouse_stock(
        client,
        product_id
    )

    batch_rows = get_batches(
        client,
        product_id
    )

    fifo_rows = get_fifo_layers(
        client,
        product_id
    )

    integrity = get_integrity(
        product,
        warehouse_rows,
        batch_rows,
        fifo_rows
    )

    sales_rows = get_sales(
        client,
        product_id
    )

    purchase_rows = get_purchases(
        client,
        product_id
    )

    adjustment_rows = get_adjustments(
        client,
        product_id
    )

    transfer_rows = get_transfers(
        client,
        product_id
    )

    refund_rows = get_refunds(
        client,
        product_id
    )

    unified_rows = get_unified_history(
        client,
        product_id
    )

    audit_rows = get_audit_history(
        client,
        product_id
    )

    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------

    render_product_header(
        product
    )

    st.divider()

    # --------------------------------------------------------------------------
    # CURRENT STATUS
    # --------------------------------------------------------------------------

    render_current_status(
        product,
        integrity
    )

    st.divider()

    # --------------------------------------------------------------------------
    # PRICING
    # --------------------------------------------------------------------------

    render_pricing(
        product
    )

    st.divider()

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    render_warehouse(
        warehouse_rows
    )

    st.divider()

    # --------------------------------------------------------------------------
    # BATCH + FIFO
    # --------------------------------------------------------------------------

    tab1, tab2 = st.tabs(
        [
            "📦 Batch / FEFO",
            "🔄 FIFO Cost Layers",
        ]
    )

    with tab1:

        render_batches(
            batch_rows
        )

    with tab2:

        render_fifo(
            fifo_rows
        )

    st.divider()

    # --------------------------------------------------------------------------
    # TRANSACTIONS
    # --------------------------------------------------------------------------

    tabs = st.tabs(
        [
            "🛒 Sales",
            "📥 Purchases",
            "🛠 Adjustments",
            "🔄 Transfers",
            "↩ Refunds",
            "📜 Unified History",
        ]
    )

    with tabs[0]:

        render_sales(
            sales_rows
        )

    with tabs[1]:

        render_purchases(
            purchase_rows
        )

    with tabs[2]:

        render_adjustments(
            adjustment_rows
        )

    with tabs[3]:

        render_transfers(
            transfer_rows
        )

    with tabs[4]:

        render_refunds(
            refund_rows
        )

    with tabs[5]:

        render_unified_history(
            unified_rows
        )

    st.divider()

    # --------------------------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------------------------

    render_audit(
        audit_rows
    )

    st.divider()

    # --------------------------------------------------------------------------
    # INTEGRITY
    # --------------------------------------------------------------------------

    render_integrity(
        integrity
    )


# ==============================================================================
# STREAMLIT PAGE ENTRY
# ==============================================================================

def render_page(
    client,
    product_id: Optional[int] = None,
):

    st.set_page_config(
        page_title="Product 360°",
        page_icon="📦",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,0.20);
            border-radius: 10px;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # PRODUCT SEARCH
    # --------------------------------------------------------------------------

    st.sidebar.header(
        "Product 360°"
    )

    search_mode = st.sidebar.selectbox(
        "Search By",
        [
            "Product ID",
            "SKU",
            "Barcode",
        ]
    )

    if search_mode == "Product ID":

        entered = st.sidebar.number_input(
            "Product ID",
            min_value=1,
            value=int(
                product_id or 1
            ),
            step=1,
        )

        selected_product_id = int(
            entered
        )

    elif search_mode == "SKU":

        sku = st.sidebar.text_input(
            "SKU"
        ).strip()

        selected_product_id = None

        if sku:

            try:

                result = (
                    client
                    .table("products")
                    .select("id")
                    .eq(
                        "sku",
                        sku
                    )
                    .limit(1)
                    .execute()
                )

                if result.data:

                    selected_product_id = int(
                        result.data[0]["id"]
                    )

            except Exception as e:

                st.sidebar.error(
                    str(e)
                )

    else:

        barcode = st.sidebar.text_input(
            "Barcode"
        ).strip()

        selected_product_id = None

        if barcode:

            try:

                result = (
                    client
                    .table("products")
                    .select("id")
                    .eq(
                        "barcode",
                        barcode
                    )
                    .limit(1)
                    .execute()
                )

                if result.data:

                    selected_product_id = int(
                        result.data[0]["id"]
                    )

            except Exception as e:

                st.sidebar.error(
                    str(e)
                )

    if selected_product_id:

        render_product_360(
            client,
            selected_product_id
        )

    else:

        st.info(
            "Select a Product ID, SKU, or Barcode."
        )


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "render_product_360",
    "render_page",
    "format_myanmar_time",
]
