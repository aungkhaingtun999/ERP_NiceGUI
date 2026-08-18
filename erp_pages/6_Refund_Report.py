# ==============================================================================
# erp_pages / pages / Refund Report
# ERP ENTERPRISE REFUND REPORT v5.0
#
# SIMPLE + COMPLETE + TAX AWARE
#
# FEATURES
#   - Date Range Filter
#   - Quick Date Filters
#   - Invoice / Cashier / Warehouse / Status Filters
#   - Net / Tax / Total
#   - Refund Detail
#   - PDF Export
#   - Excel Export
#   - CSV Export
#   - HTML Export
#   - A4 PDF with clean margins
#   - Legacy Refund Compatibility
#
# DATABASE VIEWS
#   refund_report_view
#   refund_detail_view
#
# V4 AMOUNTS
#   refund_net_amount
#   refund_tax_amount
#   refund_total_amount
# ==============================================================================

import io
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

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
    PageBreak,
)

from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


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
# TITLE
# ==============================================================================

st.title("↩️ Refund Report")
st.caption(
    "Refund financial report • Date range • PDF • Excel • CSV • HTML"
)


# ==============================================================================
# CONSTANTS
# ==============================================================================

STATUS_OPTIONS = [
    "PENDING",
    "APPROVED",
    "COMPLETED",
    "REJECTED",
    "CANCELLED",
]

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
# SESSION STATE MANAGEMENT
# ==============================================================================

def init_session_state():
    """Initialize session state variables"""
    
    if "refund_from_date" not in st.session_state:
        st.session_state.refund_from_date = date.today() - timedelta(days=30)
    
    if "refund_to_date" not in st.session_state:
        st.session_state.refund_to_date = date.today()
    
    if "refund_data" not in st.session_state:
        st.session_state.refund_data = None
    
    if "filtered_data" not in st.session_state:
        st.session_state.filtered_data = None

# Initialize session state
init_session_state()


# ==============================================================================
# SAFE HELPERS
# ==============================================================================

def safe_float(value) -> float:
    """
    Convert value safely to float.
    """
    try:
        if value is None:
            return 0.0
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def safe_text(value) -> str:
    """
    Convert value safely to string.
    """
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value)


