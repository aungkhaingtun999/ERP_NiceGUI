# erp_pages/14_Integrity.py
# ERP Integrity Check Dashboard
# Double Entry & FIFO Cost Monitoring

import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from supabase import create_client

# Import from your project
from config import SUPABASE_URL, SUPABASE_KEY
from supabase_client import get_supabase

# ============================================================
# PAGE TITLE
# ============================================================

st.set_page_config(
    page_title="ERP Integrity Check",
    page_icon="🔐",
    layout="wide"
)

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def run_sql_query(query: str) -> list:
    """Execute SQL via Supabase RPC"""
    try:
        supabase = get_supabase()
        result = supabase.rpc('execute_sql', {'query': query}).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Query Error: {e}")
        return []

# ============================================================
# CHECK 1: DOUBLE ENTRY
# ============================================================

def check_double_entry():
    """Check 1: Debit = Credit"""
    query = """
    WITH daily_ledger AS (
        SELECT 
            COALESCE(SUM(CASE 
                WHEN transaction_type IN ('PURCHASE', 'RETURN', 'OPENING', 'RECEIVE') 
                THEN quantity ELSE 0 
            END), 0) as debit,
            COALESCE(SUM(CASE 
                WHEN transaction_type IN ('SALE', 'ADJUSTMENT_OUT', 'TRANSFER_OUT', 'ISSUE') 
                THEN quantity ELSE 0 
            END), 0) as credit
        FROM inventory_ledger
        WHERE DATE(created_at) = CURRENT_DATE
    )
    SELECT debit, credit, ABS(debit - credit) as diff
    FROM daily_ledger
    """
    
    data = run_sql_query(query)
    
    if data:
        debit = float(data[0].get('debit', 0))
        credit = float(data[0].get('credit', 0))
        diff = float(data[0].get('diff', 0))
        
        status = "BALANCED" if diff < 0.01 else "IMBALANCED"
        icon = "🟢" if status == "BALANCED" else "🔴"
        
        return {
            "name": "Double Entry",
            "status": status,
            "icon": icon,
            "debit": debit,
            "credit": credit,
            "diff": diff,
            "detail": f"Debit: {debit:,.2f} | Credit: {credit:,.2f} | Diff: {diff:,.2f}"
        }
    
    return {
        "name": "Double Entry",
        "status": "ERROR",
        "icon": "⚠️",
        "debit": 0,
        "credit": 0,
        "diff": 0,
        "detail": "No data available"
    }

# ============================================================
# CHECK 2: SALES ↔ PAYMENTS
# ============================================================

def check_sales_vs_payments():
    """Check 2: Sales total matches payments"""
    today = datetime.date.today().isoformat()
    
    sales_query = f"""
    SELECT COALESCE(SUM(total), 0) as total
    FROM sales
    WHERE sale_status = 'COMPLETED'
    AND DATE(created_at) = '{today}'
    """
    sales_data = run_sql_query(sales_query)
    sales_total = float(sales_data[0].get('total', 0)) if sales_data else 0
    
    payments_query = f"""
    SELECT COALESCE(SUM(amount), 0) as total
    FROM payment_transactions
    WHERE status = 'COMPLETED'
    AND DATE(created_at) = '{today}'
    """
    payments_data = run_sql_query(payments_query)
    payments_total = float(payments_data[0].get('total', 0)) if payments_data else 0
    
    diff = abs(sales_total - payments_total)
    status = "MATCHED" if diff < 0.01 else "MISMATCHED"
    icon = "🟢" if status == "MATCHED" else "🔴"
    
    return {
        "name": "Sales ↔ Payments",
        "status": status,
        "icon": icon,
        "sales": sales_total,
        "payments": payments_total,
        "diff": diff,
        "detail": f"Sales: {sales_total:,.2f} | Payments: {payments_total:,.2f} | Diff: {diff:,.2f}"
    }

# ============================================================
# CHECK 3: STOCK ↔ LEDGER
# ============================================================

def check_stock_vs_ledger():
    """Check 3: Warehouse stock matches inventory ledger"""
    stock_query = """
    SELECT COALESCE(SUM(qty), 0) as total
    FROM warehouse_stock
    """
    stock_data = run_sql_query(stock_query)
    stock_total = float(stock_data[0].get('total', 0)) if stock_data else 0
    
    ledger_query = """
    SELECT COALESCE(SUM(
        CASE 
            WHEN transaction_type IN ('PURCHASE', 'RETURN', 'OPENING', 'RECEIVE') THEN quantity
            WHEN transaction_type IN ('SALE', 'ADJUSTMENT_OUT', 'TRANSFER_OUT', 'ISSUE') THEN -quantity
            ELSE 0
        END
    ), 0) as total
    FROM inventory_ledger
    """
    ledger_data = run_sql_query(ledger_query)
    ledger_total = float(ledger_data[0].get('total', 0)) if ledger_data else 0
    
    diff = abs(stock_total - ledger_total)
    status = "MATCHED" if diff < 0.01 else "MISMATCHED"
    icon = "🟢" if status == "MATCHED" else "🔴"
    
    return {
        "name": "Stock ↔ Inventory Ledger",
        "status": status,
        "icon": icon,
        "stock": stock_total,
        "ledger": ledger_total,
        "diff": diff,
        "detail": f"Stock: {stock_total:,.0f} | Ledger: {ledger_total:,.0f} | Diff: {diff:,.0f}"
    }

# ============================================================
# CHECK 4: FIFO COST ↔ STOCK
# ============================================================

