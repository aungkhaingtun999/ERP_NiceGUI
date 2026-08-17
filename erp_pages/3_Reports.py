# ==============================================================================
# erp_pages/3_Reports.py
#
# ERP ENTERPRISE SALES ANALYTICS REPORT v5.0
#
# Sales Summary + Product Sales + Cashier + Payment + Export
#
# PRODUCT NAME SUPPORT
# ------------------------------------------------------------------------------
#
# sales
#   ↓
# sale_items
#   ↓
# product_id
#   ↓
# products
#
# Product Name Resolution:
#
# 1. sale_items.product_name
#       ↓ if NULL / empty
# 2. products.name
#       ↓ if unavailable
# 3. "Unknown Product"
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This report is READ-ONLY.
#
# It NEVER:
# - modifies sales
# - modifies sale_items
# - modifies products
# - modifies inventory
# - modifies warehouse_stock
#
# ==============================================================================

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
import json

import pandas as pd
import streamlit as st

from erp_core.base_repo import db
from utils.ui import show_table


# ==============================================================================
# CONSTANTS
# ==============================================================================

UNKNOWN_PRODUCT = "Unknown Product"


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_number(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


# ==============================================================================
# CASHIER NAME
# ==============================================================================

def cashier_name(user):
    """
    Safely convert Supabase users relation into cashier display name.

    Current query provides:
        username
        employee_code
    """

    if not isinstance(user, dict):
        return "Unknown"

    username = str(
        user.get("username") or ""
    ).strip()

    employee_code = str(
        user.get("employee_code") or ""
    ).strip()

    if username:
        return username

    if employee_code:
        return employee_code

    return "Unknown"


# ==============================================================================
# PRODUCT NAME
# ==============================================================================

def resolve_product_name(
    item_product_name,
    product_name,
):
    """
    Product name resolution priority:

    1. sale_items.product_name
    2. products.name
    3. Unknown Product

    This protects historical sale reports if
    sale_items.product_name was stored as a snapshot.
    """

    item_name = str(
        item_product_name or ""
    ).strip()

    if item_name:
        return item_name

    master_name = str(
        product_name or ""
    ).strip()

    if master_name:
        return master_name

    return UNKNOWN_PRODUCT


# ==============================================================================
# FORMAT NUMBER
# ==============================================================================

def format_number(value):
    try:
        number = float(value or 0)

        if number.is_integer():
            return f"{int(number):,}"

        return f"{number:,.2f}"

    except Exception:
        return str(value)


# ==============================================================================
# DATE RANGE
# ==============================================================================

def get_report_utc_range(
    start_date,
    end_date,
):
    """
    Convert Myanmar local date range into UTC boundaries.

    Database created_at is timestamptz / UTC.
    """

    try:

        from zoneinfo import ZoneInfo

        myanmar_tz = ZoneInfo(
            "Asia/Yangon"
        )

        start_local = pd.Timestamp(
            start_date,
            tz=myanmar_tz,
        )

        end_local = pd.Timestamp(
            end_date + timedelta(days=1),
            tz=myanmar_tz,
        )

        start_utc = (
            start_local
            .tz_convert("UTC")
            .isoformat()
        )

        end_utc = (
            end_local
            .tz_convert("UTC")
            .isoformat()
        )

        return (
            start_utc,
            end_utc,
        )

    except Exception:

        start_utc = (
            f"{start_date.isoformat()}"
            f"T00:00:00+00:00"
        )

        end_utc = (
            f"{(end_date + timedelta(days=1)).isoformat()}"
            f"T00:00:00+00:00"
        )

        return (
            start_utc,
            end_utc,
        )


# ==============================================================================
# LOAD SALES
# ==============================================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def get_sales(
    query_start,
    query_end,
):

    try:

        response = (
            db()
            .table("sales")
            .select(
                """
                id,
                total,
                total_amount,
                discount,
                tax,
                subtotal,
                paid_amount,
                payment_method,
                created_at,
                cashier_id,
                users(
                    username,
                    employee_code
                )
                """
            )
            .gte(
                "created_at",
                query_start,
            )
            .lt(
                "created_at",
                query_end,
            )
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    except Exception as e:

        st.error(
            f"Sales loading error: {e}"
        )

        return []


# ==============================================================================
# LOAD SALE ITEMS
# ==============================================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def get_sale_items(
    sale_ids,
):
    """
    Load sale_items for the selected sales.

    Confirmed columns:

        id
        sale_id
        product_id
        quantity
        unit_price
        discount
        total
        product_name
    """

    if not sale_ids:
        return []

    try:

        normalized_ids = [
            int(x)
            for x in sale_ids
            if x is not None
        ]

        if not normalized_ids:
            return []

        response = (
            db()
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
            .in_(
                "sale_id",
                normalized_ids,
            )
            .order(
                "sale_id",
            )
            .order(
                "id",
            )
            .execute()
        )

        return response.data or []

    except Exception as e:

        st.error(
            f"Sale item loading error: {e}"
        )

        return []


