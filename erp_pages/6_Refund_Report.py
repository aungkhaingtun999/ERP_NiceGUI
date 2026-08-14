# ==============================================================================
# REFUND REPORT
# ERP ENTERPRISE REFUND REPORT v4.0
#
# Tax-aware Refund Reporting
#
# Supports:
#   refund_net_amount
#   refund_tax_amount
#   refund_total_amount
#
# Compatible with:
#   refund_process_rpc_v4
# ==============================================================================

import io
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database import db
from auth import require_login

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from utils.ui import show_table


# ==============================================================================
# AUTH
# ==============================================================================

user = require_login()

st.set_page_config(
    page_title="Refund Report",
    layout="wide",
)

st.title("📊 Refund Report v4.0")


# ==============================================================================
# SESSION STATE
# ==============================================================================

if "selected_refund_id" not in st.session_state:
    st.session_state.selected_refund_id = None


# ==============================================================================
# LOAD REPORT
# ==============================================================================

@st.cache_data(ttl=60)
def get_refund_report():

    response = (
        db()
        .table("refund_report_view")
        .select("*")
        .order("refund_date", desc=True)
        .execute()
    )

    return pd.DataFrame(response.data or [])


df = get_refund_report()


# ==============================================================================
# EMPTY DATA
# ==============================================================================

if df.empty:

    st.info("No refund records found.")

    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

    st.stop()


# ==============================================================================
# SAFE NUMERIC COLUMNS
# ==============================================================================

numeric_columns = [
    "quantity",
    "unit_price",
    "item_total",
    "refund_net_amount",
    "refund_tax_amount",
    "refund_total_amount",
    "refund_amount",
]


for col in numeric_columns:

    if col not in df.columns:
        df[col] = 0

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce",
    ).fillna(0)


# ==============================================================================
# DATE
# ==============================================================================

df["refund_date"] = pd.to_datetime(
    df["refund_date"],
    errors="coerce",
)


# ==============================================================================
# NORMALIZE STATUS
# ==============================================================================

if "status" not in df.columns:
    df["status"] = "COMPLETED"

df["status"] = (
    df["status"]
    .fillna("")
    .astype(str)
    .str.upper()
)


# ==============================================================================
# NORMALIZE TEXT COLUMNS
# ==============================================================================

text_columns = [
    "invoice_no",
    "cashier_name",
    "warehouse_name",
    "product_name",
    "processed_by",
    "reason",
]

for col in text_columns:

    if col not in df.columns:
        df[col] = ""

    df[col] = df[col].fillna("").astype(str)


# ==============================================================================
# REFUND TOTAL FALLBACK
# ==============================================================================

# v4 uses refund_total_amount.
# Older records may only have item_total.

df["report_net"] = df["refund_net_amount"]

df["report_tax"] = df["refund_tax_amount"]

df["report_total"] = df["refund_total_amount"]


# Legacy fallback
df.loc[
    df["report_total"] == 0,
    "report_total"
] = df.loc[
    df["report_total"] == 0,
    "item_total"
]


# If old rows do not contain net amount,
# use item_total as net fallback.

df.loc[
    df["report_net"] == 0,
    "report_net"
] = df.loc[
    df["report_net"] == 0,
    "item_total"
]


# ==============================================================================
# SIDEBAR FILTER
# ==============================================================================

st.sidebar.header("🔍 Report Filter")


invoice_search = st.sidebar.text_input(
    "Invoice No"
)


cashier_filter = st.sidebar.multiselect(
    "Cashier",
    sorted(
        df["cashier_name"]
        .dropna()
        .unique()
        .tolist()
    ),
)


warehouse_filter = st.sidebar.multiselect(
    "Warehouse",
    sorted(
        df["warehouse_name"]
        .dropna()
        .unique()
        .tolist()
    ),
)


status_filter = st.sidebar.multiselect(
    "Status",
    ["PENDING", "COMPLETED", "REJECTED"],
)


min_date = df["refund_date"].min()

if pd.isna(min_date):
    min_date = pd.Timestamp.today()


from_date = st.sidebar.date_input(
    "From Date",
    min_date.date(),
)


to_date = st.sidebar.date_input(
    "To Date",
    date.today(),
)


# ==============================================================================
# APPLY FILTER
# ==============================================================================

filtered = df.copy()


filtered = filtered[
    (
        filtered["refund_date"].dt.date
        >= from_date
    )
    &
    (
        filtered["refund_date"].dt.date
        <= to_date
    )
]


