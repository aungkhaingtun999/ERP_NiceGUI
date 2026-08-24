# ==============================================================================
# 2_Mobile_Inventory.py
# MOBILE INVENTORY ENTERPRISE v1.0
# NICE GUI VERSION
#
# ZXING PRIMARY BARCODE SCANNER
# PRODUCT SEARCH
# PRODUCT REGISTRATION
#
# ==============================================================================

from typing import Dict, Any, Optional, Callable
from nicegui import ui, app

from database import get_warehouses
from erp_pages.inventory.warehouse import render_warehouse_selector
from erp_pages.inventory.product_search import search_product
import erp_pages.inventory.product_form as product_form


# ==============================================================================
# SESSION STATE
# ==============================================================================

class MobileInventoryState:
    """Session state for mobile inventory."""
    
    def __init__(self):
        self.barcode: str = ""
        self.product: Optional[Dict[str, Any]] = None
        self.warehouse_id: Optional[str] = None
        self.scanner_active: bool = False
        self.last_scanned: str = ""


# ==============================================================================
# GLOBAL STATE (per client)
# ==============================================================================

def get_state() -> MobileInventoryState:
    """Get or create mobile inventory state."""
    if not hasattr(app.storage, 'mobile_inventory_state'):
        app.storage.mobile_inventory_state = {}
    
    client_id = app.context.client.id if app.context.client else 'default'
    
    if client_id not in app.storage.mobile_inventory_state:
        app.storage.mobile_inventory_state[client_id] = MobileInventoryState()
    
    return app.storage.mobile_inventory_state[client_id]


# ==============================================================================
# PRODUCT LOADING
# ==============================================================================

def load_product_by_barcode(
    barcode: str,
    state: MobileInventoryState,
    on_result: Optional[Callable] = None
):
    """Load product by barcode."""
    if not barcode:
        return
    
    try:
        product = search_product(barcode)
        state.product = product
        
        if product:
            ui.notify('✅ Product loaded successfully', type='positive', position='top')
        else:
            ui.notify('Product not found', type='warning', position='top')
        
        if on_result:
            on_result(product)
    
    except Exception as e:
        state.product = None
        ui.notify(f'Product Search Error: {e}', type='error', position='top')
        
        if on_result:
            on_result(None)


# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def render_product_view(
    container: Any,
    state: MobileInventoryState
):
    """Render product result view."""
    container.clear()
    
    product = state.product
    barcode = state.barcode
    
    with container:
        if product:
            # Product found
            ui.label('📦 Product Found').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # Product info
                with ui.card().classes('p-4 flex-1 min-w-[250px]'):
                    ui.label('Product Information').classes('font-bold mb-2')
                    
                    with ui.column().classes('gap-1'):
                        ui.label('Name:').classes('font-semibold')
                        ui.label(product.get('name', 'N/A')).classes('text-gray-700')
                        
                        ui.separator().classes('my-1')
                        
                        ui.label('Barcode:').classes('font-semibold')
                        ui.label(product.get('barcode', 'N/A')).classes('font-mono')
                        
                        ui.separator().classes('my-1')
                        
                        ui.label('SKU:').classes('font-semibold')
                        ui.label(product.get('sku', 'N/A')).classes('font-mono')
                
                # Stock info
                with ui.card().classes('p-4 flex-1 min-w-[250px]'):
                    ui.label('Stock Information').classes('font-bold mb-2')
                    
                    with ui.column().classes('gap-1'):
                        ui.label('Stock:').classes('font-semibold')
                        ui.label(str(product.get('stock', 0))).classes('text-gray-700')
                        
                        ui.separator().classes('my-1')
                        
                        ui.label('Selling Price:').classes('font-semibold')
                        ui.label(
                            f"{float(product.get('selling_price', 0) or 0):,.2f} MMK"
                        ).classes('text-gray-700')
        
        elif barcode:
            # Not found
            ui.label('Product not found').classes('text-xl font-bold text-orange-600 mb-2')
            ui.label('You can register this barcode as a new product.').classes('text-gray-500')
        
        else:
            # No barcode
            with ui.card().classes('w-full p-4 bg-gray-50'):
                ui.label('📷 Scan barcode or enter SKU').classes('text-gray-500 text-center')


def render_manual_search(
    container: Any,
    state: MobileInventoryState,
    on_search: Optional[Callable] = None
):
    """Render manual barcode input."""
    container.clear()
    
    with container:
        barcode_input = ui.input(
            '⌨️ Barcode / SKU',
            value=state.barcode,
            placeholder='Enter barcode or SKU...',
        ).classes('w-full')
        
        def handle_manual_search():
            barcode = barcode_input.value or ''
            
            if barcode != state.barcode:
                state.barcode = barcode
                
                if barcode:
                    load_product_by_barcode(barcode, state, on_search)
                else:
                    state.product = None
                    if on_search:
                        on_search(None)
        
        barcode_input.on_value_change(lambda e: handle_manual_search())


def render_new_product_section(
    container: Any,
    state: MobileInventoryState
):
    """Render new product registration section."""
    container.clear()
    
    product = state.product
    barcode = state.barcode
    
    with container:
        if product:
            return
        
        if barcode:
            ui.label('➕ Register New Product').classes('text-xl font-bold mb-4')
            
            try:
                product_form.render_new_product_form(barcode, container)
            except Exception as e:
                ui.notify(f'Error rendering product form: {e}', type='error', position='top')


