# erp_integrity_dashboard_schema_optimized.py
# POS ERP Integrity Check Dashboard
# Optimized for your exact table schema

import streamlit as st
import pandas as pd
import datetime
import json
import plotly.graph_objects as go
from supabase import create_client
import requests

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="POS ERP Integrity Dashboard",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SECRETS
# ============================================================

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")

# ============================================================
# SUPABASE CLIENT
# ============================================================

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# ============================================================
# EXECUTE SQL
# ============================================================

def run_sql_query(query: str) -> list:
    """Execute SQL via Supabase RPC"""
    try:
        result = supabase.rpc('execute_sql', {'query': query}).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Query Error: {e}")
        return []

# ============================================================
# CHECK 1: DOUBLE ENTRY
# ============================================================

def check_double_entry():
    """Check 1: Debit = Credit from inventory_ledger"""
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
    """Check 3: warehouse_stock matches inventory_ledger"""
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
# CHECK 6: FIFO DATA QUALITY
# ============================================================

def check_fifo_data_quality():
    """Check 6: Validate FIFO cost data quality"""
    
    query = """
    SELECT 
        COUNT(*) as total_sales,
        SUM(CASE WHEN fifo_cost = 1.00 THEN 1 ELSE 0 END) as default_cost_count
    FROM (
        SELECT 
            s.id as sale_id,
            si.quantity,
            COALESCE((SELECT SUM(unit_cost * qty) 
                      FROM inventory_cost_transactions 
                      WHERE sale_item_id = si.id), 1.00) as fifo_cost
        FROM sales s
        JOIN sale_items si ON s.id = si.sale_id
        WHERE s.sale_status = 'COMPLETED'
        AND DATE(s.created_at) >= CURRENT_DATE - INTERVAL '30 days'
    ) t
    """
    
    data = run_sql_query(query)
    
    if data:
        total = float(data[0].get('total_sales', 0))
        default_cost = float(data[0].get('default_cost_count', 0))
        
        status = "GOOD" if default_cost == 0 else "WARNING"
        icon = "🟢" if status == "GOOD" else "🟡"
        
        return {
            "name": "FIFO Data Quality",
            "status": status,
            "icon": icon,
            "total": total,
            "default_cost": default_cost,
            "detail": f"Total Sales: {total:.0f} | Default Cost: {default_cost:.0f}"
        }
    
    return {
        "name": "FIFO Data Quality",
        "status": "ERROR",
        "icon": "⚠️",
        "total": 0,
        "default_cost": 0,
        "detail": "No data available"
    }

# ============================================================
# CHECK 7: PRODUCT INTEGRITY
# ============================================================

def check_product_integrity():
    """Check 7: Product data integrity"""
    
    query = """
    SELECT 
        COUNT(*) as total_products,
        SUM(CASE WHEN purchase_price IS NULL OR purchase_price = 0 THEN 1 ELSE 0 END) as missing_cost,
        SUM(CASE WHEN selling_price IS NULL OR selling_price = 0 THEN 1 ELSE 0 END) as missing_price,
        SUM(CASE WHEN category_id IS NULL THEN 1 ELSE 0 END) as missing_category
    FROM products
    WHERE is_active = true
    """
    
    data = run_sql_query(query)
    
    if data:
        total = float(data[0].get('total_products', 0))
        missing_cost = float(data[0].get('missing_cost', 0))
        missing_price = float(data[0].get('missing_price', 0))
        missing_category = float(data[0].get('missing_category', 0))
        
        issues = missing_cost + missing_price + missing_category
        status = "GOOD" if issues == 0 else "WARNING"
        icon = "🟢" if status == "GOOD" else "🟡"
        
        return {
            "name": "Product Integrity",
            "status": status,
            "icon": icon,
            "total": total,
            "missing_cost": missing_cost,
            "missing_price": missing_price,
            "missing_category": missing_category,
            "detail": f"Total: {total:.0f} | Missing Cost: {missing_cost:.0f} | Missing Price: {missing_price:.0f}"
        }
    
    return {
        "name": "Product Integrity",
        "status": "ERROR",
        "icon": "⚠️",
        "total": 0,
        "missing_cost": 0,
        "missing_price": 0,
        "missing_category": 0,
        "detail": "No data available"
    }