if invoice_search:

    filtered = filtered[
        filtered["invoice_no"].str.contains(
            invoice_search,
            case=False,
            na=False,
        )
    ]


if cashier_filter:

    filtered = filtered[
        filtered["cashier_name"].isin(
            cashier_filter
        )
    ]


if warehouse_filter:

    filtered = filtered[
        filtered["warehouse_name"].isin(
            warehouse_filter
        )
    ]


if status_filter:

    filtered = filtered[
        filtered["status"].isin(
            status_filter
        )
    ]


# ==============================================================================
# REFRESH
# ==============================================================================

if st.sidebar.button("🔄 Refresh Data"):

    st.cache_data.clear()
    st.rerun()


# ==============================================================================
# KPI
# ==============================================================================

total_refunds = filtered["refund_id"].nunique()


pending = (
    filtered["status"] == "PENDING"
).sum()


completed = (
    filtered["status"] == "COMPLETED"
).sum()


rejected = (
    filtered["status"] == "REJECTED"
).sum()


total_net = filtered["report_net"].sum()

total_tax = filtered["report_tax"].sum()

total_refund = filtered["report_total"].sum()


# ==============================================================================
# KPI CARDS
# ==============================================================================

c1, c2, c3, c4, c5 = st.columns(5)


with c1:

    st.metric(
        "Total Refunds",
        f"{total_refunds:,}",
    )


with c2:

    st.metric(
        "Pending",
        f"{pending:,}",
    )


with c3:

    st.metric(
        "Completed",
        f"{completed:,}",
    )


with c4:

    st.metric(
        "Rejected",
        f"{rejected:,}",
    )


with c5:

    st.metric(
        "Refund Total",
        f"{total_refund:,.2f} MMK",
    )


# ==============================================================================
# FINANCIAL SUMMARY
# ==============================================================================

st.divider()

st.subheader("💰 Refund Financial Summary")


f1, f2, f3 = st.columns(3)


with f1:

    st.metric(
        "Refund Net",
        f"{total_net:,.2f} MMK",
    )


with f2:

    st.metric(
        "Refund Tax",
        f"{total_tax:,.2f} MMK",
    )


with f3:

    st.metric(
        "Refund Total",
        f"{total_refund:,.2f} MMK",
    )


# ==============================================================================
# PDF GENERATOR
# ==============================================================================

def create_refund_pdf(
    header,
    items,
):

    buffer = io.BytesIO()


    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
    )


    styles = getSampleStyleSheet()


    content = []


    content.append(
        Paragraph(
            "REFUND REPORT",
            styles["Title"],
        )
    )


    content.append(
        Spacer(1, 12)
    )


    header_text = f"""
    <b>Refund ID:</b> {header.get('refund_id', '')}<br/>
    <b>Invoice:</b> {header.get('invoice_no', '')}<br/>
    <b>Status:</b> {header.get('status', '')}<br/>
    <b>Cashier:</b> {header.get('cashier_name', '')}<br/>
    <b>Warehouse:</b> {header.get('warehouse_name', '')}<br/>
    <b>Reason:</b> {header.get('reason', '')}
    """


    content.append(
        Paragraph(
            header_text,
            styles["Normal"],
        )
    )


    content.append(
        Spacer(1, 12)
    )


    table_data = [
        [
            "Product",
            "Qty",
            "Price",
            "Net",
            "Tax",
            "Total",
        ]
    ]


    total_net = 0
    total_tax = 0
    total_amount = 0


    for item in items:

        net = float(
            item.get(
                "refund_net_amount",
                item.get("item_total", 0),
            )
            or 0
        )


        tax = float(
            item.get(
                "refund_tax_amount",
                0,
            )
            or 0
        )


        total = float(
            item.get(
                "refund_total_amount",
                item.get("item_total", 0),
            )
            or 0
        )


        total_net += net
        total_tax += tax
        total_amount += total


        table_data.append(
            [
                item.get(
                    "product_name",
                    "",
                ),
                item.get(
                    "quantity",
                    0,
                ),
                f"{float(item.get('unit_price', 0) or 0):,.2f}",
                f"{net:,.2f}",
                f"{tax:,.2f}",
                f"{total:,.2f}",
            ]
        )


    table_data.append(
        [
            "TOTAL",
            "",
            "",
            f"{total_net:,.2f}",
            f"{total_tax:,.2f}",
            f"{total_amount:,.2f}",
        ]
    )


    table = Table(
        table_data,
        repeatRows=1,
    )


    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
            ]
        )
    )


    content.append(table)


    doc.build(content)


    buffer.seek(0)

    return buffer