def money(value) -> str:
    """
    MMK display format.
    """
    return f"{safe_float(value):,.2f} MMK"


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize report dataframe.
    """
    if df is None or df.empty:
        return pd.DataFrame()

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
    df["status"] = df["status"].fillna("COMPLETED").astype(str).str.strip().str.upper()

    # Date
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
    legacy_total = (df["report_total"] == 0) & (df["item_total"] != 0)
    df.loc[legacy_total, "report_total"] = df.loc[legacy_total, "item_total"]

    legacy_net = (df["report_net"] == 0) & (df["item_total"] != 0)
    df.loc[legacy_net, "report_net"] = df.loc[legacy_net, "item_total"]

    return df


# ==============================================================================
# DATA LOADING
# ==============================================================================

@st.cache_data(ttl=300)  # 5 minutes cache
def load_refund_report() -> pd.DataFrame:
    """
    Load refund report from database.
    """
    try:
        response = (
            db()
            .table("refund_report_view")
            .select("*")
            .order("refund_date", desc=True)
            .execute()
        )
        return pd.DataFrame(response.data or [])
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()


# ==============================================================================
# FILTER FUNCTION
# ==============================================================================

def apply_filters(
    df: pd.DataFrame,
    from_date: date,
    to_date: date,
    invoice_search: str,
    cashier_filter: List[str],
    warehouse_filter: List[str],
    status_filter: List[str]
) -> pd.DataFrame:
    """
    Apply all filters to the dataframe.
    """
    if df.empty:
        return df

    filtered = df.copy()

    # Date filters
    filtered = filtered[filtered["refund_date"].dt.date >= from_date]
    filtered = filtered[filtered["refund_date"].dt.date <= to_date]

    # Invoice search
    if invoice_search and invoice_search.strip():
        filtered = filtered[
            filtered["invoice_no"].str.contains(invoice_search, case=False, na=False)
        ]

    # Cashier filter
    if cashier_filter:
        filtered = filtered[filtered["cashier_name"].isin(cashier_filter)]

    # Warehouse filter
    if warehouse_filter:
        filtered = filtered[filtered["warehouse_name"].isin(warehouse_filter)]

    # Status filter
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    return filtered


# ==============================================================================
# MAIN DATA LOADING FUNCTION
# ==============================================================================

def load_and_filter_data():
    """
    Load data and apply filters based on session state.
    """
    # Load data
    df = load_refund_report()
    df = normalize_dataframe(df)

    if df.empty:
        return pd.DataFrame()

    # Get current filter values from session state
    from_date = st.session_state.get("refund_from_date", date.today() - timedelta(days=30))
    to_date = st.session_state.get("refund_to_date", date.today())
    invoice_search = st.session_state.get("invoice_search", "")
    cashier_filter = st.session_state.get("cashier_filter", [])
    warehouse_filter = st.session_state.get("warehouse_filter", [])
    status_filter = st.session_state.get("status_filter", [])

    # Apply filters
    filtered = apply_filters(
        df,
        from_date,
        to_date,
        invoice_search,
        cashier_filter,
        warehouse_filter,
        status_filter
    )

    return filtered


# ==============================================================================
# PDF HELPERS
# ==============================================================================

def pdf_page_header_footer(canvas, doc):
    """Add header and footer to PDF pages."""
    canvas.saveState()
    width, height = A4

    # Header
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(40, height - 28, "ERP ENTERPRISE")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 40, height - 28, "REFUND REPORT")

    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.drawString(40, 22, "ERP Refund Report")
    canvas.drawRightString(width - 40, 22, f"Page {doc.page}")

    canvas.restoreState()


# ==============================================================================
# PDF REPORT
# ==============================================================================

def create_report_pdf(
    report_df: pd.DataFrame,
    report_from: date,
    report_to: date
) -> bytes:
    """
    Create PDF report.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=38,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RefundTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=8,
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

    normal_style = ParagraphStyle(
        "RefundNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
    )

    content = []

    # Title
    content.append(Paragraph("REFUND REPORT", title_style))
    content.append(
        Paragraph(
            f"Report Period: {report_from.strftime('%Y-%m-%d')} to {report_to.strftime('%Y-%m-%d')}",
            subtitle_style,
        )
    )

    # Summary
    report_refunds = report_df["refund_id"].nunique()
    report_net = report_df["report_net"].sum()
    report_tax = report_df["report_tax"].sum()
    report_total = report_df["report_total"].sum()

    summary_data = [
        ["Refunds", "Refund Net", "Refund Tax", "Refund Total"],
        [
            f"{report_refunds:,}",
            f"{report_net:,.2f}",
            f"{report_tax:,.2f}",
            f"{report_total:,.2f}",
        ],
    ]

    summary_table = Table(summary_data, colWidths=[110, 125, 110, 125])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9ECEF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
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
        date_text = refund_date.strftime("%Y-%m-%d") if pd.notna(refund_date) else ""

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

    # Total row
    table_data.append(
        [
            "",
            "",
            "",
            "",
            "TOTAL",
            "",
            f"{report_net:,.2f}",
            f"{report_tax:,.2f}",
            f"{report_total:,.2f}",
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
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343A40")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                # Body
                ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 6.8),
                # Total
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E9ECEF")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#BFC3C7")),
                # Alignment
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (5, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (5, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    content.append(detail_table)
    content.append(Spacer(1, 15))

    # Footer summary
    content.append(
        Paragraph(
            (
                f"<b>Refund Count:</b> {report_refunds:,}<br/>"
                f"<b>Refund Net:</b> {report_net:,.2f} MMK<br/>"
                f"<b>Refund Tax:</b> {report_tax:,.2f} MMK<br/>"
                f"<b>Refund Total:</b> {report_total:,.2f} MMK"
            ),
            normal_style,
        )
    )

    doc.build(content, onFirstPage=pdf_page_header_footer, onLaterPages=pdf_page_header_footer)
    buffer.seek(0)
    return buffer.getvalue()


# ==============================================================================
# HTML REPORT
# ==============================================================================

def create_html_report(
    report_df: pd.DataFrame,
    report_from: date,
    report_to: date
) -> str:
    """
    Create HTML report.
    """
    html_df = report_df.copy()
    html_df["Refund Date"] = html_df["refund_date"].dt.strftime("%Y-%m-%d %H:%M")

    export_html = pd.DataFrame(
        {
            "Refund ID": html_df["refund_id"],
            "Invoice": html_df["invoice_no"],
            "Refund Date": html_df["Refund Date"],
            "Status": html_df["status"],
            "Product": html_df["product_name"],
            "Quantity": html_df["quantity"],
            "Refund Net": html_df["report_net"],
            "Refund Tax": html_df["report_tax"],
            "Refund Total": html_df["report_total"],
            "Cashier": html_df["cashier_name"],
            "Warehouse": html_df["warehouse_name"],
        }
    )

    table_html = export_html.to_html(
        index=False,
        classes="refund-table",
        border=0,
        justify="center",
    )

    total_refunds = report_df["refund_id"].nunique()
    total_net = report_df["report_net"].sum()
    total_tax = report_df["report_tax"].sum()
    total_total = report_df["report_total"].sum()

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
    background: #f1f3f5;
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
    text-align: right;
    font-weight: bold;
}}
</style>
</head>
<body>
<h1>REFUND REPORT</h1>
<div class="period">
Report Period: <b>{report_from.strftime("%Y-%m-%d")}</b> to <b>{report_to.strftime("%Y-%m-%d")}</b>
</div>
<table class="summary">
<tr>
<td class="summary-title">Refunds</td>
<td class="summary-title">Refund Net</td>
<td class="summary-title">Refund Tax</td>
<td class="summary-title">Refund Total</td>
</tr>
<tr>
<td>{total_refunds:,}</td>
<td>{total_net:,.2f} MMK</td>
<td>{total_tax:,.2f} MMK</td>
<td>{total_total:,.2f} MMK</td>
</tr>
</table>
{table_html}
<div class="footer">
Refund Total: {total_total:,.2f} MMK
</div>
</body>
</html>
"""


# ==============================================================================
# EXPORT DATAFRAME
# ==============================================================================

def build_export_dataframe(report_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build export-ready dataframe.
    """
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
# MAIN PAGE
# ==============================================================================

