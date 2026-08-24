# ============================================================
# erp_pages/14_Integrity.py
# ERP ENTERPRISE INTEGRITY CHECK DASHBOARD
# NICE GUI VERSION
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
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from nicegui import ui

from supabase_client import get_supabase

from auth import require_admin


# ============================================================
# HELPERS
# ============================================================

def money(value: Any) -> float:
    """Convert value to float safely."""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def qty(value: Any) -> float:
    """Convert quantity to float safely."""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# ============================================================
# DATABASE QUERY
# ============================================================

def execute_query(
    table_name: str,
    select: str = "*",
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Execute database query with caching."""
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


def get_table_count(table_name: str) -> int:
    """Get table record count."""
    try:
        data = execute_query(table_name, select="id", limit=10000)
        return len(data) if data else 0
    except Exception:
        return 0


# ============================================================
# CHECK FUNCTIONS (Same logic as original)
# ============================================================

def check_double_entry() -> Dict[str, Any]:
    """Check double entry balance."""
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


def check_sales_vs_payments() -> Dict[str, Any]:
    """Check sales vs payments."""
    try:
        sales = execute_query("sales", select="id,total,sale_status,payment_method")
        
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
        
        payments = execute_query("payment_transactions", select="sale_id,amount,status")
        
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


def check_stock_vs_ledger() -> Dict[str, Any]:
    """Check stock vs inventory ledger."""
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


def check_fifo_vs_stock() -> Dict[str, Any]:
    """Check FIFO cost vs stock."""
    try:
        fifo_data = execute_query("inventory_cost_layers", select="product_id,qty_remaining,unit_cost")
        
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
                product = execute_query("products", select="id,name", filters={"id": product_id}, limit=1)
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
                mismatch_ids = ", ".join(f"{x['product_name']} (diff: {x['qty_diff']:,.0f})" for x in product_mismatches[:5])
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


def check_sales_vs_items(start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
    """Check sales vs sale items."""
    try:
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        all_sales = execute_query("sales", select="id,subtotal,total,created_at,sale_status")
        
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
                            sale_date = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
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
        
        all_items = []
        chunk_size = 500
        for i in range(0, len(sale_ids), chunk_size):
            chunk = sale_ids[i:i + chunk_size]
            rows = execute_query("sale_items", select="sale_id,total", filters={"sale_id": chunk})
            if rows:
                all_items.extend(rows)
        
        items_by_sale = {}
        for item in all_items:
            sale_id = item.get("sale_id")
            if sale_id is None:
                continue
            try:
                sale_id = int(sale_id)
            except (ValueError, TypeError):
                continue
            items_by_sale[sale_id] = items_by_sale.get(sale_id, 0.0) + money(item.get("total"))
        
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
            ids = ", ".join(f"#{x['sale_id']}" for x in mismatches[:5])
            suggestion = f"Subtotal mismatch for sale(s): {ids}"
        
        return {
            "name": "Sales ↔ Sale Items",
            "icon": "🧾",
            "status": status,
            "status_type": status_type,
            "passed": passed,
            "detail": f"Sales: {total_sales:,.2f} | Items: {total_items:,.2f}",
            "suggestion": suggestion,
            "period": f"{start_str} to {end_str}",
            "mismatches": mismatches
        }
    
    except Exception as e:
        return {
            "name": "Sales ↔ Sale Items",
            "icon": "🧾",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": f"Error: {str(e)[:100]}",
            "suggestion": "Check sale_items table schema.",
            "period": f"{start_str} to {end_str}",
            "mismatches": []
        }


# ============================================================
# UI RENDER FUNCTIONS
# ============================================================

def render_summary(container: Any, checks: List[Dict[str, Any]]):
    """Render summary header."""
    container.clear()
    
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c.get("passed", False))
    failed_checks = total_checks - passed_checks
    
    if failed_checks == 0:
        summary_icon = "✅"
        color = "text-green-600"
    elif failed_checks <= 2:
        summary_icon = "⚠️"
        color = "text-orange-600"
    else:
        summary_icon = "❌"
        color = "text-red-600"
    
    with container:
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label(f"{summary_icon} {passed_checks} / {total_checks} Checks Passed").classes(
                f'text-xl font-bold {color}'
            )
            ui.label(f"Last checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").classes(
                'text-sm text-gray-500'
            )


def render_check_card(check: Dict[str, Any]):
    """Render a single check card."""
    status_type = check.get("status_type", "error")
    icon = check.get("icon", "📋")
    name = check.get("name", "Unknown Check")
    status = check.get("status", "UNKNOWN")
    detail = check.get("detail", "")
    suggestion = check.get("suggestion")
    
    # Status colors
    status_colors = {
        "passed": "bg-green-50 border-green-200",
        "warning": "bg-orange-50 border-orange-200",
        "failed": "bg-red-50 border-red-200",
        "error": "bg-red-50 border-red-200",
    }
    
    card_class = status_colors.get(status_type, "bg-gray-50 border-gray-200")
    
    with ui.card().classes(f'w-full p-4 mb-4 border {card_class}'):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-2'):
            ui.label(f"{icon} {name}").classes('font-bold text-lg')
            
            # Status badge
            badge_colors = {
                "passed": "bg-green-100 text-green-700",
                "warning": "bg-orange-100 text-orange-700",
                "failed": "bg-red-100 text-red-700",
                "error": "bg-red-100 text-red-700",
            }
            
            ui.badge(status).classes(badge_colors.get(status_type, "bg-gray-100 text-gray-700"))
        
        # Detail
        ui.label(detail).classes('text-gray-600 mb-2')
        
        # Suggestion
        if suggestion:
            with ui.row().classes('items-start gap-2'):
                ui.icon('lightbulb').classes('text-yellow-500')
                ui.label(suggestion).classes('text-sm text-orange-600')
        
        # Expandable details for mismatches
        if name == "Sales ↔ Sale Items" and check.get("mismatches"):
            mismatches = check["mismatches"]
            if mismatches:
                with ui.expansion('📋 View Mismatch Details', icon='table').classes('w-full mt-2'):
                    df = pd.DataFrame(mismatches)
                    columns = [
                        {'name': col, 'label': col, 'field': col, 'sortable': True}
                        for col in df.columns
                    ]
                    ui.table(columns=columns, rows=df.to_dict('records'), row_key='sale_id').classes('w-full')
        
        if name == "Sales ↔ Payments" and check.get("mismatches"):
            mismatches = check["mismatches"]
            if mismatches:
                with ui.expansion('📋 View Payment Mismatch Details', icon='table').classes('w-full mt-2'):
                    df = pd.DataFrame(mismatches)
                    columns = [
                        {'name': col, 'label': col, 'field': col, 'sortable': True}
                        for col in df.columns
                    ]
                    ui.table(columns=columns, rows=df.to_dict('records'), row_key='sale_id').classes('w-full')
        
        if name == "Sales ↔ Payments" and check.get("cash_overpayments"):
            cash_over = check["cash_overpayments"]
            if cash_over:
                with ui.expansion('💰 View Cash Change Details', icon='table').classes('w-full mt-2'):
                    df = pd.DataFrame(cash_over)
                    columns = [
                        {'name': col, 'label': col, 'field': col, 'sortable': True}
                        for col in df.columns
                    ]
                    ui.table(columns=columns, rows=df.to_dict('records'), row_key='sale_id').classes('w-full')
        
        if name == "FIFO Cost ↔ Stock" and check.get("product_mismatches"):
            product_mismatches = check["product_mismatches"]
            if product_mismatches:
                with ui.expansion('📦 View Product-level Quantity Mismatches', icon='table').classes('w-full mt-2'):
                    df = pd.DataFrame(product_mismatches)
                    columns = [
                        {'name': col, 'label': col, 'field': col, 'sortable': True}
                        for col in df.columns
                    ]
                    ui.table(columns=columns, rows=df.to_dict('records'), row_key='product_id').classes('w-full')


# ============================================================
# MAIN PAGE
# ============================================================

def main(container: Optional[Any] = None):
    """Main page entry point."""
    
    # Admin check
    require_admin()
    
    target = container or ui.column()
    
    with target:
        ui.label("🔐 Enterprise Integrity Check").classes('text-3xl font-bold mb-4')
        
        # Date selection
        ui.label('📅 Check Period Selection').classes('text-xl font-bold mb-2')
        ui.label('Select the date range for Sales ↔ Sale Items verification').classes(
            'text-gray-500 mb-4'
        )
        
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        end_date = datetime.date.today()
        
        with ui.row().classes('w-full gap-4 items-end mb-4'):
            start_input = ui.input(
                'Start Date',
                value=start_date.strftime('%Y-%m-%d')
            ).props('type=date').classes('min-w-[200px]')
            
            end_input = ui.input(
                'End Date',
                value=end_date.strftime('%Y-%m-%d')
            ).props('type=date').classes('min-w-[200px]')
            
            refresh_btn = ui.button(
                '🔄 Refresh Checks',
                on_click=lambda: run_checks()
            ).classes('bg-primary text-white')
        
        # Stats row
        stats_container = ui.row().classes('w-full gap-4 flex-wrap mb-4')
        summary_container = ui.column().classes('w-full mb-4')
        checks_container = ui.column().classes('w-full')
        
        def run_checks():
            """Run all integrity checks."""
            try:
                start_val = datetime.datetime.strptime(start_input.value, '%Y-%m-%d').date()
                end_val = datetime.datetime.strptime(end_input.value, '%Y-%m-%d').date()
            except Exception:
                ui.notify('Invalid date format', type='error', position='top')
                return
            
            # Show loading
            refresh_btn.disable()
            refresh_btn.text = '⏳ Running...'
            
            # Stats
            stats_container.clear()
            with stats_container:
                sales_count = get_table_count("sales")
                product_count = get_table_count("products")
                stock_count = get_table_count("warehouse_stock")
                
                with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                    ui.label('Total Sales Records').classes('text-sm text-gray-600')
                    ui.label(f'{sales_count:,}').classes('text-2xl font-bold')
                
                with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                    ui.label('Total Products').classes('text-sm text-gray-600')
                    ui.label(f'{product_count:,}').classes('text-2xl font-bold')
                
                with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                    ui.label('Stock Records').classes('text-sm text-gray-600')
                    ui.label(f'{stock_count:,}').classes('text-2xl font-bold')
            
            # Run checks
            checks = [
                check_double_entry(),
                check_sales_vs_payments(),
                check_stock_vs_ledger(),
                check_fifo_vs_stock(),
                check_sales_vs_items(start_val, end_val),
            ]
            
            # Render summary
            render_summary(summary_container, checks)
            
            # Render check cards
            checks_container.clear()
            with checks_container:
                for check in checks:
                    render_check_card(check)
                
                ui.label(
                    '🔐 This page is READ-ONLY. All checks are performed against the database without modifying any data.'
                ).classes('text-sm text-gray-500 mt-4')
            
            # Re-enable button
            refresh_btn.enable()
            refresh_btn.text = '🔄 Refresh Checks'
        
        # Initial run
        run_checks()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
