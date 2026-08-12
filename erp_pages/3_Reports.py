#==============================================================================

erp_pages/3_Reports.py

ERP ENTERPRISE SALES ANALYTICS REPORT v4.1

Sales Summary + Cashier + Payment + Export

==============================================================================

from future import annotations

from datetime import date, timedelta
from io import BytesIO
import json

import pandas as pd
import streamlit as st

from erp_core.base_repo import db

from utils.ui import show_table

#==============================================================================

HELPERS

==============================================================================

def safe_number(value):
try:
return float(value or 0)
except Exception:
return 0.0

#==============================================================================

CASHIER NAME

==============================================================================

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

#==============================================================================

RUN

==============================================================================

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

# Myanmar local date.
# Avoid relying on server date directly.
try:
    from utils.timezone import get_myanmar_today

    today = get_myanmar_today()

    if not isinstance(today, date):
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

# --------------------------------------------------------------------------
# Invalid date range
# --------------------------------------------------------------------------

if start_date > end_date:

    st.error(
        "Start Date cannot be later than End Date."
    )

    return

# --------------------------------------------------------------------------
# IMPORTANT
#
# Database created_at is timestamptz / UTC.
#
# Convert Myanmar local date boundaries to UTC before querying.
# --------------------------------------------------------------------------

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

except Exception:

    # Fallback.
    start_utc = (
        f"{start_date.isoformat()}T00:00:00+00:00"
    )

    end_utc = (
        f"{(end_date + timedelta(days=1)).isoformat()}"
        "T00:00:00+00:00"
    )

