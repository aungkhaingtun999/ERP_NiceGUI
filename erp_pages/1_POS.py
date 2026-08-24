# ==============================================================================
# erp_pages/1_POS.py
# ERP ENTERPRISE POS ROUTER
# NICE GUI VERSION - ENHANCED
#
# POS Module Entry Point
# Version v12.1
# ==============================================================================

from typing import Optional, Any, Callable
from nicegui import ui

from erp_pages.pos.main import run
from auth import is_authenticated, get_current_user


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main(container: Optional[Any] = None):
    """POS module entry point.
    
    Args:
        container: NiceGUI container to render in (optional)
    """
    # Check authentication
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('lock').classes('text-orange-500')
                ui.label('Please login first to access POS').classes('text-orange-700')
        return
    
    # Render POS
    run(container)


# ==============================================================================
# POS WITH HEADER
# ==============================================================================

def run_with_header(container: Optional[Any] = None):
    """Run POS with header bar."""
    target = container or ui.column()
    
    with target:
        # Header
        with ui.card().classes('w-full p-4 bg-primary text-white mb-4'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('🛒 Point of Sale').classes('text-2xl font-bold')
                
                user = get_current_user()
                if user:
                    ui.label(f"Cashier: {user.get('full_name', 'Unknown')}").classes('text-sm')
        
        # POS content
        run(target)


# ==============================================================================
# POS WITH TABS (if needed for future expansion)
# ==============================================================================

def run_with_tabs(container: Optional[Any] = None):
    """Run POS with tabbed interface for future expansion."""
    target = container or ui.column()
    
    with target:
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_pos = ui.tab('🛒 POS', icon='point_of_sale')
            tab_hold = ui.tab('⏸ Hold', icon='pause')
            tab_history = ui.tab('📜 History', icon='history')
        
        with ui.tab_panels(tabs, value=tab_pos).classes('w-full'):
            with ui.tab_panel(tab_pos):
                run(target)
            
            with ui.tab_panel(tab_hold):
                ui.label('Held transactions will appear here').classes('text-gray-500')
            
            with ui.tab_panel(tab_history):
                ui.label('Transaction history will appear here').classes('text-gray-500')


# ==============================================================================
# FULLSCREEN POS MODE
# ==============================================================================

def run_fullscreen(container: Optional[Any] = None):
    """Run POS in fullscreen mode (no sidebar)."""
    target = container or ui.column()
    
    with target:
        with ui.row().classes('w-full h-screen'):
            # Main POS area
            with ui.column().classes('flex-1 p-4'):
                run(target)
            
            # Optional: Quick action sidebar
            with ui.column().classes('w-64 p-4 bg-gray-50'):
                ui.label('Quick Actions').classes('font-bold mb-2')
                
                ui.button('🔍 Search', icon='search').props('flat').classes('w-full mb-1')
                ui.button('📦 Products', icon='inventory').props('flat').classes('w-full mb-1')
                ui.button('💰 Payment', icon='payment').props('flat').classes('w-full mb-1')
                ui.button('📄 Receipt', icon='receipt').props('flat').classes('w-full mb-1')


# ==============================================================================
# ENTRY POINT FOR DYNAMIC ROUTER
# ==============================================================================

if __name__ == "__main__":
    main()
