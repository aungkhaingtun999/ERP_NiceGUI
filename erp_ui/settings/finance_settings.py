# ==============================================================================
# erp_ui/settings/finance_settings.py
# ERP FINANCE SETTINGS COMPONENT v2.0
# NICE GUI VERSION
#
# Approval Workflow Enabled
#
# Request -> Approval -> Apply
#
# ==============================================================================

from typing import Dict, Any, Optional, Callable, List
from nicegui import ui

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
)


# ==============================================================================
# CONSTANTS
# ==============================================================================

CURRENCY_LIST = ["MMK", "USD", "THB", "SGD"]

PAYMENT_METHODS_LIST = [
    "Cash",
    "Bank Transfer",
    "Mobile Pay",
    "Credit"
]

CURRENCY_SYMBOLS = {
    "MMK": "K",
    "USD": "$",
    "THB": "฿",
    "SGD": "S$",
}


# ==============================================================================
# FINANCE SETTINGS UI
# ==============================================================================

def render_finance_settings(
    settings: Dict[str, Any],
    user: Dict[str, Any],
    container: Optional[Any] = None,
    on_success: Optional[Callable] = None
):
    """Render finance settings component
    
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
        
        ui.label('💱 Finance Settings').classes('text-2xl font-bold mb-4')
        
        # ======================================================================
        # CURRENCY
        # ======================================================================
        
        current_currency = settings.get("CURRENCY", "MMK")
        
        if current_currency not in CURRENCY_LIST:
            current_currency = "MMK"
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Base Currency').classes('font-semibold mb-2')
            
            # Currency selector with symbols
            currency = ui.select(
                CURRENCY_LIST,
                value=current_currency,
                label='Select Currency',
            ).classes('w-full')
            
            # Show currency preview
            currency_preview = ui.column().classes('w-full mt-2')
            update_currency_preview(currency_preview, current_currency)
            
            # Update preview on change
            currency.on_value_change(
                lambda e: update_currency_preview(currency_preview, e.value)
            )
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # PAYMENT METHODS
        # ======================================================================
        
        payment_default = settings.get("PAYMENT_METHODS", "Cash")
        
        # Parse payment methods
        default_methods = [
            method.strip()
            for method in payment_default.split(",")
            if method.strip() in PAYMENT_METHODS_LIST
        ]
        
        if not default_methods:
            default_methods = ["Cash"]
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Payment Methods').classes('font-semibold mb-2')
            ui.label('Select allowed payment methods:').classes('text-sm text-gray-600 mb-2')
            
            # Payment methods checkboxes
            payment_checkboxes = {}
            
            for method in PAYMENT_METHODS_LIST:
                is_checked = method in default_methods
                
                with ui.row().classes('items-center gap-2 mb-1'):
                    checkbox = ui.checkbox(
                        method,
                        value=is_checked
                    )
                    payment_checkboxes[method] = checkbox
                    
                    # Add payment method icon
                    icon = get_payment_icon(method)
                    if icon:
                        ui.icon(icon).classes('text-gray-500')
            
            # Show selected methods summary
            methods_summary = ui.column().classes('w-full mt-2')
            update_methods_summary(methods_summary, default_methods)
            
            # Update summary on checkbox change
            for method, checkbox in payment_checkboxes.items():
                checkbox.on_value_change(
                    lambda e, m=method: update_methods_summary_from_checkboxes(
                        methods_summary,
                        payment_checkboxes
                    )
                )
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # CHANGE SUMMARY
        # ======================================================================
        
        with ui.expansion('📋 Change Summary', icon='visibility').classes('w-full mb-4'):
            summary_container = ui.column().classes('w-full p-2')
            
            update_full_summary(
                summary_container,
                currency.value,
                [m for m, cb in payment_checkboxes.items() if cb.value]
            )
            
            # Update summary on changes
            currency.on_value_change(
                lambda e: update_full_summary(
                    summary_container,
                    e.value,
                    [m for m, cb in payment_checkboxes.items() if cb.value]
                )
            )
            
            for method, checkbox in payment_checkboxes.items():
                checkbox.on_value_change(
                    lambda e: update_full_summary(
                        summary_container,
                        currency.value,
                        [m for m, cb in payment_checkboxes.items() if cb.value]
                    )
                )
        
        # ======================================================================
        # SUBMIT REQUEST
        # ======================================================================
        
        submit_button = ui.button(
            '📤 Submit Finance Change Request',
            on_click=lambda: handle_submit(
                currency.value,
                [m for m, cb in payment_checkboxes.items() if cb.value],
                user,
                submit_button,
                on_success
            )
        ).classes('w-full bg-primary text-white font-semibold py-2')


def get_payment_icon(method: str) -> Optional[str]:
    """Get icon for payment method
    
    Args:
        method: Payment method name
    
    Returns:
        Icon name or None
    """
    icons = {
        "Cash": "payments",
        "Bank Transfer": "account_balance",
        "Mobile Pay": "phone_android",
        "Credit": "credit_card",
    }
    
    return icons.get(method)


def update_currency_preview(container: Any, currency: str):
    """Update currency preview
    
    Args:
        container: Container to update
        currency: Selected currency
    """
    container.clear()
    
    with container:
        symbol = CURRENCY_SYMBOLS.get(currency, "")
        
        with ui.row().classes('items-center gap-2'):
            ui.label('Preview:').classes('text-sm text-gray-600')
            ui.label(f'{symbol} 1,000.00').classes('font-mono text-lg')
        
        ui.label(f'Currency Code: {currency}').classes('text-sm text-gray-500')


def update_methods_summary(container: Any, methods: List[str]):
    """Update payment methods summary
    
    Args:
        container: Container to update
        methods: Selected methods
    """
    container.clear()
    
    with container:
        if not methods:
            ui.label('⚠️ No payment methods selected').classes('text-orange-600')
            return
        
        ui.label(f'{len(methods)} payment method(s) selected:').classes('text-sm text-gray-600')
        
        with ui.row().classes('gap-2 flex-wrap mt-1'):
            for method in methods:
                ui.badge(method).classes('bg-blue-100 text-blue-700')


def update_methods_summary_from_checkboxes(
    container: Any,
    checkboxes: Dict[str, Any]
):
    """Update methods summary from checkboxes
    
    Args:
        container: Container to update
        checkboxes: Dictionary of checkbox components
    """
    selected = [m for m, cb in checkboxes.items() if cb.value]
    update_methods_summary(container, selected)


def update_full_summary(
    container: Any,
    currency: str,
    methods: List[str]
):
    """Update full change summary
    
    Args:
        container: Container to update
        currency: Selected currency
        methods: Selected payment methods
    """
    container.clear()
    
    with container:
        with ui.row().classes('w-full justify-between items-center py-1'):
            ui.label('Base Currency:').classes('font-semibold')
            ui.label(f'{currency} ({CURRENCY_SYMBOLS.get(currency, "")})').classes('text-lg')
        
        ui.separator().classes('my-1')
        
        with ui.row().classes('w-full justify-between items-center py-1'):
            ui.label('Payment Methods:').classes('font-semibold')
            ui.label(f'{len(methods)} selected').classes('text-lg')
        
        ui.separator().classes('my-1')
        
        ui.label('Selected Methods:').classes('text-sm text-gray-600 mt-2')
        
        with ui.row().classes('gap-2 flex-wrap mt-1'):
            for method in methods:
                ui.badge(method).classes('bg-blue-100 text-blue-700')


def handle_submit(
    currency: str,
    payment_methods: List[str],
    user: Dict[str, Any],
    submit_button: Any = None,
    on_success: Optional[Callable] = None
):
    """Handle submit finance change request
    
    Args:
        currency: Selected currency
        payment_methods: Selected payment methods
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
        
        if not payment_methods:
            show_save_error("Please select at least one payment method.")
            
            if submit_button:
                submit_button.enable()
                submit_button.text = '📤 Submit Finance Change Request'
            
            return
        
        # ======================================================================
        # CURRENCY REQUEST
        # ======================================================================
        
        currency_result = SettingsService.request_change(
            "CURRENCY",
            currency,
            "Finance Currency Change",
            user["id"]
        )
        
        # ======================================================================
        # PAYMENT METHODS REQUEST
        # ======================================================================
        
        payment_result = SettingsService.request_change(
            "PAYMENT_METHODS",
            ",".join(payment_methods),
            "Payment Methods Change",
            user["id"]
        )
        
        # ======================================================================
        # CHECK RESULTS
        # ======================================================================
        
        messages = []
        errors = []
        
        if currency_result.get("success"):
            messages.append("✅ Currency request created")
        else:
            errors.append(currency_result.get("message", "Currency request failed"))
        
        if payment_result.get("success"):
            messages.append("✅ Payment Methods request created")
        else:
            errors.append(payment_result.get("message", "Payment Methods request failed"))
        
        # ======================================================================
        # NOTIFICATIONS
        # ======================================================================
        
        if messages:
            show_save_success("💱 Finance Change Request Submitted. Waiting Approval.")
            
            # Show result dialog
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
            for err in errors:
                show_save_error(err)
            
            show_result_dialog(
                success=False,
                title="Request Failed",
                messages=[],
                errors=errors
            )
        
        elif errors:
            show_result_dialog(
                success=True,
                title="Partial Success",
                messages=messages,
                errors=errors
            )
    
    except Exception as e:
        error_message = f"Finance Request Failed : {e}"
        show_save_error(error_message)
        
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
            submit_button.text = '📤 Submit Finance Change Request'


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
# ADVANCED FINANCE SETTINGS
# ==============================================================================