def main():
    """Main function to run the refund report page."""
    
    # Load and filter data
    filtered = load_and_filter_data()
    
    if filtered.empty:
        st.info("No refund records found. Please adjust your filters.")
        
        if st.button("🔄 Refresh Data", use_container_width=False):
            st.cache_data.clear()
            st.rerun()
        return
    
    # Display report period
    from_date = st.session_state.get("refund_from_date", date.today() - timedelta(days=30))
    to_date = st.session_state.get("refund_to_date", date.today())
    
    st.info(
        f"📅 Report Period: **{from_date.strftime('%Y-%m-%d')}** to **{to_date.strftime('%Y-%m-%d')}**"
    )
    
    # KPI Summary
    total_refunds = filtered["refund_id"].nunique()
    pending = filtered["status"].eq("PENDING").sum()
    completed = filtered["status"].eq("COMPLETED").sum()
    approved = filtered["status"].eq("APPROVED").sum()
    rejected = filtered["status"].eq("REJECTED").sum()
    total_net = filtered["report_net"].sum()
    total_tax = filtered["report_tax"].sum()
    total_refund = filtered["report_total"].sum()
    
    st.subheader("📊 Refund Summary")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.metric("Refunds", f"{total_refunds:,}")
    with c2:
        st.metric("Pending", f"{pending:,}")
    with c3:
        st.metric("Approved", f"{approved:,}")
    with c4:
        st.metric("Completed", f"{completed:,}")
    with c5:
        st.metric("Refund Total", money(total_refund))
    
    # Financial summary
    st.divider()
    f1, f2, f3 = st.columns(3)
    
    with f1:
        st.metric("Refund Net", money(total_net))
    with f2:
        st.metric("Refund Tax", money(total_tax))
    with f3:
        st.metric("Refund Total", money(total_refund))
    
    # Report table
    st.divider()
    st.subheader("📋 Refund Register")
    
    display_df = pd.DataFrame(
        {
            "Refund ID": filtered["refund_id"],
            "Invoice": filtered["invoice_no"],
            "Refund Date": filtered["refund_date"].dt.strftime("%Y-%m-%d %H:%M"),
            "Status": filtered["status"],
            "Product": filtered["product_name"],
            "Qty": filtered["quantity"],
            "Refund Net": filtered["report_net"],
            "Refund Tax": filtered["report_tax"],
            "Refund Total": filtered["report_total"],
            "Cashier": filtered["cashier_name"],
            "Warehouse": filtered["warehouse_name"],
        }
    )
    
    st.dataframe(
        display_df,
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
    
    # Export section
    st.divider()
    st.subheader("📥 Export Report")
    
    export_df = build_export_dataframe(filtered)
    
    # Create files
    pdf_bytes = create_report_pdf(filtered, from_date, to_date)
    
    # Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Refund Report")
        
        workbook = writer.book
        worksheet = writer.sheets["Refund Report"]
        
        # Column widths
        widths = {
            "A": 12, "B": 15, "C": 20, "D": 14, "E": 30,
            "F": 12, "G": 16, "H": 16, "I": 16, "J": 20,
            "K": 20, "L": 20, "M": 20, "N": 20, "O": 20,
            "P": 20, "Q": 20, "R": 20
        }
        
        for col_letter, width in widths.items():
            worksheet.column_dimensions[col_letter].width = width
        
        worksheet.freeze_panes = "A2"
        if worksheet.max_row >= 2:
            worksheet.auto_filter.ref = worksheet.dimensions
        
        # Header formatting
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        
        header_fill = PatternFill("solid", fgColor="343A40")
        header_font = Font(bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
        
        # Body formatting
        for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")
        
        # Currency columns
        header_names = {cell.value: cell.column for cell in worksheet[1]}
        currency_columns = ["Unit Price", "Item Price Total", "Refund Net", "Refund Tax", "Refund Total"]
        
        for name in currency_columns:
            if name not in header_names:
                continue
            col_index = header_names[name]
            for row in worksheet.iter_rows(
                min_row=2,
                max_row=worksheet.max_row,
                min_col=col_index,
                max_col=col_index
            ):
                for cell in row:
                    cell.number_format = '#,##0.00'
    
    excel_buffer.seek(0)
    
    # CSV
    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    
    # HTML
    html_content = create_html_report(filtered, from_date, to_date)
    
    # Download buttons
    e1, e2, e3, e4 = st.columns(4)
    
    with e1:
        st.download_button(
            "📄 PDF",
            data=pdf_bytes,
            file_name=f"refund_report_{from_date}_to_{to_date}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    
    with e2:
        st.download_button(
            "📊 Excel",
            data=excel_buffer.getvalue(),
            file_name=f"refund_report_{from_date}_to_{to_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    
    with e3:
        st.download_button(
            "📑 CSV",
            data=csv_bytes,
            file_name=f"refund_report_{from_date}_to_{to_date}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    
    with e4:
        st.download_button(
            "🌐 HTML",
            data=html_content,
            file_name=f"refund_report_{from_date}_to_{to_date}.html",
            mime="text/html",
            use_container_width=True,
        )
    
    # Refund Detail
    st.divider()
    st.subheader("🔎 Refund Detail")
    
    # Select refund
    selector_data = []
    for _, row in filtered.iterrows():
        selector_data.append(
            {
                "id": row["refund_id"],
                "label": f"#{row['refund_id']} | {row['invoice_no']} | {safe_float(row['report_total']):,.2f} MMK | {row['status']}",
            }
        )
    
    selected_id = st.selectbox(
        "Select Refund",
        options=[x["id"] for x in selector_data],
        format_func=lambda x: next((item["label"] for item in selector_data if item["id"] == x), str(x)),
    )
    
    selected_rows = filtered[filtered["refund_id"] == selected_id]
    
    if not selected_rows.empty:
        selected = selected_rows.iloc[0]
        
        st.markdown(f"### Refund #{selected_id}")
        
        h1, h2, h3, h4 = st.columns(4)
        
        with h1:
            st.caption("Invoice")
            st.write(selected["invoice_no"])
        with h2:
            st.caption("Status")
            st.write(selected["status"])
        with h3:
            st.caption("Cashier")
            st.write(selected["cashier_name"] or "-")
        with h4:
            st.caption("Warehouse")
            st.write(selected["warehouse_name"] or "-")
        
        d1, d2 = st.columns(2)
        
        with d1:
            st.caption("Refund Date")
            if pd.notna(selected["refund_date"]):
                st.write(selected["refund_date"].strftime("%Y-%m-%d %H:%M"))
            else:
                st.write("-")
        
        with d2:
            st.caption("Reason")
            st.write(selected["reason"] or "-")
        
        st.divider()
        
        selected_net = safe_float(selected["report_net"])
        selected_tax = safe_float(selected["report_tax"])
        selected_total = safe_float(selected["report_total"])
        
        a1, a2, a3 = st.columns(3)
        
        with a1:
            st.metric("Refund Net", money(selected_net))
        with a2:
            st.metric("Refund Tax", money(selected_tax))
        with a3:
            st.metric("Refund Total", money(selected_total))
        
        # Load detail
        try:
            response = (
                db()
                .table("refund_detail_view")
                .select("*")
                .eq("refund_id", selected_id)
                .execute()
            )
            selected_items = response.data or []
        except Exception as e:
            selected_items = []
            st.error(f"Unable to load refund details: {e}")
        
        if selected_items:
            detail_df = pd.DataFrame(selected_items)
            
            for col in ["quantity", "unit_price", "item_total", "refund_net_amount", "refund_tax_amount", "refund_total_amount"]:
                if col not in detail_df.columns:
                    detail_df[col] = 0
                detail_df[col] = pd.to_numeric(detail_df[col], errors="coerce").fillna(0)
            
            if "product_name" not in detail_df.columns:
                detail_df["product_name"] = ""
            
            # Legacy fallback
            detail_df["display_net"] = detail_df["refund_net_amount"]
            detail_df.loc[
                (detail_df["display_net"] == 0) & (detail_df["item_total"] != 0),
                "display_net"
            ] = detail_df.loc[
                (detail_df["display_net"] == 0) & (detail_df["item_total"] != 0),
                "item_total"
            ]
            
            detail_df["display_tax"] = detail_df["refund_tax_amount"]
            detail_df["display_total"] = detail_df["refund_total_amount"]
            detail_df.loc[
                (detail_df["display_total"] == 0) & (detail_df["item_total"] != 0),
                "display_total"
            ] = detail_df.loc[
                (detail_df["display_total"] == 0) & (detail_df["item_total"] != 0),
                "item_total"
            ]
            
            detail_display = pd.DataFrame(
                {
                    "Product": detail_df["product_name"],
                    "Qty": detail_df["quantity"],
                    "Unit Price": detail_df["unit_price"],
                    "Refund Net": detail_df["display_net"],
                    "Refund Tax": detail_df["display_tax"],
                    "Refund Total": detail_df["display_total"],
                }
            )
            
            st.subheader("📦 Refund Items")
            
            st.dataframe(
                detail_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Qty": st.column_config.NumberColumn("Qty", format="%.2f"),
                    "Unit Price": st.column_config.NumberColumn("Unit Price", format="%,.2f MMK"),
                    "Refund Net": st.column_config.NumberColumn("Refund Net", format="%,.2f MMK"),
                    "Refund Tax": st.column_config.NumberColumn("Refund Tax", format="%,.2f MMK"),
                    "Refund Total": st.column_config.NumberColumn("Refund Total", format="%,.2f MMK"),
                },
            )
            
            detail_net = detail_df["display_net"].sum()
            detail_tax = detail_df["display_tax"].sum()
            detail_total = detail_df["display_total"].sum()
            
            t1, t2, t3 = st.columns(3)
            
            with t1:
                st.metric("Net", money(detail_net))
            with t2:
                st.metric("Tax", money(detail_tax))
            with t3:
                st.metric("Total", money(detail_total))
        else:
            st.warning("No refund item records found.")
    
    # Analytics
    st.divider()
    st.subheader("📈 Refund Analytics")
    
    if not filtered.empty:
        # Daily refund total
        daily = (
            filtered.assign(report_day=filtered["refund_date"].dt.date)
            .groupby("report_day")["report_total"]
            .sum()
            .sort_index()
        )
        
        st.markdown("#### Daily Refund Total")
        st.line_chart(daily, use_container_width=True)
        
        ac1, ac2 = st.columns(2)
        
        with ac1:
            st.markdown("#### 🏆 Top Refunded Products")
            top_products = (
                filtered.groupby("product_name")["quantity"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            st.bar_chart(top_products, use_container_width=True)
        
        with ac2:
            st.markdown("#### 👤 Cashier Refund Total")
            cashier_data = (
                filtered.groupby("cashier_name")["report_total"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            st.bar_chart(cashier_data, use_container_width=True)
    else:
        st.info("No data for analytics.")
    
    # Footer
    st.divider()
    st.caption(
        "ERP Enterprise Refund Report v5.0 • Tax-aware • Date-range reporting • PDF / Excel / CSV / HTML"
    )


# ==============================================================================
# RUN APPLICATION
# ==============================================================================

if __name__ == "__main__":
    main()
