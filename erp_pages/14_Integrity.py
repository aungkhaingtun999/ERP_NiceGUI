# ============================================================
# erp_pages/14_Integrity.py
# ERP ENTERPRISE INTEGRITY CHECK DASHBOARD
#
# Checks:
#   1. Double Entry
#   2. Sales <-> Payments (with Cash Change support)
#   3. Stock <-> Inventory Ledger
#   4. FIFO Cost <-> Stock (Product-level QTY + Value)
#   5. Sales <-> Sale Items (ONLY subtotal check)
#
# READ-ONLY
# This page NEVER modifies ERP data.
# ============================================================

import datetime
import streamlit as st
import pandas as pd
from supabase_client import get_supabase


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ERP Integrity Check",
    page_icon="🔐",
    layout="wide",
)


# ============================================================
# HELPERS
# ============================================================

def money(value):
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def qty(value):
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# ============================================================
# DATABASE
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def execute_query(table_name: str, select: str = "*", filters: dict = None, limit: int = None):
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        
        query = supabase.table(table_name).select(select)
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list) and len(value) > 0:
                    if len(value) == 1:
                        query = query.eq(key, value[0])
                    else:
                        query = query.in_(key, value)
                elif value is not None:
                    query = query.eq(key, value)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data if response.data else []
    
    except Exception as e:
        print(f"Query error in {table_name}: {str(e)}")
        return []


def get_table_count(table_name: str):
    try:
        data = execute_query(table_name, select="id", limit=10000)
        return len(data) if data else 0
    except Exception:
        return 0


# ============================================================
# CHECK 1: DOUBLE ENTRY
# ============================================================

def check_double_entry():
    try:
        entries = execute_query("journal_entries", select="debit,credit")
        
        if not entries:
            return {
                "name": "Double Entry",
                "icon": "📊",
                "status": "NO DATA",
                "status_type": "warning",
                "passed": True,
                "detail": "No journal entries found.",
                "suggestion": "Journal entries will be created when transactions are posted."
            }
        
        debit_total = sum(money(x.get("debit")) for x in entries)
        credit_total = sum(money(x.get("credit")) for x in entries)
        difference = abs(debit_total - credit_total)
        passed = difference < 0.01
        
        return {
            "name": "Double Entry",
            "icon": "📊",
            "status": "BALANCED" if passed else "IMBALANCED",
            "status_type": "passed" if passed else "failed",
            "passed": passed,
            "detail": f"Debit: {debit_total:,.2f} | Credit: {credit_total:,.2f}",
            "suggestion": None if passed else "Check journal_entries for unbalanced transactions."
        }
    except Exception as e:
        return {
            "name": "Double Entry",
            "icon": "📊",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": f"Error: {str(e)[:100]}",
            "suggestion": "Check journal_entries table structure."
        }


# ============================================================
# CHECK 2: SALES <-> PAYMENTS
# ============================================================