def render_finance_settings_advanced(
    settings: Dict[str, Any],
    user: Dict[str, Any],
    container: Optional[Any] = None
):
    """Render advanced finance settings with tabs
    
    Args:
        settings: Current settings dictionary
        user: Current user dictionary
        container: NiceGUI container to render in
    """
    
    target = container or ui.column()
    
    with target:
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_currency = ui.tab('Currency', icon='attach_money')
            tab_payments = ui.tab('Payment Methods', icon='payment')
            tab_preview = ui.tab('Preview', icon='visibility')
        
        with ui.tab_panels(tabs, value=tab_currency).classes('w-full'):
            with ui.tab_panel(tab_currency):
                render_currency_settings(settings, user)
            
            with ui.tab_panel(tab_payments):
                render_payment_methods_settings(settings, user)
            
            with ui.tab_panel(tab_preview):
                render_settings_preview(settings)


def render_currency_settings(settings: Dict[str, Any], user: Dict[str, Any]):
    """Render currency settings tab"""
    
    current_currency = settings.get("CURRENCY", "MMK")
    
    with ui.card().classes('w-full p-4'):
        ui.label('Currency Configuration').classes('text-xl font-bold mb-4')
        
        # Currency selector
        currency = ui.select(
            CURRENCY_LIST,
            value=current_currency if current_currency in CURRENCY_LIST else "MMK",
            label='Base Currency',
        ).classes('w-full mb-4')
        
        # Currency info
        info_container = ui.column().classes('w-full mb-4')
        update_currency_info(info_container, current_currency)
        currency.on_value_change(lambda e: update_currency_info(info_container, e.value))
        
        # Submit button
        submit_btn = ui.button(
            'Submit Currency Change',
            on_click=lambda: handle_currency_submit(currency.value, user, submit_btn)
        ).classes('w-full bg-primary text-white')


