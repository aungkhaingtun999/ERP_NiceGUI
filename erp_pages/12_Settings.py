# ==============================================================================
# erp_pages/12_Settings.py
# ERP ENTERPRISE CONTROL CENTER v5.0
# NICE GUI VERSION
#
# Settings Router Page
#
# UI Components:
#   Pricing
#   Accounting
#   Inventory
#   Finance
#   System Status
#
# Database Driven Architecture
#
# ==============================================================================

from typing import Dict, Any, Optional, Callable
from nicegui import ui

from erp_core.loaders.settings_loader import (
    get_all_settings_cached,
    clear_settings_cache,
)

from erp_ui.settings.pricing_settings import (
    render_pricing_settings,
)

from erp_ui.settings.accounting_settings import (
    render_accounting_settings,
)

from erp_ui.settings.inventory_settings import (
    render_inventory_settings,
)

from erp_ui.settings.finance_settings import (
    render_finance_settings,
)

from erp_ui.settings.system_status import (
    render_system_status,
)

from erp_ui.settings.settings_summary import (
    render_settings_summary,
)

from auth import (
    get_current_user,
    require_login,
)


# ==============================================================================
# SECURITY
# ==============================================================================

def require_admin() -> Optional[Dict[str, Any]]:
    """Check admin access.
    
    Returns:
        User dictionary if admin, None otherwise
    """
    user = get_current_user()
    
    if not user:
        ui.notify("⛔ Please login first", type='error', position='top')
        return None
    
    if user.get("role_id") != 1:
        ui.notify("⛔ Admin Access Required", type='error', position='top')
        return None
    
    return user


# ==============================================================================
# LOAD SETTINGS
# ==============================================================================

def load_settings() -> Dict[str, Any]:
    """Load all settings from cache."""
    try:
        return get_all_settings_cached()
    except Exception as e:
        ui.notify(f"Settings Load Failed : {e}", type='error', position='top')
        return {}