# ==============================================================================
# REFUND DETAIL DIALOG
# ==============================================================================

@st.dialog("Refund Detail")
def refund_detail_dialog(refund_id):

    response = (
        db()
        .table("refund_header_view")
        .select("*")
        .eq("refund_id", refund_id)
        .single()
        .execute()
    )


    header = response.data


    if not header:

        st.error("Refund header not found.")

        return


    st.subheader(
        f"Refund ID : {header['refund_id']}"
    )


    c1, c2 = st.columns(2)


    with c1:

        st.write(
            f"**Invoice:** "
            f"{header.get('invoice_no', '-')}"
        )

        st.write(
            f"**Cashier:** "
            f"{header.get('cashier_name', '-')}"
        )

        st.write(
            f"**Warehouse:** "
            f"{header.get('warehouse_name', '-')}"
        )


    with c2:

        st.write(
            f"**Status:** "
            f"{header.get('status', '-')}"
        )

        st.write(
            f"**Date:** "
            f"{header.get('refund_date', '-')}"
        )

        st.write(
            f"**Reason:** "
            f"{header.get('reason', '-')}"
        )


    st.divider()


    items_response = (
        db()
        .table("refund_detail_view")
        .select("*")
        .eq("refund_id", refund_id)
        .execute()
    )


    items = items_response.data or []


    if not items:

        st.warning(
            "No refund item records found."
        )

        return


    item_df = pd.DataFrame(items)


    # --------------------------------------------------
    # Numeric normalization
    # --------------------------------------------------

    for col in [
        "quantity",
        "unit_price",
        "item_total",
        "refund_net_amount",
        "refund_tax_amount",
        "refund_total_amount",
    ]:

        if col not in item_df.columns:

            item_df[col] = 0


        item_df[col] = pd.to_numeric(
            item_df[col],
            errors="coerce",
        ).fillna(0)


    # --------------------------------------------------
    # Display
    # --------------------------------------------------

    display_df = pd.DataFrame(
        {
            "Product":
                item_df["product_name"],

            "Qty":
                item_df["quantity"],

            "Unit Price":
                item_df["unit_price"],

            "Refund Net":
                item_df["refund_net_amount"],

            "Refund Tax":
                item_df["refund_tax_amount"],

            "Refund Total":
                item_df["refund_total_amount"],
        }
    )


    show_table(display_df)


    detail_net = item_df[
        "refund_net_amount"
    ].sum()


    detail_tax = item_df[
        "refund_tax_amount"
    ].sum()


    detail_total = item_df[
        "refund_total_amount"
    ].sum()


    st.divider()


    d1, d2, d3 = st.columns(3)


    with d1:

        st.metric(
            "Net",
            f"{detail_net:,.2f} MMK",
        )


    with d2:

        st.metric(
            "Tax",
            f"{detail_tax:,.2f} MMK",
        )


    with d3:

        st.metric(
            "Total",
            f"{detail_total:,.2f} MMK",
        )


    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    pdf_file = create_refund_pdf(
        header,
        items,
    )


    st.download_button(
        "📄 PDF",
        pdf_file,
        f"refund_{refund_id}.pdf",
        "application/pdf",
    )


    # --------------------------------------------------
    # HTML
    # --------------------------------------------------

    html_table = display_df.to_html(
        index=False,
    )


    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Refund {refund_id}</title>
    </head>

    <body>

        <h2>Refund Report</h2>

        <p>
            <b>Refund ID:</b> {refund_id}<br>
            <b>Invoice:</b> {header.get('invoice_no', '')}<br>
            <b>Status:</b> {header.get('status', '')}
        </p>

        {html_table}

        <h3>
            Net: {detail_net:,.2f} MMK
        </h3>

        <h3>
            Tax: {detail_tax:,.2f} MMK
        </h3>

        <h3>
            Total: {detail_total:,.2f} MMK
        </h3>

    </body>
    </html>
    """


    st.download_button(
        "🖨️ HTML",
        html_content,
        f"refund_{refund_id}.html",
        "text/html",
    )


# ==============================================================================
# REFUND LIST
# ==============================================================================

st.divider()

st.subheader("Refund Details")


if filtered.empty:

    st.warning(
        "No refund records match the selected filters."
    )

else:

    for _, row in filtered.iterrows():

        c1, c2, c3, c4 = st.columns(
            [1, 3, 2, 2]
        )


        with c1:

            st.write(
                row["refund_id"]
            )


        with c2:

            st.write(
                row["invoice_no"]
            )


        with c3:

            st.write(
                f"{row['report_total']:,.2f} MMK"
            )


        with c4:

            if st.button(
                "👁️ View",
                key=(
                    f"view_"
                    f"{row['refund_id']}_"
                    f"{row.name}"
                ),
            ):

                refund_detail_dialog(
                    int(row["refund_id"])
                )


# ==============================================================================
# MAIN TABLE
# ==============================================================================

display_columns = [
    "refund_id",
    "invoice_no",
    "refund_date",
    "status",
    "product_name",
    "quantity",
    "unit_price",
    "refund_net_amount",
    "refund_tax_amount",
    "refund_total_amount",
    "cashier_name",
    "processed_by",
    "warehouse_name",
    "reason",
]


for col in display_columns:

    if col not in filtered.columns:

        filtered[col] = ""


report_table = filtered[
    display_columns
].copy()


report_table = report_table.rename(
    columns={
        "refund_id": "Refund ID",
        "invoice_no": "Invoice",
        "refund_date": "Date",
        "status": "Status",
        "product_name": "Product",
        "quantity": "Qty",
        "unit_price": "Unit Price",
        "refund_net_amount": "Refund Net",
        "refund_tax_amount": "Refund Tax",
        "refund_total_amount": "Refund Total",
        "cashier_name": "Cashier",
        "processed_by": "Processed By",
        "warehouse_name": "Warehouse",
        "reason": "Reason",
    }
)


show_table(report_table)


# ==============================================================================
# ANALYTICS
# ==============================================================================

st.divider()

st.subheader("📊 Refund Analytics")


if not filtered.empty:

    # --------------------------------------------------
    # Daily Refund Total
    # --------------------------------------------------

    daily = (
        filtered
        .groupby(
            filtered["refund_date"].dt.date
        )["report_total"]
        .sum()
    )


    st.line_chart(
        daily
    )


    col1, col2 = st.columns(2)


    # --------------------------------------------------
    # Top Products
    # --------------------------------------------------

    with col1:

        st.subheader(
            "🏆 Top 10 Products"
        )


        top_products = (
            filtered
            .groupby("product_name")[
                "quantity"
            ]
            .sum()
            .sort_values(
                ascending=False
            )
            .head(10)
        )


        st.bar_chart(
            top_products
        )


    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    with col2:

        st.subheader(
            "📊 Status"
        )


        status_data = (
            filtered
            .groupby("status")[
                "refund_id"
            ]
            .nunique()
        )


        if not status_data.empty:

            st.plotly_chart(
                px.pie(
                    values=status_data.values,
                    names=status_data.index,
                    title="Refund Status",
                ),
                use_container_width=True,
            )


    # --------------------------------------------------
    # Cashier Ranking
    # --------------------------------------------------

    st.subheader(
        "👤 Cashier Ranking (Top 5)"
    )


    cashier_ranking = (
        filtered
        .groupby("cashier_name")[
            "report_total"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(5)
    )


    st.bar_chart(
        cashier_ranking
    )


else:

    st.warning(
        "No data for analytics."
    )


# ==============================================================================
# EXPORT
# ==============================================================================

st.divider()

st.subheader("📥 Export")


export_df = filtered.copy()


# Human-readable export names

export_df = export_df.rename(
    columns={
        "refund_id": "Refund ID",
        "invoice_no": "Invoice",
        "refund_date": "Refund Date",
        "status": "Status",
        "product_name": "Product",
        "quantity": "Quantity",
        "unit_price": "Unit Price",
        "refund_net_amount": "Refund Net",
        "refund_tax_amount": "Refund Tax",
        "refund_total_amount": "Refund Total",
        "cashier_name": "Cashier",
        "processed_by": "Processed By",
        "warehouse_name": "Warehouse",
        "reason": "Reason",
    }
)


# ==============================================================================
# EXCEL
# ==============================================================================

excel_buffer = io.BytesIO()


with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl",
) as writer:

    export_df.to_excel(
        writer,
        index=False,
        sheet_name="Refund Report",
    )


excel_buffer.seek(0)


st.download_button(
    "📥 Excel",
    excel_buffer.getvalue(),
    "refund_report_v4.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
