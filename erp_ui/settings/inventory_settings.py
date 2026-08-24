# ==============================================================================
# erp_ui/settings/inventory_settings.py
# ERP INVENTORY SETTINGS COMPONENT v2.0
# NICE GUI VERSION
#
# Approval Workflow:
#
# Maker
#   |
#   ↓
# settings_change_requests
#   |
#   ↓
# Checker Approval
#   |
#   ↓
# settings table update
#
# ==============================================================================

from typing import Dict, Any, Optional, Callable
from nicegui import ui

from erp_core.loaders.settings_loader import (
    get_bool,
)

from erp_core.services.settings_service import (
    SettingsService,
)

from utils.notification import (
    notify_success,
    notify_error,
)

from erp_ui.settings.common import (
    show_save_success,
    show_save_error,
    safe_float,
    safe_int,
    safe_bool,
)


# ==============================================================================
# INVENTORY SETTINGS UI
# ==============================================================================

def render_inventory_settings(
    settings: Dict[str, Any],
    user: Dict[str, Any],
    container: Optional[Any] = None,
    on_success: Optional[Callable] = None
):
    """Render inventory settings component
    
    Args:
        settings: Current settings dictionary
        user: Current user dictionary
        container: NiceGUI container to render in
        on_success: Callback after successful submission
    """
    
    target = container or ui.column()
    
    with target:
        # ----------------------------------------------------------------------
        # HEADER
        # ----------------------------------------------------------------------
        
        ui.label('📦 Inventory Rules').classes('text-2xl font-bold mb-4')
        
        # ======================================================================
        # MINIMUM STOCK ALERT
        # ======================================================================
        
        minimum_stock_value = safe_float(
            settings.get("MIN_STOCK_ALERT", 0),
            0.0
        )
        
        minimum_stock = ui.number(
            'Minimum Stock Alert',
            min=0.0,
            value=minimum_stock_value,
            step=1.0,
        ).classes('w-full mb-4').props('clearable')
        
        # ======================================================================
        # DEFAULT MINIMUM STOCK
        # ======================================================================
        
        default_min_stock_value = safe_int(
            settings.get("DEFAULT_MINIMUM_STOCK", 5),
            5
        )
        
        default_min_stock = ui.number(
            'Default Minimum Stock',
            min=0,
            value=default_min_stock_value,
            step=1,
        ).classes('w-full mb-4').props('clearable')
        
        # ======================================================================
        # DEFAULT TAX RATE
        # ======================================================================
        
        default_tax_rate_value = safe_float(
            settings.get("DEFAULT_TAX_RATE", 5.0),
            5.0
        )
        
        default_tax_rate = ui.number(
            'Default Tax Rate %',
            min=0.0,
            max=100.0,
            value=default_tax_rate_value,
            step=0.5,
        ).classes('w-full mb-4').props('clearable')
        
        # ======================================================================
        # AUTO REORDER
        # ======================================================================
        
        auto_reorder_value = safe_bool(
            get_bool(settings, "AUTO_REORDER", False),
            False
        )
        
        with ui.card().classes('w-full p-4 bg-gray-50 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('refresh').classes('text-blue-500')
                ui.label('Enable Auto Reorder').classes('font-semibold')
                
                auto_reorder = ui.switch(
                    value=auto_reorder_value
                )
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # SUBMIT CHANGE REQUEST
        # ======================================================================
        
        submit_button = ui.button(
            '📨 Submit Inventory Change Request',
            on_click=lambda: handle_submit(
                minimum_stock.value,
                default_min_stock.value,
                default_tax_rate.value,
                auto_reorder.value,
                user,
                submit_button,
                on_success
            )
        ).classes('w-full bg-primary text-white font-semibold py-2')
        
        # ======================================================================
        # CHANGE REQUEST SUMMARY
        # ======================================================================
        
        with ui.expansion('📋 View Change Summary', icon='visibility').classes('w-full mt-4'):
            display_change_summary(
                minimum_stock,
                default_min_stock,
                default_tax_rate,
                auto_reorder
            )


def handle_submit(
    minimum_stock: float,
    default_min_stock: int,
    default_tax_rate: float,
    auto_reorder: bool,
    user: Dict[str, Any],
    submit_button: Any = None,
    on_success: Optional[Callable] = None
):
    """Handle submit change request
    
    Args:
        minimum_stock: Minimum stock alert value
        default_min_stock: Default minimum stock value
        default_tax_rate: Default tax rate value
        auto_reorder: Auto reorder setting
        user: Current user dictionary
        submit_button: Submit button instance
        on_success: Callback after successful submission
    """
    
    try:
        # Disable button during submission
        if submit_button:
            submit_button.disable()
            submit_button.text = '⏳ Submitting...'
        
        # ======================================================================
        # VALIDATION
        # ======================================================================
        
        validation_errors = []
        
        if minimum_stock < 0:
            validation_errors.append("Minimum Stock Alert cannot be negative.")
        
        if default_min_stock < 0:
            validation_errors.append("Default Minimum Stock cannot be negative.")
        
        if default_tax_rate < 0 or default_tax_rate > 100:
            validation_errors.append("Default Tax Rate must be between 0 and 100.")
        
        if validation_errors:
            for error in validation_errors:
                ui.notify(error, type='error', position='top')
            
            if submit_button:
                submit_button.enable()
                submit_button.text = '📨 Submit Inventory Change Request'
            
            return
        
        # ======================================================================
        # MIN STOCK REQUEST
        # ======================================================================
        
        SettingsService.request_change(
            "MIN_STOCK_ALERT",
            str(minimum_stock),
            "Change minimum stock alert level",
            user["id"]
        )
        
        # ======================================================================
        # DEFAULT MIN STOCK REQUEST
        # ======================================================================
        
        SettingsService.request_change(
            "DEFAULT_MINIMUM_STOCK",
            str(default_min_stock),
            "Change default minimum stock",
            user["id"]
        )
        
        # ======================================================================
        # DEFAULT TAX RATE REQUEST
        # ======================================================================
        
        SettingsService.request_change(
            "DEFAULT_TAX_RATE",
            str(default_tax_rate),
            "Change default tax rate",
            user["id"]
        )
        
        # ======================================================================
        # AUTO REORDER REQUEST
        # ======================================================================
        
        SettingsService.request_change(
            "AUTO_REORDER",
            auto_reorder,
            "Change auto reorder setting",
            user["id"]
        )
        
        # ======================================================================
        # SUCCESS
        # ======================================================================
        
        success_message = "📦 Inventory change request submitted for approval"
        
        show_save_success(success_message)
        
        # Show success dialog
        show_success_dialog(success_message)
        
        # Call callback if provided
        if on_success:
            on_success()
        
    except Exception as e:
        error_message = f"Inventory Request Failed : {e}"
        show_save_error(error_message)
        
        # Show error dialog
        show_error_dialog(error_message)
    
    finally:
        # Re-enable button
        if submit_button:
            submit_button.enable()
            submit_button.text = '📨 Submit Inventory Change Request'


def display_change_summary(
    minimum_stock: Any,
    default_min_stock: Any,
    default_tax_rate: Any,
    auto_reorder: Any
):
    """Display change summary in expansion panel
    
    Args:
        minimum_stock: Minimum stock input
        default_min_stock: Default minimum stock input
        default_tax_rate: Default tax rate input
        auto_reorder: Auto reorder switch
    """
    with ui.column().classes('w-full gap-2 p-2'):
        with ui.row().classes('w-full justify-between'):
            ui.label('Minimum Stock Alert:').classes('font-semibold')
            ui.label(str(minimum_stock.value))
        
        ui.separator().classes('my-1')
        
        with ui.row().classes('w-full justify-between'):
            ui.label('Default Minimum Stock:').classes('font-semibold')
            ui.label(str(default_min_stock.value))
        
        ui.separator().classes('my-1')
        
        with ui.row().classes('w-full justify-between'):
            ui.label('Default Tax Rate:').classes('font-semibold')
            ui.label(f"{default_tax_rate.value}%")
        
        ui.separator().classes('my-1')
        
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Auto Reorder:').classes('font-semibold')
            
            if auto_reorder.value:
                ui.badge('Enabled').classes('bg-green-100 text-green-700')
            else:
                ui.badge('Disabled').classes('bg-gray-100 text-gray-700')


def show_success_dialog(message: str):
    """Show success dialog
    
    Args:
        message: Success message
    """
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[300px]'):
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon('check_circle').classes('text-green-500 text-2xl')
            ui.label('Success').classes('text-xl font-bold')
        
        ui.label(message).classes('mb-4')
        
        ui.button(
            'OK',
            on_click=dialog.close
        ).classes('w-full bg-green-500 text-white')
    
    dialog.open()


def show_error_dialog(message: str):
    """Show error dialog
    
    Args:
        message: Error message
    """
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[300px]'):
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon('error').classes('text-red-500 text-2xl')
            ui.label('Error').classes('text-xl font-bold')
        
        ui.label(message).classes('mb-4')
        
        ui.button(
            'OK',
            on_click=dialog.close
        ).classes('w-full bg-red-500 text-white')
    
    dialog.open()


# ==============================================================================
# ADVANCED INVENTORY SETTINGS WITH LIVE PREVIEW
# ==============================================================================

def render_inventory_settings_advanced(
    settings: Dict[str, Any],
    user: Dict[str, Any],
    container: Optional[Any] = None
):
    """Render advanced inventory settings with live preview
    
    Args:
        settings: Current settings dictionary
        user: Current user dictionary
        container: NiceGUI container to render in
    """
    
    target = container or ui.column()
    
    with target:
        with ui.row().classes('w-full gap-4'):
            # Left column - Settings form
            with ui.column().classes('flex-1'):
                render_inventory_settings(settings, user)
            
            # Right column - Live preview
            with ui.column().classes('flex-1'):
                with ui.card().classes('w-full p-4 bg-gray-50'):
                    ui.label('📊 Live Preview').classes('text-xl font-bold mb-4')
                    
                    preview_container = ui.column()
                    
                    update_preview(
                        preview_container,
                        settings,
                        safe_float(settings.get("MIN_STOCK_ALERT", 0)),
                        safe_int(settings.get("DEFAULT_MINIMUM_STOCK", 5)),
                        safe_float(settings.get("DEFAULT_TAX_RATE", 5.0)),
                        safe_bool(get_bool(settings, "AUTO_REORDER", False))
                    )


def update_preview(
    container: Any,
    settings: Dict[str, Any],
    min_stock_alert: float,
    default_min_stock: int,
    default_tax_rate: float,
    auto_reorder: bool
):
    """Update preview display
    
    Args:
        container: Container to update
        settings: Current settings
        min_stock_alert: Minimum stock alert value
        default_min_stock: Default minimum stock
        default_tax_rate: Default tax rate
        auto_reorder: Auto reorder setting
    """
    container.clear()
    
    with container:
        with ui.row().classes('w-full gap-2 flex-wrap'):
            with ui.card().classes('p-3 flex-1 min-w-[150px]'):
                ui.label('Min Stock Alert').classes('text-sm text-gray-600')
                ui.label(str(min_stock_alert)).classes('text-xl font-bold')
            
            with ui.card().classes('p-3 flex-1 min-w-[150px]'):
                ui.label('Default Min Stock').classes('text-sm text-gray-600')
                ui.label(str(default_min_stock)).classes('text-xl font-bold')
            
            with ui.card().classes('p-3 flex-1 min-w-[150px]'):
                ui.label('Tax Rate').classes('text-sm text-gray-600')
                ui.label(f"{default_tax_rate}%").classes('text-xl font-bold')
        
        with ui.card().classes('p-3 w-full'):
            ui.label('Auto Reorder').classes('text-sm text-gray-600')
            
            if auto_reorder:
                ui.badge('🔄 Enabled').classes('bg-green-100 text-green-700')
            else:
                ui.badge('⏸ Disabled').classes('bg-gray-100 text-gray-700')


# ==============================================================================
# SETTINGS CARD COMPONENT
# ==============================================================================

def create_settings_card(
    title: str,
    icon: str,
    content: Callable
):
    """Create settings card with title and content
    
    Args:
        title: Card title
        icon: Card icon
        content: Function to render card content
    """
    with ui.card().classes('w-full p-4 mb-4'):
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon(icon).classes('text-2xl text-primary')
            ui.label(title).classes('text-xl font-bold')
        
        ui.separator().classes('mb-2')
        
        content()


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    "render_inventory_settings",
    "render_inventory_settings_advanced",
    "handle_submit",
    "display_change_summary",
    "show_success_dialog",
    "show_error_dialog",
    "update_preview",
    "create_settings_card",
]
