# ==============================================================================
# erp_pages/inventory/product_360.py
#
# ERP ENTERPRISE PRODUCT 360°
# PART 1 / 3
#
# CLEAN REBUILD
# ------------------------------------------------------------------------------
# Product Master
# Warehouse Stock
# Batch / FEFO
# FIFO Cost Layers
# Integrity
#
# Compatibility:
#     render_product_360_page(client, product_id)
#     render_product_360(client, product_id)
#     render_page(client, product_id)
#
# IMPORTANT
# ------------------------------------------------------------------------------
# READ ONLY MODULE
# No stock mutation
# No FIFO mutation
# No approval mutation
# No product creation
#
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

    PostgreSQL timestamptz:
        aware datetime

    ISO timestamp:
        supported

    Naive datetime:
        treated as UTC for safety
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

        return dt.strftime(
            "%Y-%m-%d %H:%M:%S MMT"
        )

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

        return Decimal(
            str(value)
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):

        return default


def money(value: Any) -> str:
    """
    Format money.

    Example:
        1500 -> 1,500.00
    """

    return f"{to_decimal(value):,.2f}"


def qty(value: Any) -> str:
    """
    Format quantity.

    100     -> 100
    10.250  -> 10.250
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

    Success:
        list

    Failure:
        {"__error__": "..."}
    """

    try:

        result = query.execute()

        data = getattr(
            result,
            "data",
            None,
        )

        return data or []

    except Exception as exc:

        return {
            "__error__": str(exc)
        }


def _is_error(data: Any) -> bool:
    return (
        isinstance(data, dict)
        and "__error__" in data
    )


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
# PRODUCT MASTER
# ==============================================================================

def get_product(
    client: Any,
    product_id: int,
) -> Optional[Dict]:
    """
    Load Product Master.

    Table:
        products
    """

    try:

        result = (
            client
            .table("products")
            .select("*")
            .eq(
                "id",
                int(product_id),
            )
            .limit(1)
            .execute()
        )

        rows = getattr(
            result,
            "data",
            None,
        ) or []

        if isinstance(rows, list) and rows:
            return rows[0]

        if isinstance(rows, dict):
            return rows

        return None

    except Exception:

        return None


# ==============================================================================
# WAREHOUSE STOCK
# ==============================================================================

def get_warehouse_stock(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Load warehouse stock.

    Table:
        warehouse_stock
    """

    data = _execute(
        client
        .table("warehouse_stock")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "warehouse_id",
            desc=False,
        )
    )

    if _is_error(data):
        return []

    return data


# ==============================================================================
# INVENTORY BATCHES
# ==============================================================================

def get_batches(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Load inventory batches.

    Table:
        inventory_batches

    NOTE:
        created_at is used because received_date
        is not assumed to exist.
    """

    data = _execute(
        client
        .table("inventory_batches")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "created_at",
            desc=False,
        )
    )

    if _is_error(data):
        return []

    return data


# ==============================================================================
# FIFO COST LAYERS
# ==============================================================================

