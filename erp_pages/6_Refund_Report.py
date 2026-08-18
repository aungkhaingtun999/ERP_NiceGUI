# ==============================================================================
# ERP ENTERPRISE REFUND REPORT v5.1
#
# TAX-AWARE + DATE RANGE + REJECTED SEPARATION
#
# IMPORTANT BUSINESS RULE
#
# ACTUAL REFUND TOTAL:
#     COMPLETED + APPROVED
#
# REJECTED:
#     NEVER INCLUDED IN REFUND TOTAL
#     SHOWN SEPARATELY AS REJECTED TOTAL
#
# PENDING:
#     NEVER INCLUDED IN REFUND TOTAL
#     SHOWN SEPARATELY AS PENDING TOTAL
#
# DATE:
#     FROM DATE -> TO DATE
#
# EXPORT:
#     PDF
#     EXCEL
#     CSV
#     HTML
#
# DATABASE VIEWS:
#     refund_report_view
#     refund_detail_view
#
# V4 AMOUNTS:
#     refund_net_amount
#     refund_tax_amount
#     refund_total_amount
# ==============================================================================


# ==============================================================================
# IMPORTS
# ==============================================================================

import io

from datetime import date, timedelta

import pandas as pd
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

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.pagesizes import A4

from reportlab.lib.enums import (
    TA_LEFT,
    TA_CENTER,
)


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="Refund Report",
    page_icon="↩️",
    layout="wide",
)


# ==============================================================================
# AUTH
# ==============================================================================

user = require_login()


# ==============================================================================
# BUSINESS STATUS RULE
# ==============================================================================

ACTUAL_REFUND_STATUSES = [
    "COMPLETED",
    "APPROVED",
]

REJECTED_STATUS = "REJECTED"
PENDING_STATUS = "PENDING"


# ==============================================================================
# COLUMN DEFINITIONS
# ==============================================================================

NUMERIC_COLUMNS = [
    "quantity",
    "unit_price",
    "item_total",
    "refund_amount",
    "refund_net_amount",
    "refund_tax_amount",
    "refund_total_amount",
]

TEXT_COLUMNS = [
    "invoice_no",
    "cashier_name",
    "warehouse_name",
    "product_name",
    "processed_by",
    "reason",
]


# ==============================================================================
# SAFE HELPERS
# ==============================================================================