# ==============================================================================
# LOAD PRODUCTS
# ==============================================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def get_products(
    product_ids,
):
    """
    Load product master data.

    Used as fallback when sale_items.product_name
    is NULL or empty.
    """

    if not product_ids:
        return {}

    try:

        normalized_ids = [
            int(x)
            for x in product_ids
            if x is not None
        ]

        if not normalized_ids:
            return {}

        response = (
            db()
            .table("products")
            .select(
                """
                id,
                name,
                sku,
                barcode
                """
            )
            .in_(
                "id",
                normalized_ids,
            )
            .execute()
        )

        rows = response.data or []

        return {
            int(row["id"]): row
            for row in rows
            if row.get("id") is not None
        }

    except Exception as e:

        st.error(
            f"Product loading error: {e}"
        )

        return {}


# ==============================================================================
# BUILD PRODUCT SALES DATAFRAME
# ==============================================================================

def build_product_sales_dataframe(
    sales,
    sale_items,
    products,
):
    """
    Build item-level sales dataframe.

    Product Name:
        sale_items.product_name
            ↓ fallback
        products.name
    """

    if not sale_items:
        return pd.DataFrame()

    sales_map = {}

    for sale in sales:

        sale_id = sale.get("id")

        if sale_id is None:
            continue

        try:
            sale_id = int(sale_id)
        except Exception:
            continue

        user = sale.get("users")

        sales_map[sale_id] = {
            "created_at": sale.get(
                "created_at"
            ),
            "cashier": cashier_name(
                user
            ),
            "payment_method": sale.get(
                "payment_method"
            ),
        }

    rows = []

    for item in sale_items:

        sale_id = item.get(
            "sale_id"
        )

        if sale_id is None:
            continue

        try:
            sale_id = int(
                sale_id
            )
        except Exception:
            continue

        sale_info = sales_map.get(
            sale_id,
            {},
        )

        product_id = item.get(
            "product_id"
        )

        try:

            product_id_int = (
                int(product_id)
                if product_id is not None
                else None
            )

        except Exception:

            product_id_int = None

        product = products.get(
            product_id_int,
            {},
        )

        product_name = resolve_product_name(
            item.get("product_name"),
            product.get("name"),
        )

        rows.append(
            {
                "Sale ID": sale_id,

                "Date": sale_info.get(
                    "created_at"
                ),

                "Cashier": sale_info.get(
                    "cashier",
                    "Unknown",
                ),

                "Payment Method": (
                    sale_info.get(
                        "payment_method"
                    )
                    or "Unknown"
                ),

                "Product ID": product_id_int,

                "Product Name": product_name,

                "SKU": (
                    product.get("sku")
                    or ""
                ),

                "Barcode": (
                    product.get("barcode")
                    or ""
                ),

                "Quantity": safe_number(
                    item.get("quantity")
                ),

                "Unit Price": safe_number(
                    item.get("unit_price")
                ),

                "Discount": safe_number(
                    item.get("discount")
                ),

                "Sales": safe_number(
                    item.get("total")
                ),
            }
        )

    if not rows:
        return pd.DataFrame()

    product_df = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------------------------
    # Date
    # --------------------------------------------------------------------------

    if "Date" in product_df.columns:

        product_df["Date"] = pd.to_datetime(
            product_df["Date"],
            errors="coerce",
            utc=True,
        )

        product_df = product_df[
            product_df["Date"].notna()
        ].copy()

        if not product_df.empty:

            product_df["Date"] = (
                product_df["Date"]
                .dt.tz_convert(
                    "Asia/Yangon"
                )
                .dt.tz_localize(None)
            )

    # --------------------------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------------------------

    for col in [
        "Quantity",
        "Unit Price",
        "Discount",
        "Sales",
    ]:

        if col in product_df.columns:

            product_df[col] = (
                pd.to_numeric(
                    product_df[col],
                    errors="coerce",
                )
                .fillna(0.0)
            )

    return product_df


