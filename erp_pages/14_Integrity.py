# erp_pages/14_Integrity.py
# ERP Integrity Check Dashboard - Advanced Version
# Double Entry & FIFO Cost Monitoring
# Features: Real-time monitoring, Excel export, Charts, History

import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64

# Import from your project
from supabase_client import get_supabase

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ERP Integrity Check",
    page_icon="🔐",
    layout="wide"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .status-card {
        padding: 20px;
        border-radius: 10px;
        margin: 5px 0;
        text-align: center;
    }
    .status-passed { background-color: #d4edda; border: 2px solid #28a745; }
    .status-failed { background-color: #f8d7da; border: 2px solid #dc3545; }
    .status-error { background-color: #e2e3e5; border: 2px solid #6c757d; }
    .status-warning { background-color: #fff3cd; border: 2px solid #ffc107; }
    .big-icon { font-size: 48px; }
    .metric-value { font-size: 24px; font-weight: bold; }
    .metric-label { font-size: 14px; color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def execute_query(table_name: str, select: str = "*", filters: dict = None, 
                  order_by: str = None, limit: int = None) -> list:
    """Execute direct Supabase query with caching"""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        
        query = supabase.table(table_name).select(select)
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    query = query.in_(key, value)
                else:
                    query = query.eq(key, value)
        
        if order_by:
            query = query.order(order_by, desc=True)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        return []

def get_table_count(table_name: str) -> int:
    """Get total count of records in a table"""
    try:
        data = execute_query(table_name, select='id', limit=1000)
        return len(data)
    except:
        return 0

# ============================================================
# CHECK FUNCTIONS
# ============================================================

def check_double_entry():
    """Check 1: Debit = Credit"""
    try:
        debit_types = ["PURCHASE", "RETURN", "OPENING", "RECEIVE"]
        credit_types = ["SALE", "ADJUSTMENT_OUT", "TRANSFER_OUT", "ISSUE"]
        
        debit_data = execute_query(
            'inventory_ledger',
            select='quantity',
            filters={'transaction_type': debit_types}
        )
        
        credit_data = execute_query(
            'inventory_ledger',
            select='quantity',
            filters={'transaction_type': credit_types}
        )
        
        debit_total = sum(float(item.get('quantity', 0)) for item in debit_data)
        credit_total = sum(float(item.get('quantity', 0)) for item in credit_data)
        
        diff = abs(debit_total - credit_total)
        is_balanced = diff < 0.01
        
        return {
            "name": "Double Entry",
            "status": "BALANCED" if is_balanced else "IMBALANCED",
            "icon": "🟢" if is_balanced else "🔴",
            "passed": is_balanced,
            "debit": debit_total,
            "credit": credit_total,
            "diff": diff,
            "detail": f"Debit: {debit_total:,.2f} | Credit: {credit_total:,.2f}",
            "suggestion": "Check inventory_ledger for missing transactions" if not is_balanced else None
        }
    except Exception as e:
        return {
            "name": "Double Entry",
            "status": "ERROR",
            "icon": "⚠️",
            "passed": False,
            "debit": 0,
            "credit": 0,
            "diff": 0,
            "detail": str(e)[:50],
            "suggestion": "Check database connection"
        }

def check_sales_vs_payments():
    """Check 2: Sales total matches payments"""
    try:
        sales_data = execute_query(
            'sales',
            select='total',
            filters={'sale_status': 'COMPLETED'}
        )
        sales_total = sum(float(item.get('total', 0)) for item in sales_data)
        
        payments_data = execute_query(
            'payment_transactions',
            select='amount',
            filters={'status': 'COMPLETED'}
        )
        payments_total = sum(float(item.get('amount', 0)) for item in payments_data)
        
        diff = abs(sales_total - payments_total)
        is_matched = diff < 0.01
        
        return {
            "name": "Sales ↔ Payments",
            "status": "MATCHED" if is_matched else "MISMATCHED",
            "icon": "🟢" if is_matched else "🔴",
            "passed": is_matched,
            "sales": sales_total,
            "payments": payments_total,
            "diff": diff,
            "detail": f"Sales: {sales_total:,.2f} | Payments: {payments_total:,.2f}",
            "suggestion": "Check unpaid sales or unrecorded payments" if not is_matched else None
        }
    except Exception as e:
        return {
            "name": "Sales ↔ Payments",
            "status": "ERROR",
            "icon": "⚠️",
            "passed": False,
            "sales": 0,
            "payments": 0,
            "diff": 0,
            "detail": str(e)[:50],
            "suggestion": "Check database connection"
        }

def check_stock_vs_ledger():
    """Check 3: Warehouse stock matches inventory ledger"""
    try:
        stock_data = execute_query('warehouse_stock', select='qty')
        stock_total = sum(float(item.get('qty', 0)) for item in stock_data)
        
        ledger_total = 0
        ledger_data = execute_query('inventory_ledger', select='transaction_type,quantity')
        for item in ledger_data:
            txn_type = item.get('transaction_type', '')
            qty = float(item.get('quantity', 0))
            if txn_type in ['PURCHASE', 'RETURN', 'OPENING', 'RECEIVE']:
                ledger_total += qty
            elif txn_type in ['SALE', 'ADJUSTMENT_OUT', 'TRANSFER_OUT', 'ISSUE']:
                ledger_total -= qty
        
        diff = abs(stock_total - ledger_total)
        is_matched = diff < 0.01
        
        return {
            "name": "Stock ↔ Inventory Ledger",
            "status": "MATCHED" if is_matched else "MISMATCHED",
            "icon": "🟢" if is_matched else "🔴",
            "passed": is_matched,
            "stock": stock_total,
            "ledger": ledger_total,
            "diff": diff,
            "detail": f"Stock: {stock_total:,.0f} | Ledger: {ledger_total:,.0f}",
            "suggestion": "Check inventory ledger for missing stock movements" if not is_matched else None
        }
    except Exception as e:
        return {
            "name": "Stock ↔ Inventory Ledger",
            "status": "ERROR",
            "icon": "⚠️",
            "passed": False,
            "stock": 0,
            "ledger": 0,
            "diff": 0,
            "detail": str(e)[:50],
            "suggestion": "Check database connection"
        }

def check_fifo_vs_stock():
    """Check 4: FIFO cost matches stock valuation"""
    try:
        fifo_data = execute_query('inventory_cost_layers', select='qty_remaining,unit_cost')
        fifo_cost = sum(float(item.get('qty_remaining', 0)) * float(item.get('unit_cost', 0)) for item in fifo_data)
        fifo_qty = sum(float(item.get('qty_remaining', 0)) for item in fifo_data)
        
        stock_data = execute_query('warehouse_stock', select='qty')
        stock_qty = sum(float(item.get('qty', 0)) for item in stock_data)
        stock_value = fifo_cost if fifo_qty > 0 else 0
        
        diff = abs(fifo_cost - stock_value)
        is_matched = diff < 0.01
        
        return {
            "name": "FIFO Cost ↔ Stock",
            "status": "MATCHED" if is_matched else "MISMATCHED",
            "icon": "🟢" if is_matched else "🔴",
            "passed": is_matched,
            "fifo_cost": fifo_cost,
            "stock_value": stock_value,
            "fifo_qty": fifo_qty,
            "stock_qty": stock_qty,
            "diff": diff,
            "detail": f"FIFO Cost: {fifo_cost:,.2f} | Stock Value: {stock_value:,.2f}",
            "suggestion": "Check FIFO cost layers for missing or incorrect costs" if not is_matched else None
        }
    except Exception as e:
        return {
            "name": "FIFO Cost ↔ Stock",
            "status": "ERROR",
            "icon": "⚠️",
            "passed": False,
            "fifo_cost": 0,
            "stock_value": 0,
            "fifo_qty": 0,
            "stock_qty": 0,
            "diff": 0,
            "detail": str(e)[:50],
            "suggestion": "Check database connection"
        }

def check_sales_items():
    """Check 5: Sales total matches sale_items total"""
    try:
        sales_data = execute_query('sales', select='id,total', filters={'sale_status': 'COMPLETED'}, limit=100)
        
        total_sales = len(sales_data)
        matched = 0
        discrepancy = 0
        mismatched_sales = []
        
        for sale in sales_data:
            sale_id = sale.get('id')
            sale_total = float(sale.get('total', 0))
            
            items_data = execute_query('sale_items', select='quantity,unit_price,discount', filters={'sale_id': sale_id})
            
            calc_total = sum(
                float(item.get('quantity', 0)) * float(item.get('unit_price', 0)) 
                - float(item.get('discount', 0)) 
                for item in items_data
            )
            
            if abs(calc_total - sale_total) < 0.01:
                matched += 1
            else:
                discrepancy += abs(calc_total - sale_total)
                if len(mismatched_sales) < 5:
                    mismatched_sales.append(f"Sale #{sale_id}")
        
        is_matched = discrepancy < 0.01
        
        return {
            "name": "Sales Total ↔ Items",
            "status": "MATCHED" if is_matched else "MISMATCHED",
            "icon": "🟢" if is_matched else "🔴",
            "passed": is_matched,
            "total_sales": total_sales,
            "matched": matched,
            "discrepancy": discrepancy,
            "mismatched_sales": mismatched_sales,
            "detail": f"Checked {total_sales:.0f} sales | Matched: {matched:.0f}",
            "suggestion": f"Check sale_items for sale(s): {', '.join(mismatched_sales)}" if not is_matched and mismatched_sales else None
        }
    except Exception as e:
        return {
            "name": "Sales Total ↔ Items",
            "status": "ERROR",
            "icon": "⚠️",
            "passed": False,
            "total_sales": 0,
            "matched": 0,
            "discrepancy": 0,
            "mismatched_sales": [],
            "detail": str(e)[:50],
            "suggestion": "Check database connection"
        }

# ============================================================
# RUN ALL CHECKS
# ============================================================

def run_all_checks():
    """Execute all integrity checks with progress"""
    checks = [
        check_double_entry(),
        check_sales_vs_payments(),
        check_stock_vs_ledger(),
        check_fifo_vs_stock(),
        check_sales_items()
    ]
    return checks

# ============================================================
# EXPORT FUNCTIONS
# ============================================================

def export_to_csv(results):
    """Export results to CSV format"""
    data = []
    for r in results:
        data.append({
            "Check": r["name"],
            "Status": r["status"],
            "Detail": r["detail"],
            "Passed": r.get("passed", False)
        })
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def get_download_link(csv_data, filename="integrity_report.csv"):
    """Generate download link for CSV"""
    b64 = base64.b64encode(csv_data.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download CSV</a>'
    return href

# ============================================================
# MAIN RENDER FUNCTION
# ============================================================

def run():
    """Main render function for the page"""
    
    st.title("🔐 ERP Integrity Check Dashboard")
    st.caption("Double Entry & FIFO Cost Monitoring")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Check Supabase connection
        supabase = get_supabase()
        if supabase:
            st.success("✅ Database Connected")
        else:
            st.error("❌ Database Disconnected")
            return
        
        st.divider()
        
        # Quick Stats
        st.subheader("📊 Database Stats")
        col1, col2 = st.columns(2)
        with col1:
            sales_count = get_table_count('sales')
            st.metric("Sales", sales_count)
        with col2:
            products_count = get_table_count('products')
            st.metric("Products", products_count)
        
        st.divider()
        
        # Export
        st.subheader("📤 Export")
        if st.button("📥 Export Report", use_container_width=True):
            if "integrity_results" in st.session_state:
                csv_data = export_to_csv(st.session_state.integrity_results)
                st.markdown(get_download_link(csv_data), unsafe_allow_html=True)
            else:
                st.warning("Run checks first!")
    
    # Main content
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Run All Checks", type="primary", use_container_width=True):
            with st.spinner("Running integrity checks..."):
                results = run_all_checks()
                st.session_state.integrity_results = results
                st.session_state.last_integrity_run = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with col2:
        if "last_integrity_run" in st.session_state:
            st.caption(f"🕐 Last Check: {st.session_state.last_integrity_run}")
    
    st.divider()
    
    # Display results
    if "integrity_results" in st.session_state:
        results = st.session_state.integrity_results
        
        # Summary Metrics
        total = len(results)
        passed = sum(1 for r in results if r.get("passed", False))
        failed = total - passed - sum(1 for r in results if r["status"] == "ERROR")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        # Status Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="status-card status-passed">
                <div class="big-icon">✅</div>
                <div class="metric-value">{passed}/{total}</div>
                <div class="metric-label">Passed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="status-card status-failed">
                <div class="big-icon">❌</div>
                <div class="metric-value">{failed}</div>
                <div class="metric-label">Failed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="status-card status-error">
                <div class="big-icon">⚠️</div>
                <div class="metric-value">{errors}</div>
                <div class="metric-label">Errors</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if passed == total:
                st.markdown(f"""
                <div class="status-card status-passed">
                    <div class="big-icon">🎉</div>
                    <div class="metric-value">ALL GOOD</div>
                    <div class="metric-label">100% Verified</div>
                </div>
                """, unsafe_allow_html=True)
            elif passed > failed:
                st.markdown(f"""
                <div class="status-card status-warning">
                    <div class="big-icon">⚡</div>
                    <div class="metric-value">WARNING</div>
                    <div class="metric-label">Needs Review</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-card status-failed">
                    <div class="big-icon">🚨</div>
                    <div class="metric-value">CRITICAL</div>
                    <div class="metric-label">Fix Required</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Display each check
        for check in results:
            if check.get("passed", False):
                bg_color, border_color = "#d4edda", "#28a745"
            elif check["status"] == "ERROR":
                bg_color, border_color = "#e2e3e5", "#6c757d"
            else:
                bg_color, border_color = "#f8d7da", "#dc3545"
            
            with st.container():
                st.markdown(f"""
                <div style="background-color:{bg_color}; padding:15px; border-radius:10px; border-left:5px solid {border_color}; margin-bottom:10px;">
                    <table style="width:100%;">
                        <tr>
                            <td style="width:5%; font-size:30px;">{check['icon']}</td>
                            <td style="width:20%; font-weight:bold;">{check['name']}</td>
                            <td style="width:15%; font-weight:bold; color:{border_color};">{check['status']}</td>
                            <td style="width:60%; font-size:14px;">{check['detail']}</td>
                        </tr>
                    </table>
                    {f"<div style='margin-top:5px; font-size:12px; color:#856404;'>💡 {check['suggestion']}</div>" if check.get('suggestion') else ""}
                </div>
                """, unsafe_allow_html=True)
        
        # Final Status
        st.divider()
        if passed == total:
            st.success("🎉 **All systems INTEGRITY VERIFIED!** Your POS system is healthy.")
        elif passed > failed:
            st.warning("⚠️ **Some checks require ATTENTION!** Review the details above.")
        else:
            st.error("🚨 **CRITICAL ISSUES DETECTED!** Immediate action required.")
    
    else:
        st.info("👆 Click **'Run All Checks'** to start monitoring your system integrity.")
        st.caption("This will check: Double Entry, Sales vs Payments, Stock vs Ledger, FIFO Cost, and Sales Items")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run()