def safe_float(value):
    """Safely convert a value to float."""
    try:
        if value is None:
            return 0.0
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def safe_text(value):
    """Safely convert a value to string."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value)


def money(value):
    """MMK money formatter."""
    return f"{safe_float(value):,.2f} MMK"


# ==============================================================================
# NORMALIZE REPORT DATAFRAME
# ==============================================================================

def normalize_report_dataframe(df):
    if df is None:
        df = pd.DataFrame()
    df = df.copy()

    # Numeric columns
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Text columns
    for col in TEXT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    # ID columns
    for col in ["refund_id", "sale_id", "product_id"]:
        if col not in df.columns:
            df[col] = ""

    # Status
    if "status" not in df.columns:
        df["status"] = "COMPLETED"
    df["status"] = (
        df["status"]
        .fillna("COMPLETED")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Refund date
    if "refund_date" not in df.columns:
        df["refund_date"] = pd.NaT
    df["refund_date"] = pd.to_datetime(df["refund_date"], errors="coerce")

    # Approved at
    if "approved_at" not in df.columns:
        df["approved_at"] = ""

    # V4 report amounts
    df["report_net"] = df["refund_net_amount"].astype(float)
    df["report_tax"] = df["refund_tax_amount"].astype(float)
    df["report_total"] = df["refund_total_amount"].astype(float)

    # Legacy fallback
    legacy_total_mask = (df["report_total"] == 0) & (df["item_total"] != 0)
    df.loc[legacy_total_mask, "report_total"] = df.loc[legacy_total_mask, "item_total"]

    legacy_net_mask = (df["report_net"] == 0) & (df["item_total"] != 0)
    df.loc[legacy_net_mask, "report_net"] = df.loc[legacy_net_mask, "item_total"]

    return df


# ==============================================================================
# LOAD REFUND REPORT
# ==============================================================================

@st.cache_data(ttl=60)
def load_refund_report():
    response = (
        db()
        .table("refund_report_view")
        .select("*")
        .order("refund_date", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data or [])


# ==============================================================================
# PDF HEADER / FOOTER
# ==============================================================================

def pdf_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4

    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(40, height - 28, "ERP ENTERPRISE")

    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 40, height - 28, "REFUND REPORT")

    canvas.setFont("Helvetica", 8)
    canvas.drawString(40, 22, "ERP Refund Report")
    canvas.drawRightString(width - 40, 22, f"Page {doc.page}")

    canvas.restoreState()


# ==============================================================================
# CREATE PDF REPORT
# ==============================================================================

def create_refund_report_pdf(report_df, report_from, report_to):
    buffer = io.BytesIO()

    actual_mask = report_df["status"].isin(ACTUAL_REFUND_STATUSES)
    rejected_mask_pdf = report_df["status"] == REJECTED_STATUS
    pending_mask_pdf = report_df["status"] == PENDING_STATUS

    actual_net = report_df.loc[actual_mask, "report_net"].sum()
    actual_tax = report_df.loc[actual_mask, "report_tax"].sum()
    actual_total = report_df.loc[actual_mask, "report_total"].sum()

    rejected_total_pdf = report_df.loc[rejected_mask_pdf, "report_total"].sum()
    pending_total_pdf = report_df.loc[pending_mask_pdf, "report_total"].sum()

    refund_count_pdf = report_df.loc[actual_mask, "refund_id"].nunique()
    rejected_count_pdf = report_df.loc[rejected_mask_pdf, "refund_id"].nunique()
    pending_count_pdf = report_df.loc[pending_mask_pdf, "refund_id"].nunique()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RefundTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "RefundSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    small_style = ParagraphStyle(
        "RefundSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
    )

    content = []

    content.append(Paragraph("REFUND REPORT", title_style))
    content.append(
        Paragraph(
            f"Report Period: <b>{report_from.strftime('%Y-%m-%d')}</b> to <b>{report_to.strftime('%Y-%m-%d')}</b>",
            subtitle_style,
        )
    )

    # Summary table
    summary_data = [
        ["Actual Refunds", "Refund Net", "Refund Tax", "Refund Total"],
        [
            f"{refund_count_pdf:,}",
            f"{actual_net:,.2f}",
            f"{actual_tax:,.2f}",
            f"{actual_total:,.2f}",
        ],
        ["Rejected", "Rejected Total", "Pending", "Pending Total"],
        [
            f"{rejected_count_pdf:,}",
            f"{rejected_total_pdf:,.2f}",
            f"{pending_count_pdf:,}",
            f"{pending_total_pdf:,.2f}",
        ],
    ]

    summary_table = Table(summary_data, colWidths=[125, 125, 125, 125])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343A40")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#E9ECEF")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFC3C7")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    content.append(summary_table)
    content.append(Spacer(1, 16))

    # Detail table
    table_data = [
        ["ID", "Invoice", "Date", "Status", "Product", "Qty", "Net", "Tax", "Total"]
    ]

    for _, row in report_df.iterrows():
        refund_date = row["refund_date"]
        if pd.notna(refund_date):
            date_text = refund_date.strftime("%Y-%m-%d")
        else:
            date_text = ""

        table_data.append(
            [
                safe_text(row["refund_id"]),
                safe_text(row["invoice_no"]),
                date_text,
                safe_text(row["status"]),
                safe_text(row["product_name"]),
                f"{safe_float(row['quantity']):,.2f}",
                f"{safe_float(row['report_net']):,.2f}",
                f"{safe_float(row['report_tax']):,.2f}",
                f"{safe_float(row['report_total']):,.2f}",
            ]
        )

    table_data.append(
        [
            "", "", "", "", "REFUND TOTAL", "",
            f"{actual_net:,.2f}",
            f"{actual_tax:,.2f}",
            f"{actual_total:,.2f}",
        ]
    )

    table_data.append(
        [
            "", "", "", "", "REJECTED TOTAL", "", "", "",
            f"{rejected_total_pdf:,.2f}",
        ]
    )

    table_data.append(
        [
            "", "", "", "", "PENDING TOTAL", "", "", "",
            f"{pending_total_pdf:,.2f}",
        ]
    )

    detail_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[35, 60, 58, 55, 105, 35, 58, 48, 61],
    )

    detail_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343A40")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("FONTNAME", (0, 1), (-1, -4), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 6.8),
                ("BACKGROUND", (0, -3), (-1, -3), colors.HexColor("#E9ECEF")),
                ("FONTNAME", (0, -3), (-1, -3), "Helvetica-Bold"),
                ("BACKGROUND", (0, -2), (-1, -2), colors.HexColor("#F8D7DA")),
                ("FONTNAME", (0, -2), (-1, -2), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FFF3CD")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#BFC3C7")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (5, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (5, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    content.append(detail_table)
    content.append(Spacer(1, 14))

    content.append(
        Paragraph(
            "<b>Accounting Rule:</b> Refund Total includes only COMPLETED and APPROVED refunds. "
            "Rejected and Pending amounts are reported separately.",
            small_style,
        )
    )

    doc.build(
        content,
        onFirstPage=pdf_header_footer,
        onLaterPages=pdf_header_footer,
    )

    buffer.seek(0)
    return buffer.getvalue()


# ==============================================================================
# CREATE HTML REPORT
# ==============================================================================

def create_html_report(report_df, report_from, report_to):
    actual_mask = report_df["status"].isin(ACTUAL_REFUND_STATUSES)
    rejected_mask_html = report_df["status"] == REJECTED_STATUS
    pending_mask_html = report_df["status"] == PENDING_STATUS

    actual_net_html = report_df.loc[actual_mask, "report_net"].sum()
    actual_tax_html = report_df.loc[actual_mask, "report_tax"].sum()
    actual_total_html = report_df.loc[actual_mask, "report_total"].sum()

    rejected_total_html = report_df.loc[rejected_mask_html, "report_total"].sum()
    pending_total_html = report_df.loc[pending_mask_html, "report_total"].sum()

    actual_count_html = report_df.loc[actual_mask, "refund_id"].nunique()
    rejected_count_html = report_df.loc[rejected_mask_html, "refund_id"].nunique()
    pending_count_html = report_df.loc[pending_mask_html, "refund_id"].nunique()

    html_df = report_df.copy()
    html_df["Refund Date"] = html_df["refund_date"].dt.strftime("%Y-%m-%d %H:%M")

    display_df = pd.DataFrame(
        {
            "Refund ID": html_df["refund_id"],
            "Invoice": html_df["invoice_no"],
            "Refund Date": html_df["Refund Date"],
            "Status": html_df["status"],
            "Product": html_df["product_name"],
            "Qty": html_df["quantity"],
            "Refund Net": html_df["report_net"],
            "Refund Tax": html_df["report_tax"],
            "Refund Total": html_df["report_total"],
            "Cashier": html_df["cashier_name"],
            "Warehouse": html_df["warehouse_name"],
        }
    )

    table_html = display_df.to_html(index=False, classes="refund-table", border=0)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Refund Report</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 40px;
    color: #222;
}}
h1 {{
    text-align: center;
    margin-bottom: 5px;
}}
.period {{
    text-align: center;
    color: #666;
    margin-bottom: 25px;
}}
.summary {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
}}
.summary td {{
    border: 1px solid #ddd;
    padding: 12px;
    text-align: center;
}}
.summary-title {{
    font-weight: bold;
    background: #343a40;
    color: white;
}}
.reject-title {{
    font-weight: bold;
    background: #f8d7da;
}}
.pending-title {{
    font-weight: bold;
    background: #fff3cd;
}}
.refund-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}}
.refund-table th {{
    background: #343a40;
    color: white;
    padding: 9px;
    text-align: left;
}}
.refund-table td {{
    border: 1px solid #ddd;
    padding: 8px;
}}
.refund-table tr:nth-child(even) {{
    background: #f8f9fa;
}}
.footer {{
    margin-top: 25px;
    font-weight: bold;
}}
</style>
</head>
<body>
<h1>REFUND REPORT</h1>
<div class="period">
Report Period:
<b>{report_from.strftime("%Y-%m-%d")}</b>
to
<b>{report_to.strftime("%Y-%m-%d")}</b>
</div>
<table class="summary">
<tr>
<td class="summary-title">Actual Refunds</td>
<td class="summary-title">Refund Net</td>
<td class="summary-title">Refund Tax</td>
<td class="summary-title">Refund Total</td>
</tr>
<tr>
<td>{actual_count_html:,}</td>
<td>{actual_net_html:,.2f} MMK</td>
<td>{actual_tax_html:,.2f} MMK</td>
<td>{actual_total_html:,.2f} MMK</td>
</tr>
<tr>
<td class="reject-title">Rejected</td>
<td class="reject-title">Rejected Total</td>
<td class="pending-title">Pending</td>
<td class="pending-title">Pending Total</td>
</tr>
<tr>
<td>{rejected_count_html:,}</td>
<td>{rejected_total_html:,.2f} MMK</td>
<td>{pending_count_html:,}</td>
<td>{pending_total_html:,.2f} MMK</td>
</tr>
</table>
{table_html}
<div class="footer">
Actual Refund Total: {actual_total_html:,.2f} MMK
<br><br>
Rejected Total: {rejected_total_html:,.2f} MMK
<br><br>
Pending Total: {pending_total_html:,.2f} MMK
</div>
</body>
</html>
"""