def get_fifo_layers(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Load FIFO cost layers.

    Table:
        inventory_cost_layers

    IMPORTANT:
        Do NOT use received_date.
        Current ERP schema uses created_at.
    """

    data = _execute(
        client
        .table("inventory_cost_layers")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "created_at",
            desc=False,
        )
    )

    if _is_error(data):
        return []

    return data


# ==============================================================================
# INVENTORY INTEGRITY
# ==============================================================================

def get_integrity(
    product: Dict,
    warehouse_rows: List[Dict],
    batch_rows: List[Dict],
    fifo_rows: List[Dict],
) -> Dict:
    """
    Read-only inventory integrity calculation.

    Compares:

        Product Master
            |
            +-- Warehouse
            |
            +-- Batch
            |
            +-- FIFO
    """

    # --------------------------------------------------------------------------
    # MASTER
    # --------------------------------------------------------------------------

    master_stock = to_decimal(
        product.get("stock")
    )

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    warehouse_stock = Decimal("0")

    for row in warehouse_rows:

        value = row.get("qty")

        if value is None:
            value = row.get("quantity")

        warehouse_stock += to_decimal(
            value
        )

    # --------------------------------------------------------------------------
    # BATCH
    # --------------------------------------------------------------------------

    batch_remaining = Decimal("0")

    for row in batch_rows:

        value = row.get(
            "qty_remaining"
        )

        if value is None:
            value = row.get(
                "remaining_qty"
            )

        batch_remaining += to_decimal(
            value
        )

    # --------------------------------------------------------------------------
    # FIFO
    # --------------------------------------------------------------------------

    fifo_remaining = Decimal("0")

    for row in fifo_rows:

        value = row.get(
            "qty_remaining"
        )

        if value is None:
            value = row.get(
                "remaining_qty"
            )

        fifo_remaining += to_decimal(
            value
        )

    # --------------------------------------------------------------------------
    # CHECKS
    # --------------------------------------------------------------------------

    warnings: List[str] = []
    passed: List[str] = []

    # Warehouse vs FIFO

    if warehouse_stock == fifo_remaining:

        passed.append(
            "Warehouse stock matches FIFO remaining."
        )

    else:

        warnings.append(
            "Warehouse stock differs from FIFO remaining."
        )

    # Master vs Warehouse

    if master_stock == warehouse_stock:

        passed.append(
            "Master stock matches warehouse stock."
        )

    else:

        warnings.append(
            "Master stock differs from warehouse stock."
        )

    # Batch vs FIFO

    if batch_remaining == fifo_remaining:

        passed.append(
            "Batch remaining matches FIFO remaining."
        )

    else:

        warnings.append(
            "Batch remaining differs from FIFO remaining."
        )

    return {
        "master_stock": master_stock,
        "warehouse_stock": warehouse_stock,
        "batch_remaining": batch_remaining,
        "fifo_remaining": fifo_remaining,
        "warnings": warnings,
        "passed": passed,
    }


# ==============================================================================
# STOCK SUMMARY
# ==============================================================================

def calculate_stock_summary(
    product: Dict,
    warehouse_rows: List[Dict],
    batch_rows: List[Dict],
    fifo_rows: List[Dict],
) -> Dict:
    """
    Compatibility helper.

    Uses the same calculation rules as get_integrity().
    """

    integrity = get_integrity(
        product,
        warehouse_rows,
        batch_rows,
        fifo_rows,
    )

    return {
        "master_stock":
            integrity["master_stock"],

        "warehouse_stock":
            integrity["warehouse_stock"],

        "batch_remaining":
            integrity["batch_remaining"],

        "fifo_remaining":
            integrity["fifo_remaining"],
    }


# ==============================================================================
# PRODUCT HEADER
# ==============================================================================

def render_product_header(
    product: Dict,
):

    name = (
        product.get("name")
        or "Unknown Product"
    )

    sku = (
        product.get("sku")
        or "-"
    )

    barcode = (
        product.get("barcode")
        or "-"
    )

    active = product.get(
        "is_active",
        True,
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
    """
    Current inventory KPI panel.
    """

    st.subheader(
        "Current Inventory Status"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Master Stock",
        qty(
            integrity.get(
                "master_stock"
            )
        ),
    )

    c2.metric(
        "Warehouse Stock",
        qty(
            integrity.get(
                "warehouse_stock"
            )
        ),
    )

    c3.metric(
        "FIFO Remaining",
        qty(
            integrity.get(
                "fifo_remaining"
            )
        ),
    )

    c4.metric(
        "Batch Remaining",
        qty(
            integrity.get(
                "batch_remaining"
            )
        ),
    )

    warnings = integrity.get(
        "warnings",
        [],
    )

    if warnings:

        for warning in warnings:

            st.warning(
                f"⚠️ {warning}"
            )

    else:

        st.success(
            "Inventory integrity checks passed."
        )


# ==============================================================================
# WAREHOUSE UI
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

        qty_value = row.get("qty")

        if qty_value is None:
            qty_value = row.get(
                "quantity"
            )

        display.append(
            {
                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ) or "-",

                "Qty":
                    qty(qty_value),

                "Reserved":
                    qty(
                        row.get(
                            "reserved_qty"
                        )
                    ),

                "Available":
                    qty(
                        row.get(
                            "available_qty"
                        )
                    ),

                "Minimum":
                    qty(
                        row.get(
                            "minimum_stock"
                        )
                    ),

                "Reorder":
                    qty(
                        row.get(
                            "reorder_level"
                        )
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
# BATCH UI
# ==============================================================================

def render_batches(
    rows: List[Dict],
):

    st.subheader(
        "Batch / FEFO"
    )

    if not rows:

        empty_history(
            "Batch / FEFO"
        )

        return

    display = []

    for index, row in enumerate(
        rows,
        start=1,
    ):

        quantity_value = row.get(
            "quantity"
        )

        if quantity_value is None:
            quantity_value = row.get(
                "qty_in"
            )

        remaining_value = row.get(
            "qty_remaining"
        )

        if remaining_value is None:
            remaining_value = row.get(
                "remaining_qty"
            )

        display.append(
            {
                "FEFO Rank":
                    index,

                "Batch":
                    row.get(
                        "batch_no"
                    ) or "-",

                "Qty In":
                    qty(
                        quantity_value
                    ),

                "Remaining":
                    qty(
                        remaining_value
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
# FIFO UI
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
        start=1,
    ):

        qty_in_value = row.get(
            "qty_in"
        )

        if qty_in_value is None:
            qty_in_value = row.get(
                "quantity"
            )

        remaining_value = row.get(
            "qty_remaining"
        )

        if remaining_value is None:
            remaining_value = row.get(
                "remaining_qty"
            )

        display.append(
            {
                "FIFO Rank":
                    index,

                "Layer ID":
                    row.get(
                        "id"
                    ) or "-",

                "Qty In":
                    qty(
                        qty_in_value
                    ),

                "Remaining":
                    qty(
                        remaining_value
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
# PART 1 END
# ==============================================================================
# Part 2:
#   Pricing
#   Sales
#   Purchases
#   Adjustments
#   Transfers
#   Refunds
#   Unified History
#   Audit
# ==============================================================================
# ==============================================================================
# erp_pages/inventory/product_360.py
#
# ERP ENTERPRISE PRODUCT 360°
# PART 2 / 3
#
# UI:
#   Pricing
#   Sales
#   Purchases
#   Adjustments
#   Transfers
#   Refunds
#   Unified History
#   Audit
# ==============================================================================


# ==============================================================================
# PRICING HELPERS
# ==============================================================================

def _safe_percent(
    value: Any,
) -> Decimal:

    return to_decimal(
        value,
        Decimal("0"),
    )


def calculate_price_info(
    product: Dict,
) -> Dict:
    """
    Read-only pricing intelligence.

    This function intentionally does NOT call PricingService.
    It reads the product record safely so Product 360 can load
    even when pricing-service dependencies are unavailable.

    Supported product fields:

        purchase_price
        selling_price
        markup_percent
        owner_selling_price
        final_selling_price
        price_source
        owner_price_locked

    Global markup fallback:

        markup_percent
        DEFAULT_MARKUP_PERCENT
    """

    purchase_price = to_decimal(
        product.get(
            "purchase_price"
        )
    )

    selling_price = to_decimal(
        product.get(
            "selling_price"
        )
    )

    markup_percent = _safe_percent(
        product.get(
            "markup_percent"
        )
    )

    # --------------------------------------------------------------------------
    # FALLBACK GLOBAL MARKUP
    # --------------------------------------------------------------------------

    if markup_percent == Decimal("0"):

        markup_percent = _safe_percent(
            product.get(
                "global_markup_percent"
            )
        )

    if markup_percent == Decimal("0"):

        markup_percent = _safe_percent(
            product.get(
                "default_markup_percent"
            )
        )

    # --------------------------------------------------------------------------
    # MARKUP PRICE
    # --------------------------------------------------------------------------

    global_markup_price = (
        purchase_price
        * (
            Decimal("1")
            + (
                markup_percent
                / Decimal("100")
            )
        )
    )

    # --------------------------------------------------------------------------
    # OWNER PRICE
    # --------------------------------------------------------------------------

    owner_price_value = product.get(
        "owner_selling_price"
    )

    owner_selling_price = (
        to_decimal(
            owner_price_value
        )
        if owner_price_value is not None
        else Decimal("0")
    )

    owner_price_locked = bool(
        product.get(
            "owner_price_locked",
            False,
        )
    )

    # --------------------------------------------------------------------------
    # FINAL SELLING PRICE
    # --------------------------------------------------------------------------

    final_price_value = product.get(
        "final_selling_price"
    )

    if final_price_value is not None:

        final_selling_price = to_decimal(
            final_price_value
        )

    elif (
        owner_price_locked
        and owner_selling_price > 0
    ):

        final_selling_price = (
            owner_selling_price
        )

    elif selling_price > 0:

        final_selling_price = (
            selling_price
        )

    else:

        final_selling_price = (
            global_markup_price
        )

    # --------------------------------------------------------------------------
    # ACTUAL MARKUP
    # --------------------------------------------------------------------------

    if purchase_price > 0:

        actual_markup_percent = (
            (
                (
                    final_selling_price
                    - purchase_price
                )
                / purchase_price
            )
            * Decimal("100")
        )

    else:

        actual_markup_percent = Decimal(
            "0"
        )

    profit_per_unit = (
        final_selling_price
        - purchase_price
    )

    # --------------------------------------------------------------------------
    # PRICE SOURCE
    # --------------------------------------------------------------------------

    price_source = (
        product.get(
            "price_source"
        )
        or "PRODUCT"
    )

    return {
        "purchase_price":
            purchase_price,

        "selling_price":
            selling_price,

        "global_markup_percent":
            markup_percent,

        "global_markup_price":
            global_markup_price,

        "actual_markup_percent":
            actual_markup_percent,

        "owner_selling_price":
            owner_selling_price,

        "final_selling_price":
            final_selling_price,

        "owner_price_locked":
            owner_price_locked,

        "price_source":
            price_source,

        "profit_per_unit":
            profit_per_unit,
    }


# ==============================================================================
# PRICING UI
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
            info[
                "purchase_price"
            ]
        ),
    )

    c2.metric(
        "Global Markup",
        (
            f"{info['global_markup_percent']}"
            "%"
        ),
    )

    c3.metric(
        "Selling Price",
        money(
            info[
                "selling_price"
            ]
        ),
    )

    c4.metric(
        "Profit / Unit",
        money(
            info[
                "profit_per_unit"
            ]
        ),
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
# SALES
# ==============================================================================

def get_sales(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Product sales history.

    Uses sale_items as the primary source.

    The query intentionally uses select("*") so this module
    remains tolerant of schema variations.
    """

    data = _execute(
        client
        .table("sale_items")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "created_at",
            desc=True,
        )
    )

    if _is_error(data):
        return []

    return data


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

        quantity_value = row.get(
            "quantity"
        )

        if quantity_value is None:
            quantity_value = row.get(
                "qty"
            )

        total_value = row.get(
            "total"
        )

        if total_value is None:
            total_value = row.get(
                "line_total"
            )

        display.append(
            {
                "Invoice":
                    row.get(
                        "invoice_no"
                    )
                    or row.get(
                        "sale_id"
                    )
                    or "-",

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    )
                    or "-",

                "Qty":
                    qty(
                        quantity_value
                    ),

                "Unit Price":
                    money(
                        row.get(
                            "unit_price"
                        )
                        or row.get(
                            "selling_price"
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
                        total_value
                    ),

                "Status":
                    row.get(
                        "sale_status"
                    )
                    or row.get(
                        "status"
                    )
                    or "-",

                "Payment":
                    row.get(
                        "payment_method"
                    )
                    or "-",

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

def get_purchases(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Product purchase history.

    Primary table:
        purchase_items

    If the table does not exist or cannot be queried,
    return an empty list rather than breaking Product 360.
    """

    data = _execute(
        client
        .table("purchase_items")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "created_at",
            desc=True,
        )
    )

    if _is_error(data):
        return []

    return data


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

        quantity_value = row.get(
            "qty"
        )

        if quantity_value is None:
            quantity_value = row.get(
                "quantity"
            )

        price_value = row.get(
            "price"
        )

        if price_value is None:
            price_value = row.get(
                "unit_cost"
            )

        total_value = row.get(
            "total"
        )

        if total_value is None:
            total_value = (
                to_decimal(
                    quantity_value
                )
                * to_decimal(
                    price_value
                )
            )

        display.append(
            {
                "Purchase No":
                    row.get(
                        "purchase_no"
                    )
                    or row.get(
                        "purchase_id"
                    )
                    or "-",

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    )
                    or "-",

                "Qty":
                    qty(
                        quantity_value
                    ),

                "Unit Cost":
                    money(
                        price_value
                    ),

                "Total":
                    money(
                        total_value
                    ),

                "Status":
                    row.get(
                        "status"
                    )
                    or "-",

                "Payment":
                    row.get(
                        "payment_method"
                    )
                    or "-",

                "Reference":
                    row.get(
                        "reference_no"
                    )
                    or "-",

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
# STOCK ADJUSTMENTS
# ==============================================================================

def get_adjustments(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Stock adjustment history.

    Table:
        stock_adjustments
    """

    data = _execute(
        client
        .table("stock_adjustments")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "created_at",
            desc=True,
        )
    )

    if _is_error(data):
        return []

    return data


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
                    row.get(
                        "id"
                    ),

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    )
                    or "-",

                "Type":
                    row.get(
                        "adjustment_type"
                    )
                    or "-",

                "Qty":
                    qty(
                        row.get(
                            "qty"
                        )
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
                    )
                    or "-",

                "Status":
                    row.get(
                        "status"
                    )
                    or "-",

                "Requested By":
                    row.get(
                        "requested_by"
                    )
                    or "-",

                "Approved By":
                    row.get(
                        "approved_by"
                    )
                    or "-",

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

def get_transfers(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Stock transfer history.

    Table:
        stock_transfers

    Schema variations are tolerated.
    """

    data = _execute(
        client
        .table("stock_transfers")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "created_at",
            desc=True,
        )
    )

    if _is_error(data):
        return []

    return data


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

        quantity_value = row.get(
            "qty"
        )

        if quantity_value is None:
            quantity_value = row.get(
                "quantity"
            )

        display.append(
            {
                "Transfer No":
                    row.get(
                        "transfer_no"
                    )
                    or row.get(
                        "id"
                    )
                    or "-",

                "From Warehouse":
                    row.get(
                        "from_warehouse_id"
                    )
                    or "-",

                "To Warehouse":
                    row.get(
                        "to_warehouse_id"
                    )
                    or "-",

                "Qty":
                    qty(
                        quantity_value
                    ),

                "Status":
                    row.get(
                        "status"
                    )
                    or "-",

                "Remarks":
                    row.get(
                        "remarks"
                    )
                    or "-",

                "Requested By":
                    row.get(
                        "requested_by"
                    )
                    or "-",

                "Approved By":
                    row.get(
                        "approved_by"
                    )
                    or "-",

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

def get_refunds(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Refund history.

    Table:
        refunds

    Depending on ERP schema, product_id may be stored directly
    or inside refund_items.

    Primary attempt:
        refunds.product_id
    """

    data = _execute(
        client
        .table("refunds")
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "refund_date",
            desc=True,
        )
    )

    if _is_error(data):
        return []

    return data


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
                    )
                    or row.get(
                        "id"
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
                    )
                    or "-",

                "Status":
                    row.get(
                        "status"
                    )
                    or "-",

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
# UNIFIED MOVEMENT HISTORY
# ==============================================================================

