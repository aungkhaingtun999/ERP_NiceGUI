# ==========================================================
# pages/Search.py
# ERP ENTERPRISE v15
# GLOBAL SEARCH ENGINE
# NICE GUI VERSION
# ==========================================================

from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from nicegui import ui

from database import get_supabase
from utils.ui import show_table


# ----------------------------------------------------------
# DATABASE
# ----------------------------------------------------------

supabase = get_supabase()


# ==============================================================================
# SEARCH FUNCTIONS
# ==============================================================================

def search_products(keyword: str) -> List[Dict[str, Any]]:
    """Search products by name or barcode."""
    try:
        return (
            supabase
            .table("products")
            .select("*")
            .or_(
                f"name.ilike.%{keyword}%,"
                f"barcode.ilike.%{keyword}%,"
                f"sku.ilike.%{keyword}%"
            )
            .limit(50)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def search_suppliers(keyword: str) -> List[Dict[str, Any]]:
    """Search suppliers by code, name, or phone."""
    try:
        return (
            supabase
            .table("suppliers")
            .select("*")
            .or_(
                f"supplier_code.ilike.%{keyword}%,"
                f"company_name.ilike.%{keyword}%,"
                f"phone.ilike.%{keyword}%"
            )
            .limit(50)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def search_customers(keyword: str) -> List[Dict[str, Any]]:
    """Search customers by name, phone, or code."""
    try:
        return (
            supabase
            .table("customers")
            .select("*")
            .or_(
                f"full_name.ilike.%{keyword}%,"
                f"phone.ilike.%{keyword}%,"
                f"customer_code.ilike.%{keyword}%"
            )
            .limit(50)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def search_sales(keyword: str) -> List[Dict[str, Any]]:
    """Search sales by invoice number."""
    try:
        return (
            supabase
            .table("sales")
            .select("*")
            .ilike("invoice_no", f"%{keyword}%")
            .limit(50)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def build_section_header(container: Any, title: str, icon: str, count: int):
    """Build section header with count."""
    container.clear()
    
    with container:
        with ui.row().classes('w-full items-center gap-2 mb-2'):
            ui.icon(icon).classes('text-gray-500')
            ui.label(title).classes('text-xl font-bold')
            ui.badge(str(count)).classes('bg-blue-100 text-blue-700')


def build_data_table(container: Any, data: List[Dict[str, Any]]):
    """Build data table from list of dicts."""
    container.clear()
    
    if not data:
        with container:
            with ui.card().classes('w-full p-3 bg-gray-50'):
                ui.label('No results found').classes('text-gray-500 text-center')
        return
    
    with container:
        df = pd.DataFrame(data)
        
        # Limit columns for display
        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in df.columns
        ]
        
        ui.table(
            columns=columns,
            rows=df.to_dict('records'),
            row_key=df.columns[0],
            pagination=10,
        ).classes('w-full')


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main global search page."""
    
    target = container or ui.column()
    
    with target:
        # Header
        ui.label('🔎 ERP Global Search Engine').classes('text-3xl font-bold mb-2')
        ui.label('Search Products, Suppliers, Customers and Transactions').classes('text-gray-500 mb-4')
        
        # Search input
        search_input = ui.input(
            'Enter search keyword',
            placeholder='Barcode / Name / Phone / Invoice...',
        ).classes('w-full mb-4').props('clearable')
        
        # Results containers
        results_container = ui.column().classes('w-full')
        
        # Loading indicator
        loading_container = ui.column().classes('w-full')
        
        def perform_search():
            """Perform search across all tables."""
            keyword = (search_input.value or '').strip()
            
            results_container.clear()
            loading_container.clear()
            
            if not keyword:
                with results_container:
                    with ui.card().classes('w-full p-4 bg-gray-50'):
                        ui.label('🔍 Type something to search...').classes('text-gray-500 text-center')
                return
            
            # Show loading
            with loading_container:
                with ui.row().classes('items-center gap-2'):
                    ui.spinner(size='sm')
                    ui.label(f'Searching for "{keyword}"...').classes('text-gray-500')
            
            # Search all tables
            products = search_products(keyword)
            suppliers = search_suppliers(keyword)
            customers = search_customers(keyword)
            sales = search_sales(keyword)
            
            # Clear loading
            loading_container.clear()
            
            # Display results
            with results_container:
                # Products
                ui.label(f'📦 Products ({len(products)})').classes('text-xl font-bold mb-2')
                
                if products:
                    build_data_table(ui.column(), products)
                else:
                    ui.label('No products found').classes('text-gray-500 mb-4')
                
                ui.separator().classes('my-4')
                
                # Suppliers
                ui.label(f'🏭 Suppliers ({len(suppliers)})').classes('text-xl font-bold mb-2')
                
                if suppliers:
                    build_data_table(ui.column(), suppliers)
                else:
                    ui.label('No suppliers found').classes('text-gray-500 mb-4')
                
                ui.separator().classes('my-4')
                
                # Customers
                ui.label(f'👥 Customers ({len(customers)})').classes('text-xl font-bold mb-2')
                
                if customers:
                    build_data_table(ui.column(), customers)
                else:
                    ui.label('No customers found').classes('text-gray-500 mb-4')
                
                ui.separator().classes('my-4')
                
                # Sales
                ui.label(f'🧾 Sales ({len(sales)})').classes('text-xl font-bold mb-2')
                
                if sales:
                    build_data_table(ui.column(), sales)
                else:
                    ui.label('No sales found').classes('text-gray-500 mb-4')
                
                # Summary
                total_results = len(products) + len(suppliers) + len(customers) + len(sales)
                
                with ui.card().classes('w-full p-3 bg-blue-50 mt-4'):
                    ui.label(
                        f'📊 Total Results: {total_results} '
                        f'(Products: {len(products)}, Suppliers: {len(suppliers)}, '
                        f'Customers: {len(customers)}, Sales: {len(sales)})'
                    ).classes('text-blue-700 font-semibold')
        
        # Wire up search
        search_input.on_value_change(lambda e: perform_search())
        
        # Initial state
        with results_container:
            with ui.card().classes('w-full p-4 bg-gray-50'):
                ui.label('🔍 Type something to search...').classes('text-gray-500 text-center')


# ==============================================================================
# ADVANCED VIEW WITH TABS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced search with tabs."""
    
    target = container or ui.column()
    
    with target:
        ui.label('🔎 ERP Global Search').classes('text-3xl font-bold mb-4')
        
        search_input = ui.input(
            'Search',
            placeholder='Enter keyword...',
        ).classes('w-full mb-4')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_products = ui.tab('📦 Products', icon='inventory')
            tab_suppliers = ui.tab('🏭 Suppliers', icon='factory')
            tab_customers = ui.tab('👥 Customers', icon='people')
            tab_sales = ui.tab('🧾 Sales', icon='receipt')
        
        with ui.tab_panels(tabs, value=tab_products).classes('w-full'):
            with ui.tab_panel(tab_products):
                products_container = ui.column().classes('w-full')
            
            with ui.tab_panel(tab_suppliers):
                suppliers_container = ui.column().classes('w-full')
            
            with ui.tab_panel(tab_customers):
                customers_container = ui.column().classes('w-full')
            
            with ui.tab_panel(tab_sales):
                sales_container = ui.column().classes('w-full')
        
        def perform_search():
            """Perform search."""
            keyword = (search_input.value or '').strip()
            
            if not keyword:
                return
            
            # Products
            products = search_products(keyword)
            products_container.clear()
            with products_container:
                build_data_table(ui.column(), products)
            
            # Suppliers
            suppliers = search_suppliers(keyword)
            suppliers_container.clear()
            with suppliers_container:
                build_data_table(ui.column(), suppliers)
            
            # Customers
            customers = search_customers(keyword)
            customers_container.clear()
            with customers_container:
                build_data_table(ui.column(), customers)
            
            # Sales
            sales = search_sales(keyword)
            sales_container.clear()
            with sales_container:
                build_data_table(ui.column(), sales)
        
        search_input.on_value_change(lambda e: perform_search())


# ==============================================================================
# QUICK SEARCH SIDEBAR
# ==============================================================================

def render_quick_search(container: Optional[Any] = None):
    """Render quick search sidebar widget."""
    target = container or ui.column()
    
    with target:
        ui.label('🔎 Quick Search').classes('font-bold mb-2')
        
        search_input = ui.input(
            placeholder='Search...',
        ).classes('w-full mb-2').props('clearable')
        
        results_container = ui.column().classes('w-full')
        
        def quick_search():
            keyword = (search_input.value or '').strip()
            results_container.clear()
            
            if not keyword:
                return
            
            # Quick product search
            products = search_products(keyword)
            
            with results_container:
                if products:
                    ui.label(f'Products ({len(products)})').classes('text-sm font-bold')
                    
                    for p in products[:5]:
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('inventory').classes('text-gray-400 text-sm')
                            ui.label(p.get('name', 'Unknown')).classes('text-sm')
                    
                    if len(products) > 5:
                        ui.label(f'+{len(products) - 5} more...').classes('text-xs text-gray-400')
                else:
                    ui.label('No results').classes('text-xs text-gray-400')
        
        search_input.on_value_change(lambda e: quick_search())


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
