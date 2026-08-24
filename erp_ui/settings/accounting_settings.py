# ==============================================================================
# erp_ui/settings/accounting_settings.py
# ERP ACCOUNTING & TAX SETTINGS COMPONENT v3.0
# NICE GUI VERSION
#
# Maker - Checker Approval Workflow
# Request → Approval → Apply
#
# Features
# - Tax Rate Request
# - Discount Policy Request
# - Duplicate Pending Notification
# - No Change Notification
# - Success Notification
# ==============================================================================

from typing import Dict, Any, Optional, Callable, List, Tuple
from nicegui import ui

from erp_core.services.settings_service import SettingsService
from utils.notification import notify_success, notify_error
from erp_ui.settings.common import (
    show_save_success,
    show_save_error,
    safe_float,
)


# ==============================================================================
# ACCOUNTING SETTINGS UI
# ==============================================================================

def render_accounting_settings(
    settings: Dict[str, Any],
    user: Dict[str, Any],
    container: Optional[Any] = None,
    on_success: Optional[Callable] = None
):
    """Render accounting settings component
    
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
        
        ui.label('🧾 Accounting & Tax').classes('text-2xl font-bold mb-4')
        
        # ======================================================================
        # CURRENT TAX RATE
        # ======================================================================
        
        tax_value = safe_float(
            settings.get("DEFAULT_TAX_RATE", 0),
            0.0
        )
        
        # Display current tax rate
        with ui.card().classes('w-full p-4 bg-blue-50 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('info').classes('text-blue-500')
                ui.label('Current Tax Rate:').classes('font-semibold')
                ui.label(f'{tax_value:.2f}%').classes('text-xl font-bold text-blue-700')
        
        # Tax rate input
        tax_rate = ui.number(
            'Change Tax Rate (%)',
            min=0.0,
            max=100.0,
            value=tax_value,
            step=0.1,
        ).classes('w-full mb-4').props('clearable')
        
        # Add tax rate quick select buttons
        with ui.row().classes('w-full gap-2 mb-4'):
            ui.label('Quick Set:').classes('text-sm text-gray-600')
            
            common_rates = [0, 5, 7, 10, 15, 20]
            
            for rate in common_rates:
                ui.button(
                    f'{rate}%',
                    on_click=lambda r=rate: setattr(tax_rate, 'value', float(r))
                ).props('flat dense').classes('bg-gray-100 hover:bg-gray-200')
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # DISCOUNT POLICY
        # ======================================================================
        
        current_discount = settings.get("DISCOUNT_POLICY", "allowed")
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Discount Policy').classes('font-semibold mb-2')
            
            discount_policy = ui.select(
                ['allowed', 'restricted'],
                value=current_discount if current_discount in ['allowed', 'restricted'] else 'allowed',
                label='Select Policy',
            ).classes('w-full')
            
            # Show policy description
            policy_container = ui.column().classes('w-full mt-2')
            update_policy_description(policy_container, current_discount)
            
            # Update description on change
            discount_policy.on_value_change(
                lambda e: update_policy_description(policy_container, e.value)
            )
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # CHANGE SUMMARY
        # ======================================================================
        
        with ui.expansion('📋 Change Summary', icon='visibility').classes('w-full mb-4'):
            summary_container = ui.column().classes('w-full p-2')
            update_summary(summary_container, tax_rate.value, discount_policy.value)
            
            # Update summary on change
            tax_rate.on_value_change(
                lambda e: update_summary(summary_container, e.value, discount_policy.value)
            )
            discount_policy.on_value_change(
                lambda e: update_summary(summary_container, tax_rate.value, e.value)
            )
        
        # ======================================================================
        # SUBMIT REQUEST
        # ======================================================================
        
        submit_button = ui.button(
            '📤 Submit Accounting Change Request',
            on_click=lambda: handle_submit(
                tax_rate.value,
                discount_policy.value,
                user,
                submit_button,
                on_success
            )
        ).classes('w-full bg-primary text-white font-semibold py-2')


def update_policy_description(container: Any, policy: str):
    """Update discount policy description
    
    Args:
        container: Container to update
        policy: Selected policy
    """
    container.clear()
    
    with container:
        if policy == 'allowed':
            ui.label('✅ Discounts are allowed on all transactions').classes('text-green-600')
            ui.label('Staff can apply discounts without approval').classes('text-sm text-gray-500')
        elif policy == 'restricted':
            ui.label('⚠️ Discounts are restricted').classes('text-orange-600')
            ui.label('Staff need manager approval for discounts').classes('text-sm text-gray-500')


def update_summary(container: Any, tax_rate: float, discount_policy: str):
    """Update change summary display
    
    Args:
        container: Container to update
        tax_rate: New tax rate
        discount_policy: New discount policy
    """
    container.clear()
    
    with container:
        with ui.row().classes('w-full justify-between items-center py-1'):
            ui.label('Tax Rate:').classes('font-semibold')
            ui.label(f'{tax_rate:.2f}%').classes('text-lg')
        
        ui.separator().classes('my-1')
        
        with ui.row().classes('w-full justify-between items-center py-1'):
            ui.label('Discount Policy:').classes('font-semibold')
            
            if discount_policy == 'allowed':
                ui.badge('Allowed').classes('bg-green-100 text-green-700')
            else:
                ui.badge('Restricted').classes('bg-orange-100 text-orange-700')


def handle_submit(
    tax_rate: float,
    discount_policy: str,
    user: Dict[str, Any],
    submit_button: Any = None,
    on_success: Optional[Callable] = None
):
    """Handle submit accounting change request
    
    Args:
        tax_rate: New tax rate
        discount_policy: New discount policy
        user: Current user dictionary
        submit_button: Submit button instance
        on_success: Callback after successful submission
    """
    
    try:
        # Disable button during submission
        if submit_button:
            submit_button.disable()
            submit_button.text = '⏳ Submitting...'
        
        messages = []
        errors = []
        
        # ======================================================================
        # TAX RATE REQUEST
        # ======================================================================
        
        tax_result = SettingsService.request_change(
            "DEFAULT_TAX_RATE",
            str(tax_rate),
            "Accounting Tax Rate Change",
            user["id"]
        )
        
        if tax_result.get("success"):
            messages.append("✅ Tax Rate request created")
        else:
            errors.append(tax_result.get("message", "Tax request failed"))
        
        # ======================================================================
        # DISCOUNT POLICY REQUEST
        # ======================================================================
        
        discount_result = SettingsService.request_change(
            "DISCOUNT_POLICY",
            discount_policy,
            "Discount Policy Change",
            user["id"]
        )
        
        if discount_result.get("success"):
            messages.append("✅ Discount Policy request created")
        else:
            errors.append(discount_result.get("message", "Discount request failed"))
        
        # ======================================================================
        # NOTIFICATIONS
        # ======================================================================
        
        if messages:
            # Show success notification
            show_save_success("⏳ Approval request submitted successfully")
            
            # Show success dialog with details
            show_result_dialog(
                success=True,
                title="Request Submitted",
                messages=messages,
                errors=errors
            )
            
            # Call callback if provided
            if on_success:
                on_success()
        
        if errors and not messages:
            # Show error notifications
            for err in errors:
                show_save_error(err)
            
            # Show error dialog
            show_result_dialog(
                success=False,
                title="Request Failed",
                messages=messages,
                errors=errors
            )
        
        elif errors:
            # Show mixed result dialog
            show_result_dialog(
                success=True,
                title="Partial Success",
                messages=messages,
                errors=errors
            )
    
    except Exception as e:
        error_message = f"Accounting Request Failed : {e}"
        show_save_error(error_message)
        
        # Show error dialog
        show_result_dialog(
            success=False,
            title="Error",
            messages=[],
            errors=[error_message]
        )
    
    finally:
        # Re-enable button
        if submit_button:
            submit_button.enable()
            submit_button.text = '📤 Submit Accounting Change Request'


def show_result_dialog(
    success: bool,
    title: str,
    messages: List[str] = None,
    errors: List[str] = None
):
    """Show result dialog with messages and errors
    
    Args:
        success: Whether operation was successful
        title: Dialog title
        messages: Success messages
        errors: Error messages
    """
    messages = messages or []
    errors = errors or []
    
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
        # Header
        with ui.row().classes('items-center gap-2 mb-4'):
            if success:
                ui.icon('check_circle').classes('text-green-500 text-2xl')
            else:
                ui.icon('error').classes('text-red-500 text-2xl')
            
            ui.label(title).classes('text-xl font-bold')
        
        # Success messages
        if messages:
            ui.label('Success:').classes('font-semibold mb-2')
            
            for msg in messages:
                with ui.row().classes('items-center gap-2 ml-4 mb-1'):
                    ui.icon('check').classes('text-green-500')
                    ui.label(msg)
        
        # Error messages
        if errors:
            if messages:
                ui.separator().classes('my-2')
            
            ui.label('Errors:').classes('font-semibold mb-2 text-red-600')
            
            for err in errors:
                with ui.row().classes('items-center gap-2 ml-4 mb-1'):
                    ui.icon('close').classes('text-red-500')
                    ui.label(err).classes('text-red-600')
        
        # Close button
        ui.button(
            'OK',
            on_click=dialog.close
        ).classes('w-full bg-primary text-white mt-4')
    
    dialog.open()


# ==============================================================================
# ADVANCED ACCOUNTING SETTINGS
# ==============================================================================

def render_accounting_settings_advanced(
    settings: Dict[str, Any],
    user: Dict[str, Any],
    container: Optional[Any] = None
):
    """Render advanced accounting settings with tabs
    
    Args:
        settings: Current settings dictionary
        user: Current user dictionary
        container: NiceGUI container to render in
    """
    
    target = container or ui.column()
    
    with target:
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_tax = ui.tab('Tax Settings', icon='percent')
            tab_discount = ui.tab('Discount Policy', icon='local_offer')
            tab_history = ui.tab('Change History', icon='history')
        
        with ui.tab_panels(tabs, value=tab_tax).classes('w-full'):
            with ui.tab_panel(tab_tax):
                render_tax_settings(settings, user)
            
            with ui.tab_panel(tab_discount):
                render_discount_settings(settings, user)
            
            with ui.tab_panel(tab_history):
                render_change_history(settings)


def render_tax_settings(settings: Dict[str, Any], user: Dict[str, Any]):
    """Render tax settings tab"""
    
    tax_value = safe_float(settings.get("DEFAULT_TAX_RATE", 0), 0.0)
    
    with ui.card().classes('w-full p-4'):
        ui.label('Tax Rate Configuration').classes('text-xl font-bold mb-4')
        
        # Current rate
        with ui.row().classes('items-center gap-2 mb-4'):
            ui.label('Current Rate:').classes('font-semibold')
            ui.label(f'{tax_value:.2f}%').classes('text-xl font-bold text-blue-700')
        
        # New rate
        new_tax_rate = ui.number(
            'New Tax Rate (%)',
            min=0.0,
            max=100.0,
            value=tax_value,
            step=0.1,
        ).classes('w-full mb-4')
        
        # Slider for quick adjustment
        ui.label('Quick Adjust:').classes('text-sm text-gray-600 mb-2')
        tax_slider = ui.slider(
            min=0,
            max=30,
            step=0.5,
            value=tax_value if tax_value <= 30 else 30,
        ).classes('w-full mb-4')
        
        # Sync slider with number input
        tax_slider.on_value_change(
            lambda e: setattr(new_tax_rate, 'value', e.value)
        )
        new_tax_rate.on_value_change(
            lambda e: setattr(tax_slider, 'value', e.value if e.value <= 30 else 30)
        )
        
        # Submit button
        submit_btn = ui.button(
            'Submit Tax Rate Change',
            on_click=lambda: handle_tax_submit(new_tax_rate.value, user, submit_btn)
        ).classes('w-full bg-primary text-white')


def render_discount_settings(settings: Dict[str, Any], user: Dict[str, Any]):
    """Render discount policy settings tab"""
    
    current_discount = settings.get("DISCOUNT_POLICY", "allowed")
    
    with ui.card().classes('w-full p-4'):
        ui.label('Discount Policy Configuration').classes('text-xl font-bold mb-4')
        
        # Policy selection
        discount_policy = ui.select(
            ['allowed', 'restricted'],
            value=current_discount if current_discount in ['allowed', 'restricted'] else 'allowed',
            label='Discount Policy',
        ).classes('w-full mb-4')
        
        # Policy description
        description = ui.column().classes('w-full mb-4')
        update_policy_description(description, current_discount)
        discount_policy.on_value_change(
            lambda e: update_policy_description(description, e.value)
        )
        
        # Submit button
        submit_btn = ui.button(
            'Submit Policy Change',
            on_click=lambda: handle_discount_submit(
                discount_policy.value,
                user,
                submit_btn
            )
        ).classes('w-full bg-primary text-white')


def render_change_history(settings: Dict[str, Any]):
    """Render change history tab"""
    
    with ui.card().classes('w-full p-4'):
        ui.label('Recent Changes').classes('text-xl font-bold mb-4')
        
        try:
            # Fetch change history
            history = SettingsService.get_change_history(
                setting_type='accounting'
            )
            
            if history:
                # Create table
                columns = [
                    {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True},
                    {'name': 'setting', 'label': 'Setting', 'field': 'setting', 'sortable': True},
                    {'name': 'old_value', 'label': 'Old Value', 'field': 'old_value'},
                    {'name': 'new_value', 'label': 'New Value', 'field': 'new_value'},
                    {'name': 'status', 'label': 'Status', 'field': 'status'},
                ]
                
                ui.table(
                    columns=columns,
                    rows=history,
                    row_key='id',
                ).classes('w-full')
            else:
                ui.label('No changes found').classes('text-gray-500 text-center py-4')
        
        except Exception as e:
            ui.label(f'Error loading history: {e}').classes('text-red-500')


def handle_tax_submit(
    tax_rate: float,
    user: Dict[str, Any],
    submit_btn: Any = None
):
    """Handle tax rate submission"""
    try:
        if submit_btn:
            submit_btn.disable()
            submit_btn.text = '⏳ Submitting...'
        
        result = SettingsService.request_change(
            "DEFAULT_TAX_RATE",
            str(tax_rate),
            "Accounting Tax Rate Change",
            user["id"]
        )
        
        if result.get("success"):
            show_save_success("✅ Tax Rate request created")
        else:
            show_save_error(result.get("message", "Tax request failed"))
    
    except Exception as e:
        show_save_error(f"Tax Request Failed : {e}")
    
    finally:
        if submit_btn:
            submit_btn.enable()
            submit_btn.text = 'Submit Tax Rate Change'


def handle_discount_submit(
    discount_policy: str,
    user: Dict[str, Any],
    submit_btn: Any = None
):
    """Handle discount policy submission"""
    try:
        if submit_btn:
            submit_btn.disable()
            submit_btn.text = '⏳ Submitting...'
        
        result = SettingsService.request_change(
            "DISCOUNT_POLICY",
            discount_policy,
            "Discount Policy Change",
            user["id"]
        )
        
        if result.get("success"):
            show_save_success("✅ Discount Policy request created")
        else:
            show_save_error(result.get("message", "Discount request failed"))
    
    except Exception as e:
        show_save_error(f"Discount Request Failed : {e}")
    
    finally:
        if submit_btn:
            submit_btn.enable()
            submit_btn.text = 'Submit Policy Change'


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    "render_accounting_settings",
    "render_accounting_settings_advanced",
    "handle_submit",
    "update_policy_description",
    "update_summary",
    "show_result_dialog",
    "render_tax_settings",
    "render_discount_settings",
    "render_change_history",
    "handle_tax_submit",
    "handle_discount_submit",
]