# ==========================================================================
# LOAD SALES
# ==========================================================================

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

        # ------------------------------------------------------------------
        # Some ERP schemas have total_amount but not total.
        # Retry using the confirmed sales columns.
        # ------------------------------------------------------------------

        try:

            response = (
                db()
                .table("sales")
                .select(
                    """
                    id,
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

        except Exception as retry_error:

            st.error(
                f"Sales loading error: {retry_error}"
            )

            return []

sales = get_sales(
    start_utc,
    end_utc,
)

# ==========================================================================
# NO DATA
# ==========================================================================

if not sales:

    st.warning(
        "No sales data found for the selected date range."
    )

    st.caption(
        f"Checked: {start_date} → {end_date}"
    )

    return

# ==========================================================================
# DATAFRAME
# ==========================================================================

df = pd.DataFrame(
    sales
)

# ==========================================================================
# NORMALIZE SALES AMOUNT
# ==========================================================================

# --------------------------------------------------------------------------
# Your confirmed database contains total_amount.
# If total exists, use it.
# Otherwise use total_amount.
# --------------------------------------------------------------------------

if "total" not in df.columns:

    if "total_amount" in df.columns:

        df["total"] = df[
            "total_amount"
        ]

    else:

        df["total"] = 0.0

else:

    # If total exists but is completely missing,
    # fall back to total_amount.
    if (
        df["total"].isna().all()
        and "total_amount" in df.columns
    ):

        df["total"] = df[
            "total_amount"
        ]

# ==========================================================================
# MONEY COLUMNS
# ==========================================================================

money_columns = [
    "total",
    "total_amount",
    "discount",
    "tax",
    "subtotal",
    "paid_amount",
]

for col in money_columns:

    if col in df.columns:

        df[col] = (
            pd.to_numeric(
                df[col],
                errors="coerce",
            )
            .fillna(0.0)
        )

# ==========================================================================
# CREATED AT
# ==========================================================================

if "created_at" not in df.columns:

    st.error(
        "Sales data does not contain created_at."
    )

    return

df["created_at"] = pd.to_datetime(
    df["created_at"],
    errors="coerce",
    utc=True,
)

df = df[
    df["created_at"].notna()
].copy()

if df.empty:

    st.warning(
        "Sales records were found, but created_at values are invalid."
    )

    return

# --------------------------------------------------------------------------
# Convert UTC → Myanmar time
# --------------------------------------------------------------------------

df["created_at"] = (
    df["created_at"]
    .dt.tz_convert("Asia/Yangon")
    .dt.tz_localize(None)
)

# ==========================================================================
# CASHIER
# ==========================================================================

if "users" in df.columns:

    df["Cashier"] = (
        df["users"]
        .apply(cashier_name)
    )

else:

    df["Cashier"] = "SYSTEM"

# ==========================================================================
# FILTERS
# ==========================================================================

st.sidebar.subheader(
    "🔎 Filters"
)

cashier_values = (
    df["Cashier"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .replace("", "Unknown")
    .unique()
    .tolist()
)

cashier_options = (
    ["All"]
    + sorted(cashier_values)
)

selected_cashier = st.sidebar.selectbox(
    "Cashier",
    cashier_options,
    key="reports_cashier_filter",
)

if selected_cashier != "All":

    df = df[
        df["Cashier"]
        == selected_cashier
    ].copy()

# ==========================================================================
# EMPTY AFTER FILTER
# ==========================================================================

if df.empty:

    st.warning(
        "No data after filter."
    )

    return

# ==========================================================================
# KPI
# ==========================================================================

revenue = safe_number(
    df["total"].sum()
)

discount = safe_number(
    df["discount"].sum()
    if "discount" in df.columns
    else 0
)

tax = safe_number(
    df["tax"].sum()
    if "tax" in df.columns
    else 0
)

bills = len(df)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "💰 Revenue",
    f"{revenue:,.0f} MMK",
)

c2.metric(
    "🧾 Bills",
    bills,
)

c3.metric(
    "🏷 Discount",
    f"{discount:,.0f} MMK",
)

c4.metric(
    "🧮 Tax",
    f"{tax:,.0f} MMK",
)

st.divider()

# ==========================================================================
# TABS
# ==========================================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📈 Sales Summary",
        "👨‍💼 Cashier",
        "💳 Payment",
        "📥 Export",
    ]
)

# ==========================================================================
# SALES SUMMARY
# ==========================================================================

with tab1:

    st.subheader(
        "Daily Sales"
    )

    daily = (
        df.groupby(
            df["created_at"].dt.date
        )["total"]
        .sum()
        .reset_index()
    )

    daily.columns = [
        "Date",
        "Sales",
    ]

    show_table(
        daily
    )

    st.subheader(
        "Monthly Sales"
    )

    monthly = (
        df.groupby(
            df["created_at"]
            .dt.to_period("M")
            .astype(str)
        )["total"]
        .sum()
        .reset_index()
    )

    monthly.columns = [
        "Month",
        "Sales",
    ]

    show_table(
        monthly
    )

# ==========================================================================
# CASHIER
# ==========================================================================

with tab2:

    cashier = (
        df.groupby(
            "Cashier"
        )
        .agg(
            Bills=("id", "count"),
            Sales=("total", "sum"),
        )
        .reset_index()
    )

    show_table(
        cashier
    )

# ==========================================================================
# PAYMENT
# ==========================================================================

with tab3:

    if "payment_method" in df.columns:

        payment = (
            df.assign(
                payment_method=(
                    df["payment_method"]
                    .fillna("Unknown")
                    .astype(str)
                    .replace("", "Unknown")
                )
            )
            .groupby(
                "payment_method"
            )
            .agg(
                Bills=("id", "count"),
                Amount=("total", "sum"),
            )
            .reset_index()
        )

        show_table(
            payment
        )

    else:

        st.info(
            "Payment method data is not available."
        )

# ==========================================================================
# EXPORT
# ==========================================================================

with tab4:

    export_df = df.copy()

    export_df.drop(
        columns=[
            "cashier_id",
            "users",
        ],
        errors="ignore",
        inplace=True,
    )

    # ----------------------------------------------------------------------
    # Make timezone-naive / Excel-safe datetime
    # ----------------------------------------------------------------------

    if "created_at" in export_df.columns:

        export_df["created_at"] = (
            pd.to_datetime(
                export_df["created_at"],
                errors="coerce",
            )
        )

    # ----------------------------------------------------------------------
    # Convert nested objects to JSON
    # ----------------------------------------------------------------------

    for col in export_df.columns:

        if export_df[col].dtype == "object":

            export_df[col] = (
                export_df[col]
                .apply(
                    lambda x:
                    json.dumps(
                        x,
                        ensure_ascii=False,
                    )
                    if isinstance(
                        x,
                        (dict, list),
                    )
                    else x
                )
            )

    export_df = export_df.fillna("")

    # ----------------------------------------------------------------------
    # CSV
    # ----------------------------------------------------------------------

    csv_data = (
        export_df
        .to_csv(
            index=False
        )
        .encode("utf-8-sig")
    )

    st.download_button(
        "⬇ Download CSV",
        data=csv_data,
        file_name="ERP_Sales_Report.csv",
        mime="text/csv",
        key="reports_download_csv",
    )

    # ----------------------------------------------------------------------
    # Excel
    # ----------------------------------------------------------------------

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Sales",
        )

    st.download_button(
        "⬇ Download Excel",
        data=output.getvalue(),
        file_name="ERP_Sales_Report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key="reports_download_excel",
    )

==============================================================================

DIRECT ENTRY

==============================================================================

if name == "main":
run()
