# ==============================================================================
# erp_pages/3_Reports.py
#
# ERP ENTERPRISE SALES ANALYTICS REPORT v5.0
# NICE GUI VERSION
#
# Sales Summary + Product Sales + Cashier + Payment + Export
#
# READ-ONLY REPORT
# ==============================================================================

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
from nicegui import ui

from erp_core.base_repo import db
from utils.ui import show_table


# ==============================================================================
# CONSTANTS
# ==============================================================================

UNKNOWN_PRODUCT = "Unknown Product"


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_number(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def cashier_name(user: Any) -> str:
    """Safely convert Supabase users relation into cashier display name."""
    if not isinstance(user, dict):
        return "Unknown"
    
    username = str(user.get("username") or "").strip()
    employee_code = str(user.get("employee_code") or "").strip()
    
    if username:
        return username
    if employee_code:
        return employee_code
    
    return "Unknown"


def resolve_product_name(item_product_name: Any, product_name: Any) -> str:
    """Resolve product name with priority."""
    item_name = str(item_product_name or "").strip()
    if item_name:
        return item_name
    
    master_name = str(product_name or "").strip()
    if master_name:
        return master_name
    
    return UNKNOWN_PRODUCT


def format_number(value: Any) -> str:
    """Format number with thousand separators."""
    try:
        number = float(value or 0)
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.2f}"
    except Exception:
        return str(value)


def get_report_utc_range(start_date: date, end_date: date) -> tuple:
    """Convert Myanmar local date range into UTC boundaries."""
    try:
        from zoneinfo import ZoneInfo
        
        myanmar_tz = ZoneInfo("Asia/Yangon")
        start_local = pd.Timestamp(start_date, tz=myanmar_tz)
        end_local = pd.Timestamp(end_date + timedelta(days=1), tz=myanmar_tz)
        
        start_utc = start_local.tz_convert("UTC").isoformat()
        end_utc = end_local.tz_convert("UTC").isoformat()
        
        return start_utc, end_utc
    
    except Exception:
        start_utc = f"{start_date.isoformat()}T00:00:00+00:00"
        end_utc = f"{(end_date + timedelta(days=1)).isoformat()}T00:00:00+00:00"
        return start_utc, end_utc


# ==============================================================================
# DATABASE LOADERS
# ==============================================================================

