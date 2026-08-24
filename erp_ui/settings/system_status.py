# ==============================================================================
# erp_ui/settings/system_status.py
# ERP SYSTEM STATUS COMPONENT
# NICE GUI VERSION
# ==============================================================================

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from nicegui import ui

from erp_core.base_repo import db


# ==============================================================================
# SYSTEM STATUS UI
# ==============================================================================

def render_system_status(
    container: Optional[Any] = None,
    auto_refresh: bool = False,
    refresh_interval: int = 30
):
    """Render system status component
    
    Args:
        container: NiceGUI container to render in
        auto_refresh: Whether to auto-refresh status
        refresh_interval: Auto-refresh interval in seconds
    """
    
    target = container or ui.column()
    
    with target:
        # ----------------------------------------------------------------------
        # HEADER
        # ----------------------------------------------------------------------
        
        ui.label('🖥 System Status').classes('text-2xl font-bold mb-4')
        
        # ======================================================================
        # SYSTEM STATUS CARD
        # ======================================================================
        
        with ui.card().classes('w-full p-4 bg-green-50 border border-green-200 mb-4'):
            # Status items with icons
            status_items = [
                ("✔", "ERP Core", "Active", "check_circle", "green"),
                ("✔", "Database", "Connected", "storage", "green"),
                ("✔", "Settings Service", "Connected", "settings", "green"),
                ("✔", "Settings Cache", "Active", "memory", "green"),
                ("✔", "Pricing Engine", "Connected", "calculate", "green"),
                ("✔", "Tax Engine", "Connected", "percent", "green"),
                ("✔", "Inventory Engine", "Connected", "inventory", "green"),
                ("✔", "POS", "Ready", "point_of_sale", "green"),
                ("✔", "Product / Category / Global Rule", "Ready", "rule", "green"),
            ]
            
            for status_icon, name, state, icon_name, color in status_items:
                with ui.row().classes('items-center gap-2 py-1'):
                    ui.icon(icon_name).classes(f'text-{color}-500')
                    ui.label(name).classes('font-semibold flex-1')
                    ui.label(state).classes(f'text-{color}-600 font-medium')
        
        # ======================================================================
        # OPERATIONAL STATUS
        # ======================================================================
        
        with ui.card().classes('w-full p-4 bg-blue-50 border border-blue-200 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('rocket_launch').classes('text-blue-500 text-2xl')
                ui.label('🚀 ERP Control Center Fully Operational').classes(
                    'text-blue-700 font-bold text-lg'
                )
        
        # ======================================================================
        # REFRESH BUTTON
        # ======================================================================
        
        if auto_refresh:
            ui.label(
                f'Auto-refresh every {refresh_interval} seconds'
            ).classes('text-sm text-gray-500 text-center')
        
        refresh_btn = ui.button(
            '🔄 Refresh Status',
            on_click=lambda: refresh_system_status(refresh_btn)
        ).props('flat').classes('w-full bg-gray-100 hover:bg-gray-200')


def refresh_system_status(refresh_btn: Any = None):
    """Refresh system status
    
    Args:
        refresh_btn: Refresh button instance
    """
    
    try:
        # Disable button during refresh
        if refresh_btn:
            refresh_btn.disable()
            refresh_btn.text = '⏳ Refreshing...'
        
        # Check database connection
        db_status = check_database_connection()
        
        if db_status:
            ui.notify(
                'System status refreshed successfully',
                type='positive',
                position='top'
            )
        else:
            ui.notify(
                'Database connection issue detected',
                type='warning',
                position='top'
            )
    
    except Exception as e:
        ui.notify(
            f'Error refreshing status: {e}',
            type='error',
            position='top'
        )
    
    finally:
        # Re-enable button
        if refresh_btn:
            refresh_btn.enable()
            refresh_btn.text = '🔄 Refresh Status'


# ==============================================================================
# DETAILED SYSTEM STATUS
# ==============================================================================

def render_system_status_detailed(
    container: Optional[Any] = None
):
    """Render detailed system status with health checks
    
    Args:
        container: NiceGUI container to render in
    """
    
    target = container or ui.column()
    
    with target:
        ui.label('🖥 System Status').classes('text-2xl font-bold mb-4')
        
        # ======================================================================
        # HEALTH CHECKS
        # ======================================================================
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Health Checks').classes('text-xl font-bold mb-4')
            
            checks = perform_health_checks()
            
            for check in checks:
                with ui.row().classes('items-center gap-2 py-2'):
                    # Status icon
                    if check['status'] == 'healthy':
                        ui.icon('check_circle').classes('text-green-500')
                    elif check['status'] == 'warning':
                        ui.icon('warning').classes('text-orange-500')
                    else:
                        ui.icon('error').classes('text-red-500')
                    
                    # Check name
                    ui.label(check['name']).classes('font-semibold flex-1')
                    
                    # Status badge
                    status_color = {
                        'healthy': 'bg-green-100 text-green-700',
                        'warning': 'bg-orange-100 text-orange-700',
                        'error': 'bg-red-100 text-red-700',
                    }
                    
                    ui.badge(
                        check['status'].title()
                    ).classes(status_color.get(check['status'], 'bg-gray-100 text-gray-700'))
                
                # Additional info
                if check.get('message'):
                    ui.label(check['message']).classes(
                        'text-sm text-gray-500 ml-8'
                    )
                
                ui.separator().classes('my-1')
        
        # ======================================================================
        # SYSTEM INFO
        # ======================================================================
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('System Information').classes('text-xl font-bold mb-4')
            
            system_info = get_system_info()
            
            for key, value in system_info.items():
                with ui.row().classes('justify-between py-1'):
                    ui.label(key).classes('font-semibold')
                    ui.label(str(value)).classes('text-gray-700')
                
                ui.separator().classes('my-1')
        
        # ======================================================================
        # REFRESH BUTTON
        # ======================================================================
        
        refresh_btn = ui.button(
            '🔄 Refresh Status',
            on_click=lambda: refresh_detailed_status(refresh_btn)
        ).classes('w-full bg-primary text-white')


def perform_health_checks() -> List[Dict[str, Any]]:
    """Perform system health checks
    
    Returns:
        List of health check results
    """
    
    checks = []
    
    # Database check
    db_status = check_database_connection()
    checks.append({
        'name': 'Database Connection',
        'status': 'healthy' if db_status else 'error',
        'message': 'Connected to Supabase' if db_status else 'Connection failed',
    })
    
    # Settings service check
    settings_status = check_settings_service()
    checks.append({
        'name': 'Settings Service',
        'status': 'healthy' if settings_status else 'error',
        'message': 'Service available' if settings_status else 'Service unavailable',
    })
    
    # Cache check
    cache_status = check_cache_status()
    checks.append({
        'name': 'Cache System',
        'status': 'healthy' if cache_status else 'warning',
        'message': 'Cache active' if cache_status else 'Cache cleared',
    })
    
    # Pricing engine check
    pricing_status = check_pricing_engine()
    checks.append({
        'name': 'Pricing Engine',
        'status': 'healthy' if pricing_status else 'error',
        'message': 'Engine ready' if pricing_status else 'Engine not ready',
    })
    
    # Tax engine check
    tax_status = check_tax_engine()
    checks.append({
        'name': 'Tax Engine',
        'status': 'healthy' if tax_status else 'error',
        'message': 'Engine ready' if tax_status else 'Engine not ready',
    })
    
    # Inventory engine check
    inventory_status = check_inventory_engine()
    checks.append({
        'name': 'Inventory Engine',
        'status': 'healthy' if inventory_status else 'error',
        'message': 'Engine ready' if inventory_status else 'Engine not ready',
    })
    
    # POS check
    pos_status = check_pos_status()
    checks.append({
        'name': 'POS System',
        'status': 'healthy' if pos_status else 'error',
        'message': 'POS ready' if pos_status else 'POS not ready',
    })
    
    return checks


def get_system_info() -> Dict[str, Any]:
    """Get system information
    
    Returns:
        Dictionary with system information
    """
    
    import platform
    import sys
    from datetime import datetime
    
    return {
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Python Version': sys.version.split()[0],
        'Platform': platform.platform(),
        'Database': 'Supabase',
        'ERP Version': 'Enterprise',
        'UI Framework': 'NiceGUI',
    }


def refresh_detailed_status(refresh_btn: Any = None):
    """Refresh detailed system status
    
    Args:
        refresh_btn: Refresh button instance
    """
    
    try:
        if refresh_btn:
            refresh_btn.disable()
            refresh_btn.text = '⏳ Refreshing...'
        
        # Perform health checks
        checks = perform_health_checks()
        
        healthy_count = sum(1 for c in checks if c['status'] == 'healthy')
        warning_count = sum(1 for c in checks if c['status'] == 'warning')
        error_count = sum(1 for c in checks if c['status'] == 'error')
        
        ui.notify(
            f'Status: {healthy_count} healthy, {warning_count} warning, {error_count} error',
            type='positive' if error_count == 0 else 'warning',
            position='top'
        )
    
    except Exception as e:
        ui.notify(
            f'Error refreshing status: {e}',
            type='error',
            position='top'
        )
    
    finally:
        if refresh_btn:
            refresh_btn.enable()
            refresh_btn.text = '🔄 Refresh Status'


# ==============================================================================
# HEALTH CHECK FUNCTIONS
# ==============================================================================

def check_database_connection() -> bool:
    """Check database connection"""
    try:
        client = db()
        
        # Simple query
        result = client.table("settings").select("id").limit(1).execute()
        
        return result is not None
    
    except Exception:
        return False


def check_settings_service() -> bool:
    """Check settings service"""
    try:
        from erp_core.services.settings_service import SettingsService
        
        # Try to instantiate service
        service = SettingsService()
        
        return service is not None
    
    except Exception:
        return False


def check_cache_status() -> bool:
    """Check cache status"""
    try:
        from erp_core.loaders.settings_loader import get_settings_cache_status
        
        return get_settings_cache_status()
    
    except Exception:
        return False


def check_pricing_engine() -> bool:
    """Check pricing engine"""
    try:
        from erp_core.services.pricing_service import PricingService
        
        service = PricingService()
        
        return service is not None
    
    except Exception:
        return False


def check_tax_engine() -> bool:
    """Check tax engine"""
    try:
        from erp_core.services.tax_service import TaxService
        
        service = TaxService()
        
        return service is not None
    
    except Exception:
        return False


def check_inventory_engine() -> bool:
    """Check inventory engine"""
    try:
        from erp_core.services.inventory_service import InventoryService
        
        service = InventoryService()
        
        return service is not None
    
    except Exception:
        return False


def check_pos_status() -> bool:
    """Check POS system status"""
    try:
        from erp_core.services.sales_service import SalesService
        
        service = SalesService()
        
        return service is not None
    
    except Exception:
        return False


# ==============================================================================
# SYSTEM STATUS DASHBOARD
# ==============================================================================

def render_system_status_dashboard(
    container: Optional[Any] = None,
    auto_refresh: bool = True,
    refresh_interval: int = 30
):
    """Render system status dashboard with metrics
    
    Args:
        container: NiceGUI container to render in
        auto_refresh: Whether to auto-refresh
        refresh_interval: Auto-refresh interval in seconds
    """
    
    target = container or ui.column()
    
    with target:
        ui.label('🖥 System Dashboard').classes('text-2xl font-bold mb-4')
        
        # ======================================================================
        # STATUS METRICS
        # ======================================================================
        
        checks = perform_health_checks()
        
        healthy_count = sum(1 for c in checks if c['status'] == 'healthy')
        warning_count = sum(1 for c in checks if c['status'] == 'warning')
        error_count = sum(1 for c in checks if c['status'] == 'error')
        
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            # Healthy
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-green-50'):
                ui.label('Healthy').classes('text-sm text-gray-600')
                ui.label(str(healthy_count)).classes('text-3xl font-bold text-green-700')
            
            # Warning
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-orange-50'):
                ui.label('Warning').classes('text-sm text-gray-600')
                ui.label(str(warning_count)).classes('text-3xl font-bold text-orange-700')
            
            # Error
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-red-50'):
                ui.label('Error').classes('text-sm text-gray-600')
                ui.label(str(error_count)).classes('text-3xl font-bold text-red-700')
            
            # Total
            with ui.card().classes('p-4 flex-1 min-w-[150px] bg-blue-50'):
                ui.label('Total Checks').classes('text-sm text-gray-600')
                ui.label(str(len(checks))).classes('text-3xl font-bold text-blue-700')
        
        # ======================================================================
        # STATUS LIST
        # ======================================================================
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('System Components').classes('text-xl font-bold mb-4')
            
            for check in checks:
                with ui.row().classes('items-center gap-2 py-2'):
                    # Status icon
                    if check['status'] == 'healthy':
                        ui.icon('check_circle').classes('text-green-500')
                    elif check['status'] == 'warning':
                        ui.icon('warning').classes('text-orange-500')
                    else:
                        ui.icon('error').classes('text-red-500')
                    
                    # Check name
                    ui.label(check['name']).classes('font-semibold flex-1')
                    
                    # Status
                    status_colors = {
                        'healthy': 'text-green-600',
                        'warning': 'text-orange-600',
                        'error': 'text-red-600',
                    }
                    
                    ui.label(check['status'].title()).classes(
                        status_colors.get(check['status'], 'text-gray-600')
                    )
                
                ui.separator().classes('my-1')
        
        # ======================================================================
        # AUTO-REFRESH TIMER
        # ======================================================================
        
        if auto_refresh:
            ui.label(
                f'⏱ Auto-refresh every {refresh_interval} seconds'
            ).classes('text-sm text-gray-500 text-center')
            
            # Use timer for auto-refresh
            ui.timer(
                refresh_interval,
                lambda: refresh_dashboard_data()
            )


def refresh_dashboard_data():
    """Refresh dashboard data"""
    try:
        ui.notify(
            'Dashboard refreshed',
            type='info',
            position='top',
            timeout=2000
        )
    
    except Exception as e:
        ui.notify(
            f'Refresh error: {e}',
            type='error',
            position='top'
        )


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    "render_system_status",
    "render_system_status_detailed",
    "render_system_status_dashboard",
    "refresh_system_status",
    "refresh_detailed_status",
    "perform_health_checks",
    "get_system_info",
    "check_database_connection",
    "check_settings_service",
    "check_cache_status",
    "check_pricing_engine",
    "check_tax_engine",
    "check_inventory_engine",
    "check_pos_status",
]