def render_payment_methods_settings(settings: Dict[str, Any], user: Dict[str, Any]):
    """Render payment methods settings tab"""
    
    payment_default = settings.get("PAYMENT_METHODS", "Cash")
    default_methods = [m.strip() for m in payment_default.split(",") if m.strip()]
    
    with ui.card().classes('w-full p-4'):
        ui.label('Payment Methods Configuration').classes('text-xl font-bold mb-4')
        
        # Payment method checkboxes
        checkboxes = {}
        
        for method in PAYMENT_METHODS_LIST:
            is_checked = method in default_methods
            
            with ui.row().classes('items-center gap-2 mb-2'):
                checkbox = ui.checkbox(method, value=is_checked)
                checkboxes[method] = checkbox
                
                icon = get_payment_icon(method)
                if icon:
                    ui.icon(icon).classes('text-gray-500')
        
        # Submit button
        submit_btn = ui.button(
            'Submit Payment Methods Change',
            on_click=lambda: handle_payment_submit(
                [m for m, cb in checkboxes.items() if cb.value],
                user,
                submit_btn
            )
        ).classes('w-full bg-primary text-white mt-4')


def render_settings_preview(settings: Dict[str, Any]):
    """Render settings preview tab"""
    
    with ui.card().classes('w-full p-4'):
        ui.label('Current Settings Preview').classes('text-xl font-bold mb-4')
        
        current_currency = settings.get("CURRENCY", "MMK")
        payment_default = settings.get("PAYMENT_METHODS", "Cash")
        payment_methods = [m.strip() for m in payment_default.split(",") if m.strip()]
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                ui.label('Base Currency').classes('text-sm text-gray-600')
                ui.label(f'{current_currency} ({CURRENCY_SYMBOLS.get(current_currency, "")})').classes('text-2xl font-bold')
            
            with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                ui.label('Payment Methods').classes('text-sm text-gray-600')
                ui.label(str(len(payment_methods))).classes('text-2xl font-bold')
        
        ui.label('Available Payment Methods:').classes('font-semibold mt-4 mb-2')
        
        with ui.row().classes('gap-2 flex-wrap'):
            for method in payment_methods:
                ui.badge(method).classes('bg-blue-100 text-blue-700')