def get_unified_history(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Load unified product movement history.

    Preferred source:
        product_inventory_history

    Fallback:
        inventory_movements

    The function is READ ONLY.
    """

    # --------------------------------------------------------------------------
    # PRIMARY
    # --------------------------------------------------------------------------

    data = _execute(
        client
        .table(
            "product_inventory_history"
        )
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "transaction_time",
            desc=True,
        )
    )

    if not _is_error(data):

        return data

    # --------------------------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------------------------

    data = _execute(
        client
        .table(
            "inventory_movements"
        )
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "created_at",
            desc=True,
        )
    )

    if _is_error(data):

        return []

    return data


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

        transaction_time = row.get(
            "transaction_time"
        )

        if transaction_time is None:

            transaction_time = row.get(
                "created_at"
            )

        quantity_value = row.get(
            "quantity"
        )

        if quantity_value is None:

            quantity_value = row.get(
                "qty"
            )

        balance = row.get(
            "balance_after"
        )

        display.append(
            {
                "Time (MMT)":
                    format_myanmar_time(
                        transaction_time
                    ),

                "Source":
                    row.get(
                        "transaction_source"
                    )
                    or row.get(
                        "source"
                    )
                    or "-",

                "Type":
                    row.get(
                        "transaction_type"
                    )
                    or row.get(
                        "movement_type"
                    )
                    or "-",

                "Reference":
                    row.get(
                        "reference_id"
                    )
                    or "-",

                "Transaction":
                    row.get(
                        "transaction_id"
                    )
                    or row.get(
                        "id"
                    )
                    or "-",

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    )
                    or "-",

                "Qty":
                    qty(
                        quantity_value
                    ),

                "Balance":
                    (
                        qty(balance)
                        if balance is not None
                        else "-"
                    ),

                "Remarks":
                    row.get(
                        "remarks"
                    )
                    or row.get(
                        "reason"
                    )
                    or "-",
            }
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# AUDIT HISTORY
# ==============================================================================

def get_audit_history(
    client: Any,
    product_id: int,
) -> List[Dict]:
    """
    Product audit history.

    Primary:
        product_audit_logs

    Fallback:
        inventory_audit_logs
    """

    # --------------------------------------------------------------------------
    # PRIMARY
    # --------------------------------------------------------------------------

    data = _execute(
        client
        .table(
            "product_audit_logs"
        )
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "changed_at",
            desc=True,
        )
    )

    if not _is_error(data):

        return data

    # --------------------------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------------------------

    data = _execute(
        client
        .table(
            "inventory_audit_logs"
        )
        .select("*")
        .eq(
            "product_id",
            int(product_id),
        )
        .order(
            "changed_at",
            desc=True,
        )
    )

    if _is_error(data):

        return []

    return data


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
            )
            or row.get(
                "action"
            )
            or "UNKNOWN"
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

            # ------------------------------------------------------------------
            # BEFORE
            # ------------------------------------------------------------------

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

            # ------------------------------------------------------------------
            # AFTER
            # ------------------------------------------------------------------

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
                "Changed By: "
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

    passed = integrity.get(
        "passed",
        [],
    )

    warnings = integrity.get(
        "warnings",
        [],
    )

    for item in passed:

        st.success(
            f"✓ {item}"
        )

    for item in warnings:

        st.warning(
            f"⚠ {item}"
        )

    if not passed and not warnings:

        st.info(
            "No inventory integrity result available."
        )


# ==============================================================================
# PART 2 END
# ==============================================================================
#
# Part 3 will contain ONLY:
#
#   render_product_360()
#   render_product_360_page()
#   render_page()
#   __all__
#
# No duplicate get_integrity()
# No duplicate render_current_status()
# No duplicate render_fifo()
# No duplicate render_warehouse()
#
# ==============================================================================
# ==============================================================================
# erp_pages/inventory/product_360.py
#
# ERP ENTERPRISE PRODUCT 360°
# ------------------------------------------------------------------------------
# PART 2 / 3
#
# UI RENDERERS
# ------------------------------------------------------------------------------
# Pricing
# Sales
# Purchases
# Adjustments
# Transfers
# Refunds
# Unified History
# Audit
# Integrity
# ==============================================================================


# ==============================================================================
# PRICING INTELLIGENCE
# ==============================================================================

def calculate_price_info(
    product: Dict,
) -> Dict:
    """
    Calculate Product 360 pricing information.

    READ ONLY.
    No database update is performed.
    """

    purchase_price = to_decimal(
        product.get("purchase_price")
    )

    selling_price = to_decimal(
        product.get("selling_price")
    )

    markup_percent = to_decimal(
        product.get("markup_percent")
    )

    owner_selling_price = to_decimal(
        product.get("owner_selling_price")
    )

    final_selling_price = to_decimal(
        product.get("final_selling_price")
    )

    # --------------------------------------------------------------------------
    # Fallback selling price
    # --------------------------------------------------------------------------

    if final_selling_price == 0:

        final_selling_price = selling_price

    # --------------------------------------------------------------------------
    # Markup price
    # --------------------------------------------------------------------------

    global_markup_price = (
        purchase_price
        * (
            Decimal("1")
            + markup_percent / Decimal("100")
        )
    )

    # --------------------------------------------------------------------------
    # Actual markup
    # --------------------------------------------------------------------------

    if purchase_price != 0:

        actual_markup_percent = (
            (
                final_selling_price
                - purchase_price
            )
            / purchase_price
            * Decimal("100")
        )

    else:

        actual_markup_percent = Decimal("0")

    # --------------------------------------------------------------------------
    # Profit
    # --------------------------------------------------------------------------

    profit_per_unit = (
        final_selling_price
        - purchase_price
    )

    # --------------------------------------------------------------------------
    # Price source
    # --------------------------------------------------------------------------

    price_source = (
        product.get("price_source")
        or "PRODUCT"
    )

    owner_price_locked = bool(
        product.get(
            "owner_price_locked",
            False,
        )
    )

    return {
        "purchase_price":
            purchase_price,

        "selling_price":
            selling_price,

        "global_markup_percent":
            markup_percent,

        "global_markup_price":
            global_markup_price,

        "actual_markup_percent":
            actual_markup_percent,

        "owner_selling_price":
            owner_selling_price,

        "final_selling_price":
            final_selling_price,

        "profit_per_unit":
            profit_per_unit,

        "price_source":
            price_source,

        "owner_price_locked":
            owner_price_locked,
    }


def render_pricing(
    product: Dict,
):
    """
    Render pricing intelligence.
    """

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
        ),
    )

    c2.metric(
        "Global Markup",
        f"{info['global_markup_percent']}%",
    )

    c3.metric(
        "Selling Price",
        money(
            info["selling_price"]
        ),
    )

    c4.metric(
        "Profit / Unit",
        money(
            info["profit_per_unit"]
        ),
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
# WAREHOUSE STOCK
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

        qty_value = row.get(
            "qty"
        )

        if qty_value is None:

            qty_value = row.get(
                "quantity"
            )

        reserved_value = row.get(
            "reserved_qty"
        )

        available_value = row.get(
            "available_qty"
        )

        display.append(
            {
                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ) or "-",

                "Qty":
                    qty(
                        qty_value
                    ),

                "Reserved":
                    qty(
                        reserved_value
                    ),

                "Available":
                    qty(
                        available_value
                    ),

                "Minimum":
                    qty(
                        row.get(
                            "minimum_stock"
                        )
                    ),

                "Reorder":
                    qty(
                        row.get(
                            "reorder_level"
                        )
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
# BATCH / FEFO
# ==============================================================================

def render_batches(
    rows: List[Dict],
):

    st.subheader(
        "Batch / FEFO"
    )

    if not rows:

        empty_history(
            "Batch / FEFO"
        )

        return

    display = []

    for index, row in enumerate(
        rows,
        start=1,
    ):

        quantity_value = row.get(
            "quantity"
        )

        if quantity_value is None:

            quantity_value = row.get(
                "qty_in"
            )

        remaining_value = row.get(
            "qty_remaining"
        )

        if remaining_value is None:

            remaining_value = row.get(
                "remaining_qty"
            )

        display.append(
            {
                "FEFO Rank":
                    index,

                "Batch":
                    row.get(
                        "batch_no"
                    ) or "-",

                "Qty In":
                    qty(
                        quantity_value
                    ),

                "Remaining":
                    qty(
                        remaining_value
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
# FIFO COST LAYERS
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
        start=1,
    ):

        qty_in_value = row.get(
            "qty_in"
        )

        if qty_in_value is None:

            qty_in_value = row.get(
                "quantity"
            )

        remaining_value = row.get(
            "qty_remaining"
        )

        if remaining_value is None:

            remaining_value = row.get(
                "remaining_qty"
            )

        display.append(
            {
                "FIFO Rank":
                    index,

                "Layer ID":
                    row.get(
                        "id"
                    ) or "-",

                "Qty In":
                    qty(
                        qty_in_value
                    ),

                "Remaining":
                    qty(
                        remaining_value
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

        quantity_value = row.get(
            "qty"
        )

        if quantity_value is None:

            quantity_value = row.get(
                "quantity"
            )

        price_value = row.get(
            "price"
        )

        if price_value is None:

            price_value = row.get(
                "unit_cost"
            )

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
                        quantity_value
                    ),

                "Unit Cost":
                    money(
                        price_value
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
# STOCK ADJUSTMENTS
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
                    row.get(
                        "id"
                    ),

                "Warehouse":
                    row.get(
                        "warehouse_id"
                    ) or "-",

                "Type":
                    row.get(
                        "adjustment_type"
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
                    ) or "-",

                "To Warehouse":
                    row.get(
                        "to_warehouse_id"
                    ) or "-",

                "Qty":
                    qty(
                        row.get(
                            "qty"
                        )
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
# UNIFIED MOVEMENT HISTORY
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

        balance = row.get(
            "balance_after"
        )

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
                        qty(balance)
                        if balance is not None
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
# AUDIT HISTORY
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
            )
            or "UNKNOWN"
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
                "Changed By: "
                f"{row.get('changed_by') or 'SYSTEM'}"
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
            integrity.get(
                "master_stock"
            )
        ),
    )

    c2.metric(
        "Warehouse Stock",
        qty(
            integrity.get(
                "warehouse_stock"
            )
        ),
    )

    c3.metric(
        "FIFO Remaining",
        qty(
            integrity.get(
                "fifo_remaining"
            )
        ),
    )

    c4.metric(
        "Batch Remaining",
        qty(
            integrity.get(
                "batch_remaining"
            )
        ),
    )

    warnings = integrity.get(
        "warnings",
        [],
    )

    if warnings:

        for warning in warnings:

            st.warning(
                f"⚠️ {warning}"
            )

    else:

        st.success(
            "Inventory integrity checks passed."
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

    passed = integrity.get(
        "passed",
        [],
    )

    warnings = integrity.get(
        "warnings",
        [],
    )

    for item in passed:

        st.success(
            f"✓ {item}"
        )

    for item in warnings:

        st.warning(
            f"⚠ {item}"
        )

    if not passed and not warnings:

        st.info(
            "No inventory integrity result available."
        )


# ==============================================================================
# PART 2 END
# ==============================================================================
#
# IMPORTANT
# ------------------------------------------------------------------------------
# There is intentionally NO call to get_integrity() in this part.
#
# Part 3 will calculate integrity locally inside render_product_360().
#
# ==============================================================================
