# ==============================================================================
# erp_pages/2_Inventory.py
# ERP ENTERPRISE INVENTORY ENTRY
# NICE GUI VERSION
# ==============================================================================

from typing import Optional, Any
from nicegui import ui

from erp_pages.inventory.page import run
from auth import is_authenticated, get_current_user


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main(container: Optional[Any] = None):
    """Inventory module entry point.
    
    Args:
        container: NiceGUI container to render in (optional)
    """
    # Check authentication
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('lock').classes('text-orange-500')
                ui.label('Please login first to access Inventory').classes('text-orange-700')
        return
    
    # Render inventory
    run(container)


# ==============================================================================
# ALTERNATIVE ENTRY POINTS
# ==============================================================================

def run_inventory(container: Optional[Any] = None):
    """Alias for main entry point."""
    main(container)


def run_with_header(container: Optional[Any] = None):
    """Run inventory with header bar."""
    target = container or ui.column()
    
    with target:
        # Header
        with ui.card().classes('w-full p-4 bg-primary text-white mb-4'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('📦 Inventory Management').classes('text-2xl font-bold')
                
                user = get_current_user()
                if user:
                    ui.label(f"User: {user.get('full_name', 'Unknown')}").classes('text-sm')
        
        # Inventory content
        run(target)


def run_with_tabs(container: Optional[Any] = None):
    """Run inventory with tabbed interface."""
    target = container or ui.column()
    
    with target:
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_stock = ui.tab('📦 Stock', icon='inventory')
            tab_movements = ui.tab('🔄 Movements', icon='swap_horiz')
            tab_adjustments = ui.tab('⚙️ Adjustments', icon='tune')
        
        with ui.tab_panels(tabs, value=tab_stock).classes('w-full'):
            with ui.tab_panel(tab_stock):
                run(target)
            
            with ui.tab_panel(tab_movements):
                ui.label('Stock movements will appear here').classes('text-gray-500')
            
            with ui.tab_panel(tab_adjustments):
                ui.label('Stock adjustments will appear here').classes('text-gray-500')


def run_standalone():
    """Run inventory as standalone page."""
    ui.label('📦 Inventory Management').classes('text-3xl font-bold mb-4')
    main()


# ==============================================================================
# ENTRY POINT FOR DYNAMIC ROUTER
# ==============================================================================

if __name__ == "__main__":
    main()
