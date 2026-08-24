# ==============================================================================
# erp_pages/6_Receipt_Viewer.py
# ERP ENTERPRISE RECEIPT VIEWER v4.0
# NICE GUI VERSION
# ERP CORE CONNECTED
# Myanmar Time Supported
# ==============================================================================

from typing import Dict, Any, Optional, List
import pandas as pd
from nicegui import ui, app

from database import (
    search_receipts,
    get_receipt,
    get_sale_items
)

from utils.timezone import (
    format_db_datetime
)

from auth import is_authenticated


# ==============================================================================
# SESSION STATE
# ==============================================================================

class ReceiptViewerState:
    """Session state for receipt viewer."""
    
    def __init__(self):
        self.receipt_data: Optional[Dict[str, Any]] = None
        self.selected_invoice: Optional[str] = None


def get_state() -> ReceiptViewerState:
    """Get or create receipt viewer state."""
    client_id = app.context.client.id if app.context.client else 'default'
    
    if not hasattr(app.storage, 'receipt_viewer_state'):
        app.storage.receipt_viewer_state = {}
    
    if client_id not in app.storage.receipt_viewer_state:
        app.storage.receipt_viewer_state[client_id] = ReceiptViewerState()
    
    return app.storage.receipt_viewer_state[client_id]


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_float(value: Any) -> float:
    """Safely convert value to float."""
    try:
        return float(value or 0)
    except Exception:
        return 0.0


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main receipt viewer page."""
    
    # Auth check
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            ui.label('⛔ Please log in first.').classes('text-orange-700')
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        ui.label('🧾 ERP Enterprise Receipt Viewer').classes('text-3xl font-bold mb-4')
        
        # ======================================================================
        # SEARCH SECTION
        # ======================================================================
        
        search_input = ui.input(
            '🔍 Search Invoice No',
            value=state.selected_invoice or "",
            placeholder='INV-20260726081229',
        ).classes('w-full mb-2')
        
        search_results = ui.column().classes('w-full mb-4')
        
        def handle_search():
            """Handle receipt search."""
            search_results.clear()
            
            search_query = search_input.value or ''
            
            if not search_query:
                return
            
            matches = search_receipts(search_query)
            
            if not matches:
                with search_results:
                    ui.notify(f'No invoice found: {search_query}', type='error', position='top')
                return
            
            with search_results:
                if len(matches) > 1:
                    # Multiple matches - show selector
                    options = {
                        f"{r.get('invoice_no','-')} | {safe_float(r.get('total')):,.0f} MMK": r
                        for r in matches
                    }
                    
                    selected = ui.select(
                        list(options.keys()),
                        label='Select Invoice',
                    ).classes('w-full mb-2')
                    
                    load_btn = ui.button(
                        '📥 Load Receipt',
                        on_click=lambda: load_receipt(options[selected.value])
                    ).classes('w-full bg-primary text-white')
                
                else:
                    # Single match
                    sale = matches[0]
                    
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('check_circle').classes('text-green-500')
                        ui.label(f"Found: {sale.get('invoice_no')}").classes('text-green-700')
                    
                    load_btn = ui.button(
                        '📥 Load Receipt',
                        on_click=lambda: load_receipt(sale)
                    ).classes('w-full bg-primary text-white')
        
        search_input.on_value_change(lambda e: handle_search())
        
        # ======================================================================
        # DYNAMIC CONTENT CONTAINER
        # ======================================================================
        
        content_container = ui.column().classes('w-full')
        
        def load_receipt(sale: Dict[str, Any]):
            """Load receipt data."""
            receipt = get_receipt(sale.get("invoice_no"))
            
            state.receipt_data = receipt
            state.selected_invoice = sale.get("invoice_no")
            
            display_receipt()
        
        def display_receipt():
            """Display loaded receipt."""
            content_container.clear()
            
            receipt = state.receipt_data
            
            if not receipt:
                with content_container:
                    ui.label('🔎 Search and load receipt').classes('text-gray-500')
                return
            
            # Load items
            sale_id = receipt.get("id")
            items = []
            
            if sale_id:
                items = get_sale_items(str(sale_id))
            
            with content_container:
                ui.separator().classes('my-4')
                ui.label(f"🧾 Invoice: {receipt.get('invoice_no','-')}").classes('text-xl font-bold mb-4')
                
                # Summary cards
                total = safe_float(receipt.get("total"))
                paid = safe_float(receipt.get("paid_amount"))
                change = safe_float(receipt.get("change_amount", paid - total))
                
                with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                    with ui.card().classes('p-4 flex-1 min-w-[150px] bg-blue-50'):
                        ui.label('Total').classes('text-sm text-gray-600')
                        ui.label(f'{total:,.0f} MMK').classes('text-2xl font-bold text-blue-700')
                    
                    with ui.card().classes('p-4 flex-1 min-w-[150px] bg-green-50'):
                        ui.label('Paid').classes('text-sm text-gray-600')
                        ui.label(f'{paid:,.0f} MMK').classes('text-2xl font-bold text-green-700')
                    
                    with ui.card().classes('p-4 flex-1 min-w-[150px] bg-orange-50'):
                        ui.label('Change').classes('text-sm text-gray-600')
                        ui.label(f'{change:,.0f} MMK').classes('text-2xl font-bold text-orange-700')
                
                # Date
                if receipt.get("created_at"):
                    ui.label(f"📅 Date: {format_db_datetime(receipt['created_at'])}").classes(
                        'text-sm text-gray-500 mb-4'
                    )
                
                ui.separator().classes('my-4')
                ui.label('🛒 Sale Items').classes('text-xl font-bold mb-4')
                
                # Items table
                rows = []
                
                for item in items:
                    qty = safe_float(item.get("quantity"))
                    price = safe_float(item.get("unit_price"))
                    amount = safe_float(item.get("total"))
                    
                    if amount == 0:
                        amount = qty * price
                    
                    rows.append({
                        "Product ID": item.get("product_id"),
                        "Qty": f"{qty:,.0f}",
                        "Unit Price": f"{price:,.0f}",
                        "Amount": f"{amount:,.0f}",
                    })
                
                if rows:
                    columns = [
                        {'name': col, 'label': col, 'field': col, 'sortable': True}
                        for col in rows[0].keys()
                    ]
                    
                    ui.table(
                        columns=columns,
                        rows=rows,
                        row_key='Product ID',
                        pagination=10,
                    ).classes('w-full mb-4')
                else:
                    ui.label('No items found').classes('text-gray-500')
                
                # Calculated total
                calculated_total = sum(
                    safe_float(i.get("quantity")) * safe_float(i.get("unit_price"))
                    for i in items
                )
                
                with ui.card().classes('w-full p-3 bg-gray-50 mb-4'):
                    ui.label(f'Calculated Items Total: {calculated_total:,.0f} MMK').classes('text-gray-700')
                
                # Clear button
                clear_btn = ui.button(
                    '🆕 Clear',
                    on_click=clear_receipt
                ).classes('w-full bg-gray-500 text-white')
        
        def clear_receipt():
            """Clear receipt state."""
            state.receipt_data = None
            state.selected_invoice = None
            search_input.value = ""
            search_results.clear()
            content_container.clear()
            
            with content_container:
                ui.label('🔎 Search and load receipt').classes('text-gray-500')
            
            ui.notify('Cleared', type='info', position='top')
        
        # Initial state
        if state.receipt_data:
            display_receipt()
        else:
            with content_container:
                ui.label('🔎 Search and load receipt').classes('text-gray-500')


# ==============================================================================
# ADVANCED VIEW WITH TABS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced receipt viewer with tabs."""
    
    if not is_authenticated():
        ui.label('⛔ Please log in first.').classes('text-orange-700')
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        ui.label('🧾 Receipt Viewer').classes('text-3xl font-bold mb-4')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_search = ui.tab('🔍 Search', icon='search')
            tab_view = ui.tab('📄 View', icon='receipt')
        
        with ui.tab_panels(tabs, value=tab_search).classes('w-full'):
            with ui.tab_panel(tab_search):
                search_input = ui.input('🔍 Search Invoice No').classes('w-full mb-2')
                results_container = ui.column().classes('w-full')
                
                def handle_search():
                    results_container.clear()
                    query = search_input.value or ''
                    
                    if not query:
                        return
                    
                    matches = search_receipts(query)
                    
                    if not matches:
                        ui.notify(f'No invoice found: {query}', type='error', position='top')
                        return
                    
                    with results_container:
                        if len(matches) > 1:
                            options = {
                                f"{r.get('invoice_no','-')} | {safe_float(r.get('total')):,.0f} MMK": r
                                for r in matches
                            }
                            selected = ui.select(list(options.keys()), label='Select').classes('w-full mb-2')
                            ui.button(
                                'Load',
                                on_click=lambda: load_receipt_data(options[selected.value])
                            ).classes('w-full bg-primary text-white')
                        else:
                            ui.button(
                                f"Load: {matches[0].get('invoice_no')}",
                                on_click=lambda: load_receipt_data(matches[0])
                            ).classes('w-full bg-primary text-white')
                
                search_input.on_value_change(lambda e: handle_search())
            
            with ui.tab_panel(tab_view):
                if state.receipt_data:
                    receipt = state.receipt_data
                    sale_id = receipt.get("id")
                    items = get_sale_items(str(sale_id)) if sale_id else []
                    
                    ui.label(f"Invoice: {receipt.get('invoice_no','-')}").classes('text-xl font-bold mb-4')
                    
                    total = safe_float(receipt.get("total"))
                    paid = safe_float(receipt.get("paid_amount"))
                    
                    with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                        with ui.card().classes('p-4 flex-1'):
                            ui.label('Total').classes('text-sm text-gray-600')
                            ui.label(f'{total:,.0f} MMK').classes('text-xl font-bold')
                        
                        with ui.card().classes('p-4 flex-1'):
                            ui.label('Paid').classes('text-sm text-gray-600')
                            ui.label(f'{paid:,.0f} MMK').classes('text-xl font-bold')
                else:
                    ui.label('No receipt loaded').classes('text-gray-500')
        
        def load_receipt_data(sale):
            receipt = get_receipt(sale.get("invoice_no"))
            state.receipt_data = receipt
            state.selected_invoice = sale.get("invoice_no")
            ui.notify('Receipt loaded', type='positive', position='top')


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
