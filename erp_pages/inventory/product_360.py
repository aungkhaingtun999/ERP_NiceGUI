# ==============================================================================
# erp_pages/inventory/product_360.py
#
# ERP ENTERPRISE PRODUCT 360°
# ------------------------------------------------------------------------------
# PART 1 / 3
#
# Product Master
# Warehouse Stock
# Batch / FEFO
# FIFO Cost Layers
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This module is designed to work with:
#
#     erp_pages/inventory/page.py
#
# Main Inventory entry:
#
#     render_product_360_page(client, product_id)
#
# Internal renderer:
#
#     render_product_360(client, product_id)
#
# Timezone:
#     Database -> PostgreSQL timestamptz
#     UI      -> Asia/Yangon / MMT / UTC+06:30
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


def format_myanmar_time(
    value: Any,
) -> str:
    """
    Convert database timestamp to Myanmar Standard Time.

    PostgreSQL timestamptz normally arrives as an aware datetime.
    ISO strings are also supported.
    """

    if value is None:
        return "-"

    if value == "":
        return "-"

    try:

        # ----------------------------------------------------------------------
        # String timestamp
        # ----------------------------------------------------------------------

        if isinstance(value, str):

            text = value.strip()

            if not text:
                return "-"

            if text.endswith("Z"):
                text = text[:-1] + "+00:00"

            dt = datetime.fromisoformat(text)

        # ----------------------------------------------------------------------
        # Python datetime
        # ----------------------------------------------------------------------

        elif isinstance(value, datetime):

            dt = value

        else:

            return str(value)

        # ----------------------------------------------------------------------
        # Safety for naive datetime
        # ----------------------------------------------------------------------

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=UTC
            )

        # ----------------------------------------------------------------------
        # Convert to Myanmar Time
        # ----------------------------------------------------------------------

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
    Safely convert any numeric value to Decimal.
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


def money(
    value: Any,
) -> str:
    """
    Format monetary values.

    Example:
        1500 -> 1,500.00
    """

    amount = to_decimal(value)

    return f"{amount:,.2f}"


def qty(
    value: Any,
) -> str:
    """
    Format quantity.

    Integer:
        100 -> 100

    Decimal:
        10.250 -> 10.250
    """

    amount = to_decimal(value)

    try:

        if (
            amount
            == amount.to_integral_value()
        ):

            return f"{int(amount):,}"

    except Exception:
        pass

    return f"{amount:,.3f}"


# ==============================================================================
# SAFE DATABASE EXECUTION
# ==============================================================================