# ============================================================
# CHECK 8: BACKUP TABLES COUNT
# ============================================================

def check_backup_tables():
    """Check 8: Count backup tables"""
    
    query = """
    SELECT 
        COUNT(*) as total_backups,
        COUNT(DISTINCT table_name) as unique_tables
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE 'backup_%'
    """
    
    data = run_sql_query(query)
    
    if data:
        total = float(data[0].get('total_backups', 0))
        unique = float(data[0].get('unique_tables', 0))
        
        status = "GOOD" if total < 50 else "WARNING"
        icon = "🟢" if status == "GOOD" else "🟡"
        
        return {
            "name": "Backup Tables",
            "status": status,
            "icon": icon,
            "total": total,
            "unique": unique,
            "detail": f"Total Backups: {total:.0f} | Unique: {unique:.0f}"
        }
    
    return {
        "name": "Backup Tables",
        "status": "ERROR",
        "icon": "⚠️",
        "total": 0,
        "unique": 0,
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
        check_sales_items(),
        check_fifo_data_quality(),
        check_product_integrity(),
        check_backup_tables()
    ]
    return checks

# ============================================================
# SAVE TO GITHUB
# ============================================================

def save_to_github(results):
    """Save results to GitHub"""
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"integrity_reports/report_{timestamp}.json"
        
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "checks": results,
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r["status"] in ["BALANCED", "MATCHED", "GOOD"]),
                "failed": sum(1 for r in results if r["status"] in ["IMBALANCED", "MISMATCHED"]),
                "warnings": sum(1 for r in results if r["status"] == "WARNING"),
                "errors": sum(1 for r in results if r["status"] == "ERROR")
            }
        }
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        content = json.dumps(data, indent=2)
        encoded = content.encode('utf-8').hex()
        
        response = requests.get(url, headers=headers)
        
        payload = {
            "message": f"Integrity check {timestamp}",
            "content": encoded
        }
        
        if response.status_code == 200:
            payload["sha"] = response.json()["sha"]
            requests.put(url, headers=headers, json=payload)
        else:
            requests.put(url, headers=headers, json=payload)
        
        return True, filename
    except Exception as e:
        return False, str(e)

# ============================================================
# STREAMLIT UI
# ============================================================

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/shop.png", width=60)
    st.title("🏪 POS ERP")
    st.caption("Integrity Check Dashboard")
    
    st.divider()
    
    if st.button("🔄 Run All Checks", type="primary", use_container_width=True):
        st.session_state.run_checks = True
    
    st.divider()
    
    if st.button("💾 Save to GitHub", use_container_width=True):
        if "results" in st.session_state:
            success, msg = save_to_github(st.session_state.results)
            if success:
                st.success(f"✅ Saved: {msg}")
            else:
                st.error(f"❌ {msg}")
        else:
            st.warning("⚠️ Run checks first!")
    
    st.divider()
    
    if "last_run" in st.session_state:
        st.caption(f"🕐 Last Run: {st.session_state.last_run}")
    
    st.caption(f"📦 {GITHUB_REPO if GITHUB_REPO else 'GitHub not configured'}")

# Main Content
st.title("📊 ERP Integrity Check Dashboard")
st.caption("POS App - Double Entry & FIFO Cost Monitoring")

# Tab Layout
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "📈 Analytics",
    "📋 SQL Queries",
    "📁 History"
])

# ============================================================
# TAB 1: DASHBOARD
# ============================================================

