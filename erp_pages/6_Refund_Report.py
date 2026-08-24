# ==============================================================================
# erp_pages/6_Refund_Report.py
# ERP ENTERPRISE REFUND REPORT v5.2
# NICE GUI VERSION
# TAX-AWARE + FROM/TO DATE + REJECTED SEPARATION
# ==============================================================================

from typing import Dict, Any, Optional, List
import io
from datetime import date, timedelta
import pandas as pd
from nicegui import ui

from database import db
from auth import require_login

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER


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
    "quantity", "unit_price", "item_total",
    "refund_amount", "refund_net_amount",
    "refund_tax_amount", "refund_total_amount",
]

TEXT_COLUMNS = [
    "invoice_no", "cashier_name", "warehouse_name",
    "product_name", "processed_by", "reason",
]


# ==============================================================================
# SAFE HELPERS
# ==============================================================================

def safe_float(value: Any) -> float:
    """Safely convert value to float."""
    try:
        if value is None:
            return 0.0
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def safe_text(value: Any) -> str:
    """Safely convert value to string."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value)


def money(value: Any) -> str:
    """Format as MMK currency."""
    return f"{safe_float(value):,.2f} MMK"


# ==============================================================================
# NORMALIZE REPORT DATAFRAME
# ==============================================================================

def normalize_report_dataframe(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Normalize report dataframe with required columns."""
    if df is None:
        df = pd.DataFrame()
    df = df.copy()
    
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    
    for col in TEXT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    
    for col in ["refund_id", "sale_id", "product_id"]:
        if col not in df.columns:
            df[col] = ""
    
    if "status" not in df.columns:
        df["status"] = "COMPLETED"
    df["status"] = df["status"].fillna("COMPLETED").astype(str).str.strip().str.upper()
    
    if "refund_date" not in df.columns:
        df["refund_date"] = pd.NaT
    df["refund_date"] = pd.to_datetime(df["refund_date"], errors="coerce", utc=True).dt.tz_localize(None)
    
    if "approved_at" not in df.columns:
        df["approved_at"] = ""
    
    df["report_net"] = pd.to_numeric(df["refund_net_amount"], errors="coerce").fillna(0.0)
    df["report_tax"] = pd.to_numeric(df["refund_tax_amount"], errors="coerce").fillna(0.0)
    df["report_total"] = pd.to_numeric(df["refund_total_amount"], errors="coerce").fillna(0.0)
    
    return df.reset_index(drop=True)


# ==============================================================================
# LOAD REFUND REPORT
# ==============================================================================

def load_refund_report() -> pd.DataFrame:
    """Load refund report from database."""
    try:
        response = (
            db()
            .table("refund_report_view")
            .select("*")
            .order("refund_date", desc=True)
            .execute()
        )
        return normalize_report_dataframe(pd.DataFrame(response.data or []))
    except Exception as e:
        ui.notify(f"Failed to load refund report: {e}", type='error', position='top')
        return pd.DataFrame()


# ==============================================================================
# FILTER BY DATE
# ==============================================================================

