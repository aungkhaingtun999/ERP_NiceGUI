"""
==============================================================================
REFUND REPORT
ERP ENTERPRISE REFUND REPORT v5.0
Tax-aware Refund Reporting with Enhanced Features
==============================================================================
"""

import io
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.enums import TA_CENTER

from database import db
from auth import require_login

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Refund Report v5.0",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
.report-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}
.report-title {
    color: white;
    font-size: 2.5em;
    font-weight: bold;
    margin: 0;
}
.report-subtitle {
    color: #e0e0e0;
    font-size: 1.2em;
    margin: 5px 0 0 0;
}
.kpi-card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# AUTHENTICATION
# ==============================================================================

user = require_login()

# ==============================================================================
# SESSION STATE
# ==============================================================================

if "selected_refund_id" not in st.session_state:
    st.session_state.selected_refund_id = None

# ==============================================================================
# LOAD REPORT DATA
# ==============================================================================

@st.cache_data(ttl=60)
def get_refund_report():
    """Fetch refund report data from database"""
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
        st.error(f"Error loading refund data: {e}")
        return pd.DataFrame()

df = get_refund_report()

# ==============================================================================
# DATA PREPROCESSING
# ==============================================================================

def preprocess_data(df):
    """Preprocess and normalize dataframe columns"""
    
    # Safe numeric columns
    numeric_columns = [
        "quantity", "unit_price", "item_total",
        "refund_amount", "refund_net_amount",
        "refund_tax_amount", "refund_total_amount",
    ]
    
    for col in numeric_columns:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    # Date conversion
    df["refund_date"] = pd.to_datetime(df["refund_date"], errors="coerce")
    
    # Status normalization
    if "status" not in df.columns:
        df["status"] = "COMPLETED"
    df["status"] = df["status"].fillna("").astype(str).str.strip().str.upper()
    
    # Text normalization
    text_columns = [
        "invoice_no", "cashier_name", "warehouse_name",
        "product_name", "processed_by", "reason",
    ]
    
    for col in text_columns:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    
    # V4 Report amounts
    df["report_net"] = df["refund_net_amount"]
    df["report_tax"] = df["refund_tax_amount"]
    df["report_total"] = df["refund_total_amount"]
    
    # Legacy fallback
    legacy_mask = (df["report_total"] == 0) & (df["item_total"] != 0)
    df.loc[legacy_mask, "report_total"] = df.loc[legacy_mask, "item_total"]
    
    legacy_net_mask = (df["report_net"] == 0) & (df["item_total"] != 0)
    df.loc[legacy_net_mask, "report_net"] = df.loc[legacy_net_mask, "item_total"]
    
    return df

if not df.empty:
    df = preprocess_data(df)

# ==============================================================================
# HEADER SECTION
# ==============================================================================

st.markdown("""
<div class="report-header">
    <h1 class="report-title">📊 Refund Report</h1>
    <p class="report-subtitle">ERP Enterprise Refund Reporting System v5.0</p>
</div>
""", unsafe_allow_html=True)