# ==============================================================================
# BUILD EXPORT DATAFRAME
# ==============================================================================

def build_export_dataframe(report_df):
    export_df = report_df.copy()

    if "refund_date" in export_df.columns:
        export_df["refund_date"] = export_df["refund_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    export_columns = [
        "refund_id",
        "sale_id",
        "invoice_no",
        "refund_date",
        "status",
        "reason",
        "product_id",
        "product_name",
        "quantity",
        "unit_price",
        "item_total",
        "refund_net_amount",
        "refund_tax_amount",
        "refund_total_amount",
        "cashier_name",
        "processed_by",
        "approved_at",
        "warehouse_name",
    ]

    for col in export_columns:
        if col not in export_df.columns:
            export_df[col] = ""

    export_df = export_df[export_columns].copy()

    export_df = export_df.rename(
        columns={
            "refund_id": "Refund ID",
            "sale_id": "Sale ID",
            "invoice_no": "Invoice",
            "refund_date": "Refund Date",
            "status": "Status",
            "reason": "Reason",
            "product_id": "Product ID",
            "product_name": "Product",
            "quantity": "Quantity",
            "unit_price": "Unit Price",
            "item_total": "Item Price Total",
            "refund_net_amount": "Refund Net",
            "refund_tax_amount": "Refund Tax",
            "refund_total_amount": "Refund Total",
            "cashier_name": "Cashier",
            "processed_by": "Processed By",
            "approved_at": "Approved At",
            "warehouse_name": "Warehouse",
        }
    )

    return export_df