def filter_by_date(df: pd.DataFrame, from_date: date, to_date: date) -> pd.DataFrame:
    """Filter dataframe by date range."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    result = df.copy()
    if "refund_date" not in result.columns:
        return result.iloc[0:0].copy()
    
    result["refund_date"] = pd.to_datetime(result["refund_date"], errors="coerce", utc=True).dt.tz_localize(None)
    
    start_datetime = pd.Timestamp(from_date)
    end_datetime = pd.Timestamp(to_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    
    mask = (
        result["refund_date"].notna()
        & (result["refund_date"] >= start_datetime)
        & (result["refund_date"] <= end_datetime)
    )
    return result.loc[mask].copy().reset_index(drop=True)


# ==============================================================================
# SPLIT REPORT BY STATUS
# ==============================================================================

def split_report_by_status(df: pd.DataFrame) -> tuple:
    """Split report into actual, rejected, and pending dataframes."""
    if df is None or df.empty:
        empty = pd.DataFrame()
        return empty.copy(), empty.copy(), empty.copy()
    
    normalized = normalize_report_dataframe(df)
    
    actual_df = normalized[normalized["status"].isin(ACTUAL_REFUND_STATUSES)].copy()
    rejected_df = normalized[normalized["status"] == REJECTED_STATUS].copy()
    pending_df = normalized[normalized["status"] == PENDING_STATUS].copy()
    
    return (
        actual_df.reset_index(drop=True),
        rejected_df.reset_index(drop=True),
        pending_df.reset_index(drop=True),
    )


# ==============================================================================
# CALCULATE SUMMARY
# ==============================================================================

def calculate_summary(actual_df, rejected_df, pending_df) -> Dict[str, Any]:
    """Calculate summary statistics."""
    actual_net = actual_df["report_net"].sum() if not actual_df.empty else 0.0
    actual_tax = actual_df["report_tax"].sum() if not actual_df.empty else 0.0
    actual_total = actual_df["report_total"].sum() if not actual_df.empty else 0.0
    
    rejected_total = rejected_df["report_total"].sum() if not rejected_df.empty else 0.0
    pending_total = pending_df["report_total"].sum() if not pending_df.empty else 0.0
    
    actual_count = actual_df["refund_id"].nunique() if not actual_df.empty else 0
    rejected_count = rejected_df["refund_id"].nunique() if not rejected_df.empty else 0
    pending_count = pending_df["refund_id"].nunique() if not pending_df.empty else 0
    
    return {
        "actual_net": safe_float(actual_net),
        "actual_tax": safe_float(actual_tax),
        "actual_total": safe_float(actual_total),
        "rejected_total": safe_float(rejected_total),
        "pending_total": safe_float(pending_total),
        "actual_count": int(actual_count),
        "rejected_count": int(rejected_count),
        "pending_count": int(pending_count),
    }


# ==============================================================================
# PDF GENERATION (Simplified for NiceGUI)
# ==============================================================================

def create_refund_report_pdf(actual_df, rejected_df, pending_df, report_from, report_to) -> bytes:
    """Create PDF report."""
    buffer = io.BytesIO()
    summary = calculate_summary(actual_df, rejected_df, pending_df)
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=48, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, alignment=TA_CENTER)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11)
    
    content = []
    content.append(Paragraph("REFUND REPORT", title_style))
    content.append(Paragraph(f"Report Period: {report_from} to {report_to}", styles["Normal"]))
    content.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ["Actual Refunds", "Refund Net", "Refund Tax", "Refund Total"],
        [str(summary["actual_count"]), f"{summary['actual_net']:,.2f}", f"{summary['actual_tax']:,.2f}", f"{summary['actual_total']:,.2f}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[100, 100, 100, 100])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343A40")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    content.append(summary_table)
    content.append(Spacer(1, 20))
    
    # Actual refund table
    content.append(Paragraph("ACTUAL REFUND REGISTER", section_style))
    
    table_data = [["ID", "Invoice", "Date", "Product", "Qty", "Total"]]
    
    for _, row in actual_df.head(100).iterrows():
        table_data.append([
            safe_text(row["refund_id"])[:10],
            safe_text(row["invoice_no"])[:15],
            row["refund_date"].strftime("%Y-%m-%d") if pd.notna(row["refund_date"]) else "",
            safe_text(row["product_name"])[:25],
            f"{safe_float(row['quantity']):,.0f}",
            f"{safe_float(row['report_total']):,.2f}",
        ])
    
    detail_table = Table(table_data, repeatRows=1, colWidths=[40, 70, 80, 120, 40, 70])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343A40")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    content.append(detail_table)
    
    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main refund report page."""
    
    user = require_login()
    
    if not user:
        return
    
    target = container or ui.column()
    
    with target:
        ui.label('↩️ ERP ENTERPRISE REFUND REPORT').classes('text-3xl font-bold mb-2')
        ui.label('Tax-Aware Refund Reporting | Date Range | Rejected Separation').classes('text-gray-500 mb-4')
        
        # Load data
        all_refunds_df = load_refund_report()
        
        # Date range
        today = date.today()
        
        with ui.row().classes('w-full gap-4 items-end mb-4'):
            from_input = ui.input('From Date', value=today.strftime('%Y-%m-%d')).props('type=date').classes('min-w-[200px]')
            to_input = ui.input('To Date', value=today.strftime('%Y-%m-%d')).props('type=date').classes('min-w-[200px]')
            
            refresh_btn = ui.button('🔄 Refresh', on_click=lambda: refresh_report()).classes('bg-primary text-white')
        
        # Dynamic containers
        kpi_container = ui.column().classes('w-full mb-4')
        tabs_container = ui.column().classes('w-full')
        
        def refresh_report():
            """Refresh report data."""
            try:
                refresh_btn.disable()
                refresh_btn.text = '⏳ Loading...'
                
                report_from = date.fromisoformat(from_input.value)
                report_to = date.fromisoformat(to_input.value)
                
                if report_from > report_to:
                    ui.notify('From Date cannot be later than To Date.', type='error', position='top')
                    return
                
                # Filter and split
                date_filtered_df = filter_by_date(all_refunds_df, report_from, report_to)
                actual_df, rejected_df, pending_df = split_report_by_status(date_filtered_df)
                summary = calculate_summary(actual_df, rejected_df, pending_df)
                
                # Build KPI cards
                kpi_container.clear()
                with kpi_container:
                    with ui.row().classes('w-full gap-4 flex-wrap'):
                        kpis = [
                            ("Actual Refunds", str(summary['actual_count']), "bg-blue-50 text-blue-700"),
                            ("Refund Net", money(summary["actual_net"]), "bg-green-50 text-green-700"),
                            ("Refund Tax", money(summary["actual_tax"]), "bg-purple-50 text-purple-700"),
                            ("Refund Total", money(summary["actual_total"]), "bg-teal-50 text-teal-700"),
                            ("Rejected Total", money(summary["rejected_total"]), "bg-red-50 text-red-700"),
                        ]
                        
                        for label, value, color in kpis:
                            with ui.card().classes(f'p-4 flex-1 min-w-[180px] {color.split()[0]}'):
                                ui.label(label).classes('text-sm text-gray-600')
                                ui.label(value).classes(f'text-xl font-bold {color.split()[1]}')
                
                # Build tabs with data
                tabs_container.clear()
                with tabs_container:
                    build_report_tabs(actual_df, rejected_df, pending_df, summary, report_from, report_to)
            
            except Exception as e:
                ui.notify(f'Report error: {e}', type='error', position='top')
            
            finally:
                refresh_btn.enable()
                refresh_btn.text = '🔄 Refresh'
        
        # Initial load
        refresh_report()