def check_sales_vs_payments():
    try:
        sales = execute_query(
            "sales",
            select="id,total,sale_status,payment_method"
        )
        
        if not sales:
            return {
                "name": "Sales ↔ Payments",
                "icon": "💰",
                "status": "NO DATA",
                "status_type": "warning",
                "passed": True,
                "detail": "No sales records found.",
                "suggestion": None,
                "mismatches": [],
                "cash_overpayments": []
            }
        
        completed_sales = [s for s in sales if s.get("sale_status") == "COMPLETED"]
        
        if not completed_sales:
            return {
                "name": "Sales ↔ Payments",
                "icon": "💰",
                "status": "NO DATA",
                "status_type": "warning",
                "passed": True,
                "detail": "No completed sales found.",
                "suggestion": None,
                "mismatches": [],
                "cash_overpayments": []
            }
        
        sale_ids = [int(s["id"]) for s in completed_sales if s.get("id") is not None]
        
        payments = execute_query(
            "payment_transactions",
            select="sale_id,amount,status"
        )
        
        payment_map = {}
        for payment in payments if payments else []:
            if payment.get("status") != "COMPLETED":
                continue
            sale_id = payment.get("sale_id")
            if sale_id is None:
                continue
            try:
                sale_id = int(sale_id)
            except (ValueError, TypeError):
                continue
            payment_map[sale_id] = payment_map.get(sale_id, 0.0) + money(payment.get("amount"))
        
        sales_total = 0.0
        payments_total = 0.0
        mismatches = []
        cash_overpayments = []
        
        for sale in completed_sales:
            sale_id = int(sale["id"])
            sale_amount = money(sale.get("total"))
            payment_amount = money(payment_map.get(sale_id))
            
            sales_total += sale_amount
            payments_total += payment_amount
            
            payment_method = str(sale.get("payment_method") or "UNKNOWN").upper()
            
            if payment_method in ["CASH", "CASH_MMK"]:
                if payment_amount >= sale_amount:
                    change = payment_amount - sale_amount
                    if change > 0.01:
                        cash_overpayments.append({
                            "sale_id": sale_id,
                            "sale_amount": sale_amount,
                            "payment_amount": payment_amount,
                            "change": change,
                            "payment_method": payment_method,
                        })
                    continue
            
            if abs(sale_amount - payment_amount) >= 0.01:
                mismatches.append({
                    "sale_id": sale_id,
                    "sale_amount": sale_amount,
                    "payment_amount": payment_amount,
                    "difference": sale_amount - payment_amount,
                    "payment_method": payment_method,
                })
        
        has_mismatch = len(mismatches) > 0
        has_cash_change = len(cash_overpayments) > 0
        
        if has_mismatch:
            status = "MISMATCHED"
            status_type = "failed"
            passed = False
            ids = ", ".join(f"#{x['sale_id']}" for x in mismatches[:5])
            suggestion = f"Payment mismatch sale(s): {ids}"
        elif has_cash_change:
            status = "WARNING"
            status_type = "warning"
            passed = True
            ids = ", ".join(f"#{x['sale_id']}" for x in cash_overpayments[:5])
            suggestion = f"CASH overpayment/change: {ids}"
        else:
            status = "MATCHED"
            status_type = "passed"
            passed = True
            suggestion = None
        
        detail = f"Sales: {sales_total:,.2f} | Applied: {payments_total:,.2f}"
        if has_cash_change:
            change_total = sum(x["change"] for x in cash_overpayments)
            detail += f" | Cash Change: {change_total:,.2f}"
        
        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": status,
            "status_type": status_type,
            "passed": passed,
            "detail": detail,
            "suggestion": suggestion,
            "mismatches": mismatches,
            "cash_overpayments": cash_overpayments,
        }
    
    except Exception as e:
        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": f"Error: {str(e)[:100]}",
            "suggestion": "Verify payment_transactions schema.",
            "mismatches": [],
            "cash_overpayments": []
        }


# ============================================================
# CHECK 3: STOCK <-> INVENTORY LEDGER
# ============================================================

def check_stock_vs_ledger():
    try:
        stock_data = execute_query("warehouse_stock", select="qty")
        stock_total = sum(qty(x.get("qty")) for x in stock_data) if stock_data else 0
        
        ledger_data = execute_query("inventory_ledger", select="qty_in,qty_out")
        if ledger_data:
            ledger_total = sum(qty(x.get("qty_in")) - qty(x.get("qty_out")) for x in ledger_data)
        else:
            ledger_total = 0
        
        difference = abs(stock_total - ledger_total)
        passed = difference < 0.01
        
        return {
            "name": "Stock ↔ Inventory Ledger",
            "icon": "📦",
            "status": "MATCHED" if passed else "MISMATCHED",
            "status_type": "passed" if passed else "failed",
            "passed": passed,
            "detail": f"Stock: {stock_total:,.0f} | Ledger: {ledger_total:,.0f}",
            "suggestion": None if passed else "Check inventory ledger for missing or duplicated movements."
        }
    except Exception as e:
        return {
            "name": "Stock ↔ Inventory Ledger",
            "icon": "📦",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": f"Error: {str(e)[:100]}",
            "suggestion": "Check warehouse_stock and inventory_ledger."
        }