# Display current date/time
current_datetime = datetime.now()
st.caption(f"Generated on: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

# ==============================================================================
# EMPTY DATA CHECK
# ==============================================================================

if df.empty:
    st.info("No refund records found in the database.")
    if st.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# ==============================================================================
# SIDEBAR FILTERS
# ==============================================================================

with st.sidebar:
    st.markdown("## 🔍 Report Filters")
    st.markdown("### 📅 Date Range")
    
    # Date range presets
    date_presets = {
        "Today": (date.today(), date.today()),
        "Yesterday": (date.today() - timedelta(days=1), date.today() - timedelta(days=1)),
        "Last 7 Days": (date.today() - timedelta(days=7), date.today()),
        "Last 30 Days": (date.today() - timedelta(days=30), date.today()),
        "This Month": (date.today().replace(day=1), date.today()),
        "This Year": (date.today().replace(month=1, day=1), date.today()),
        "Custom Range": None,
    }
    
    selected_preset = st.selectbox(
        "Quick Select",
        list(date_presets.keys()),
        index=4,
        key="date_preset"
    )
    
    if selected_preset == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input("From Date", value=date.today().replace(day=1))
        with col2:
            to_date = st.date_input("To Date", value=date.today())
    else:
        from_date, to_date = date_presets[selected_preset]
        st.info(f"From: {from_date}\n\nTo: {to_date}")
    
    st.divider()
    st.markdown("### 🏷️ Quick Filters")
    
    # Invoice search
    invoice_search = st.text_input("Search Invoice No", placeholder="Enter invoice number...")
    
    # Cashier filter
    cashier_options = sorted(df["cashier_name"].dropna().unique().tolist())
    if cashier_options:
        cashier_filter = st.multiselect("Cashier", cashier_options)
    else:
        cashier_filter = []
    
    # Warehouse filter
    warehouse_options = sorted(df["warehouse_name"].dropna().unique().tolist())
    if warehouse_options:
        warehouse_filter = st.multiselect("Warehouse", warehouse_options)
    else:
        warehouse_filter = []
    
    # Status filter
    status_options = ["PENDING", "COMPLETED", "REJECTED"]
    status_filter = st.multiselect("Status", status_options, default=["COMPLETED"])
    
    st.divider()
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()

# ==============================================================================
# APPLY FILTERS
# ==============================================================================

filtered = df.copy()

# Date filter
filtered = filtered[
    (filtered["refund_date"].dt.date >= from_date) &
    (filtered["refund_date"].dt.date <= to_date)
]

# Invoice search
if invoice_search:
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

# ==============================================================================
# KPI METRICS
# ==============================================================================

total_refunds = filtered["refund_id"].nunique()
pending = (filtered["status"] == "PENDING").sum()
completed = (filtered["status"] == "COMPLETED").sum()
rejected = (filtered["status"] == "REJECTED").sum()
total_net = filtered["report_net"].sum()
total_tax = filtered["report_tax"].sum()
total_refund = filtered["report_total"].sum()
avg_refund = total_refund / total_refunds if total_refunds > 0 else 0

# Display KPI Cards
st.markdown("### 📈 Key Performance Indicators")
kpi_cols = st.columns(5)

with kpi_cols[0]:
    st.metric("Total Refunds", f"{total_refunds:,}")

with kpi_cols[1]:
    st.metric("Pending", f"{pending:,}")

with kpi_cols[2]:
    st.metric("Completed", f"{completed:,}")

with kpi_cols[3]:
    st.metric("Rejected", f"{rejected:,}")

with kpi_cols[4]:
    st.metric("Total Amount", f"{total_refund:,.2f} MMK")

# Financial Summary
st.markdown("### 💰 Financial Summary")
fin_cols = st.columns(4)

with fin_cols[0]:
    st.metric("Refund Net", f"{total_net:,.2f} MMK")

with fin_cols[1]:
    st.metric("Refund Tax", f"{total_tax:,.2f} MMK")

with fin_cols[2]:
    st.metric("Refund Total", f"{total_refund:,.2f} MMK")

with fin_cols[3]:
    st.metric("Average Refund", f"{avg_refund:,.2f} MMK")

# ==============================================================================
# PDF GENERATOR
# ==============================================================================

def create_refund_pdf(header, items, report_type="detailed"):
    """Generate PDF for refund report"""
    buffer = io.BytesIO()
    
    if report_type == "full":
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    else:
        doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    content = []
    content.append(Paragraph("REFUND REPORT", title_style))
    content.append(Spacer(1, 10))
    
    if report_type == "detailed":
        header_text = f"""
        <b>Refund ID:</b> {header.get('refund_id', '')}<br/>
        <b>Invoice:</b> {header.get('invoice_no', '')}<br/>
        <b>Status:</b> {header.get('status', '')}<br/>
        <b>Cashier:</b> {header.get('cashier_name', '')}<br/>
        <b>Warehouse:</b> {header.get('warehouse_name', '')}<br/>
        <b>Reason:</b> {header.get('reason', '')}
        """
        content.append(Paragraph(header_text, styles["Normal"]))
        content.append(Spacer(1, 15))
        
        table_data = [["Product", "Qty", "Unit Price", "Net", "Tax", "Total"]]
        
        total_net_val = 0
        total_tax_val = 0
        total_amount_val = 0
        
        for item in items:
            net = float(item.get("refund_net_amount", item.get("item_total", 0)) or 0)
            tax = float(item.get("refund_tax_amount", 0) or 0)
            total = float(item.get("refund_total_amount", item.get("item_total", 0)) or 0)
            
            total_net_val += net
            total_tax_val += tax
            total_amount_val += total
            
            table_data.append([
                item.get("product_name", ""),
                f"{float(item.get('quantity', 0) or 0):.2f}",
                f"{float(item.get('unit_price', 0) or 0):,.2f}",
                f"{net:,.2f}",
                f"{tax:,.2f}",
                f"{total:,.2f}"
            ])
        
        table_data.append(["TOTAL", "", "", f"{total_net_val:,.2f}", 
                          f"{total_tax_val:,.2f}", f"{total_amount_val:,.2f}"])
        
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
        ]))
        
        content.append(table)
    
    else:
        table_data = [["Refund ID", "Invoice", "Date", "Status", "Cashier", 
                       "Warehouse", "Net", "Tax", "Total"]]
        
        for item in items:
            table_data.append([
                str(item.get("refund_id", "")),
                item.get("invoice_no", ""),
                str(item.get("refund_date", ""))[:10],
                item.get("status", ""),
                item.get("cashier_name", ""),
                item.get("warehouse_name", ""),
                f"{float(item.get('report_net', 0) or 0):,.2f}",
                f"{float(item.get('report_tax', 0) or 0):,.2f}",
                f"{float(item.get('report_total', 0) or 0):,.2f}"
            ])
        
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (6, 1), (-1, -1), "RIGHT"),
        ]))
        
        content.append(table)
    
    doc.build(content)
    buffer.seek(0)
    return buffer

