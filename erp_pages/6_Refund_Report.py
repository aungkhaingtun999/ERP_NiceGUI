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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER


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

ACTUAL_REFUND_STATUSES = ["COMPLETED", "APPROVED"]
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
            "Report Period: <b>{}</b> to <b>{}</b>".format(
                report_from.strftime("%Y-%m-%d"),
                report_to.strftime("%Y-%m-%d")
            ),
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

    html_content = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Refund Report</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 40px;
    color: #222;
}
h1 {
    text-align: center;
    margin-bottom: 5px;
}
.period {
    text-align: center;
    color: #666;
    margin-bottom: 25px;
}
.summary {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
}
.summary td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: center;
}
.summary-title {
    font-weight: bold;
    background: #343a40;
    color: white;
}
.reject-title {
    font-weight: bold;
    background: #f8d7da;
}
.pending-title {
    font-weight: bold;
    background: #fff3cd;
}
.refund-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}
.refund-table th {
    background: #343a40;
    color: white;
    padding: 9px;
    text-align: left;
}
.refund-table td {
    border: 1px solid #ddd;
    padding: 8px;
}
.refund-table tr:nth-child(even) {
    background: #f8f9fa;
}
.footer {
    margin-top: 25px;
    font-weight: bold;
}
</style>
</head>
<body>
<h1>REFUND REPORT</h1>
<div class="period">
Report Period: <b>{}</b> to <b>{}</b>
</div>
<table class="summary">
<tr>
<td class="summary-title">Actual Refunds</td>
<td class="summary-title">Refund Net</td>
<td class="summary-title">Refund Tax</td>
<td class="summary-title">Refund Total</td>
</tr>
<tr>
<td>{:,}</td>
<td>{:,.2f} MMK</td>
<td>{:,.2f} MMK</td>
<td>{:,.2f} MMK</td>
</tr>
<tr>
<td class="reject-title">Rejected</td>
<td class="reject-title">Rejected Total</td>
<td class="pending-title">Pending</td>
<td class="pending-title">Pending Total</td>
</tr>
<tr>
<td>{:,}</td>
<td>{:,.2f} MMK</td>
<td>{:,}</td>
<td>{:,.2f} MMK</td>
</tr>
</table>
{}
<div class="footer">
Actual Refund Total: {:,.2f} MMK
<br><br>
Rejected Total: {:,.2f} MMK
<br><br>
Pending Total: {:,.2f} MMK
</div>
</body>
</html>
""".format(
        report_from.strftime("%Y-%m-%d"),
        report_to.strftime("%Y-%m-%d"),
        actual_count_html,
        actual_net_html,
        actual_tax_html,
        actual_total_html,
        rejected_count_html,
        rejected_total_html,
        pending_count_html,
        pending_total_html,
        table_html,
        actual_total_html,
        rejected_total_html,
        pending_total_html,
    )

    return html_content


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
    