def update_currency_info(container: Any, currency: str):
    """Update currency information
    
    Args:
        container: Container to update
        currency: Selected currency
    """
    container.clear()
    
    with container:
        symbol = CURRENCY_SYMBOLS.get(currency, "")
        
        with ui.row().classes('items-center gap-2'):
            ui.label('Symbol:').classes('font-semibold')
            ui.label(symbol).classes('text-xl')
        
        ui.label(f'Example: {symbol} 1,000.00').classes('text-gray-600')


def handle_currency_submit(
    currency: str,
    user: Dict[str, Any],
    submit_btn: Any = None
):
    """Handle currency submission"""
    try:
        if submit_btn:
            submit_btn.disable()
            submit_btn.text = '⏳ Submitting...'
        
        result = SettingsService.request_change(
            "CURRENCY",
            currency,
            "Finance Currency Change",
            user["id"]
        )
        
        if result.get("success"):
            show_save_success("💱 Currency change request submitted")
        else:
            show_save_error(result.get("message", "Currency request failed"))
    
    except Exception as e:
        show_save_error(f"Currency Request Failed : {e}")
    
    finally:
        if submit_btn:
            submit_btn.enable()
            submit_btn.text = 'Submit Currency Change'


def handle_payment_submit(
    payment_methods: List[str],
    user: Dict[str, Any],
    submit_btn: Any = None
):
    """Handle payment methods submission"""
    try:
        if submit_btn:
            submit_btn.disable()
            submit_btn.text = '⏳ Submitting...'
        
        if not payment_methods:
            show_save_error("Please select at least one payment method.")
            return
        
        result = SettingsService.request_change(
            "PAYMENT_METHODS",
            ",".join(payment_methods),
            "Payment Methods Change",
            user["id"]
        )
        
        if result.get("success"):
            show_save_success("💳 Payment methods change request submitted")
        else:
            show_save_error(result.get("message", "Payment methods request failed"))
    
    except Exception as e:
        show_save_error(f"Payment Methods Request Failed : {e}")
    
    finally:
        if submit_btn:
            submit_btn.enable()
            submit_btn.text = 'Submit Payment Methods Change'


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    "render_finance_settings",
    "render_finance_settings_advanced",
    "handle_submit",
    "get_payment_icon",
    "update_currency_preview",
    "update_methods_summary",
    "update_full_summary",
    "show_result_dialog",
    "render_currency_settings",
    "render_payment_methods_settings",
    "render_settings_preview",
    "handle_currency_submit",
    "handle_payment_submit",
    "CURRENCY_LIST",
    "PAYMENT_METHODS_LIST",
    "CURRENCY_SYMBOLS",
]