with tab1:
    if "run_checks" in st.session_state and st.session_state.run_checks:
        with st.spinner("🔄 Running integrity checks..."):
            results = run_all_checks()
            st.session_state.results = results
            st.session_state.last_run = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            st.session_state.run_checks = False
            st.rerun()
    
    if "results" in st.session_state:
        results = st.session_state.results
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r["status"] in ["BALANCED", "MATCHED", "GOOD"])
        failed = sum(1 for r in results if r["status"] in ["IMBALANCED", "MISMATCHED"])
        warnings = sum(1 for r in results if r["status"] == "WARNING")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric(
            "✅ Passed",
            f"{passed}/{total}",
            f"{passed/total*100:.0f}%",
            delta_color="normal" if passed == total else "off"
        )
        col2.metric("❌ Failed", failed)
        col3.metric("⚠️ Warnings", warnings)
        col4.metric("💀 Errors", errors)
        
        with col5:
            if passed == total:
                st.success("🎉 ALL VERIFIED!")
            elif passed > failed:
                st.warning("⚠️ PARTIAL VERIFIED!")
            else:
                st.error("🚨 CRITICAL ISSUES!")
        
        st.divider()
        
        # Display each check
        for check in results:
            if check["status"] in ["BALANCED", "MATCHED", "GOOD"]:
                bg_color = "#d4edda"
                border_color = "#28a745"
            elif check["status"] in ["IMBALANCED", "MISMATCHED"]:
                bg_color = "#f8d7da"
                border_color = "#dc3545"
            elif check["status"] == "WARNING":
                bg_color = "#fff3cd"
                border_color = "#ffc107"
            else:
                bg_color = "#e2e3e5"
                border_color = "#6c757d"
            
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
                </div>
                """, unsafe_allow_html=True)
        
        # Data Quality Warning
        fifo_check = next((r for r in results if r["name"] == "FIFO Data Quality"), None)
        if fifo_check and fifo_check.get("default_cost", 0) > 0:
            st.warning("""
            ⚠️ **FIFO Cost Issue Detected!**
            
            ဆရာကြီးရဲ့ data မှာ `fifo_cost = 1.00` ဖြစ်နေတဲ့ sale records တွေရှိပါတယ်။
            
            ဒါက FIFO layer မရှိလို့ ဒါမှမဟုတ် `consume_cost_layers_fifo()` function က cost ကို မတွက်ပေးလို့ ဖြစ်နိုင်ပါတယ်။
            
            **ဖြေရှင်းနည်း:**
            1. `inventory_cost_layers` မှာ data ရှိမရှိစစ်ပါ
            2. `consume_cost_layers_fifo()` function ကို စစ်ဆေးပါ
            3. Product cost data ကို ပြန်သတ်မှတ်ပါ
            """)
    
    else:
        st.info("👆 Click 'Run All Checks' to start monitoring")

# ============================================================
# TAB 2: ANALYTICS
# ============================================================

with tab2:
    st.subheader("📈 Integrity Analytics")
    
    if "results" in st.session_state:
        results = st.session_state.results
        
        # Create dataframe
        df_data = []
        for check in results:
            df_data.append({
                "Check": check["name"],
                "Status": check["status"],
                "Detail": check["detail"]
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Chart
        status_counts = {
            "Passed": sum(1 for r in results if r["status"] in ["BALANCED", "MATCHED", "GOOD"]),
            "Failed": sum(1 for r in results if r["status"] in ["IMBALANCED", "MISMATCHED"]),
            "Warning": sum(1 for r in results if r["status"] == "WARNING"),
            "Error": sum(1 for r in results if r["status"] == "ERROR")
        }
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                marker=dict(colors=['#28a745', '#dc3545', '#ffc107', '#6c757d']),
                hole=0.4
            )
        ])
        
        fig.update_layout(
            title="Overall Status Distribution",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 3: SQL QUERIES
# ============================================================

with tab3:
    st.subheader("📋 SQL Queries Used")
    
    queries = [
        ("1. Double Entry Check", """
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
        """),
        
        ("2. Sales vs Payments", """
        -- Sales
        SELECT COALESCE(SUM(total), 0) as total
        FROM sales
        WHERE sale_status = 'COMPLETED'
        AND DATE(created_at) = CURRENT_DATE
        
        -- Payments
        SELECT COALESCE(SUM(amount), 0) as total
        FROM payment_transactions
        WHERE status = 'COMPLETED'
        AND DATE(created_at) = CURRENT_DATE
        """),
        
        ("3. Stock vs Ledger", """
        -- Stock
        SELECT COALESCE(SUM(qty), 0) as total
        FROM warehouse_stock
        
        -- Ledger
        SELECT COALESCE(SUM(
            CASE 
                WHEN transaction_type IN ('PURCHASE', 'RETURN', 'OPENING', 'RECEIVE') THEN quantity
                WHEN transaction_type IN ('SALE', 'ADJUSTMENT_OUT', 'TRANSFER_OUT', 'ISSUE') THEN -quantity
                ELSE 0
            END
        ), 0) as total
        FROM inventory_ledger
        """),
        
        ("4. FIFO Cost vs Stock", """
        -- FIFO
        SELECT 
            COALESCE(SUM(qty_remaining * unit_cost), 0) as cost,
            COALESCE(SUM(qty_remaining), 0) as qty
        FROM inventory_cost_layers
        
        -- Stock
        SELECT 
            COALESCE(SUM(qty * COALESCE(unit_cost, 0)), 0) as value,
            COALESCE(SUM(qty), 0) as qty
        FROM warehouse_stock
        """),
        
        ("5. Sales Total vs Items", """
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
        AND DATE(s.created_at) = CURRENT_DATE
        """),
        
        ("6. FIFO Data Quality", """
        SELECT 
            COUNT(*) as total_sales,
            SUM(CASE WHEN fifo_cost = 1.00 THEN 1 ELSE 0 END) as default_cost_count
        FROM (
            SELECT 
                s.id as sale_id,
                COALESCE((SELECT SUM(unit_cost * qty) 
                          FROM inventory_cost_transactions 
                          WHERE sale_item_id = si.id), 1.00) as fifo_cost
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            WHERE s.sale_status = 'COMPLETED'
            AND DATE(s.created_at) >= CURRENT_DATE - INTERVAL '30 days'
        ) t
        """),
        
        ("7. Product Integrity", """
        SELECT 
            COUNT(*) as total_products,
            SUM(CASE WHEN purchase_price IS NULL OR purchase_price = 0 THEN 1 ELSE 0 END) as missing_cost,
            SUM(CASE WHEN selling_price IS NULL OR selling_price = 0 THEN 1 ELSE 0 END) as missing_price,
            SUM(CASE WHEN category_id IS NULL THEN 1 ELSE 0 END) as missing_category
        FROM products
        WHERE is_active = true
        """),
        
        ("8. Backup Tables", """
        SELECT 
            COUNT(*) as total_backups,
            COUNT(DISTINCT table_name) as unique_tables
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'backup_%'
        """)
    ]
    
    for title, query in queries:
        with st.expander(title, expanded=False):
            st.code(query, language="sql")

# ============================================================
# TAB 4: HISTORY
# ============================================================

with tab4:
    st.subheader("📁 Historical Reports")
    
    if GITHUB_REPO and GITHUB_TOKEN:
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/integrity_reports"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                files = response.json()
                file_names = [f["name"] for f in files if f["name"].endswith(".json")]
                
                if file_names:
                    selected = st.selectbox("Select report:", sorted(file_names, reverse=True))
                    
                    if selected:
                        file_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/integrity_reports/{selected}"
                        content = requests.get(file_url).json()
                        
                        col1, col2, col3, col4 = st.columns(4)
                        summary = content.get("summary", {})
                        col1.metric("Passed", summary.get("passed", 0))
                        col2.metric("Failed", summary.get("failed", 0))
                        col3.metric("Warnings", summary.get("warnings", 0))
                        col4.metric("Errors", summary.get("errors", 0))
                        
                        with st.expander("📄 Full Report", expanded=True):
                            st.json(content)
                else:
                    st.info("No reports found")
            else:
                st.warning("Unable to fetch reports")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Configure GitHub token to enable history")

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption("🔐 Powered by Supabase | 📦 Stored on GitHub | 🚀 Built with Streamlit")