def _execute(
    query: Any,
):
    """
    Execute a Supabase query safely.

    Returns:
        list -> successful query
        dict -> error
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


def _is_error(
    data: Any,
) -> bool:
    """
    Check safe-query error object.
    """

    return (
        isinstance(data, dict)
        and "__error__" in data
    )

# ==============================================================================
# INVENTORY INTEGRITY CHECK
# ==============================================================================

def get_integrity(
    product: Dict,
    warehouse_rows: List[Dict],
    batch_rows: List[Dict],
    fifo_rows: List[Dict],
) -> Dict:
    """
    Compare:

        Product Master Stock
            =
        Warehouse Stock
            =
        Batch Remaining
            =
        FIFO Remaining

    This is a READ-ONLY integrity check.
    It does NOT modify database data.
    """

    # --------------------------------------------------------------------------
    # PRODUCT MASTER STOCK
    # --------------------------------------------------------------------------

    master_stock = to_decimal(
        product.get("stock")
    )

    # --------------------------------------------------------------------------
    # WAREHOUSE STOCK
    # --------------------------------------------------------------------------

    warehouse_stock = Decimal("0")

    for row in warehouse_rows:

        warehouse_stock += to_decimal(
            row.get("qty")
        )

    # --------------------------------------------------------------------------
    # BATCH REMAINING
    # --------------------------------------------------------------------------

    batch_remaining = Decimal("0")

    for row in batch_rows:

        batch_remaining += to_decimal(
            row.get("qty_remaining")
        )

    # --------------------------------------------------------------------------
    # FIFO REMAINING
    # --------------------------------------------------------------------------

    fifo_remaining = Decimal("0")

    for row in fifo_rows:

        fifo_remaining += to_decimal(
            row.get("qty_remaining")
        )

    # --------------------------------------------------------------------------
    # RESULT
    # --------------------------------------------------------------------------

    warnings = []
    passed = []

    # --------------------------------------------------------------------------
    # WAREHOUSE vs FIFO
    # --------------------------------------------------------------------------

    if warehouse_stock == fifo_remaining:

        passed.append(
            "Warehouse stock matches FIFO remaining."
        )

    else:

        warnings.append(
            "Warehouse stock differs from FIFO remaining."
        )

    # --------------------------------------------------------------------------
    # MASTER vs WAREHOUSE
    # --------------------------------------------------------------------------

    if master_stock == warehouse_stock:

        passed.append(
            "Master stock matches warehouse stock."
        )

    else:

        warnings.append(
            "Master stock differs from warehouse stock."
        )

    # --------------------------------------------------------------------------
    # BATCH vs FIFO
    # --------------------------------------------------------------------------

    if batch_remaining == fifo_remaining:

        passed.append(
            "Batch remaining matches FIFO remaining."
        )

    else:

        warnings.append(
            "Batch remaining differs from FIFO remaining."
        )

    # --------------------------------------------------------------------------
    # RETURN
    # --------------------------------------------------------------------------

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
# PRODUCT MASTER
# ==============================================================================

def get_product(
    client: Any,
    product_id: int,
) -> Optional[Dict]:
    """
    Load one Product Master record.

    Source:
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

        data = (
            getattr(
                result,
                "data",
                None,
            )
            or []
        )

        if isinstance(data, list):

            return (
                data[0]
                if data
                else None
            )

        if isinstance(data, dict):

            return data

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
    Load warehouse stock for a product.

    Source:
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

    Source:
        inventory_batches

    Ordering:
        created_at ASC

    This preserves the oldest batch first,
    which is useful for FEFO/FIFO inspection.
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

    Source:
        inventory_cost_layers

    IMPORTANT
    ----------------------------------------------------------------------------
    Do not assume a received_date column.

    The current ERP schema uses created_at for ordering.
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
# PRODUCT STOCK SUMMARY
# ==============================================================================

def calculate_stock_summary(
    product: Dict,
    warehouse_rows: List[Dict],
    batch_rows: List[Dict],
    fifo_rows: List[Dict],
) -> Dict:
    """
    Calculate Product 360 stock totals.

    The summary is informational only.

    No database changes are performed here.
    """

    # --------------------------------------------------------------------------
    # Product master stock
    # --------------------------------------------------------------------------

    master_stock = to_decimal(
        product.get("stock")
    )

    # --------------------------------------------------------------------------
    # Warehouse stock
    #
    # Primary field:
    #     qty
    #
    # Fallback:
    #     quantity
    # --------------------------------------------------------------------------

    warehouse_stock = Decimal("0")

    for row in warehouse_rows:

        value = row.get("qty")

        if value is None:

            value = row.get(
                "quantity"
            )

        warehouse_stock += (
            to_decimal(value)
        )

    # --------------------------------------------------------------------------
    # Batch remaining
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

        batch_remaining += (
            to_decimal(value)
        )

    # --------------------------------------------------------------------------
    # FIFO remaining
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

        fifo_remaining += (
            to_decimal(value)
        )

    # --------------------------------------------------------------------------
    # Return
    # --------------------------------------------------------------------------

    return {
        "master_stock":
            master_stock,

        "warehouse_stock":
            warehouse_stock,

        "batch_remaining":
            batch_remaining,

        "fifo_remaining":
            fifo_remaining,
    }


# ==============================================================================
# EMPTY STATE
# ==============================================================================

