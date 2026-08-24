# ==============================================================================
# erp_pages/2_Receipt.py
# ERP ENTERPRISE RECEIPT VIEWER v5.1
# NICE GUI VERSION
# ERP CORE CONNECTED
# PDF + THERMAL PRINT READY
# Myanmar Time Supported
# Sale ID Display Added
# ==============================================================================

from typing import Dict, Any, Optional, List
import pandas as pd
from nicegui import ui, app

# ==============================================================================
# ERP DATABASE BRIDGE
# ==============================================================================

from database import (
    search_receipts,
    get_receipt,
    get_sale_items,
)

# ==============================================================================
# TIME ENGINE
# ==============================================================================

from utils.timezone import (
    format_db_datetime
)

# ==============================================================================
# RECEIPT ENGINE
# ==============================================================================

from utils.receipt_pdf import (
    generate_pdf
)

from utils.thermal_receipt import (
    build_receipt_data,
    print_thermal
)

from auth import is_authenticated


# ==============================================================================
# SESSION STATE
# ==============================================================================

class ReceiptState:
    """Session state for receipt viewer."""
    
    def __init__(self):
        self.selected_receipt: Optional[str] = None
        self.receipt_data: Optional[Dict[str, Any]] = None
        self.pdf_result: Optional[tuple] = None


def get_state() -> ReceiptState:
    """Get or create receipt state."""
    client_id = app.context.client.id if app.context.client else 'default'
    
    if not hasattr(app.storage, 'receipt_state'):
        app.storage.receipt_state = {}
    
    if client_id not in app.storage.receipt_state:
        app.storage.receipt_state[client_id] = ReceiptState()
    
    return app.storage.receipt_state[client_id]


# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def build_receipt_summary(
    container: Any,
    receipt: Dict[str, Any],
    sale_id: Any
):
    """Build receipt summary cards."""
    container.clear()
    
    with container:
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Sale ID
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Sale ID').classes('text-sm text-gray-600')
                ui.label(str(sale_id) if sale_id is not None else '-').classes(
                    'text-xl font-bold font-mono'
                )
            
            # Invoice No
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Invoice No').classes('text-sm text-gray-600')
                ui.label(receipt.get("invoice_no", "-")).classes('text-xl font-bold')
            
            # Total
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Total').classes('text-sm text-gray-600')
                ui.label(f"{float(receipt.get('total', 0)):,.0f} MMK").classes(
                    'text-xl font-bold text-green-700'
                )
            
            # Status
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Status').classes('text-sm text-gray-600')
                status = receipt.get("status", "-")
                ui.label(status).classes('text-xl font-bold')
        
        # Date
        raw_time = receipt.get("created_at") or receipt.get("date")
        
        if raw_time:
            ui.label(f"📅 Date: {format_db_datetime(raw_time)}").classes('text-sm text-gray-500 mt-2')
        else:
            ui.label("📅 Date: -").classes('text-sm text-gray-500 mt-2')


def build_items_table(container: Any, items: List[Dict[str, Any]]):
    """Build sale items table."""
    container.clear()
    
    rows = []
    
    for item in items:
        qty = float(item.get("quantity", 0))
        price = float(item.get("unit_price", 0))
        total = float(item.get("total", qty * price))
        
        product_name = item.get("name", item.get("product_id", "-"))
        
        rows.append({
            "Product": product_name,
            "Quantity": f"{qty:,.0f}",
            "Unit Price": f"{price:,.0f}",
            "Amount": f"{total:,.0f}"
        })
    
    if not rows:
        with container:
            with ui.card().classes('w-full p-4 bg-orange-50'):
                ui.label('No items found').classes('text-orange-700')
        return
    
    with container:
        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in rows[0].keys()
        ]
        
        ui.table(
            columns=columns,
            rows=rows,
            row_key='Product',
            pagination=10,
            title='Sale Items',
        ).classes('w-full')