# ==============================================================================
# MAIN FUNCTION
# ==============================================================================

def main():
    # Title
    st.title("↩️ Refund Report")
    st.caption(
        "ERP Enterprise Refund Report • "
        "Date Range • Tax Aware • PDF • Excel • CSV • HTML"
    )

    # Load data
    try:
        df = load_refund_report()
    except Exception as e:
        st.error("Unable to load refund report.")
        st.exception(e)
        st.stop()

    df = normalize_report_dataframe(df)

    if df.empty:
        st.info("No refund records found.")
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
        st.stop()

    # Session date defaults
    valid_dates = df["refund_date"].dropna()

    if valid_dates.empty:
        default_from_date = date.today()
        default_to_date = date.today()
    else:
        default_from_date = valid_dates.min().date()
        default_to_date = date.today()
        if default_to_date < default_from_date:
            default_to_date = default_from_date

    if "refund_from_date" not in st.session_state:
        st.session_state.refund_from_date = default_from_date

    if "refund_to_date" not in st.session_state:
        st.session_state.refund_to_date = default_to_date

    # Sidebar
    st.sidebar.header("🔍 Report Filter")
    st.sidebar.subheader("📅 Report Period")

    # Quick date buttons
    q1, q2 = st.sidebar.columns(2)
    with q1:
        today_clicked = st.button("Today", use_container_width=True)
    with q2:
        yesterday_clicked = st.button("Yesterday", use_container_width=True)

    q3, q4 = st.sidebar.columns(2)
    with q3:
        month_clicked = st.button("This Month", use_container_width=True)
    with q4:
        last_month_clicked = st.button("Last Month", use_container_width=True)

    # Quick date logic
    today = date.today()

    if today_clicked:
        st.session_state.refund_from_date = today
        st.session_state.refund_to_date = today
    elif yesterday_clicked:
        yesterday = today - timedelta(days=1)
        st.session_state.refund_from_date = yesterday
        st.session_state.refund_to_date = yesterday
    elif month_clicked:
        first_day = today.replace(day=1)
        st.session_state.refund_from_date = first_day
        st.session_state.refund_to_date = today
    elif last_month_clicked:
        first_this_month = today.replace(day=1)
        last_previous_month = first_this_month - timedelta(days=1)
        first_previous_month = last_previous_month.replace(day=1)
        st.session_state.refund_from_date = first_previous_month
        st.session_state.refund_to_date = last_previous_month

    # Date inputs
    from_date = st.sidebar.date_input(
        "From Date",
        value=st.session_state.refund_from_date,
    )

    to_date = st.sidebar.date_input(
        "To Date",
        value=st.session_state.refund_to_date,
    )

    st.session_state.refund_from_date = from_date
    st.session_state.refund_to_date = to_date

    if from_date > to_date:
        st.sidebar.error("From Date cannot be later than To Date.")
        st.stop()

    # Invoice search
    invoice_search = st.sidebar.text_input(
        "Invoice No",
        placeholder="Search invoice...",
    )

    # Cashier filter
    cashiers = sorted(
        [safe_text(x) for x in df["cashier_name"].unique() if safe_text(x).strip()]
    )
    cashier_filter = st.sidebar.multiselect("Cashier", cashiers)

    # Warehouse filter
    warehouses = sorted(
        [safe_text(x) for x in df["warehouse_name"].unique() if safe_text(x).strip()]
    )
    warehouse_filter = st.sidebar.multiselect("Warehouse", warehouses)

    # Status filter
    statuses = sorted(
        [safe_text(x) for x in df["status"].unique() if safe_text(x).strip()]
    )
    status_filter = st.sidebar.multiselect("Status", statuses)

    # Refresh button
    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Apply filters
    filtered = df.copy()

    filtered = filtered[
        (filtered["refund_date"].dt.date >= from_date)
        & (filtered["refund_date"].dt.date <= to_date)
    ]

    if invoice_search:
        filtered = filtered[
            filtered["invoice_no"].str.contains(invoice_search, case=False, na=False)
        ]

    if cashier_filter:
        filtered = filtered[filtered["cashier_name"].isin(cashier_filter)]

    if warehouse_filter:
        filtered = filtered[filtered["warehouse_name"].isin(warehouse_filter)]

    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    # Report period info
    st.info(
        f"📅 Report Period: **{from_date.strftime('%Y-%m-%d')}** → **{to_date.strftime('%Y-%m-%d')}**"
    )

    # Financial status masks
    actual_refund_mask = filtered["status"].isin(ACTUAL_REFUND_STATUSES)
    rejected_mask = filtered["status"] == REJECTED_STATUS
    pending_mask = filtered["status"] == PENDING_STATUS

    # Counts
    total_refunds = filtered["refund_id"].nunique()
    completed_count = (filtered["status"] == "COMPLETED").sum()
    approved_count = (filtered["status"] == "APPROVED").sum()
    pending_count = pending_mask.sum()
    rejected_count = rejected_mask.sum()
    actual_refund_count = filtered.loc[actual_refund_mask, "refund_id"].nunique()

    # Financial totals
    total_net = filtered.loc[actual_refund_mask, "report_net"].sum()
    total_tax = filtered.loc[actual_refund_mask, "report_tax"].sum()
    total_refund = filtered.loc[actual_refund_mask, "report_total"].sum()

    rejected_net = filtered.loc[rejected_mask, "report_net"].sum()
    rejected_tax = filtered.loc[rejected_mask, "report_tax"].sum()
    rejected_total = filtered.loc[rejected_mask, "report_total"].sum()

    pending_net = filtered.loc[pending_mask, "report_net"].sum()
    pending_tax = filtered.loc[pending_mask, "report_tax"].sum()
    pending_total = filtered.loc[pending_mask, "report_total"].sum()

    # Summary
    st.subheader("📊 Refund Summary")
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("Refund Records", f"{total_refunds:,}")
    with c2:
        st.metric("Completed", f"{completed_count:,}")
    with c3:
        st.metric("Pending", f"{pending_count:,}")
    with c4:
        st.metric("Rejected", f"{rejected_count:,}")
    with c5:
        st.metric("Refund Total", money(total_refund))

    # Financial summary
    st.divider()
    st.subheader("💰 Financial Summary")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        st.metric("Refund Net", money(total_net))
    with f2:
        st.metric("Refund Tax", money(total_tax))
    with f3:
        st.metric("Refund Total", money(total_refund))
    with f4:
        st.metric("Rejected Total", money(rejected_total))

    if pending_total != 0:
        st.warning(f"⏳ Pending Refund Total: **{money(pending_total)}**")

    if rejected_total != 0:
        st.error(f"❌ Rejected Refund Total: **{money(rejected_total)}**")

    # ==========================================================================
    # REFUND REGISTER WITH DATE RANGE
    # ==========================================================================

    st.divider()
    st.subheader("📋 Refund Register")

    # Register date range filter
    st.markdown("#### 📅 Register Date Filter")

    reg_col1, reg_col2, reg_col3, reg_col4 = st.columns([2, 2, 1, 1])

    with reg_col1:
        register_from_date = st.date_input(
            "Register From Date",
            value=from_date,
            key="register_from_date",
        )

    with reg_col2:
        register_to_date = st.date_input(
            "Register To Date",
            value=to_date,
            key="register_to_date",
        )

    with reg_col3:
        st.write("")
        st.write("")
        apply_register_filter = st.button(
            "🔄 Apply",
            use_container_width=True,
            key="apply_register_filter",
        )

    with reg_col4:
        st.write("")
        st.write("")
        reset_register_filter = st.button(
            "↩️ Reset",
            use_container_width=True,
            key="reset_register_filter",
        )

    if reset_register_filter:
        register_from_date = from_date
        register_to_date = to_date
        st.rerun()

    if register_from_date > register_to_date:
        st.error("Register From Date cannot be later than Register To Date.")
        st.stop()

    register_df = filtered[
        (filtered["refund_date"].dt.date >= register_from_date)
        & (filtered["refund_date"].dt.date <= register_to_date)
    ]

    st.caption(
        f"Showing refunds from **{register_from_date.strftime('%Y-%m-%d')}** "
        f"to **{register_to_date.strftime('%Y-%m-%d')}**"
    )

    if register_df.empty:
        st.warning("No refund records match the selected date range.")
    else:
        display_register_df = pd.DataFrame(
            {
                "Refund ID": register_df["refund_id"],
                "Invoice": register_df["invoice_no"],
                "Refund Date": register_df["refund_date"].dt.strftime("%Y-%m-%d %H:%M"),
                "Status": register_df["status"],
                "Product": register_df["product_name"],
                "Qty": register_df["quantity"],
                "Refund Net": register_df["report_net"],
                "Refund Tax": register_df["report_tax"],
                "Refund Total": register_df["report_total"],
                "Cashier": register_df["cashier_name"],
                "Warehouse": register_df["warehouse_name"],
            }
        )

        st.dataframe(
            display_register_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Refund ID": st.column_config.TextColumn("Refund ID"),
                "Refund Date": st.column_config.TextColumn("Refund Date"),
                "Qty": st.column_config.NumberColumn("Qty", format="%.2f"),
                "Refund Net": st.column_config.NumberColumn("Refund Net", format="%,.2f MMK"),
                "Refund Tax": st.column_config.NumberColumn("Refund Tax", format="%,.2f MMK"),
                "Refund Total": st.column_config.NumberColumn("Refund Total", format="%,.2f MMK"),
            },
        )

        # Register summary
        st.markdown("#### 📊 Register Summary")
        rs1, rs2, rs3, rs4 = st.columns(4)

        with rs1:
            register_total_records = register_df["refund_id"].nunique()
            st.metric("Records", f"{register_total_records:,}")
        with rs2:
            register_completed = (register_df["status"] == "COMPLETED").sum()
            st.metric("Completed", f"{register_completed:,}")
        with rs3:
            register_pending = (register_df["status"] == "PENDING").sum()
            st.metric("Pending", f"{register_pending:,}")
        with rs4:
            register_rejected = (register_df["status"] == "REJECTED").sum()
            st.metric("Rejected", f"{register_rejected:,}")

        # Register financial summary
        st.markdown("#### 💰 Register Financial Summary")
        rf1, rf2, rf3, rf4 = st.columns(4)

        with rf1:
            register_net = register_df.loc[
                register_df["status"].isin(ACTUAL_REFUND_STATUSES), "report_net"
            ].sum()
            st.metric("Actual Net", money(register_net))
        with rf2:
            register_tax = register_df.loc[
                register_df["status"].isin(ACTUAL_REFUND_STATUSES), "report_tax"
            ].sum()
            st.metric("Actual Tax", money(register_tax))
        with rf3:
            register_total = register_df.loc[
                register_df["