def empty_history(
    title: str,
    message: str = (
        "No historical record available."
    ),
):
    """
    Standard Product 360 empty-state UI.
    """

    st.info(
        f"**{title}**\n\n{message}"
    )


# ==============================================================================
# PRODUCT HEADER
# ==============================================================================

def render_product_header(
    product: Dict,
):
    """
    Product identity header.
    """

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
# CURRENT INVENTORY STATUS
# ==============================================================================

def render_current_status(
    summary: Dict,
):
    """
    Current inventory KPI cards.
    """

    st.subheader(
        "Current Inventory Status"
    )

    c1, c2, c3, c4 = st.columns(4)

    # --------------------------------------------------------------------------
    # Master
    # --------------------------------------------------------------------------

    c1.metric(
        "Master Stock",
        qty(
            summary.get(
                "master_stock"
            )
        ),
    )

    # --------------------------------------------------------------------------
    # Warehouse
    # --------------------------------------------------------------------------

    c2.metric(
        "Warehouse Stock",
        qty(
            summary.get(
                "warehouse_stock"
            )
        ),
    )

    # --------------------------------------------------------------------------
    # FIFO
    # --------------------------------------------------------------------------

    c3.metric(
        "FIFO Remaining",
        qty(
            summary.get(
                "fifo_remaining"
            )
        ),
    )

    # --------------------------------------------------------------------------
    # Batch
    # --------------------------------------------------------------------------

    c4.metric(
        "Batch Remaining",
        qty(
            summary.get(
                "batch_remaining"
            )
        ),
    )


# ==============================================================================
# WAREHOUSE STOCK UI
# ==============================================================================

def render_warehouse(
    rows: List[Dict],
):
    """
    Render warehouse stock table.
    """

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
                    ) or "-",

                "Qty":
                    qty(
                        row.get(
                            "qty"
                        )
                    ),

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
# BATCH / FEFO UI
# ==============================================================================

def render_batches(
    rows: List[Dict],
):
    """
    Render inventory batches.

    FEFO display is ordered according to the
    database query order.
    """

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
# FIFO COST LAYER UI
# ==============================================================================

def render_fifo(
    rows: List[Dict],
):
    """
    Render FIFO cost layers.
    """

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
#
# Part 2 will continue with:
#
#   - Pricing Intelligence
#   - Sales
#   - Purchases
#   - Stock Adjustments
#   - Transfers
#   - Transfer Costs
#   - Refunds
#   - Unified Movement History
#   - Audit History
#
# ==============================================================================
# ==============================================================================
# PART 2 / 3
# PRODUCT 360° — UI RENDERERS
# ==============================================================================


# ==============================================================================
# CURRENT STATUS
# ==============================================================================