def render_scanner_section(
    container: Any,
    state: MobileInventoryState
):
    """Render scanner section."""
    container.clear()
    
    with container:
        if state.scanner_active:
            with ui.card().classes('w-full p-4 bg-green-50'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('videocam').classes('text-green-500')
                    ui.label('📷 Scanner Active').classes('text-green-700 font-semibold')
            
            # Scanner placeholder (ZXING integration)
            with ui.card().classes('w-full p-4'):
                ui.label('Camera Scanner').classes('font-bold mb-2')
                ui.label('Scanner functionality requires camera integration').classes('text-gray-500')
                
                # Simulated scan button (for testing)
                test_barcode = ui.input('Test Barcode (for development)', placeholder='Enter test barcode').classes('w-full mb-2')
                
                ui.button(
                    'Simulate Scan',
                    on_click=lambda: handle_simulated_scan(test_barcode.value, state)
                ).classes('w-full bg-primary text-white')
        
        else:
            with ui.card().classes('w-full p-4 bg-gray-50'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('videocam_off').classes('text-gray-500')
                    ui.label('Scanner OFF').classes('text-gray-600')


def handle_simulated_scan(barcode: str, state: MobileInventoryState):
    """Handle simulated scan (for development/testing)."""
    if barcode and barcode != state.last_scanned:
        state.last_scanned = barcode
        state.barcode = barcode
        load_product_by_barcode(barcode, state)
        ui.notify(f'Scanned: {barcode}', type='info', position='top')


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main mobile inventory page entry point."""
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        # Header
        ui.label('📦 Mobile Inventory Enterprise').classes('text-3xl font-bold mb-2')
        ui.label('ZXING Primary Scanner | Barcode + SKU Search | Product Registration').classes(
            'text-gray-500 mb-4'
        )
        
        # Warehouse selector
        warehouses = get_warehouses()
        
        warehouse_container = ui.column().classes('w-full mb-4')
        
        with warehouse_container:
            try:
                selected_wh_id, selected_wh_name = render_warehouse_selector(
                    warehouses,
                    key="mobile_inventory_warehouse"
                )
                state.warehouse_id = selected_wh_id
                
                if selected_wh_name:
                    ui.label(f'Selected Warehouse: {selected_wh_name}').classes('text-sm text-gray-500')
            except Exception as e:
                ui.notify(f'Error loading warehouses: {e}', type='error', position='top')
        
        ui.separator().classes('my-4')
        
        # Control buttons
        with ui.row().classes('w-full gap-2 mb-4'):
            # Scanner toggle
            scanner_btn = ui.button(
                '📷 Start Scanner' if not state.scanner_active else '📷 Stop Scanner',
                on_click=lambda: toggle_scanner(state, scanner_btn)
            ).classes('flex-1 bg-primary text-white' if not state.scanner_active else 'flex-1 bg-orange-500 text-white')
            
            # Clear button
            clear_btn = ui.button(
                '🧹 Clear',
                on_click=lambda: clear_state(state)
            ).classes('flex-1 bg-gray-500 text-white')
        
        # Dynamic containers
        scanner_container = ui.column().classes('w-full mb-4')
        search_container = ui.column().classes('w-full mb-4')
        product_container = ui.column().classes('w-full mb-4')
        new_product_container = ui.column().classes('w-full')
        
        # Function to refresh all sections
        def refresh_sections():
            render_scanner_section(scanner_container, state)
            render_manual_search(search_container, state, lambda p: refresh_product_view())
            render_product_view(product_container, state)
            render_new_product_section(new_product_container, state)
        
        def refresh_product_view():
            render_product_view(product_container, state)
            render_new_product_section(new_product_container, state)
        
        # Initial render
        refresh_sections()


def toggle_scanner(state: MobileInventoryState, scanner_btn: Any):
    """Toggle scanner state."""
    state.scanner_active = not state.scanner_active
    
    if state.scanner_active:
        scanner_btn.text = '📷 Stop Scanner'
        scanner_btn.classes('flex-1 bg-orange-500 text-white')
        ui.notify('Scanner activated', type='positive', position='top')
    else:
        scanner_btn.text = '📷 Start Scanner'
        scanner_btn.classes('flex-1 bg-primary text-white')
        ui.notify('Scanner deactivated', type='info', position='top')


def clear_state(state: MobileInventoryState):
    """Clear mobile inventory state."""
    state.barcode = ""
    state.product = None
    state.scanner_active = False
    state.last_scanned = ""
    
    ui.notify('Cleared', type='info', position='top')


# ==============================================================================
# ADVANCED VIEW WITH TABS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced view with tabs."""
    state = get_state()
    target = container or ui.column()
    
    with target:
        ui.label('📦 Mobile Inventory Enterprise').classes('text-3xl font-bold mb-4')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_scan = ui.tab('📷 Scan', icon='qr_code_scanner')
            tab_search = ui.tab('🔍 Search', icon='search')
            tab_register = ui.tab('➕ Register', icon='add')
        
        with ui.tab_panels(tabs, value=tab_scan).classes('w-full'):
            with ui.tab_panel(tab_scan):
                render_scanner_section(ui.column(), state)
            
            with ui.tab_panel(tab_search):
                search_container = ui.column().classes('w-full')
                product_container = ui.column().classes('w-full')
                
                render_manual_search(
                    search_container,
                    state,
                    lambda p: render_product_view(product_container, state)
                )
                render_product_view(product_container, state)
            
            with ui.tab_panel(tab_register):
                render_new_product_section(ui.column(), state)


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