# ============================================================
# CHECK 4: FIFO COST <-> STOCK
# ============================================================

def check_fifo_vs_stock():
    try:
        fifo_data = execute_query(
            "inventory_cost_layers",
            select="product_id,qty_remaining,unit_cost"
        )
        
        if not fifo_data:
            return {
                "name": "FIFO Cost ↔ Stock",
                "icon": "📈",
                "status": "NO DATA",
                "status_type": "warning",
                "passed": True,
                "fifo_qty": 0,
                "stock_qty": 0,
                "qty_difference": 0,
                "fifo_value": 0,
                "product_mismatches": [],
                "detail": "No FIFO cost layers found.",
                "suggestion": "No inventory_cost_layers data available."
            }
        
        fifo_qty = sum(qty(row.get("qty_remaining")) for row in fifo_data)
        fifo_value = sum(qty(row.get("qty_remaining")) * money(row.get("unit_cost")) for row in fifo_data)
        
        stock_data = execute_query("warehouse_stock", select="product_id,qty")
        stock_qty = sum(qty(row.get("qty")) for row in stock_data) if stock_data else 0
        
        fifo_by_product = {}
        for row in fifo_data:
            product_id = row.get("product_id")
            if product_id is None:
                continue
            try:
                product_id = int(product_id)
            except (ValueError, TypeError):
                continue
            
            if product_id not in fifo_by_product:
                fifo_by_product[product_id] = {"qty": 0.0, "value": 0.0}
            
            fifo_by_product[product_id]["qty"] += qty(row.get("qty_remaining"))
            fifo_by_product[product_id]["value"] += qty(row.get("qty_remaining")) * money(row.get("unit_cost"))
        
        stock_by_product = {}
        for row in stock_data if stock_data else []:
            product_id = row.get("product_id")
            if product_id is None:
                continue
            try:
                product_id = int(product_id)
            except (ValueError, TypeError):
                continue
            stock_by_product[product_id] = qty(row.get("qty"))
        
        product_mismatches = []
        all_product_ids = set(list(fifo_by_product.keys()) + list(stock_by_product.keys()))
        
        for product_id in all_product_ids:
            fifo_qty_prod = fifo_by_product.get(product_id, {}).get("qty", 0.0)
            stock_qty_prod = stock_by_product.get(product_id, 0.0)
            qty_diff_prod = abs(fifo_qty_prod - stock_qty_prod)
            
            if qty_diff_prod >= 0.01:
                product = execute_query(
                    "products",
                    select="id,name",
                    filters={"id": product_id},
                    limit=1
                )
                product_name = product[0].get("name", f"ID:{product_id}") if product else f"ID:{product_id}"
                
                product_mismatches.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "fifo_qty": fifo_qty_prod,
                    "stock_qty": stock_qty_prod,
                    "qty_diff": qty_diff_prod,
                })
        
        qty_difference = fifo_qty - stock_qty
        qty_matched = abs(qty_difference) < 0.01
        product_level_matched = len(product_mismatches) == 0
        passed = qty_matched and product_level_matched
        
        suggestion = None
        if not passed:
            if product_mismatches:
                mismatch_ids = ", ".join(
                    f"{x['product_name']} (diff: {x['qty_diff']:,.0f})"
                    for x in product_mismatches[:5]
                )
                suggestion = f"Product-level quantity mismatch: {mismatch_ids}"
            else:
                suggestion = f"FIFO quantity differs from stock by {abs(qty_difference):,.2f} units."
        else:
            suggestion = "FIFO quantity matches warehouse stock."
        
        return {
            "name": "FIFO Cost ↔ Stock",
            "icon": "📈",
            "status": "MATCHED" if passed else "MISMATCHED",
            "status_type": "passed" if passed else "failed",
            "passed": passed,
            "fifo_qty": fifo_qty,
            "stock_qty": stock_qty,
            "qty_difference": qty_difference,
            "fifo_value": fifo_value,
            "product_mismatches": product_mismatches,
            "detail": f"FIFO Qty: {fifo_qty:,.0f} | Stock Qty: {stock_qty:,.0f} | FIFO Value: {fifo_value:,.2f}",
            "suggestion": suggestion,
        }
    
    except Exception as e:
        return {
            "name": "FIFO Cost ↔ Stock",
            "icon": "📈",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "fifo_qty": 0,
            "stock_qty": 0,
            "qty_difference": 0,
            "fifo_value": 0,
            "product_mismatches": [],
            "detail": f"Error: {str(e)[:100]}",
            "suggestion": "Check inventory_cost_layers and warehouse_stock schema."
        }