def render_current_status(
    product: Dict,
    integrity: Dict,
):

    st.subheader("Current Inventory Status")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Master Stock",
        qty(integrity["master_stock"]),
    )

    c2.metric(
        "Warehouse Stock",
        qty(integrity["warehouse_stock"]),
    )

    c3.metric(
        "FIFO Remaining",
        qty(integrity["fifo_remaining"]),
    )

    c4.metric(
        "Batch Remaining",
        qty(integrity["batch_remaining"]),
    )

    if integrity["warnings"]:

        for warning in integrity["warnings"]:
            st.warning(f"⚠️ {warning}")

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

    st.subheader("Pricing Intelligence")

    info = calculate_price_info(product)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Purchase Price",
        money(info["purchase_price"]),
    )

    c2.metric(
        "Global Markup",
        f"{info['global_markup_percent']}%",
    )

    c3.metric(
        "Selling Price",
        money(info["selling_price"]),
    )

    c4.metric(
        "Profit / Unit",
        money(info["profit_per_unit"]),
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

    st.subheader("Warehouse Stock")

    if not rows:

        empty_history("Warehouse Stock")

        return

    display = []

    for row in rows:

        display.append(
            {
                "Warehouse":
                    row.get("warehouse_id") or "-",

                "Qty":
                    qty(row.get("qty")),

                "Reserved":
                    qty(row.get("reserved_qty")),

                "Available":
                    qty(row.get("available_qty")),

                "Minimum":
                    qty(row.get("minimum_stock")),

                "Reorder":
                    qty(row.get("reorder_level")),

                "Location":
                    row.get("location") or "-",

                "Batch No":
                    row.get("batch_no") or "-",

                "Updated":
                    format_myanmar_time(
                        row.get("updated_at")
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

    st.subheader("Batch / FEFO")

    if not rows:

        empty_history("Batch History")

        return

    display = []

    for index, row in enumerate(
        rows,
        start=1,
    ):

        display.append(
            {
                "FEFO Rank":
                    index,

                "Batch":
                    row.get("batch_no") or "-",

                "Qty":
                    qty(
                        row.get("quantity")
                    ),

                "Remaining":
                    qty(
                        row.get("qty_remaining")
                    ),

                "Unit Cost":
                    money(
                        row.get("unit_cost")
                    ),

                "MFG Date":
                    row.get("mfg_date") or "-",

                "Expiry":
                    row.get("expiry_date") or "-",

                "Supplier":
                    row.get("supplier_code") or "-",

                "Created":
                    format_myanmar_time(
                        row.get("created_at")
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

    st.subheader("FIFO Cost Layers")

    if not rows:

        empty_history("FIFO Cost Layers")

        return

    display = []

    for index, row in enumerate(
        rows,
        start=1,
    ):

        display.append(
            {
                "FIFO Rank":
                    index,

                "Layer ID":
                    row.get("id"),

                "Qty In":
                    qty(
                        row.get("qty_in")
                    ),

                "Remaining":
                    qty(
                        row.get("qty_remaining")
                    ),

                "Unit Cost":
                    money(
                        row.get("unit_cost")
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
                        row.get("created_at")
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

    st.subheader("Sales History")

    if not rows:

        empty_history("Sales History")

        return

    display = []

    for row in rows:

        display.append(
            {
                "Invoice":
                    row.get("invoice_no") or "-",

                "Warehouse":
                    row.get("warehouse_id") or "-",

                "Qty":
                    qty(
                        row.get("quantity")
                    ),

                "Unit Price":
                    money(
                        row.get("unit_price")
                    ),

                "Discount":
                    money(
                        row.get("discount")
                    ),

                "Total":
                    money(
                        row.get("total")
                    ),

                "Status":
                    row.get("sale_status") or "-",

                "Payment":
                    row.get(
                        "payment_method"
                    ) or "-",

                "Time":
                    format_myanmar_time(
                        row.get("created_at")
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

    st.subheader("Purchase History")

    if not rows:

        empty_history("Purchase History")

        return

    display = []

    for row in rows:

        display.append(
            {
                "Purchase No":
                    row.get("purchase_no") or "-",

                "Warehouse":
                    row.get("warehouse_id") or "-",

                "Qty":
                    qty(row.get("qty")),

                "Unit Cost":
                    money(row.get("price")),

                "Total":
                    money(row.get("total")),

                "Status":
                    row.get("status") or "-",

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
                        row.get("created_at")
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

    st.subheader("Stock Adjustment History")

    if not rows:

        empty_history("Adjustment History")

        return

    display = []

    for row in rows:

        display.append(
            {
                "ID":
                    row.get("id"),

                "Warehouse":
                    row.get("warehouse_id") or "-",

                "Type":
                    row.get(
                        "adjustment_type"
                    ) or "-",

                "Qty":
                    qty(row.get("qty")),

                "Unit Cost":
                    money(
                        row.get("unit_cost")
                    ),

                "Reason":
                    row.get("reason") or "-",

                "Status":
                    row.get("status") or "-",

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
                        row.get("created_at")
                    ),

                "Approved":
                    format_myanmar_time(
                        row.get("approved_at")
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

    st.subheader("Stock Transfer History")

    if not rows:

        empty_history("Transfer History")

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
                    qty(row.get("qty")),

                "Status":
                    row.get("status") or "-",

                "Remarks":
                    row.get("remarks") or "-",

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
                        row.get("created_at")
                    ),

                "Approved":
                    format_myanmar_time(
                        row.get("approved_at")
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

    st.subheader("Refund History")

    if not rows:

        empty_history("Refund History")

        return

    display = []

    for row in rows:

        display.append(
            {
                "Refund ID":
                    row.get("refund_id"),

                "Sale ID":
                    row.get("sale_id"),

                "Qty":
                    qty(
                        row.get("quantity")
                    ),

                "Unit Price":
                    money(
                        row.get("unit_price")
                    ),

                "Total":
                    money(
                        row.get("total")
                    ),

                "Refund Amount":
                    money(
                        row.get("refund_amount")
                    ),

                "Reason":
                    row.get("reason") or "-",

                "Status":
                    row.get("status") or "-",

                "Date":
                    format_myanmar_time(
                        row.get("refund_date")
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
                        row.get("quantity")
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

    st.subheader("Product Audit History")

    if not rows:

        empty_history(
            "Audit History",
            "No historical audit record available.",
        )

        return

    for row in rows:

        operation = (
            row.get("operation")
            or "UNKNOWN"
        )

        changed_at = format_myanmar_time(
            row.get("changed_at")
        )

        with st.expander(
            f"{operation} — {changed_at}"
        ):

            c1, c2 = st.columns(2)

            with c1:

                st.markdown("### Before")

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

                st.markdown("### After")

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

    st.subheader("Inventory Integrity")

    for item in integrity.get(
        "passed",
        [],
    ):

        st.success(
            f"✓ {item}"
        )

    for item in integrity.get(
        "warnings",
        [],
    ):

        st.warning(
            f"⚠ {item}"
        )

    if not integrity.get(
        "passed"
    ) and not integrity.get(
        "warnings"
    ):

        st.info(
            "No inventory integrity result available."
        )

# ==============================================================================
# PART 3 / 3
# PRODUCT 360° — MAIN RENDER + COMPATIBILITY ENTRY
# ==============================================================================
# ==============================================================================
# MAIN PRODUCT 360 RENDER
# ==============================================================================

def render_product_360(
    client,
    product_id: int,
):
    """
    Main Product 360 renderer.

    IMPORTANT:
    Integrity calculation is intentionally performed locally here.
    This avoids dependency on a separate get_integrity() function and
    prevents NameError when this module is loaded through Inventory page.
    """

    # --------------------------------------------------------------------------
    # VALIDATE PRODUCT ID
    # --------------------------------------------------------------------------

    try:

        product_id = int(product_id)

    except (
        TypeError,
        ValueError,
    ):

        st.error(
            "Invalid Product ID."
        )

        return

    # --------------------------------------------------------------------------
    # PRODUCT MASTER
    # --------------------------------------------------------------------------

    product = get_product(
        client,
        product_id,
    )

    if not product:

        st.error(
            f"Product ID {product_id} not found."
        )

        return

    # --------------------------------------------------------------------------
    # INVENTORY DATA
    # --------------------------------------------------------------------------

    warehouse_rows = get_warehouse_stock(
        client,
        product_id,
    )

    batch_rows = get_batches(
        client,
        product_id,
    )

    fifo_rows = get_fifo_layers(
        client,
        product_id,
    )

    # ==========================================================================
    # INVENTORY INTEGRITY
    # ==========================================================================
    #
    # DO NOT CALL get_integrity() HERE.
    #
    # Calculate directly so Product 360 cannot fail because of a missing
    # helper function.
    # ==========================================================================

    master_stock = to_decimal(
        product.get("stock")
    )

    warehouse_stock = Decimal("0")

    for row in warehouse_rows:

        warehouse_stock += to_decimal(
            row.get("qty")
        )

    batch_remaining = Decimal("0")

    for row in batch_rows:

        batch_remaining += to_decimal(
            row.get("qty_remaining")
        )

    fifo_remaining = Decimal("0")

    for row in fifo_rows:

        fifo_remaining += to_decimal(
            row.get("qty_remaining")
        )

    integrity_warnings = []
    integrity_passed = []

    # --------------------------------------------------------------------------
    # WAREHOUSE vs FIFO
    # --------------------------------------------------------------------------

    if warehouse_stock == fifo_remaining:

        integrity_passed.append(
            "Warehouse stock matches FIFO remaining."
        )

    else:

        integrity_warnings.append(
            "Warehouse stock differs from FIFO remaining."
        )

    # --------------------------------------------------------------------------
    # MASTER vs WAREHOUSE
    # --------------------------------------------------------------------------

    if master_stock == warehouse_stock:

        integrity_passed.append(
            "Master stock matches warehouse stock."
        )

    else:

        integrity_warnings.append(
            "Master stock differs from warehouse stock."
        )

    # --------------------------------------------------------------------------
    # BATCH vs FIFO
    # --------------------------------------------------------------------------

    if batch_remaining == fifo_remaining:

        integrity_passed.append(
            "Batch remaining matches FIFO remaining."
        )

    else:

        integrity_warnings.append(
            "Batch remaining differs from FIFO remaining."
        )

    # --------------------------------------------------------------------------
    # INTEGRITY OBJECT
    # --------------------------------------------------------------------------

    integrity = {
        "master_stock":
            master_stock,

        "warehouse_stock":
            warehouse_stock,

        "batch_remaining":
            batch_remaining,

        "fifo_remaining":
            fifo_remaining,

        "warnings":
            integrity_warnings,

        "passed":
            integrity_passed,
    }

    # ==========================================================================
    # TRANSACTION DATA
    # ==========================================================================

    sales_rows = get_sales(
        client,
        product_id,
    )

    purchase_rows = get_purchases(
        client,
        product_id,
    )

    adjustment_rows = get_adjustments(
        client,
        product_id,
    )

    transfer_rows = get_transfers(
        client,
        product_id,
    )

    refund_rows = get_refunds(
        client,
        product_id,
    )

    unified_rows = get_unified_history(
        client,
        product_id,
    )

    audit_rows = get_audit_history(
        client,
        product_id,
    )

    # ==========================================================================
    # PRODUCT HEADER
    # ==========================================================================

    render_product_header(
        product
    )

    st.divider()

    # ==========================================================================
    # CURRENT STATUS
    # ==========================================================================

    render_current_status(
        product,
        integrity,
    )

    st.divider()

    # ==========================================================================
    # PRICING
    # ==========================================================================

    render_pricing(
        product
    )

    st.divider()

    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================

    render_warehouse(
        warehouse_rows
    )

    st.divider()

    # ==========================================================================
    # BATCH / FIFO
    # ==========================================================================

    batch_tab, fifo_tab = st.tabs(
        [
            "📦 Batch / FEFO",
            "🔄 FIFO Cost Layers",
        ]
    )

    with batch_tab:

        render_batches(
            batch_rows
        )

    with fifo_tab:

        render_fifo(
            fifo_rows
        )

    st.divider()

    # ==========================================================================
    # TRANSACTIONS
    # ==========================================================================

    transaction_tabs = st.tabs(
        [
            "🛒 Sales",
            "📥 Purchases",
            "🛠 Adjustments",
            "🔄 Transfers",
            "↩ Refunds",
            "📜 Unified History",
        ]
    )

    with transaction_tabs[0]:

        render_sales(
            sales_rows
        )

    with transaction_tabs[1]:

        render_purchases(
            purchase_rows
        )

    with transaction_tabs[2]:

        render_adjustments(
            adjustment_rows
        )

    with transaction_tabs[3]:

        render_transfers(
            transfer_rows
        )

    with transaction_tabs[4]:

        render_refunds(
            refund_rows
        )

    with transaction_tabs[5]:

        render_unified_history(
            unified_rows
        )

    st.divider()

    # ==========================================================================
    # AUDIT
    # ==========================================================================

    render_audit(
        audit_rows
    )

    st.divider()

    # ==========================================================================
    # INTEGRITY
    # ==========================================================================

    render_integrity(
        integrity
    )


# ==============================================================================
# COMPATIBILITY WRAPPER
# ==============================================================================

def render_product_360_page(
    client,
    product_id: Optional[int] = None,
):
    """
    Compatibility wrapper used by:

        erp_pages/inventory/page.py
    """

    if client is None:

        st.error(
            "ERP database client is not available."
        )

        return

    if product_id is None:

        st.info(
            "Select a product to open Product 360°."
        )

        return

    try:

        product_id = int(
            product_id
        )

    except (
        TypeError,
        ValueError,
    ):

        st.error(
            "Invalid Product ID."
        )

        return

    render_product_360(
        client,
        product_id,
)



# ==============================================================================
# STANDALONE PRODUCT 360 PAGE
# ==============================================================================

def render_page(
    client,
    product_id: Optional[int] = None,
):
    """
    Standalone Product 360 page.

    Can be used independently from Inventory page.
    """

    st.title(
        "📦 Product 360°"
    )

    st.caption(
        "Enterprise Product Intelligence | "
        "Inventory | FIFO | FEFO | Pricing | Audit"
    )

    # --------------------------------------------------------------------------
    # PRODUCT SEARCH
    # --------------------------------------------------------------------------

    with st.sidebar:

        st.header(
            "Product 360°"
        )

        search_mode = st.selectbox(
            "Search By",
            [
                "Product ID",
                "SKU",
                "Barcode",
            ],
            key="product_360_search_mode",
        )

        selected_product_id = None

        # ----------------------------------------------------------------------
        # PRODUCT ID
        # ----------------------------------------------------------------------

        if search_mode == "Product ID":

            entered_id = st.number_input(
                "Product ID",
                min_value=1,
                value=int(
                    product_id or 1
                ),
                step=1,
                key="product_360_product_id",
            )

            selected_product_id = int(
                entered_id
            )

        # ----------------------------------------------------------------------
        # SKU
        # ----------------------------------------------------------------------

        elif search_mode == "SKU":

            sku = st.text_input(
                "SKU",
                key="product_360_sku",
            ).strip()

            if sku:

                try:

                    result = (
                        client
                        .table("products")
                        .select("id")
                        .eq(
                            "sku",
                            sku,
                        )
                        .limit(1)
                        .execute()
                    )

                    rows = result.data or []

                    if rows:

                        selected_product_id = int(
                            rows[0]["id"]
                        )

                    else:

                        st.warning(
                            "SKU not found."
                        )

                except Exception as e:

                    st.error(
                        f"SKU lookup failed: {e}"
                    )

        # ----------------------------------------------------------------------
        # BARCODE
        # ----------------------------------------------------------------------

        else:

            barcode = st.text_input(
                "Barcode",
                key="product_360_barcode",
            ).strip()

            if barcode:

                try:

                    result = (
                        client
                        .table("products")
                        .select("id")
                        .eq(
                            "barcode",
                            barcode,
                        )
                        .limit(1)
                        .execute()
                    )

                    rows = result.data or []

                    if rows:

                        selected_product_id = int(
                            rows[0]["id"]
                        )

                    else:

                        st.warning(
                            "Barcode not found."
                        )

                except Exception as e:

                    st.error(
                        f"Barcode lookup failed: {e}"
                    )

    # --------------------------------------------------------------------------
    # RENDER
    # --------------------------------------------------------------------------

    if selected_product_id:

        render_product_360(
            client,
            selected_product_id,
        )

    else:

        st.info(
            "Select a Product ID, SKU, or Barcode."
        )


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "render_product_360",
    "render_product_360_page",
    "render_page",
    "format_myanmar_time",
]