# ==============================================================================
# REFUND SELECTOR
# ==============================================================================

st.divider()
st.markdown("### 🔎 Refund Details")

if filtered.empty:
    st.warning("No refund records match the selected filters.")
else:
    # Build refund selector
    selector_options = []
    for _, row in filtered.iterrows():
        refund_id = row["refund_id"]
        invoice_no = row["invoice_no"]
        status = row["status"]
        total = float(row["report_total"] or 0)
        date_str = row["refund_date"].strftime("%Y-%m-%d") if pd.notna(row["refund_date"]) else ""
        
        selector_options.append((
            refund_id,
            f"#{refund_id} | {invoice_no} | {date_str} | {total:,.2f} MMK | {status}"
        ))
    
    selected_refund_id = st.selectbox(
        "Select Refund",
        options=[item[0] for item in selector_options],
        format_func=lambda refund_id: next(
            (item[1] for item in selector_options if item[0] == refund_id),
            str(refund_id)
        ),
        key="refund_selector"
    )
    
    selected_rows = filtered[filtered["refund_id"] == selected_refund_id]
    
    if not selected_rows.empty:
        selected_row = selected_rows.iloc[0]
        
        st.markdown(f"#### Refund #{selected_refund_id}")
        
        header_cols = st.columns(4)
        with header_cols[0]:
            st.markdown("**Invoice**")
            st.write(selected_row["invoice_no"])
        with header_cols[1]:
            st.markdown("**Status**")
            st.write(selected_row["status"])
        with header_cols[2]:
            st.markdown("**Cashier**")
            st.write(selected_row["cashier_name"])
        with header_cols[3]:
            st.markdown("**Warehouse**")
            st.write(selected_row["warehouse_name"])
        
        detail_cols = st.columns(2)
        with detail_cols[0]:
            if pd.notna(selected_row["refund_date"]):
                st.markdown("**Refund Date**")
                st.write(selected_row["refund_date"].strftime("%Y-%m-%d %H:%M:%S"))
        with detail_cols[1]:
            st.markdown("**Reason**")
            st.write(selected_row["reason"] if selected_row["reason"] else "-")
        
        st.divider()
        
        selected_net = float(selected_row["report_net"] or 0)
        selected_tax = float(selected_row["report_tax"] or 0)
        selected_total = float(selected_row["report_total"] or 0)
        
        amount_cols = st.columns(3)
        with amount_cols[0]:
            st.metric("Refund Net", f"{selected_net:,.2f} MMK")
        with amount_cols[1]:
            st.metric("Refund Tax", f"{selected_tax:,.2f} MMK")
        with amount_cols[2]:
            st.metric("Refund Total", f"{selected_total:,.2f} MMK")
        
        st.divider()
        
        # Load selected refund items
        try:
            items_response = (
                db()
                .table("refund_detail_view")
                .select("*")
                .eq("refund_id", selected_refund_id)
                .execute()
            )
            selected_items = items_response.data or []
        except Exception as e:
            selected_items = []
            st.error(f"Unable to load refund details: {e}")
        
        if selected_items:
            detail_df = pd.DataFrame(selected_items)
            
            detail_numeric_columns = [
                "quantity", "unit_price", "item_total",
                "refund_net_amount", "refund_tax_amount", "refund_total_amount"
            ]
            
            for col in detail_numeric_columns:
                if col not in detail_df.columns:
                    detail_df[col] = 0
                detail_df[col] = pd.to_numeric(detail_df[col], errors="coerce").fillna(0)
            
            detail_df["display_net"] = detail_df["refund_net_amount"]
            legacy_net = (detail_df["display_net"].isna() | (detail_df["display_net"] == 0)) & \
                        (detail_df["item_total"] != 0)
            detail_df.loc[legacy_net, "display_net"] = detail_df.loc[legacy_net, "item_total"]
            
            detail_df["display_tax"] = detail_df["refund_tax_amount"].fillna(0)
            detail_df["display_total"] = detail_df["refund_total_amount"]
            legacy_total = (detail_df["display_total"].isna() | (detail_df["display_total"] == 0)) & \
                          (detail_df["item_total"] != 0)
            detail_df.loc[legacy_total, "display_total"] = detail_df.loc[legacy_total, "item_total"]
            
            selected_detail_display = pd.DataFrame({
                "Product": detail_df["product_name"],
                "Qty": detail_df["quantity"],
                "Unit Price": detail_df["unit_price"],
                "Refund Net": detail_df["display_net"],
                "Refund Tax": detail_df["display_tax"],
                "Refund Total": detail_df["display_total"],
            })
            
            st.subheader("📦 Refund Items")
            
            st.dataframe(
                selected_detail_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Product": st.column_config.TextColumn("Product", width="large"),
                    "Qty": st.column_config.NumberColumn("Qty", format="%.2f"),
                    "Unit Price": st.column_config.NumberColumn("Unit Price", format="%,.2f MMK"),
                    "Refund Net": st.column_config.NumberColumn("Refund Net", format="%,.2f MMK"),
                    "Refund Tax": st.column_config.NumberColumn("Refund Tax", format="%,.2f MMK"),
                    "Refund Total": st.column_config.NumberColumn("Refund Total", format="%,.2f MMK"),
                }
            )
            
            detail_net = detail_df["display_net"].sum()
            detail_tax = detail_df["display_tax"].sum()
            detail_total = detail_df["display_total"].sum()
            
            total_cols = st.columns(3)
            with total_cols[0]:
                st.metric("Net Total", f"{detail_net:,.2f} MMK")
            with total_cols[1]:
                st.metric("Tax Total", f"{detail_tax:,.2f} MMK")
            with total_cols[2]:
                st.metric("Grand Total", f"{detail_total:,.2f} MMK")
            
            st.markdown("#### 📥 Download Options")
            
            download_cols = st.columns(4)
            
            with download_cols[0]:
                pdf_file = create_refund_pdf(selected_row.to_dict(), selected_items, "detailed")
                st.download_button(
                    "📄 PDF",
                    pdf_file,
                    f"refund_{selected_refund_id}.pdf",
                    "application/pdf",
                    key=f"pdf_{selected_refund_id}",
                    use_container_width=True
                )
            
            with download_cols[1]:
                csv_file = selected_detail_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📊 CSV",
                    csv_file,
                    f"refund_{selected_refund_id}.csv",
                    "text/csv",
                    key=f"csv_{selected_refund_id}",
                    use_container_width=True
                )
            
            with download_cols[2]:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    selected_detail_display.to_excel(writer, index=False, sheet_name="Refund Items")
                excel_buffer.seek(0)
                st.download_button(
                    "📗 Excel",
                    excel_buffer.getvalue(),
                    f"refund_{selected_refund_id}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"excel_{selected_refund_id}",
                    use_container_width=True
                )
            
            with download_cols[3]:
                html_table = selected_detail_display.to_html(index=False)
                html_content = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Refund {selected_refund_id}</title>
                </head>
                <body>
                    <h2>Refund Report</h2>
                    <p>
                        <b>Refund ID:</b> {selected_refund_id}<br>
                        <b>Invoice:</b> {selected_row["invoice_no"]}<br>
                        <b>Status:</b> {selected_row["status"]}
                    </p>
                    {html_table}
                    <h3>Net: {detail_net:,.2f} MMK</h3>
                    <h3>Tax: {detail_tax:,.2f} MMK</h3>
                    <h3>Total: {detail_total:,.2f} MMK</h3>
                </body>
                </html>
                """
                st.download_button(
                    "🖨️ HTML",
                    html_content,
                    f"refund_{selected_refund_id}.html",
                    "text/html",
                    key=f"html_{selected_refund_id}",
                    use_container_width=True
                )
        else:
            st.warning("No refund item records found.")

# ==============================================================================
# ANALYTICS SECTION
# ==============================================================================

st.divider()
st.markdown("### 📊 Refund Analytics")

if not filtered.empty:
    analytics_tab1, analytics_tab2 = st.tabs(["📈 Trends", "🏆 Top Products"])
    
    with analytics_tab1:
        daily_refunds = (
            filtered.groupby(filtered["refund_date"].dt.date)
            .agg({
                "refund_id": "count",
                "report_total": "sum"
            })
            .reset_index()
            .rename(columns={
                "refund_date": "Date",
                "refund_id": "Number of Refunds",
                "report_total": "Total Amount"
            })
        )
        
        trend_col1, trend_col2 = st.columns(2)
        
        with trend_col1:
            st.markdown("**Number of Refunds Over Time**")
            st.line_chart(daily_refunds.set_index("Date")["Number of Refunds"])
        
        with trend_col2:
            st.markdown("**Total Refund Amount Over Time**")
            st.line_chart(daily_refunds.set_index("Date")["Total Amount"])
    
    with analytics_tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 10 Products by Quantity")
            top_products_qty = (
                filtered.groupby("product_name")["quantity"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            st.bar_chart(top_products_qty)
        
        with col2:
            st.subheader("💰 Top 10 Products by Value")
            top_products_value = (
                filtered.groupby("product_name")["report_total"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            st.bar_chart(top_products_value)
        
        st.subheader("📊 Refund Status Distribution")
        status_data = filtered.groupby("status")["refund_id"].nunique()
        if not status_data.empty:
            fig = px.pie(
                values=status_data.values,
                names=status_data.index,
                title="Refund Status",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("👤 Top 5 Cashiers by Refund Value")
        cashier_ranking = (
            filtered.groupby("cashier_name")["report_total"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        st.bar_chart(cashier_ranking)

else:
    st.warning("No data available for analytics with current filters.")

# ==============================================================================
# FULL REPORT TABLE
# ==============================================================================

st.divider()
st.markdown("### 📋 Full Report Table")

if not filtered.empty:
    display_columns = [
        "refund_id", "invoice_no", "refund_date", "status",
        "product_name", "quantity", "unit_price", "report_net",
        "report_tax", "report_total", "cashier_name", "warehouse_name"
    ]
    
    display_df = filtered[display_columns].copy()
    display_df["refund_date"] = display_df["refund_date"].dt.strftime("%Y-%m-%d %H:%M")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "refund_id": st.column_config.NumberColumn("Refund ID", format="%d"),
            "invoice_no": st.column_config.TextColumn("Invoice"),
            "refund_date": st.column_config.TextColumn("Date"),
            "status": st.column_config.TextColumn("Status"),
            "product_name": st.column_config.TextColumn("Product", width="large"),
            "quantity": st.column_config.NumberColumn("Qty", format="%.2f"),
            "unit_price": st.column_config.NumberColumn("Unit Price", format="%,.2f"),
            "report_net": st.column_config.NumberColumn("Net", format="%,.2f"),
            "report_tax": st.column_config.NumberColumn("Tax", format="%,.2f"),
            "report_total": st.column_config.NumberColumn("Total", format="%,.2f"),
            "cashier_name": st.column_config.TextColumn("Cashier"),
            "warehouse_name": st.column_config.TextColumn("Warehouse"),
        }
    )
    
    # Export full report
    st.markdown("#### 📥 Export Full Report")
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        # Excel export
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            display_df.to_excel(writer, index=False, sheet_name="Refund Report")
            # Add summary sheet
            summary_data = {
                "Metric": ["Total Refunds", "Total Net", "Total Tax", "Total Amount"],
                "Value": [total_refunds, total_net, total_tax, total_refund]
            }
            pd.DataFrame(summary_data).to_excel(writer, index=False, sheet_name="Summary")
        excel_buffer.seek(0)
        
        st.download_button(
            "📗 Excel Report",
            excel_buffer.getvalue(),
            f"refund_report_{from_date}_to_{to_date}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="full_excel",
            use_container_width=True
        )
    
    with export_col2:
        # CSV export
        csv_file = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📊 CSV Report",
            csv_file,
            f"refund_report_{from_date}_to_{to_date}.csv",
            "text/csv",
            key="full_csv",
            use_container_width=True
        )
    
    with export_col3:
        # PDF export
        full_pdf = create_refund_pdf(None, filtered.to_dict('records'), "full")
        st.download_button(
            "📄 PDF Report",
            full_pdf,
            f"refund_report_{from_date}_to_{to_date}.pdf",
            "application/pdf",
            key="full_pdf",
            use_container_width=True
        )

else:
    st.warning("No data available for the full report table.")
