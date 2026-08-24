# ==============================================================================
# pages/3_Dashboard.py
# ERP ENTERPRISE ANALYTICS DASHBOARD V30.5
# NICE GUI VERSION
# ==============================================================================

from typing import Dict, Any, Optional, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from nicegui import ui

from auth import (
    require_login,
    current_user
)

from erp_core.base_repo import (
    db,
    safe_float
)

# Correct loader
try:
    from erp_core.loaders.warehouse_loader import (
        get_warehouses
    )
except Exception:
    get_warehouses = lambda: []


# ==============================================================================
# MAIN
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main dashboard entry point."""
    
    require_login()
    user = current_user()
    
    target = container or ui.column()
    
    with target:
        # Header
        ui.label('📈 Enterprise Analytics Dashboard').classes('text-3xl font-bold mb-2')
        ui.label('Real-time financial, inventory, and sales performance metrics.').classes(
            'text-gray-500 mb-4'
        )
        
        # ======================================================================
        # FILTERS
        # ======================================================================
        
        with ui.row().classes('w-full gap-4 flex-wrap items-end mb-4'):
            # Warehouse selector
            warehouses = get_warehouses() or []
            
            warehouse_options = [{"id": None, "name": "All Warehouses"}]
            for w in warehouses:
                warehouse_options.append({
                    "id": w.get("id"),
                    "name": w.get("name")
                })
            
            warehouse_select = ui.select(
                warehouse_options,
                label='Select Warehouse',
                value=warehouse_options[0],
                format_func=lambda x: x["name"]
            ).classes('min-w-[250px]')
            
            # Period selector
            period_select = ui.select(
                ['This Month', 'Today', 'Last 7 Days', 'Year to Date'],
                label='Time Period',
                value='This Month',
            ).classes('min-w-[200px]')
            
            # Refresh button
            refresh_btn = ui.button(
                '🔄 Refresh',
                on_click=lambda: refresh_dashboard()
            ).classes('bg-primary text-white')
        
        # ======================================================================
        # DYNAMIC CONTAINERS
        # ======================================================================
        
        kpi_container = ui.column().classes('w-full mb-4')
        trend_container = ui.column().classes('w-full mb-4')
        inventory_container = ui.column().classes('w-full mb-4')
        transactions_container = ui.column().classes('w-full')
        
        # ======================================================================
        # DATE CALCULATION
        # ======================================================================
        
        def calculate_dates(period: str) -> tuple:
            """Calculate start and end dates based on period."""
            now = datetime.now()
            
            if period == "Today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "Last 7 Days":
                start_date = now - timedelta(days=7)
            elif period == "Year to Date":
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:  # This Month
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            return start_date, now
        
        # ======================================================================
        # LOAD SALES DATA
        # ======================================================================
        
        def load_sales_data(warehouse_id: Optional[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
            """Load sales data from database."""
            try:
                supabase = db()
                
                query = (
                    supabase
                    .table("sales")
                    .select("""
                        id,
                        total,
                        total_amount,
                        paid_amount,
                        sale_status,
                        status,
                        warehouse_id,
                        created_at
                    """)
                )
                
                if warehouse_id:
                    query = query.eq("warehouse_id", warehouse_id)
                
                query = (
                    query
                    .gte("created_at", start_date.isoformat())
                    .lte("created_at", end_date.isoformat())
                    .order("created_at", desc=True)
                )
                
                result = query.execute()
                return pd.DataFrame(result.data or [])
            
            except Exception as e:
                ui.notify(f"Sales loading error: {e}", type='error', position='top')
                return pd.DataFrame()
        
        # ======================================================================
        # BUILD KPI CARDS
        # ======================================================================
        
        def build_kpi_cards(container: Any, df_sales: pd.DataFrame):
            """Build KPI cards."""
            container.clear()
            
            gross_sales = 0
            total_paid = 0
            refunds = 0
            transactions = 0
            sales_column = None
            
            if not df_sales.empty:
                transactions = len(df_sales)
                
                if "total" in df_sales.columns:
                    sales_column = "total"
                elif "total_amount" in df_sales.columns:
                    sales_column = "total_amount"
                
                if sales_column:
                    gross_sales = df_sales[sales_column].apply(safe_float).sum()
                
                if "paid_amount" in df_sales.columns:
                    total_paid = df_sales["paid_amount"].apply(safe_float).sum()
            
            with container:
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    # Gross Revenue
                    with ui.card().classes('p-4 flex-1 min-w-[200px] bg-blue-50'):
                        ui.label('Gross Revenue').classes('text-sm text-gray-600')
                        ui.label(f"{gross_sales:,.0f} MMK").classes('text-2xl font-bold text-blue-700')
                        ui.label(f"{transactions} transactions").classes('text-xs text-gray-500')
                    
                    # Collections
                    with ui.card().classes('p-4 flex-1 min-w-[200px] bg-green-50'):
                        ui.label('Collections').classes('text-sm text-gray-600')
                        ui.label(f"{total_paid:,.0f} MMK").classes('text-2xl font-bold text-green-700')
                    
                    # Refunds
                    with ui.card().classes('p-4 flex-1 min-w-[200px] bg-orange-50'):
                        ui.label('Refunds').classes('text-sm text-gray-600')
                        ui.label(f"{refunds:,.0f} MMK").classes('text-2xl font-bold text-orange-700')
                    
                    # Net Revenue
                    with ui.card().classes('p-4 flex-1 min-w-[200px] bg-purple-50'):
                        ui.label('Net Revenue').classes('text-sm text-gray-600')
                        ui.label(f"{gross_sales - refunds:,.0f} MMK").classes('text-2xl font-bold text-purple-700')
        
        # ======================================================================
        # BUILD SALES TREND
        # ======================================================================
        
        def build_sales_trend(container: Any, df_sales: pd.DataFrame, sales_column: Optional[str]):
            """Build sales trend chart."""
            container.clear()
            
            with container:
                ui.label('📈 Sales Trend').classes('text-xl font-bold mb-2')
                
                if not df_sales.empty and sales_column:
                    chart = df_sales.copy()
                    chart["date"] = pd.to_datetime(chart["created_at"]).dt.date
                    trend = chart.groupby("date")[sales_column].sum().reset_index()
                    
                    fig = px.line(
                        trend,
                        x="date",
                        y=sales_column,
                        title="Daily Sales",
                        labels={"date": "Date", sales_column: "Sales (MMK)"}
                    )
                    fig.update_layout(height=350)
                    ui.plotly(fig).classes('w-full')
                else:
                    ui.label('No sales data').classes('text-gray-500')
        
        # ======================================================================
        # BUILD INVENTORY HEALTH
        # ======================================================================
        
        def build_inventory_health(container: Any):
            """Build inventory health section."""
            container.clear()
            
            with container:
                ui.label('📦 Inventory Health').classes('text-xl font-bold mb-2')
                
                try:
                    supabase = db()
                    inventory = (
                        supabase
                        .table("view_inventory_status")
                        .select("""
                            warehouse_name,
                            product_name,
                            qty,
                            reorder_level
                        """)
                        .execute()
                        .data
                        or []
                    )
                    
                    df_inv = pd.DataFrame(inventory)
                    
                    if not df_inv.empty:
                        low_stock = df_inv[df_inv["qty"] <= df_inv["reorder_level"]]
                        
                        with ui.card().classes('w-full p-4 bg-orange-50 mb-2'):
                            ui.label('Low Stock Items').classes('text-sm text-gray-600')
                            ui.label(str(len(low_stock))).classes('text-3xl font-bold text-orange-700')
                        
                        if len(low_stock) > 0:
                            columns = [
                                {'name': col, 'label': col, 'field': col, 'sortable': True}
                                for col in low_stock.columns
                            ]
                            ui.table(
                                columns=columns,
                                rows=low_stock.to_dict('records'),
                                row_key='product_name',
                                pagination=5,
                            ).classes('w-full')
                    else:
                        ui.label('No inventory data').classes('text-gray-500')
                
                except Exception as e:
                    ui.notify(f"Inventory error: {e}", type='error', position='top')
        
        # ======================================================================
        # BUILD RECENT TRANSACTIONS
        # ======================================================================
        
        def build_recent_transactions(container: Any, df_sales: pd.DataFrame):
            """Build recent transactions table."""
            container.clear()
            
            with container:
                ui.label('📋 Recent Transactions').classes('text-xl font-bold mb-2')
                
                if not df_sales.empty:
                    display_df = df_sales.head(20)
                    
                    columns = [
                        {'name': col, 'label': col, 'field': col, 'sortable': True}
                        for col in display_df.columns
                    ]
                    
                    ui.table(
                        columns=columns,
                        rows=display_df.to_dict('records'),
                        row_key='id',
                        pagination=10,
                    ).classes('w-full')
                else:
                    ui.label('No transaction records found.').classes('text-gray-500')
        
        # ======================================================================
        # REFRESH FUNCTION
        # ======================================================================
        
        def refresh_dashboard():
            """Refresh all dashboard sections."""
            try:
                refresh_btn.disable()
                refresh_btn.text = '⏳ Loading...'
                
                # Get filter values
                selected_wh = warehouse_select.value
                warehouse_id = selected_wh.get("id") if selected_wh else None
                period = period_select.value
                
                # Calculate dates
                start_date, end_date = calculate_dates(period)
                
                # Load data
                df_sales = load_sales_data(warehouse_id, start_date, end_date)
                
                # Determine sales column
                sales_column = None
                if not df_sales.empty:
                    if "total" in df_sales.columns:
                        sales_column = "total"
                    elif "total_amount" in df_sales.columns:
                        sales_column = "total_amount"
                
                # Build sections
                build_kpi_cards(kpi_container, df_sales)
                build_sales_trend(trend_container, df_sales, sales_column)
                build_inventory_health(inventory_container)
                build_recent_transactions(transactions_container, df_sales)
            
            except Exception as e:
                ui.notify(f'Dashboard error: {e}', type='error', position='top')
            
            finally:
                refresh_btn.enable()
                refresh_btn.text = '🔄 Refresh'
        
        # Wire up filter events
        warehouse_select.on_value_change(lambda e: refresh_dashboard())
        period_select.on_value_change(lambda e: refresh_dashboard())
        
        # Initial load
        refresh_dashboard()


# ==============================================================================
# ADVANCED DASHBOARD WITH CHARTS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced dashboard with additional charts."""
    
    require_login()
    
    target = container or ui.column()
    
    with target:
        ui.label('📈 Enterprise Analytics Dashboard').classes('text-3xl font-bold mb-4')
        
        # Filters
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            period = ui.select(
                ['Today', 'Last 7 Days', 'This Month', 'Year to Date'],
                label='Period',
                value='This Month',
            ).classes('min-w-[200px]')
            
            refresh_btn = ui.button('🔄 Refresh').classes('bg-primary text-white')
        
        # Tabbed charts
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_sales = ui.tab('📈 Sales', icon='trending_up')
            tab_inventory = ui.tab('📦 Inventory', icon='inventory')
            tab_payments = ui.tab('💰 Payments', icon='payments')
        
        with ui.tab_panels(tabs, value=tab_sales).classes('w-full'):
            with ui.tab_panel(tab_sales):
                charts_container = ui.column().classes('w-full')
                
                def load_sales_charts():
                    charts_container.clear()
                    
                    try:
                        supabase = db()
                        result = supabase.table("sales").select("*").limit(100).execute()
                        df = pd.DataFrame(result.data or [])
                        
                        if not df.empty:
                            with charts_container:
                                # Sales by day
                                df['date'] = pd.to_datetime(df['created_at']).dt.date
                                daily_sales = df.groupby('date')['total'].sum().reset_index()
                                
                                fig1 = px.line(daily_sales, x='date', y='total', title='Daily Sales')
                                ui.plotly(fig1).classes('w-full mb-4')
                                
                                # Sales by status
                                fig2 = px.pie(df, names='sale_status', title='Sales by Status')
                                ui.plotly(fig2).classes('w-full')
                    
                    except Exception as e:
                        ui.notify(f'Error: {e}', type='error', position='top')
                
                load_sales_charts()
            
            with ui.tab_panel(tab_inventory):
                ui.label('Inventory analytics coming soon').classes('text-gray-500')
            
            with ui.tab_panel(tab_payments):
                ui.label('Payment analytics coming soon').classes('text-gray-500')


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