# ============================================================
# CHECK 5: SALES <-> SALE ITEMS
# ============================================================

def check_sales_vs_items(start_date, end_date):
    try:
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        all_sales = execute_query(
            "sales",
            select="id,subtotal,total,created_at,sale_status"
        )
        
        if not all_sales:
            return {
                "name": "Sales ↔ Sale Items",
                "icon": "🧾",
                "status": "NO DATA",
                "status_type": "warning",
                "passed": True,
                "detail": "No sales records found.",
                "suggestion": None,
                "period": f"{start_str} to {end_str}",
                "mismatches": []
            }
        
        sales = []
        for sale in all_sales:
            try:
                created_at = sale.get('created_at')
                if created_at:
                    if isinstance(created_at, str):
                        if 'T' in created_at:
                            sale_date = datetime.datetime.fromisoformat(
                                created_at.replace('Z', '+00:00')
                            ).date()
                        else:
                            sale_date = datetime.datetime.strptime(created_at, '%Y-%m-%d').date()
                    else:
                        sale_date = created_at.date() if hasattr(created_at, 'date') else created_at
                    
                    if start_date <= sale_date <= end_date and sale.get('sale_status') == 'COMPLETED':
                        sales.append(sale)
            except Exception:
                continue
        
        if not sales:
            return {
                "name": "Sales ↔ Sale Items",
                "icon": "🧾",
                "status": "NO DATA",
                "status_type": "warning",
                "passed": True,
                "detail": f"No completed sales found for period {start_str} to {end_str}",
                "suggestion": "Try adjusting the date range.",
                "period": f"{start_str} to {end_str}",
                "mismatches": []
            }
        
        sale_ids = [int(s["id"]) for s in sales if s.get("id") is not None]
        
        sale_items = execute_query(
            "sale_items",
            select="sale_id,subtotal",
            filters={"sale_id": sale_ids}
        )
        
        items_by_sale = {}
        for item in sale_items if sale_items else []:
            sale_id = item.get("sale_id")
            if sale_id is None:
                continue
            try:
                sale_id = int(sale_id)
            except (ValueError, TypeError):
                continue
            items_by_sale[sale_id] = items_by_sale.get(sale_id, 0.0) + money(item.get("subtotal"))
        
        mismatches = []
        total_sales = 0.0
        total_items = 0.0
        
        for sale in sales:
            sale_id = int(sale["id"])
            sale_subtotal = money(sale.get("subtotal", 0))
            items_subtotal = money(items_by_sale.get(sale_id, 0))
            
            total_sales += sale_subtotal
            total_items += items_subtotal
            
            if abs(sale_subtotal - items_subtotal) >= 0.01:
                mismatches.append({
                    "sale_id": sale_id,
                    "sale_subtotal": sale_subtotal,
                    "items_subtotal": items_subtotal,
                    "difference": sale_subtotal - items_subtotal,
                })
        
        passed = len(mismatches) == 0
        
        if passed:
            status = "MATCHED"
            status_type = "passed"
            suggestion = None
        else:
            status = "MISMATCHED"
            status_type = "failed"
            mismatch_ids = ", ".join(f"#{x['sale_id']}" for x in mismatches[:5])
            suggestion = f"Subtotal mismatch for sale(s): {mismatch_ids}"
        
        return {
            "name": "Sales ↔ Sale Items",
            "icon": "🧾",
            "status": status,
            "status_type": status_type,
            "passed": passed,
            "detail": f"Sales: {total_sales:,.2f} | Items: {total_items:,.2f}",
            "suggestion": suggestion,
            "period": f"{start_str} to {end_str}",
            "mismatches": mismatches,
            "total_sales_checked": len(sales),
            "total_items_checked": len(sale_items) if sale_items else 0,
        }
    
    except Exception as e:
        return {
            "name": "Sales ↔ Sale Items",
            "icon": "🧾",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": f"Error: {str(e)[:100]}",
            "suggestion": "Verify sale_items table and sale_id relationships.",
            "period": "Error retrieving period",
            "mismatches": []
        }


# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_summary(checks):
    """Render summary header without HTML display issues"""
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c.get("passed", False))
    failed_checks = total_checks - passed_checks
    
    if failed_checks == 0:
        summary_icon = "✅"
        border_color = "#28a745"
    elif failed_checks <= 2:
        summary_icon = "⚠️"
        border_color = "#ffc107"
    else:
        summary_icon = "❌"
        border_color = "#dc3545"
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {summary_icon} {passed_checks} / {total_checks} Checks Passed")
    with col2:
        st.caption(f"Last checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.markdown("---")


def render_check_card(check):
    """Render a single check card without HTML display issues"""
    
    status_type = check.get("status_type", "error")
    icon = check.get("icon", "📋")
    name = check.get("name", "Unknown Check")
    status = check.get("status", "UNKNOWN")
    detail = check.get("detail", "")
    suggestion = check.get("suggestion")
    
    # Determine colors
    if status_type == "passed":
        border_color = "#28a745"
        bg_color = "#f0fff4"
        badge_bg = "#28a745"
        badge_color = "white"
    elif status_type == "failed":
        border_color = "#dc3545"
        bg_color = "#fff5f5"
        badge_bg = "#dc3545"
        badge_color = "white"
    elif status_type == "warning":
        border_color = "#ffc107"
        bg_color = "#fffcf0"
        badge_bg = "#ffc107"
        badge_color = "#856404"
    else:
        border_color = "#6c757d"
        bg_color = "#f8f9fa"
        badge_bg = "#6c757d"
        badge_color = "white"
    
    # Period info for sales items check
    period_info = ""
    if name == "Sales ↔ Sale Items" and "period" in check:
        period_info = f" ({check['period']})"
    
    # Card using st.container with simple markdown
    with st.container():
        # Header row with columns
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{icon} {name}**{period_info}")
        with col2:
            st.markdown(f"**{status}**")
        
        # Detail
        st.markdown(f"*{detail}*")
        
        # Suggestion
        if suggestion:
            st.info(f"💡 {suggestion}")
        
        # Mismatch details
        if name == "Sales ↔ Sale Items" and check.get("mismatches"):
            mismatches = check["mismatches"]
            if mismatches:
                with st.expander("📋 View Mismatch Details"):
                    df = pd.DataFrame(mismatches)
                    df["sale_id"] = df["sale_id"].apply(lambda x: f"#{x}")
                    df["sale_subtotal"] = df["sale_subtotal"].apply(lambda x: f"{x:,.2f}")
                    df["items_subtotal"] = df["items_subtotal"].apply(lambda x: f"{x:,.2f}")
                    df["difference"] = df["difference"].apply(lambda x: f"{x:,.2f}")
                    df.columns = ["Sale ID", "Sale Subtotal", "Items Subtotal", "Difference"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
        
        if name == "Sales ↔ Payments" and check.get("mismatches"):
            mismatches = check["mismatches"]
            if mismatches:
                with st.expander("📋 View Payment Mismatch Details"):
                    df = pd.DataFrame(mismatches)
                    df["sale_id"] = df["sale_id"].apply(lambda x: f"#{x}")
                    df["sale_amount"] = df["sale_amount"].apply(lambda x: f"{x:,.2f}")
                    df["payment_amount"] = df["payment_amount"].apply(lambda x: f"{x:,.2f}")
                    df["difference"] = df["difference"].apply(lambda x: f"{x:,.2f}")
                    df.columns = ["Sale ID", "Sale Amount", "Payment Amount", "Difference", "Payment Method"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
        
        if name == "Sales ↔ Payments" and check.get("cash_overpayments"):
            cash_over = check["cash_overpayments"]
            if cash_over:
                with st.expander("💰 View Cash Change Details"):
                    df_cash = pd.DataFrame(cash_over)
                    df_cash["sale_id"] = df_cash["sale_id"].apply(lambda x: f"#{x}")
                    df_cash["sale_amount"] = df_cash["sale_amount"].apply(lambda x: f"{x:,.2f}")
                    df_cash["payment_amount"] = df_cash["payment_amount"].apply(lambda x: f"{x:,.2f}")
                    df_cash["change"] = df_cash["change"].apply(lambda x: f"{x:,.2f}")
                    df_cash.columns = ["Sale ID", "Sale Amount", "Payment Amount", "Change", "Payment Method"]
                    st.dataframe(df_cash, use_container_width=True, hide_index=True)
        
        if name == "FIFO Cost ↔ Stock" and check.get("product_mismatches"):
            product_mismatches = check["product_mismatches"]
            if product_mismatches:
                with st.expander("📦 View Product-level Quantity Mismatches"):
                    df = pd.DataFrame(product_mismatches)
                    df["fifo_qty"] = df["fifo_qty"].apply(lambda x: f"{x:,.0f}")
                    df["stock_qty"] = df["stock_qty"].apply(lambda x: f"{x:,.0f}")
                    df["qty_diff"] = df["qty_diff"].apply(lambda x: f"{x:,.0f}")
                    df.columns = ["Product ID", "Product Name", "FIFO Qty", "Stock Qty", "Qty Difference"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")


# ============================================================
# MAIN PAGE
# ============================================================

def main():
    st.title("🔐 Enterprise Integrity Check")
    st.markdown("---")
    
    # Initialize session state for dates if not exists
    if 'integrity_start_date' not in st.session_state:
        st.session_state.integrity_start_date = datetime.date.today() - datetime.timedelta(days=30)
    if 'integrity_end_date' not in st.session_state:
        st.session_state.integrity_end_date = datetime.date.today()
    
    # Date Range Selector
    st.markdown("### 📅 Check Period Selection")
    st.caption("Select the date range for Sales ↔ Sale Items verification")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.integrity_start_date,
            key="integrity_start_date_widget"
        )
        st.session_state.integrity_start_date = start_date
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.integrity_end_date,
            key="integrity_end_date_widget"
        )
        st.session_state.integrity_end_date = end_date
    
    with col3:
        st.write("")
        if st.button("🔄 Refresh Checks", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sales_count = get_table_count("sales")
        st.metric(label="Total Sales Records", value=f"{sales_count:,}")
    
    with col2:
        product_count = get_table_count("products")
        st.metric(label="Total Products", value=f"{product_count:,}")
    
    with col3:
        stock_count = get_table_count("warehouse_stock")
        st.metric(label="Stock Records", value=f"{stock_count:,}")
    
    st.markdown("---")
    
    # Run Checks
    with st.spinner("Running integrity checks..."):
        checks = [
            check_double_entry(),
            check_sales_vs_payments(),
            check_stock_vs_ledger(),
            check_fifo_vs_stock(),
            check_sales_vs_items(start_date, end_date),
        ]
    
    # Summary
    render_summary(checks)
    
    # Render each check
    for check in checks:
        render_check_card(check)
    
    # Footer
    st.caption(
        "🔐 This page is READ-ONLY. "
        "All checks are performed against the database "
        "without modifying any data."
    )


if __name__ == "__main__":
    main()