def build_payment_details(container: Any, receipt: Dict[str, Any]):
    """Build payment details section."""
    container.clear()
    
    with container:
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Subtotal
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-gray-50'):
                ui.label('Subtotal').classes('text-sm text-gray-600')
                ui.label(f"{float(receipt.get('subtotal', 0)):,.0f} MMK").classes('font-semibold')
            
            # Tax
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-gray-50'):
                ui.label('Tax').classes('text-sm text-gray-600')
                ui.label(f"{float(receipt.get('tax', 0)):,.0f} MMK").classes('font-semibold')
            
            # Tax Rate
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-gray-50'):
                ui.label('Tax Rate').classes('text-sm text-gray-600')
                ui.label(f"{float(receipt.get('tax_rate', 0)):,.2f}%").classes('font-semibold')
            
            # Grand Total
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-green-50'):
                ui.label('Grand Total').classes('text-sm text-gray-600')
                ui.label(f"{float(receipt.get('total', 0)):,.0f} MMK").classes(
                    'font-semibold text-green-700'
                )


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point."""
    
    # Auth check
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            ui.label('⛔ Please login first').classes('text-orange-700')
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        # Header
        ui.label('🧾 ERP Enterprise Receipt Viewer v5.1').classes('text-3xl font-bold mb-4')
        
        # ======================================================================
        # SEARCH SECTION
        # ======================================================================
        
        search_container = ui.column().classes('w-full mb-4')
        
        with search_container:
            search_input = ui.input(
                '🔍 Search Invoice No',
                placeholder='Enter invoice number...'
            ).classes('w-full mb-2')
            
            results_container = ui.column().classes('w-full')
            
            def handle_search():
                results_container.clear()
                
                keyword = search_input.value or ''
                
                if not keyword:
                    return
                
                results = search_receipts(keyword)
                
                if not results:
                    with results_container:
                        ui.notify('❌ No receipt found', type='error', position='top')
                    return
                
                options = {
                    f"{r.get('invoice_no')} | {float(r.get('total', 0)):,.0f} MMK": r
                    for r in results
                }
                
                with results_container:
                    selected = ui.select(
                        list(options.keys()),
                        label='Select Receipt',
                    ).classes('w-full mb-2')
                    
                    load_btn = ui.button(
                        '📥 Load Receipt',
                        on_click=lambda: handle_load_receipt(options[selected.value])
                    ).classes('w-full bg-primary text-white')
            
            search_input.on_value_change(lambda e: handle_search())
        
        # ======================================================================
        # RECEIPT DISPLAY CONTAINERS
        # ======================================================================
        
        summary_container = ui.column().classes('w-full mb-4')
        items_container = ui.column().classes('w-full mb-4')
        payment_container = ui.column().classes('w-full mb-4')
        action_container = ui.column().classes('w-full mb-4')
        
        def handle_load_receipt(receipt_meta: Dict[str, Any]):
            """Load receipt data."""
            receipt = get_receipt(receipt_meta.get("invoice_no"))
            
            state.receipt_data = receipt
            state.selected_receipt = receipt_meta.get("invoice_no")
            state.pdf_result = None
            
            display_receipt()
        
        def display_receipt():
            """Display loaded receipt."""
            receipt = state.receipt_data
            
            if not receipt:
                with summary_container:
                    ui.label('Search and load receipt').classes('text-gray-500')
                return
            
            # Sale ID
            sale_id = receipt.get("id")
            
            # Load items
            items = []
            if sale_id:
                items = get_sale_items(str(sale_id))
            
            # Build sections
            build_receipt_summary(summary_container, receipt, sale_id)
            
            ui.separator().classes('my-2')
            build_items_table(items_container, items)
            
            ui.separator().classes('my-2')
            build_payment_details(payment_container, receipt)
            
            # Action buttons
            action_container.clear()
            with action_container:
                with ui.row().classes('w-full gap-2 flex-wrap'):
                    # PDF Generate
                    pdf_btn = ui.button(
                        '📄 Generate PDF',
                        on_click=lambda: handle_generate_pdf(receipt, items, pdf_btn)
                    ).classes('flex-1 bg-blue-500 text-white')
                    
                    # Thermal Print
                    print_btn = ui.button(
                        '🖨 Print Receipt',
                        on_click=lambda: handle_print(receipt, items, print_btn)
                    ).classes('flex-1 bg-green-500 text-white')
                    
                    # Clear
                    clear_btn = ui.button(
                        '🆕 Clear Receipt',
                        on_click=handle_clear
                    ).classes('flex-1 bg-gray-500 text-white')
                
                # PDF Download
                if state.pdf_result:
                    pdf_bytes, filename = state.pdf_result
                    
                    ui.button(
                        '⬇ Download Receipt',
                        on_click=lambda: ui.download(pdf_bytes, f"{filename}.pdf")
                    ).props('flat').classes('w-full bg-green-50 mt-2')
                
                # Debug expander
                with ui.expansion('🔎 Debug Receipt Data', icon='bug_report').classes('w-full mt-2'):
                    data = build_receipt_data(receipt, items)
                    ui.json_editor({'content': {'json': data}}).classes('w-full')
        
        def handle_generate_pdf(receipt: Dict, items: List, pdf_btn: Any):
            """Handle PDF generation."""
            try:
                pdf_btn.disable()
                pdf_btn.text = '⏳ Generating...'
                
                data = build_receipt_data(receipt, items)
                result = generate_pdf(data)
                
                if result:
                    state.pdf_result = result
                    ui.notify('✅ PDF generated successfully', type='positive', position='top')
                    display_receipt()
                else:
                    state.pdf_result = None
                    ui.notify('❌ PDF generation failed', type='error', position='top')
            
            except Exception as e:
                state.pdf_result = None
                ui.notify(f'❌ PDF generation error: {e}', type='error', position='top')
            
            finally:
                pdf_btn.enable()
                pdf_btn.text = '📄 Generate PDF'
        
        def handle_print(receipt: Dict, items: List, print_btn: Any):
            """Handle thermal print."""
            try:
                print_btn.disable()
                print_btn.text = '⏳ Printing...'
                
                data = build_receipt_data(receipt, items)
                result = print_thermal(data)
                
                if result:
                    ui.notify('✅ Receipt printed successfully', type='positive', position='top')
                else:
                    ui.notify('❌ Print failed', type='error', position='top')
            
            except Exception as e:
                ui.notify(f'❌ Print error: {e}', type='error', position='top')
            
            finally:
                print_btn.enable()
                print_btn.text = '🖨 Print Receipt'
        
        def handle_clear():
            """Clear receipt data."""
            state.receipt_data = None
            state.selected_receipt = None
            state.pdf_result = None
            
            summary_container.clear()
            items_container.clear()
            payment_container.clear()
            action_container.clear()
            
            with summary_container:
                ui.label('Search and load receipt').classes('text-gray-500')
            
            ui.notify('Cleared', type='info', position='top')
        
        # Initial state
        with summary_container:
            ui.label('Search and load receipt').classes('text-gray-500')


# ==============================================================================
# ADVANCED VIEW WITH TABS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced view with tabs."""
    
    if not is_authenticated():
        ui.label('⛔ Please login first').classes('text-orange-700')
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        ui.label('🧾 Receipt Viewer').classes('text-3xl font-bold mb-4')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_search = ui.tab('🔍 Search', icon='search')
            tab_view = ui.tab('📄 View Receipt', icon='receipt')
            tab_print = ui.tab('🖨 Print', icon='print')
        
        with ui.tab_panels(tabs, value=tab_search).classes('w-full'):
            with ui.tab_panel(tab_search):
                # Search functionality
                search_input = ui.input('🔍 Search Invoice No').classes('w-full mb-2')
                results_container = ui.column().classes('w-full')
                
                def handle_search():
                    results_container.clear()
                    keyword = search_input.value or ''
                    
                    if not keyword:
                        return
                    
                    results = search_receipts(keyword)
                    
                    if not results:
                        ui.notify('❌ No receipt found', type='error', position='top')
                        return
                    
                    options = {
                        f"{r.get('invoice_no')} | {float(r.get('total', 0)):,.0f} MMK": r
                        for r in results
                    }
                    
                    with results_container:
                        selected = ui.select(list(options.keys()), label='Select Receipt').classes('w-full mb-2')
                        ui.button(
                            '📥 Load Receipt',
                            on_click=lambda: handle_load(options[selected.value])
                        ).classes('w-full bg-primary text-white')
                
                search_input.on_value_change(lambda e: handle_search())
            
            with ui.tab_panel(tab_view):
                if state.receipt_data:
                    receipt = state.receipt_data
                    sale_id = receipt.get("id")
                    items = get_sale_items(str(sale_id)) if sale_id else []
                    
                    build_receipt_summary(ui.column(), receipt, sale_id)
                    ui.separator()
                    build_items_table(ui.column(), items)
                    ui.separator()
                    build_payment_details(ui.column(), receipt)
                else:
                    ui.label('No receipt loaded. Search first.').classes('text-gray-500')
            
            with ui.tab_panel(tab_print):
                if state.receipt_data:
                    receipt = state.receipt_data
                    sale_id = receipt.get("id")
                    items = get_sale_items(str(sale_id)) if sale_id else []
                    
                    ui.button(
                        '🖨 Print Receipt',
                        on_click=lambda: handle_print(receipt, items, None)
                    ).classes('w-full bg-green-500 text-white mb-2')
                    
                    ui.button(
                        '📄 Generate PDF',
                        on_click=lambda: handle_generate_pdf(receipt, items, None)
                    ).classes('w-full bg-blue-500 text-white')
                else:
                    ui.label('No receipt loaded. Search first.').classes('text-gray-500')
        
        def handle_load(receipt_meta):
            receipt = get_receipt(receipt_meta.get("invoice_no"))
            state.receipt_data = receipt
            state.selected_receipt = receipt_meta.get("invoice_no")
            state.pdf_result = None
            ui.notify('Receipt loaded', type='positive', position='top')


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