def check_fifo_vs_stock():
    """Check 4: FIFO cost matches stock valuation"""
    fifo_query = """
    SELECT 
        COALESCE(SUM(qty_remaining * unit_cost), 0) as cost,
        COALESCE(SUM(qty_remaining), 0) as qty
    FROM inventory_cost_layers
    """
    fifo_data = run_sql_query(fifo_query)
    fifo_cost = float(fifo_data[0].get('cost', 0)) if fifo_data else 0
    fifo_qty = float(fifo_data[0].get('qty', 0)) if fifo_data else 0
    
    stock_query = """
    SELECT 
        COALESCE(SUM(qty * COALESCE(unit_cost, 0)), 0) as value,
        COALESCE(SUM(qty), 0) as qty
    FROM warehouse_stock
    """
    stock_data = run_sql_query(stock_query)
    stock_value = float(stock_data[0].get('value', 0)) if stock_data else 0
    stock_qty = float(stock_data[0].get('qty', 0)) if stock_data else 0
    
    diff = abs(fifo_cost - stock_value)
    status = "MATCHED" if diff < 0.01 else "MISMATCHED"
    icon = "🟢" if status == "MATCHED" else "🔴"
    
    return {
        "name": "FIFO Cost ↔ Stock",
        "status": status,
        "icon": icon,
        "fifo_cost": fifo_cost,
        "stock_value": stock_value,
        "fifo_qty": fifo_qty,
        "stock_qty": stock_qty,
        "diff": diff,
        "detail": f"FIFO Cost: {fifo_cost:,.2f} | Stock Value: {stock_value:,.2f} | Diff: {diff:,.2f}"
    }

# ============================================================
# CHECK 5: SALES TOTAL ↔ ITEMS
# ============================================================

def check_sales_items():
    """Check 5: Sales total matches sale_items total"""
    today = datetime.date.today().isoformat()
    
    query = f"""
    WITH items_summary AS (
        SELECT 
            sale_id,
            COALESCE(SUM(quantity * unit_price - COALESCE(discount, 0)), 0) as calculated
        FROM sale_items
        GROUP BY sale_id
    )
    SELECT 
        COUNT(s.id) as total_sales,
        COALESCE(SUM(CASE 
            WHEN ABS(COALESCE(i.calculated, 0) - s.total) < 0.01 
            THEN 1 ELSE 0 
        END), 0) as matched_count,
        COALESCE(SUM(ABS(COALESCE(i.calculated, 0) - s.total)), 0) as discrepancy
    FROM sales s
    LEFT JOIN items_summary i ON s.id = i.sale_id
    WHERE s.sale_status = 'COMPLETED'
    AND DATE(s.created_at) = '{today}'
    """
    
    data = run_sql_query(query)
    
    if data:
        total = float(data[0].get('total_sales', 0))
        matched = float(data[0].get('matched_count', 0))
        discrepancy = float(data[0].get('discrepancy', 0))
        
        status = "MATCHED" if discrepancy < 0.01 else "MISMATCHED"
        icon = "🟢" if status == "MATCHED" else "🔴"
        
        return {
            "name": "Sales Total ↔ Items",
            "status": status,
            "icon": icon,
            "total_sales": total,
            "matched": matched,
            "discrepancy": discrepancy,
            "detail": f"Checked {total:.0f} sales | Matched: {matched:.0f} | Discrepancy: {discrepancy:,.2f}"
        }
    
    return {
        "name": "Sales Total ↔ Items",
        "status": "ERROR",
        "icon": "⚠️",
        "total_sales": 0,
        "matched": 0,
        "discrepancy": 0,
        "detail": "No data available"
    }

# ============================================================
# RUN ALL CHECKS
# ============================================================

def run_all_checks():
    """Execute all integrity checks"""
    checks = [
        check_double_entry(),
        check_sales_vs_payments(),
        check_stock_vs_ledger(),
        check_fifo_vs_stock(),
        check_sales_items()
    ]
    return checks

# ============================================================
# MAIN RENDER FUNCTION
# ============================================================

def run():
    """Main render function for the page"""
    
    st.title("🔐 ERP Integrity Check Dashboard")
    st.caption("Double Entry & FIFO Cost Monitoring")
    
    # Run button
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
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r["status"] in ["BALANCED", "MATCHED"])
        failed = sum(1 for r in results if r["status"] in ["IMBALANCED", "MISMATCHED"])
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Passed", f"{passed}/{total}", f"{passed/total*100:.0f}%")
        col2.metric("❌ Failed", failed)
        col3.metric("⚠️ Errors", errors)
        col4.metric("📊 Total", total)
        
        st.divider()
        
        # Display each check
        for check in results:
            if check["status"] in ["BALANCED", "MATCHED"]:
                bg_color = "#d4edda"
                border_color = "#28a745"
            elif check["status"] in ["IMBALANCED", "MISMATCHED"]:
                bg_color = "#f8d7da"
                border_color = "#dc3545"
            else:
                bg_color = "#e2e3e5"
                border_color = "#6c757d"
            
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
            </div>
            """, unsafe_allow_html=True)
        
        # Show pass/fail summary
        if passed == total:
            st.success("🎉 All systems INTEGRITY VERIFIED!")
        elif passed > failed:
            st.warning("⚠️ Some checks require ATTENTION!")
        else:
            st.error("🚨 CRITICAL ISSUES DETECTED!")
    
    else:
        st.info("👆 Click 'Run All Checks' to start monitoring")
        st.caption("This will check: Double Entry, Sales vs Payments, Stock vs Ledger, FIFO Cost, Sales Items")

# ============================================================
# MAIN (for standalone testing)
# ============================================================

if __name__ == "__main__":
    run()