# ==============================================================================
# PRODUCT DETAIL REPORT
# ==============================================================================

def render_product_sales_report(
    product_df,
):

    st.subheader(
        "📦 Product Sales Report"
    )

    if product_df.empty:

        st.info(
            "No product sales data found."
        )

        return

    # ==========================================================================
    # PRODUCT KPI
    # ==========================================================================

    total_products = (
        product_df["Product Name"]
        .nunique()
    )

    total_qty = safe_number(
        product_df["Quantity"].sum()
    )

    total_discount = safe_number(
        product_df["Discount"].sum()
    )

    total_sales = safe_number(
        product_df["Sales"].sum()
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📦 Products",
        total_products,
    )

    c2.metric(
        "🔢 Qty Sold",
        format_number(
            total_qty
        ),
    )

    c3.metric(
        "🏷 Discount",
        f"{total_discount:,.0f} MMK",
    )

    c4.metric(
        "💰 Product Sales",
        f"{total_sales:,.0f} MMK",
    )

    st.divider()

    # ==========================================================================
    # PRODUCT SUMMARY
    # ==========================================================================

    st.markdown(
        "### 🏆 Product Sales Summary"
    )

    product_summary = (
        product_df
        .groupby(
            [
                "Product Name",
                "SKU",
                "Barcode",
            ],
            dropna=False,
        )
        .agg(
            Quantity=(
                "Quantity",
                "sum",
            ),
            Discount=(
                "Discount",
                "sum",
            ),
            Sales=(
                "Sales",
                "sum",
            ),
        )
        .reset_index()
        .sort_values(
            "Sales",
            ascending=False,
        )
    )

    display_summary = product_summary.copy()

    display_summary[
        "Quantity"
    ] = display_summary[
        "Quantity"
    ].apply(
        format_number
    )

    display_summary[
        "Discount"
    ] = display_summary[
        "Discount"
    ].apply(
        lambda x: f"{safe_number(x):,.0f}"
    )

    display_summary[
        "Sales"
    ] = display_summary[
        "Sales"
    ].apply(
        lambda x: f"{safe_number(x):,.0f}"
    )

    show_table(
        display_summary
    )

    st.divider()

    # ==========================================================================
    # ITEM-LEVEL DETAIL
    # ==========================================================================

    st.markdown(
        "### 🧾 Sale Item Detail"
    )

    detail_columns = [
        "Date",
        "Sale ID",
        "Product Name",
        "SKU",
        "Barcode",
        "Quantity",
        "Unit Price",
        "Discount",
        "Sales",
        "Cashier",
        "Payment Method",
    ]

    detail_df = product_df[
        [
            col
            for col in detail_columns
            if col in product_df.columns
        ]
    ].copy()

    if "Date" in detail_df.columns:

        detail_df["Date"] = (
            detail_df["Date"]
            .dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    for col in [
        "Quantity",
        "Unit Price",
        "Discount",
        "Sales",
    ]:

        if col in detail_df.columns:

            detail_df[col] = detail_df[
                col
            ].apply(
                format_number
            )

    show_table(
        detail_df
    )


# ==============================================================================
# MAIN
# ==============================================================================

def run():

    st.title(
        "📊 ERP Executive Analytics & Reports"
    )

    st.caption(
        "MYANMAR ERP - Sales Performance Analytics"
    )

    # ==========================================================================
    # DATE FILTER
    # ==========================================================================

    try:

        from utils.timezone import (
            get_myanmar_today
        )

        today = get_myanmar_today()

        if not isinstance(
            today,
            date,
        ):

            today = date.today()

    except Exception:

        today = date.today()

    c1, c2 = st.columns(2)

    start_date = c1.date_input(
        "Start Date",
        value=today,
        key="reports_start_date",
    )

    end_date = c2.date_input(
        "End Date",
        value=today,
        key="reports_end_date",
    )

    if start_date > end_date:

        st.error(
            "Start Date cannot be later than End Date."
        )

        return

    # ==========================================================================
    # UTC RANGE
    # ==========================================================================

    (
        start_utc,
        end_utc,
    ) = get_report_utc_range(
        start_date,
        end_date,
    )

    # ==========================================================================
    # LOAD SALES
    # ==========================================================================

    sales = get_sales(
        start_utc,
        end_utc,
    )

    if not sales:

        st.warning(
            "No sales data found for the selected date range."
        )

        st.caption(
            f"Checked: {start_date} → {end_date}"
        )

        return

    # ==========================================================================
    # DEBUG — REPORT SALES DATA
    # ==========================================================================

    df = pd.DataFrame(sales)

    st.write("### DEBUG — REPORT SALES DATA")

    st.dataframe(
        df[
            [
                "id",
                "total",
                "subtotal",
                "discount",
                "tax",
                "total_amount",
                "created_at",
            ]
        ],
        use_container_width=True,
    )

    st.write(
        "DEBUG Revenue:",
        df["total"].sum()
    )

    # ==========================================================================
    # SALES DATAFRAME
    # ==========================================================================

    sales_df = df.copy()

    # Convert numeric columns
    for col in [
        "total",
        "total_amount",
        "discount",
        "tax",
        "subtotal",
        "paid_amount",
    ]:
        if col in sales_df.columns:
            sales_df[col] = pd.to_numeric(
                sales_df[col],
                errors="coerce",
            ).fillna(0)

    # Cashier name
    sales_df["Cashier"] = sales_df["users"].apply(
        lambda u: cashier_name(u) if isinstance(u, dict) else "Unknown"
    )

    # Date
    sales_df["created_at"] = pd.to_datetime(
        sales_df["created_at"],
        errors="coerce",
        utc=True,
    )

    if not sales_df.empty:

        sales_df["created_at"] = (
            sales_df["created_at"]
            .dt.tz_convert(
                "Asia/Yangon"
            )
            .dt.tz_localize(None)
        )

    # ==========================================================================
    # SALES SUMMARY
    # ==========================================================================

    st.subheader(
        "📊 Sales Summary"
    )

    total_sales = safe_number(
        sales_df["total"].sum()
    )

    total_subtotal = safe_number(
        sales_df["subtotal"].sum()
    )

    total_discount = safe_number(
        sales_df["discount"].sum()
    )

    total_tax = safe_number(
        sales_df["tax"].sum()
    )

    total_amount = safe_number(
        sales_df["total_amount"].sum()
    )

    transaction_count = len(sales_df)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "🧾 Transactions",
        transaction_count,
    )

    c2.metric(
        "💰 Total Sales",
        f"{total_sales:,.0f} MMK",
    )

    c3.metric(
        "🏷 Discount",
        f"{total_discount:,.0f} MMK",
    )

    c4.metric(
        "🧾 Subtotal",
        f"{total_subtotal:,.0f} MMK",
    )

    c5.metric(
        "📊 Total Amount",
        f"{total_amount:,.0f} MMK",
    )

    st.divider()

    # ==========================================================================
    # PAYMENT METHOD BREAKDOWN
    # ==========================================================================

    st.subheader(
        "💳 Payment Method Breakdown"
    )

    payment_df = (
        sales_df
        .groupby("payment_method", dropna=False)
        .agg(
            Count=("id", "count"),
            Total=("total", "sum"),
        )
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    if not payment_df.empty:

        payment_display = payment_df.copy()

        payment_display["payment_method"] = (
            payment_display["payment_method"]
            .fillna("Unknown")
        )

        payment_display["Total"] = payment_display["Total"].apply(
            lambda x: f"{safe_number(x):,.0f} MMK"
        )

        show_table(
            payment_display
        )

    st.divider()

    # ==========================================================================
    # CASHIER PERFORMANCE
    # ==========================================================================

    st.subheader(
        "👤 Cashier Performance"
    )

    cashier_df = (
        sales_df
        .groupby("Cashier", dropna=False)
        .agg(
            Transactions=("id", "count"),
            Total=("total", "sum"),
        )
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    if not cashier_df.empty:

        cashier_display = cashier_df.copy()

        cashier_display["Cashier"] = (
            cashier_display["Cashier"]
            .fillna("Unknown")
        )

        cashier_display["Total"] = cashier_display["Total"].apply(
            lambda x: f"{safe_number(x):,.0f} MMK"
        )

        show_table(
            cashier_display
        )

    st.divider()

    # ==========================================================================
    # TRANSACTION DETAIL
    # ==========================================================================

    st.subheader(
        "📋 Transaction Detail"
    )

    detail_columns = [
        "created_at",
        "id",
        "Cashier",
        "payment_method",
        "subtotal",
        "discount",
        "tax",
        "total",
    ]

    detail_df = sales_df[
        [
            col
            for col in detail_columns
            if col in sales_df.columns
        ]
    ].copy()

    if "created_at" in detail_df.columns:

        detail_df["created_at"] = (
            detail_df["created_at"]
            .dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    for col in [
        "subtotal",
        "discount",
        "tax",
        "total",
    ]:

        if col in detail_df.columns:

            detail_df[col] = detail_df[col].apply(
                lambda x: f"{safe_number(x):,.0f}"
            )

    detail_df.columns = [
        "Date",
        "Sale ID",
        "Cashier",
        "Payment Method",
        "Subtotal",
        "Discount",
        "Tax",
        "Total",
    ]

    show_table(
        detail_df
    )

    # ==========================================================================
    # PRODUCT SALES
    # ==========================================================================

    # Load sale items
    sale_ids = sales_df["id"].tolist()

    if sale_ids:

        sale_items = get_sale_items(
            sale_ids
        )

        if sale_items:

            product_ids = []

            for item in sale_items:

                pid = item.get(
                    "product_id"
                )

                if pid is not None:

                    try:

                        product_ids.append(
                            int(pid)
                        )

                    except Exception:

                        pass

            products = get_products(
                product_ids
            )

            product_df = build_product_sales_dataframe(
                sales,
                sale_items,
                products,
            )

            render_product_sales_report(
                product_df
            )

        else:

            st.info(
                "No sale items found for this date range."
            )

    # ==========================================================================
    # EXPORT
    # ==========================================================================

    st.divider()

    st.subheader(
        "📤 Export Data"
    )

    export_col1, export_col2, export_col3 = st.columns(3)

    # Export Sales Data
    with export_col1:

        if st.button(
            "📊 Export Sales Data (Excel)",
            use_container_width=True,
        ):

            export_df = sales_df.copy()

            if "created_at" in export_df.columns:

                export_df["created_at"] = (
                    export_df["created_at"]
                    .dt.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="xlsxwriter",
            ) as writer:

                export_df.to_excel(
                    writer,
                    sheet_name="Sales",
                    index=False,
                )

            output.seek(0)

            st.download_button(
                label="Download Sales Excel",
                data=output,
                file_name=(
                    f"sales_report_"
                    f"{start_date}_to_{end_date}.xlsx"
                ),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_sales_excel",
            )

    # Export Product Data
    with export_col2:

        if st.button(
            "📦 Export Product Data (Excel)",
            use_container_width=True,
        ):

            if "product_df" in locals() and not product_df.empty:

                export_df = product_df.copy()

                if "Date" in export_df.columns:

                    export_df["Date"] = (
                        export_df["Date"]
                        .dt.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )

                output = BytesIO()

                with pd.ExcelWriter(
                    output,
                    engine="xlsxwriter",
                ) as writer:

                    export_df.to_excel(
                        writer,
                        sheet_name="Product Sales",
                        index=False,
                    )

                output.seek(0)

                st.download_button(
                    label="Download Product Excel",
                    data=output,
                    file_name=(
                        f"product_sales_report_"
                        f"{start_date}_to_{end_date}.xlsx"
                    ),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_product_excel",
                )

            else:

                st.warning(
                    "No product data to export."
                )

    # Export Summary JSON
    with export_col3:

        if st.button(
            "📄 Export Summary (JSON)",
            use_container_width=True,
        ):

            summary = {
                "date_range": {
                    "start": str(start_date),
                    "end": str(end_date),
                },
                "transactions": transaction_count,
                "total_sales": total_sales,
                "total_discount": total_discount,
                "total_tax": total_tax,
                "total_amount": total_amount,
                "payment_breakdown": (
                    payment_df.to_dict("records")
                    if not payment_df.empty
                    else []
                ),
                "cashier_performance": (
                    cashier_df.to_dict("records")
                    if not cashier_df.empty
                    else []
                ),
            }

            json_output = json.dumps(
                summary,
                indent=2,
                default=str,
            )

            st.download_button(
                label="Download Summary JSON",
                data=json_output,
                file_name=(
                    f"summary_report_"
                    f"{start_date}_to_{end_date}.json"
                ),
                mime="application/json",
                key="download_summary_json",
            )