# ==============================================================================
# PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point."""
    clear_settings_cache()
    
    user = require_admin()
    
    if not user:
        return
    
    settings = load_settings()
    
    target = container or ui.column()
    
    with target:
        # Header
        ui.label("⚙ ERP Control Center").classes('text-3xl font-bold mb-2')
        
        with ui.card().classes('w-full p-4 bg-green-50 border border-green-200 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('admin_panel_settings').classes('text-green-600')
                ui.label(f"🔐 Welcome Admin : {user.get('full_name','Admin')}").classes(
                    'text-green-700 font-semibold'
                )
        
        ui.label("Enterprise Configuration Center (Database Driven)").classes(
            'text-gray-500 mb-4'
        )
        
        # Settings Summary
        with ui.expansion('⚡ Current Configuration', icon='dashboard', value=True).classes('w-full mb-4'):
            render_settings_summary(settings, user)
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # SETTINGS COMPONENTS WITH TABS
        # ======================================================================
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_pricing = ui.tab('💰 Pricing', icon='calculate')
            tab_accounting = ui.tab('🧾 Accounting', icon='receipt_long')
            tab_inventory = ui.tab('📦 Inventory', icon='inventory')
            tab_finance = ui.tab('💱 Finance', icon='payments')
            tab_system = ui.tab('🖥 System Status', icon='monitor_heart')
        
        with ui.tab_panels(tabs, value=tab_pricing).classes('w-full'):
            # Pricing Settings
            with ui.tab_panel(tab_pricing):
                with ui.card().classes('w-full p-4'):
                    render_pricing_settings(settings, user)
            
            # Accounting Settings
            with ui.tab_panel(tab_accounting):
                with ui.card().classes('w-full p-4'):
                    render_accounting_settings(settings, user)
            
            # Inventory Settings
            with ui.tab_panel(tab_inventory):
                with ui.card().classes('w-full p-4'):
                    render_inventory_settings(settings, user)
            
            # Finance Settings
            with ui.tab_panel(tab_finance):
                with ui.card().classes('w-full p-4'):
                    render_finance_settings(settings, user)
            
            # System Status
            with ui.tab_panel(tab_system):
                with ui.card().classes('w-full p-4'):
                    render_system_status()


# ==============================================================================
# ADVANCED SETTINGS VIEW (WITH SIDEBAR NAVIGATION)
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced settings view with sidebar navigation."""
    clear_settings_cache()
    
    user = require_admin()
    
    if not user:
        return
    
    settings = load_settings()
    
    target = container or ui.column()
    
    with target:
        ui.label("⚙ ERP Control Center").classes('text-3xl font-bold mb-4')
        
        # Create layout with left sidebar navigation
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Left navigation
            with ui.column().classes('w-64'):
                with ui.card().classes('w-full p-2'):
                    ui.label('Navigation').classes('font-bold mb-2')
                    
                    nav_buttons = {}
                    nav_items = [
                        ('summary', '⚡ Summary', 'dashboard'),
                        ('pricing', '💰 Pricing', 'calculate'),
                        ('accounting', '🧾 Accounting', 'receipt_long'),
                        ('inventory', '📦 Inventory', 'inventory'),
                        ('finance', '💱 Finance', 'payments'),
                        ('system', '🖥 System', 'monitor_heart'),
                    ]
                    
                    for key, label, icon in nav_items:
                        nav_buttons[key] = ui.button(
                            label,
                            icon=icon,
                            on_click=lambda k=key: switch_section(k)
                        ).props('flat align-left').classes('w-full mb-1')
                    
                    # Refresh button
                    ui.separator().classes('my-2')
                    ui.button(
                        '🔄 Refresh',
                        icon='refresh',
                        on_click=lambda: refresh_settings()
                    ).props('flat').classes('w-full bg-gray-100')
            
            # Right content area
            with ui.column().classes('flex-1 min-w-[600px]'):
                content_container = ui.column().classes('w-full')
                
                # Function to switch sections
                def switch_section(section: str):
                    content_container.clear()
                    
                    with content_container:
                        if section == 'summary':
                            render_settings_summary(settings, user)
                        elif section == 'pricing':
                            render_pricing_settings(settings, user)
                        elif section == 'accounting':
                            render_accounting_settings(settings, user)
                        elif section == 'inventory':
                            render_inventory_settings(settings, user)
                        elif section == 'finance':
                            render_finance_settings(settings, user)
                        elif section == 'system':
                            render_system_status()
                
                # Function to refresh settings
                def refresh_settings():
                    clear_settings_cache()
                    new_settings = load_settings()
                    
                    ui.notify(
                        'Settings refreshed',
                        type='info',
                        position='top',
                        timeout=2000
                    )
                    
                    # Re-render current section
                    switch_section('summary')
                
                # Initial render
                switch_section('summary')


# ==============================================================================
# COMPACT SETTINGS VIEW
# ==============================================================================

def run_compact(container: Optional[Any] = None):
    """Compact settings view with collapsible sections."""
    clear_settings_cache()
    
    user = require_admin()
    
    if not user:
        return
    
    settings = load_settings()
    
    target = container or ui.column()
    
    with target:
        ui.label("⚙ ERP Control Center").classes('text-2xl font-bold mb-2')
        ui.label(f"Welcome: {user.get('full_name', 'Admin')}").classes('text-gray-500 mb-4')
        
        # All sections as collapsible expansions
        with ui.expansion('⚡ Current Configuration', icon='dashboard', value=True).classes('w-full mb-2'):
            render_settings_summary(settings, user)
        
        with ui.expansion('💰 Pricing Settings', icon='calculate').classes('w-full mb-2'):
            render_pricing_settings(settings, user)
        
        with ui.expansion('🧾 Accounting Settings', icon='receipt_long').classes('w-full mb-2'):
            render_accounting_settings(settings, user)
        
        with ui.expansion('📦 Inventory Settings', icon='inventory').classes('w-full mb-2'):
            render_inventory_settings(settings, user)
        
        with ui.expansion('💱 Finance Settings', icon='payments').classes('w-full mb-2'):
            render_finance_settings(settings, user)
        
        with ui.expansion('🖥 System Status', icon='monitor_heart').classes('w-full mb-2'):
            render_system_status()


# ==============================================================================
# SETTINGS DASHBOARD VIEW
# ==============================================================================

def run_dashboard(container: Optional[Any] = None):
    """Dashboard-style settings view with metrics."""
    clear_settings_cache()
    
    user = require_admin()
    
    if not user:
        return
    
    settings = load_settings()
    
    target = container or ui.column()
    
    with target:
        ui.label("⚙ ERP Control Center").classes('text-3xl font-bold mb-4')
        
        # Quick stats row
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            stats = [
                ('💰 Tax Rate', f"{settings.get('DEFAULT_TAX_RATE', '0')}%", 'percent'),
                ('📦 Min Stock', str(settings.get('MIN_STOCK_ALERT', '0')), 'inventory'),
                ('💱 Currency', settings.get('CURRENCY', 'MMK'), 'payments'),
                ('🏷️ Pricing', settings.get('PRICING_PRIORITY', 'OWNER_FIRST'), 'calculate'),
            ]
            
            for label, value, icon in stats:
                with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon(icon).classes('text-gray-500')
                        ui.label(label).classes('text-sm text-gray-600')
                    ui.label(value).classes('text-2xl font-bold')
        
        # Settings sections in grid
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Left column
            with ui.column().classes('flex-1 min-w-[400px]'):
                with ui.card().classes('w-full p-4 mb-4'):
                    ui.label('💰 Pricing Settings').classes('text-xl font-bold mb-2')
                    render_pricing_settings(settings, user)
                
                with ui.card().classes('w-full p-4 mb-4'):
                    ui.label('🧾 Accounting Settings').classes('text-xl font-bold mb-2')
                    render_accounting_settings(settings, user)
            
            # Right column
            with ui.column().classes('flex-1 min-w-[400px]'):
                with ui.card().classes('w-full p-4 mb-4'):
                    ui.label('📦 Inventory Settings').classes('text-xl font-bold mb-2')
                    render_inventory_settings(settings, user)
                
                with ui.card().classes('w-full p-4 mb-4'):
                    ui.label('💱 Finance Settings').classes('text-xl font-bold mb-2')
                    render_finance_settings(settings, user)
        
        # System status full width
        with ui.card().classes('w-full p-4'):
            render_system_status()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