def build_report_tabs(actual_df, rejected_df, pending_df, summary, report_from, report_to):
    """Build report tabs."""
    
    with ui.tabs().classes('w-full mb-4') as tabs:
        tab_refund = ui.tab('↩️ Refund Register', icon='receipt')
        tab_rejected = ui.tab('❌ Rejected', icon='cancel')
        tab_pending = ui.tab('⏳ Pending', icon='pending')
        tab_export = ui.tab('📤 Export', icon='download')
    
    with ui.tab_panels(tabs, value=tab_refund).classes('w-full'):
        # Actual Refund Register
        with ui.tab_panel(tab_refund):
            if actual_df.empty:
                ui.label('No actual refund records found for the selected date range.').classes('text-gray-500')
            else:
                display_actual = actual_df.copy()
                display_actual["Refund Date"] = display_actual["refund_date"].dt.strftime("%Y-%m-%d %H:%M")
                
                display_cols = [
                    "refund_id", "sale_id", "invoice_no", "refund_date",
                    "status", "product_name", "quantity", "report_net",
                    "report_tax", "report_total", "cashier_name", "warehouse_name"
                ]
                
                display_df = display_actual[display_cols].copy()
                display_df.columns = [
                    "Refund ID", "Sale ID", "Invoice", "Refund Date",
                    "Status", "Product", "Qty", "Refund Net",
                    "Refund Tax", "Refund Total", "Cashier", "Warehouse"
                ]
                
                columns = [{'name': col, 'label': col, 'field': col, 'sortable': True} for col in display_df.columns]
                ui.table(columns=columns, rows=display_df.to_dict('records'), row_key='Refund ID', pagination=20).classes('w-full')
        
        # Rejected
        with ui.tab_panel(tab_rejected):
            if rejected_df.empty:
                ui.label('No rejected refunds found.').classes('text-gray-500')
            else:
                display_rejected = rejected_df.copy()
                display_rejected["Refund Date"] = display_rejected["refund_date"].dt.strftime("%Y-%m-%d %H:%M")
                
                display_cols = ["refund_id", "sale_id", "invoice_no", "refund_date", "product_name", "quantity", "report_total", "reason"]
                display_df = display_rejected[display_cols].copy()
                display_df.columns = ["Refund ID", "Sale ID", "Invoice", "Refund Date", "Product", "Qty", "Rejected Amount", "Reason"]
                
                columns = [{'name': col, 'label': col, 'field': col, 'sortable': True} for col in display_df.columns]
                ui.table(columns=columns, rows=display_df.to_dict('records'), row_key='Refund ID', pagination=20).classes('w-full')
                
                with ui.card().classes('w-full p-3 bg-red-50 mt-2'):
                    ui.label(f'Rejected Total: {money(summary["rejected_total"])} — NOT INCLUDED in Refund Total.').classes('text-red-700')
        
        # Pending
        with ui.tab_panel(tab_pending):
            if pending_df.empty:
                ui.label('No pending refunds found.').classes('text-gray-500')
            else:
                display_pending = pending_df.copy()
                display_pending["Refund Date"] = display_pending["refund_date"].dt.strftime("%Y-%m-%d %H:%M")
                
                display_cols = ["refund_id", "sale_id", "invoice_no", "refund_date", "product_name", "quantity", "report_total", "reason"]
                display_df = display_pending[display_cols].copy()
                display_df.columns = ["Refund ID", "Sale ID", "Invoice", "Refund Date", "Product", "Qty", "Pending Amount", "Reason"]
                
                columns = [{'name': col, 'label': col, 'field': col, 'sortable': True} for col in display_df.columns]
                ui.table(columns=columns, rows=display_df.to_dict('records'), row_key='Refund ID', pagination=20).classes('w-full')
                
                with ui.card().classes('w-full p-3 bg-orange-50 mt-2'):
                    ui.label(f'Pending Total: {money(summary["pending_total"])} — NOT INCLUDED in Refund Total.').classes('text-orange-700')
        
        # Export
        with ui.tab_panel(tab_export):
            ui.label('📤 Refund Report Export').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full gap-2 flex-wrap'):
                # PDF Export
                pdf_btn = ui.button('📄 Download PDF', on_click=lambda: export_pdf(actual_df, rejected_df, pending_df, report_from, report_to)).classes('flex-1 bg-red-500 text-white')
                
                # CSV Export
                csv_btn = ui.button('📊 Download CSV', on_click=lambda: export_csv(actual_df, report_from, report_to)).classes('flex-1 bg-green-500 text-white')


def export_pdf(actual_df, rejected_df, pending_df, report_from, report_to):
    """Export PDF report."""
    try:
        pdf_bytes = create_refund_report_pdf(actual_df, rejected_df, pending_df, report_from, report_to)
        ui.download(pdf_bytes, f'refund_report_{report_from.strftime("%Y%m%d")}_{report_to.strftime("%Y%m%d")}.pdf')
    except Exception as e:
        ui.notify(f'PDF export error: {e}', type='error', position='top')


def export_csv(actual_df, report_from, report_to):
    """Export CSV report."""
    try:
        csv_bytes = actual_df.to_csv(index=False).encode('utf-8-sig')
        ui.download(csv_bytes, f'actual_refund_register_{report_from.strftime("%Y%m%d")}_{report_to.strftime("%Y%m%d")}.csv')
    except Exception as e:
        ui.notify(f'CSV export error: {e}', type='error', position='top')


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
