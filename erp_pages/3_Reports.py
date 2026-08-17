# ==============================================================================
# erp_pages/3_Reports.py
#
# ERP ENTERPRISE SALES ANALYTICS REPORT v5.0
#
# Sales Summary + Product Sales + Cashier + Payment + Export
#
# READ-ONLY REPORT
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
    Load sale_items for selected sales.
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
            sale_id = int(sale_id)
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

    product_df = pd.DataFrame(rows)

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
    # SALES DATAFRAME
    # ==========================================================================

    df = pd.DataFrame(
        sales
    )

    # ==========================================================================
    # NORMALIZE TOTAL
    # ==========================================================================
    #
    # sales.total is the canonical sale total.
    #

    if "total" in df.columns:

        df["total"] = (
            pd.to_numeric(
                df["total"],
                errors="coerce",
            )
            .fillna(0.0)
        )

    elif "total_amount" in df.columns:

        df["total"] = (
            pd.to_numeric(
                df["total_amount"],
                errors="coerce",
            )
            .fillna(0.0)
        )

    else:

        df["total"] = 0.0

    # ==========================================================================
    # SALE IDS
    # ==========================================================================

    sale_ids = []

    for sale in sales:

        sale_id = sale.get("id")

        if sale_id is not None:

            try:
                sale_ids.append(
                    int(sale_id)
                )
            except Exception:
                pass

    # ==========================================================================
    # LOAD SALE ITEMS
    # ==========================================================================

    sale_items = get_sale_items(
        sale_ids
    )

    # ==========================================================================
    # LOAD PRODUCTS
    # ==========================================================================

    product_ids = []

    for item in sale_items:

        product_id = item.get(
            "product_id"
        )

        if product_id is not None:

            try:
                product_ids.append(
                    int(product_id)
                )
            except Exception:
                pass

    products = get_products(
        product_ids
    )

    # ==========================================================================
    # BUILD PRODUCT DATAFRAME
    # ==========================================================================

    product_df = build_product_sales_dataframe(
        sales,
        sale_items,
        products,
    )

    # ==========================================================================
    # SALE SUMMARY KPI
    # ==========================================================================

    total_sales_amount = safe_number(
        df["total"].sum()
    )

    total_transactions = len(df)

    total_discount = safe_number(
        df["discount"].sum()
    )

    total_tax = safe_number(
        df["tax"].sum()
    )

    paid_amount = safe_number(
        df["paid_amount"].sum()
    )

    # ==========================================================================
    # KPI ROW
    # ==========================================================================

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(
        "💰 Total Sales",
        f"{total_sales_amount:,.0f} MMK",
    )

    k2.metric(
        "🧾 Transactions",
        total_transactions,
    )

    k3.metric(
        "🏷 Discount",
        f"{total_discount:,.0f} MMK",
    )

    k4.metric(
        "🧾 Tax",
        f"{total_tax:,.0f} MMK",
    )

    k5.metric(
        "💳 Paid",
        f"{paid_amount:,.0f} MMK",
    )

    st.divider()

    # ==========================================================================
    # PAYMENT METHOD BREAKDOWN
    # ==========================================================================

    st.markdown(
        "### 💳 Payment Method Breakdown"
    )

    payment_counts = (
        df["payment_method"]
        .value_counts()
    )

    payment_amounts = (
        df.groupby("payment_method")["total"]
        .sum()
    )

    payment_df = pd.DataFrame({
        "Payment Method": payment_counts.index,
        "Transactions": payment_counts.values,
        "Amount": payment_amounts.values,
    })

    payment_df["Amount"] = payment_df["Amount"].apply(
        lambda x: f"{safe_number(x):,.0f} MMK"
    )

    show_table(
        payment_df
    )

    st.divider()

    # ==========================================================================
    # CASHIER PERFORMANCE
    # ==========================================================================

    st.markdown(
        "### 👤 Cashier Performance"
    )

    cashier_data = []

    for sale in sales:

        user = sale.get("users")
        cashier = cashier_name(user)

        cashier_data.append({
            "cashier": cashier,
            "total": safe_number(
                sale.get("total")
            ),
        })

    cashier_df = pd.DataFrame(
        cashier_data
    )

    if not cashier_df.empty:

        cashier_summary = (
            cashier_df
            .groupby("cashier")["total"]
            .agg(["count", "sum"])
            .reset_index()
        )

        cashier_summary.columns = [
            "Cashier",
            "Transactions",
            "Total Sales",
        ]

        cashier_summary["Total Sales"] = (
            cashier_summary["Total Sales"]
            .apply(
                lambda x: f"{safe_number(x):,.0f} MMK"
            )
        )

        show_table(
            cashier_summary
        )

    st.divider()

    # ==========================================================================
    # PRODUCT SALES REPORT
    # ==========================================================================

    render_product_sales_report(
        product_df
    )

    # ==========================================================================
    # EXPORT
    # ==========================================================================

    st.divider()

    st.markdown(
        "### 📥 Export Reports"
    )

    export_col1, export_col2, export_col3 = st.columns(3)

    # --------------------------------------------------------------------------
    # Export Sales Summary
    # --------------------------------------------------------------------------

    with export_col1:

        if st.button(
            "📊 Export Sales Summary",
            use_container_width=True,
        ):

            try:

                export_data = []

                for sale in sales:

                    user = sale.get("users")
                    cashier = cashier_name(user)

                    export_data.append({
                        "Sale ID": sale.get("id"),
                        "Date": sale.get("created_at"),
                        "Cashier": cashier,
                        "Payment Method": sale.get(
                            "payment_method"
                        ),
                        "Subtotal": safe_number(
                            sale.get("subtotal")
                        ),
                        "Discount": safe_number(
                            sale.get("discount")
                        ),
                        "Tax": safe_number(
                            sale.get("tax")
                        ),
                        "Total": safe_number(
                            sale.get("total")
                        ),
                        "Paid Amount": safe_number(
                            sale.get("paid_amount")
                        ),
                    })

                export_df = pd.DataFrame(
                    export_data
                )

                if not export_df.empty:

                    if "Date" in export_df.columns:

                        export_df["Date"] = (
                            pd.to_datetime(
                                export_df["Date"],
                                errors="coerce",
                                utc=True,
                            )
                            .dt.tz_convert(
                                "Asia/Yangon"
                            )
                            .dt.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )

                    csv = (
                        export_df
                        .to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8-sig"
                        )
                    )

                    st.download_button(
                        label="⬇ Download CSV",
                        data=csv,
                        file_name=(
                            f"sales_summary_"
                            f"{start_date}_"
                            f"{end_date}.csv"
                        ),
                        mime="text/csv",
                        key="export_sales_summary",
                    )

                else:

                    st.warning(
                        "No data to export"
                    )

            except Exception as e:

                st.error(
                    f"Export error: {e}"
                )

    # --------------------------------------------------------------------------
    # Export Product Sales
    # --------------------------------------------------------------------------

    with export_col2:

        if st.button(
            "📦 Export Product Sales",
            use_container_width=True,
        ):

            try:

                if not product_df.empty:

                    export_df = product_df.copy()

                    if "Date" in export_df.columns:

                        export_df["Date"] = (
                            export_df["Date"]
                            .dt.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )

                    csv = (
                        export_df
                        .to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8-sig"
                        )
                    )

                    st.download_button(
                        label="⬇ Download CSV",
                        data=csv,
                        file_name=(
                            f"product_sales_"
                            f"{start_date}_"
                            f"{end_date}.csv"
                        ),
                        mime="text/csv",
                        key="export_product_sales",
                    )

                else:

                    st.warning(
                        "No product sales data to export"
                    )

            except Exception as e:

                st.error(
                    f"Export error: {e}"
                )

    # --------------------------------------------------------------------------
    # Export Product Summary
    # --------------------------------------------------------------------------

    with export_col3:

        if st.button(
            "🏆 Export Product Summary",
            use_container_width=True,
        ):

            try:

                if not product_df.empty:

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

                    csv = (
                        product_summary
                        .to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8-sig"
                        )
                    )

                    st.download_button(
                        label="⬇ Download CSV",
                        data=csv,
                        file_name=(
                            f"product_summary_"
                            f"{start_date}_"
                            f"{end_date}.csv"
                        ),
                        mime="text/csv",
                        key="export_product_summary",
                    )

                else:

                    st.warning(
                        "No product data to export"
                    )

            except Exception as e:

                st.error(
                    f"Export error: {e}"
                )

    # ==========================================================================
    # FOOTER
    # ==========================================================================

    st.divider()

    st.caption(
        f"📊 Report generated for {start_date} → {end_date} | "
        f"Total Sales: {total_transactions} transactions | "
        f"Total Revenue: {total_sales_amount:,.0f} MMK"
    )