def get_sales(query_start: str, query_end: str) -> List[Dict[str, Any]]:
    """Load sales from database."""
    try:
        response = (
            db()
            .table("sales")
            .select("""
                id,
                total,
                total_amount,
                discount,
                tax,
                subtotal,
                paid_amount,
                payment_method,
                created_at,
                cashier_id,
                users(username, employee_code)
            """)
            .gte("created_at", query_start)
            .lt("created_at", query_end)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    
    except Exception as e:
        ui.notify(f"Sales loading error: {e}", type='error', position='top')
        return []


def get_sale_items(sale_ids: List[int]) -> List[Dict[str, Any]]:
    """Load sale items for selected sales."""
    if not sale_ids:
        return []
    
    try:
        normalized_ids = [int(x) for x in sale_ids if x is not None]
        if not normalized_ids:
            return []
        
        response = (
            db()
            .table("sale_items")
            .select("""
                id, sale_id, product_id, quantity,
                unit_price, discount, total, product_name
            """)
            .in_("sale_id", normalized_ids)
            .order("sale_id")
            .order("id")
            .execute()
        )
        return response.data or []
    
    except Exception as e:
        ui.notify(f"Sale item loading error: {e}", type='error', position='top')
        return []


def get_products(product_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Load product master data."""
    if not product_ids:
        return {}
    
    try:
        normalized_ids = [int(x) for x in product_ids if x is not None]
        if not normalized_ids:
            return {}
        
        response = (
            db()
            .table("products")
            .select("id, name, sku, barcode")
            .in_("id", normalized_ids)
            .execute()
        )
        
        rows = response.data or []
        return {int(row["id"]): row for row in rows if row.get("id") is not None}
    
    except Exception as e:
        ui.notify(f"Product loading error: {e}", type='error', position='top')
        return {}


def build_product_sales_dataframe(
    sales: List[Dict],
    sale_items: List[Dict],
    products: Dict[int, Dict]
) -> pd.DataFrame:
    """Build item-level sales dataframe."""
    if not sale_items:
        return pd.DataFrame()
    
    sales_map = {}
    for sale in sales:
        sale_id = sale.get("id")
        if sale_id is None:
            continue
        try:
            sale_id = int(sale_id)
        except Exception:
            continue
        
        user = sale.get("users")
        sales_map[sale_id] = {
            "created_at": sale.get("created_at"),
            "cashier": cashier_name(user),
            "payment_method": sale.get("payment_method"),
        }
    
    rows = []
    for item in sale_items:
        sale_id = item.get("sale_id")
        if sale_id is None:
            continue
        try:
            sale_id = int(sale_id)
        except Exception:
            continue
        
        sale_info = sales_map.get(sale_id, {})
        product_id = item.get("product_id")
        
        try:
            product_id_int = int(product_id) if product_id is not None else None
        except Exception:
            product_id_int = None
        
        product = products.get(product_id_int, {})
        product_name = resolve_product_name(item.get("product_name"), product.get("name"))
        
        rows.append({
            "Sale ID": sale_id,
            "Date": sale_info.get("created_at"),
            "Cashier": sale_info.get("cashier", "Unknown"),
            "Payment Method": sale_info.get("payment_method") or "Unknown",
            "Product ID": product_id_int,
            "Product Name": product_name,
            "SKU": product.get("sku") or "",
            "Barcode": product.get("barcode") or "",
            "Quantity": safe_number(item.get("quantity")),
            "Unit Price": safe_number(item.get("unit_price")),
            "Discount": safe_number(item.get("discount")),
            "Sales": safe_number(item.get("total")),
        })
    
    if not rows:
        return pd.DataFrame()
    
    product_df = pd.DataFrame(rows)
    
    # Convert date
    if "Date" in product_df.columns:
        product_df["Date"] = pd.to_datetime(product_df["Date"], errors="coerce", utc=True)
        product_df = product_df[product_df["Date"].notna()].copy()
        if not product_df.empty:
            product_df["Date"] = product_df["Date"].dt.tz_convert("Asia/Yangon").dt.tz_localize(None)
    
    # Numeric columns
    for col in ["Quantity", "Unit Price", "Discount", "Sales"]:
        if col in product_df.columns:
            product_df[col] = pd.to_numeric(product_df[col], errors="coerce").fillna(0.0)
    
    return product_df


# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def build_kpi_cards(container: Any, df: pd.DataFrame):
    """Build KPI cards."""
    container.clear()
    
    total_sales_amount = safe_number(df["total"].sum())
    total_transactions = len(df)
    total_discount = safe_number(df["discount"].sum()) if "discount" in df.columns else 0
    total_tax = safe_number(df["tax"].sum()) if "tax" in df.columns else 0
    paid_amount = safe_number(df["paid_amount"].sum()) if "paid_amount" in df.columns else 0
    
    with container:
        with ui.row().classes('w-full gap-4 flex-wrap'):
            metrics = [
                ("💰 Total Sales", f"{total_sales_amount:,.0f} MMK", "bg-blue-50 text-blue-700"),
                ("🧾 Transactions", str(total_transactions), "bg-green-50 text-green-700"),
                ("🏷 Discount", f"{total_discount:,.0f} MMK", "bg-orange-50 text-orange-700"),
                ("🧾 Tax", f"{total_tax:,.0f} MMK", "bg-purple-50 text-purple-700"),
                ("💳 Paid", f"{paid_amount:,.0f} MMK", "bg-teal-50 text-teal-700"),
            ]
            
            for label, value, color_class in metrics:
                with ui.card().classes(f'p-4 flex-1 min-w-[180px] {color_class.split()[0]}'):
                    ui.label(label).classes('text-sm text-gray-600')
                    ui.label(value).classes(f'text-2xl font-bold {color_class.split()[1]}')


def build_payment_breakdown(container: Any, df: pd.DataFrame):
    """Build payment method breakdown."""
    container.clear()
    
    with container:
        ui.label('💳 Payment Method Breakdown').classes('text-xl font-bold mb-2')
        
        if df.empty:
            ui.label('No data').classes('text-gray-500')
            return
        
        payment_counts = df["payment_method"].value_counts()
        payment_amounts = df.groupby("payment_method")["total"].sum()
        
        payment_df = pd.DataFrame({
            "Payment Method": payment_counts.index,
            "Transactions": payment_counts.values,
            "Amount": [f"{safe_number(x):,.0f}" for x in payment_amounts.values],
        })
        
        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in payment_df.columns
        ]
        
        ui.table(columns=columns, rows=payment_df.to_dict('records'), row_key='Payment Method').classes('w-full')


def build_cashier_performance(container: Any, sales: List[Dict]):
    """Build cashier performance table."""
    container.clear()
    
    with container:
        ui.label('👤 Cashier Performance').classes('text-xl font-bold mb-2')
        
        cashier_data = []
        for sale in sales:
            user = sale.get("users")
            cashier = cashier_name(user)
            cashier_data.append({
                "cashier": cashier,
                "total": safe_number(sale.get("total")),
            })
        
        cashier_df = pd.DataFrame(cashier_data)
        
        if cashier_df.empty:
            ui.label('No data').classes('text-gray-500')
            return
        
        cashier_summary = (
            cashier_df.groupby("cashier")["total"]
            .agg(["count", "sum"])
            .reset_index()
        )
        cashier_summary.columns = ["Cashier", "Transactions", "Total Sales"]
        cashier_summary["Total Sales"] = cashier_summary["Total Sales"].apply(lambda x: f"{safe_number(x):,.0f} MMK")
        
        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in cashier_summary.columns
        ]
        
        ui.table(columns=columns, rows=cashier_summary.to_dict('records'), row_key='Cashier').classes('w-full')


def build_product_sales_report(container: Any, product_df: pd.DataFrame):
    """Build product sales report."""
    container.clear()
    
    with container:
        ui.label('📦 Product Sales Report').classes('text-xl font-bold mb-4')
        
        if product_df.empty:
            ui.label('No product sales data found.').classes('text-gray-500')
            return
        
        # Product KPIs
        total_products = product_df["Product Name"].nunique()
        total_qty = safe_number(product_df["Quantity"].sum())
        total_discount = safe_number(product_df["Discount"].sum())
        total_sales = safe_number(product_df["Sales"].sum())
        
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            kpis = [
                ("📦 Products", str(total_products)),
                ("🔢 Qty Sold", format_number(total_qty)),
                ("🏷 Discount", f"{total_discount:,.0f} MMK"),
                ("💰 Product Sales", f"{total_sales:,.0f} MMK"),
            ]
            
            for label, value in kpis:
                with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                    ui.label(label).classes('text-sm text-gray-600')
                    ui.label(value).classes('text-xl font-bold')
        
        # Product summary
        ui.label('🏆 Product Sales Summary').classes('font-bold mb-2')
        
        product_summary = (
            product_df.groupby(["Product Name", "SKU", "Barcode"], dropna=False)
            .agg(Quantity=("Quantity", "sum"), Discount=("Discount", "sum"), Sales=("Sales", "sum"))
            .reset_index()
            .sort_values("Sales", ascending=False)
        )
        
        display_summary = product_summary.copy()
        display_summary["Quantity"] = display_summary["Quantity"].apply(format_number)
        display_summary["Discount"] = display_summary["Discount"].apply(lambda x: f"{safe_number(x):,.0f}")
        display_summary["Sales"] = display_summary["Sales"].apply(lambda x: f"{safe_number(x):,.0f}")
        
        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in display_summary.columns
        ]
        
        ui.table(columns=columns, rows=display_summary.to_dict('records'), row_key='Product Name', pagination=10).classes('w-full mb-4')


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point."""
    target = container or ui.column()
    
    with target:
        ui.label('📊 ERP Executive Analytics & Reports').classes('text-3xl font-bold mb-2')
        ui.label('MYANMAR ERP - Sales Performance Analytics').classes('text-gray-500 mb-4')
        
        # Date filter
        today = date.today()
        
        with ui.row().classes('w-full gap-4 items-end mb-4'):
            start_input = ui.input('Start Date', value=today.strftime('%Y-%m-%d')).props('type=date').classes('min-w-[200px]')
            end_input = ui.input('End Date', value=today.strftime('%Y-%m-%d')).props('type=date').classes('min-w-[200px]')
            
            load_btn = ui.button('📊 Load Report', on_click=lambda: load_report()).classes('bg-primary text-white')
        
        # Dynamic containers
        kpi_container = ui.column().classes('w-full mb-4')
        payment_container = ui.column().classes('w-full mb-4')
        cashier_container = ui.column().classes('w-full mb-4')
        product_container = ui.column().classes('w-full')
        
        def load_report():
            """Load and display report."""
            try:
                start_date = date.fromisoformat(start_input.value)
                end_date = date.fromisoformat(end_input.value)
                
                if start_date > end_date:
                    ui.notify('Start Date cannot be later than End Date.', type='error', position='top')
                    return
                
                load_btn.disable()
                load_btn.text = '⏳ Loading...'
                
                # Get UTC range
                start_utc, end_utc = get_report_utc_range(start_date, end_date)
                
                # Load sales
                sales = get_sales(start_utc, end_utc)
                
                if not sales:
                    ui.notify('No sales data found for the selected date range.', type='warning', position='top')
                    return
                
                df = pd.DataFrame(sales)
                
                # Normalize total
                if "total" in df.columns:
                    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0.0)
                elif "total_amount" in df.columns:
                    df["total"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0.0)
                else:
                    df["total"] = 0.0
                
                # Load sale items and products
                sale_ids = [int(s["id"]) for s in sales if s.get("id") is not None]
                sale_items = get_sale_items(sale_ids)
                
                product_ids = [int(item["product_id"]) for item in sale_items if item.get("product_id") is not None]
                products = get_products(product_ids)
                
                # Build product dataframe
                product_df = build_product_sales_dataframe(sales, sale_items, products)
                
                # Build sections
                build_kpi_cards(kpi_container, df)
                build_payment_breakdown(payment_container, df)
                build_cashier_performance(cashier_container, sales)
                build_product_sales_report(product_container, product_df)
                
                # Footer
                ui.label(
                    f'📊 Report generated for {start_date} → {end_date} | '
                    f'Total Sales: {len(df)} transactions | '
                    f'Total Revenue: {safe_number(df["total"].sum()):,.0f} MMK'
                ).classes('text-sm text-gray-500 mt-4')
            
            except Exception as e:
                ui.notify(f'Report error: {e}', type='error', position='top')
            
            finally:
                load_btn.enable()
                load_btn.text = '📊 Load Report'
        
        # Initial load
        load_report()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
