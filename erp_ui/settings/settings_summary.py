# ==============================================================================
# erp_ui/settings/settings_summary.py
# ERP SETTINGS SUMMARY + PENDING REQUESTS
# NICE GUI VERSION
# ==============================================================================

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from nicegui import ui

from .pending_settings import get_pending_settings_df

from erp_core.services.settings_service import SettingsService

from erp_core.loaders.settings_loader import clear_settings_cache

from utils.notification import (
    notify_success,
    notify_error,
)

from erp_ui.settings.common import (
    show_save_success,
    show_save_error,
    safe_float,
    safe_int,
)


# ==============================================================================
# SUMMARY UI
# ==============================================================================

def render_settings_summary(
    settings: Dict[str, Any],
    user: Dict[str, Any],
    container: Optional[Any] = None,
    on_change: Optional[Callable] = None
):
    """Render settings summary component
    
    Args:
        settings: Current settings dictionary
        user: Current user dictionary
        container: NiceGUI container to render in
        on_change: Callback after cancellation
    """
    
    target = container or ui.column()
    
    with target:
        # ----------------------------------------------------------------------
        # CURRENT CONFIGURATION HEADER
        # ----------------------------------------------------------------------
        
        ui.markdown("### ⚡ Current Configuration").classes('mb-4')
        
        # ======================================================================
        # ROW 1 - MAIN SETTINGS
        # ======================================================================
        
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            # Tax Rate
            with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                ui.label('Tax Rate').classes('text-sm text-gray-600')
                ui.label(f"{settings.get('DEFAULT_TAX_RATE', '0')}%").classes('text-2xl font-bold')
            
            # Pricing
            with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                ui.label('Pricing').classes('text-sm text-gray-600')
                ui.label(settings.get("PRICING_PRIORITY", "OWNER_FIRST")).classes('text-2xl font-bold')
            
            # Low Stock
            with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                ui.label('Low Stock').classes('text-sm text-gray-600')
                ui.label(str(settings.get("MIN_STOCK_ALERT", "0"))).classes('text-2xl font-bold')
            
            # Currency
            with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                ui.label('Currency').classes('text-sm text-gray-600')
                ui.label(settings.get("CURRENCY", "MMK")).classes('text-2xl font-bold')
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # ROW 2 - MARKUP & DEFAULT SETTINGS
        # ======================================================================
        
        ui.markdown("#### 📊 Markup & Default Settings").classes('mb-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            # Product Markup
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Product Markup').classes('text-sm text-gray-600')
                ui.label(f"{settings.get('PRODUCT_MARKUP_PERCENT', '15')}%").classes('text-xl font-bold')
            
            # Category Markup
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Category Markup').classes('text-sm text-gray-600')
                ui.label(f"{settings.get('CATEGORY_MARKUP_PERCENT', '20')}%").classes('text-xl font-bold')
            
            # Global Markup
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Global Markup').classes('text-sm text-gray-600')
                ui.label(f"{settings.get('DEFAULT_MARKUP_PERCENT', '20')}%").classes('text-xl font-bold')
            
            # Default Min Stock
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Default Min Stock').classes('text-sm text-gray-600')
                ui.label(str(settings.get('DEFAULT_MINIMUM_STOCK', '5'))).classes('text-xl font-bold')
            
            # Default Tax Rate
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Default Tax Rate').classes('text-sm text-gray-600')
                ui.label(f"{settings.get('DEFAULT_TAX_RATE', '5')}%").classes('text-xl font-bold')
        
        # Payment Methods
        payment_methods = settings.get('PAYMENT_METHODS', 'Cash')
        
        with ui.card().classes('w-full p-4 bg-gray-50 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('payment').classes('text-gray-500')
                ui.label('Payment Methods:').classes('font-semibold')
                ui.label(payment_methods).classes('text-gray-700')
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # PENDING REQUESTS
        # ======================================================================
        
        pending_df = get_pending_settings_df()
        
        if pending_df.empty:
            # No pending changes
            with ui.card().classes('w-full p-4 bg-green-50'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('check_circle').classes('text-green-500')
                    ui.label('✔ No Pending Setting Changes').classes('text-green-700 font-semibold')
            
            ui.separator().classes('my-4')
            return
        
        # Pending changes warning
        with ui.card().classes('w-full p-4 bg-orange-50 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning').classes('text-orange-500')
                ui.label(
                    f'⏳ Pending Changes: {len(pending_df)} request(s) waiting approval'
                ).classes('text-orange-700 font-semibold')
        
        # ======================================================================
        # PENDING REQUESTS LIST
        # ======================================================================
        
        ui.markdown("#### Pending Requests").classes('mb-4')
        
        for idx, row in pending_df.iterrows():
            with ui.card().classes('w-full p-4 mb-4 border border-gray-200'):
                # Setting key
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('settings').classes('text-gray-500')
                    ui.label('Setting:').classes('font-semibold')
                    ui.label(str(row['setting_key'])).classes('font-mono')
                
                # Old value
                with ui.row().classes('items-center gap-2 mb-1'):
                    ui.label('Current:').classes('font-semibold')
                    ui.label(str(row['old_value'])).classes('font-mono text-gray-600')
                
                # New value
                with ui.row().classes('items-center gap-2 mb-1'):
                    ui.label('Pending:').classes('font-semibold')
                    ui.label(str(row['new_value'])).classes('font-mono text-blue-600')
                
                # Created at
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label('Requested At:').classes('font-semibold')
                    ui.label(str(row['created_at'])).classes('font-mono text-gray-500')
                
                # Reason
                reason = row.get("reason")
                if reason:
                    with ui.row().classes('items-start gap-2 mb-2'):
                        ui.icon('description').classes('text-gray-500')
                        ui.label('Reason:').classes('font-semibold')
                        ui.label(str(reason)).classes('text-gray-600')
                
                # Cancel button (if requested by current user)
                if row.get("requested_by") == user.get("id"):
                    ui.separator().classes('my-2')
                    
                    cancel_btn = ui.button(
                        '🗑 Cancel Request',
                        on_click=lambda r=row: handle_cancel_request(
                            r,
                            user,
                            cancel_btn,
                            on_change
                        )
                    ).classes('w-full bg-red-500 text-white')
        
        ui.separator().classes('my-4')


def handle_cancel_request(
    row: Dict[str, Any],
    user: Dict[str, Any],
    cancel_btn: Any = None,
    on_change: Optional[Callable] = None
):
    """Handle cancel request
    
    Args:
        row: Request row data
        user: Current user dictionary
        cancel_btn: Cancel button instance
        on_change: Callback after successful cancellation
    """
    
    try:
        # Disable button during cancellation
        if cancel_btn:
            cancel_btn.disable()
            cancel_btn.text = '⏳ Cancelling...'
        
        # Show confirmation dialog
        show_cancel_confirmation(row, user, cancel_btn, on_change)
    
    except Exception as e:
        notify_error(str(e))
        
        if cancel_btn:
            cancel_btn.enable()
            cancel_btn.text = '🗑 Cancel Request'


def show_cancel_confirmation(
    row: Dict[str, Any],
    user: Dict[str, Any],
    cancel_btn: Any = None,
    on_change: Optional[Callable] = None
):
    """Show cancel confirmation dialog
    
    Args:
        row: Request row data
        user: Current user dictionary
        cancel_btn: Cancel button instance
        on_change: Callback after successful cancellation
    """
    
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
        ui.label('Confirm Cancellation').classes('text-xl font-bold mb-4')
        
        ui.label('Are you sure you want to cancel this request?').classes('mb-4')
        
        # Request details
        with ui.card().classes('w-full p-3 bg-gray-50 mb-4'):
            ui.label(f"Setting: {row['setting_key']}").classes('font-mono')
            ui.label(f"Current: {row['old_value']}").classes('font-mono text-gray-600')
            ui.label(f"Pending: {row['new_value']}").classes('font-mono text-blue-600')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button(
                'No, Keep Request',
                on_click=dialog.close
            ).props('flat')
            
            ui.button(
                'Yes, Cancel Request',
                on_click=lambda: execute_cancel(
                    row,
                    user,
                    dialog,
                    cancel_btn,
                    on_change
                )
            ).classes('bg-red-500 text-white')
    
    dialog.open()


def execute_cancel(
    row: Dict[str, Any],
    user: Dict[str, Any],
    dialog: Any,
    cancel_btn: Any = None,
    on_change: Optional[Callable] = None
):
    """Execute request cancellation
    
    Args:
        row: Request row data
        user: Current user dictionary
        dialog: Dialog instance
        cancel_btn: Cancel button instance
        on_change: Callback after successful cancellation
    """
    
    try:
        result = SettingsService.cancel_request(
            row["id"],
            user["id"]
        )
        
        if result.get("success"):
            clear_settings_cache()
            show_save_success("Request Cancelled Successfully")
            
            # Close dialog
            dialog.close()
            
            # Call callback if provided
            if on_change:
                on_change()
        
        else:
            notify_error(result.get("message", "Cancel failed"))
            dialog.close()
    
    except Exception as e:
        notify_error(str(e))
        dialog.close()
    
    finally:
        # Re-enable button if still exists
        if cancel_btn:
            cancel_btn.enable()
            cancel_btn.text = '🗑 Cancel Request'


# ==============================================================================
# COMPACT SUMMARY VIEW
# ==============================================================================

def render_settings_summary_compact(
    settings: Dict[str, Any],
    container: Optional[Any] = None
):
    """Render compact settings summary
    
    Args:
        settings: Current settings dictionary
        container: NiceGUI container to render in
    """
    
    target = container or ui.column()
    
    with target:
        with ui.grid(columns=4).classes('w-full gap-4'):
            # Tax Rate
            with ui.card().classes('p-3'):
                ui.label('Tax').classes('text-xs text-gray-500')
                ui.label(f"{settings.get('DEFAULT_TAX_RATE', '0')}%").classes('text-lg font-bold')
            
            # Currency
            with ui.card().classes('p-3'):
                ui.label('Currency').classes('text-xs text-gray-500')
                ui.label(settings.get("CURRENCY", "MMK")).classes('text-lg font-bold')
            
            # Low Stock Alert
            with ui.card().classes('p-3'):
                ui.label('Low Stock').classes('text-xs text-gray-500')
                ui.label(str(settings.get("MIN_STOCK_ALERT", "0"))).classes('text-lg font-bold')
            
            # Pricing
            with ui.card().classes('p-3'):
                ui.label('Pricing').classes('text-xs text-gray-500')
                ui.label(settings.get("PRICING_PRIORITY", "OWNER_FIRST")).classes('text-lg font-bold')


# ==============================================================================
# PENDING REQUESTS TIMELINE
# ==============================================================================

def render_pending_requests_timeline(
    user: Dict[str, Any],
    container: Optional[Any] = None,
    on_change: Optional[Callable] = None
):
    """Render pending requests as timeline
    
    Args:
        user: Current user dictionary
        container: NiceGUI container to render in
        on_change: Callback after cancellation
    """
    
    target = container or ui.column()
    
    pending_df = get_pending_settings_df()
    
    if pending_df.empty:
        with target:
            with ui.card().classes('w-full p-4 bg-green-50'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('check_circle').classes('text-green-500')
                    ui.label('No pending requests').classes('text-green-700')
        return
    
    with target:
        with ui.column().classes('w-full gap-4'):
            for idx, row in pending_df.iterrows():
                with ui.card().classes('w-full p-4'):
                    # Timeline indicator
                    with ui.row().classes('items-start gap-4'):
                        # Timeline dot
                        with ui.column().classes('items-center'):
                            ui.icon('circle').classes('text-orange-500 text-xs')
                            if idx < len(pending_df) - 1:
                                ui.element('div').classes('w-px h-full bg-gray-300')
                        
                        # Request content
                        with ui.column().classes('flex-1'):
                            with ui.row().classes('items-center gap-2 mb-2'):
                                ui.label(str(row['setting_key'])).classes('font-bold')
                                
                                # Status badge
                                ui.badge('Pending').classes('bg-orange-100 text-orange-700')
                            
                            ui.label(f"From: {row['old_value']}").classes('text-gray-600')
                            ui.label(f"To: {row['new_value']}").classes('text-blue-600')
                            
                            # Timestamp
                            ui.label(
                                format_timestamp(row.get('created_at'))
                            ).classes('text-xs text-gray-400 mt-2')
                            
                            # Reason
                            if row.get("reason"):
                                ui.label(f"Reason: {row['reason']}").classes('text-sm text-gray-500')
                            
                            # Cancel button
                            if row.get("requested_by") == user.get("id"):
                                ui.separator().classes('my-2')
                                
                                cancel_btn = ui.button(
                                    'Cancel Request',
                                    icon='delete',
                                    on_click=lambda r=row: handle_cancel_request(
                                        r,
                                        user,
                                        cancel_btn,
                                        on_change
                                    )
                                ).props('flat').classes('bg-red-50 text-red-700')


def format_timestamp(timestamp: Any) -> str:
    """Format timestamp for display
    
    Args:
        timestamp: Timestamp value
    
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return ""
    
    try:
        if isinstance(timestamp, str):
            # Try parsing ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return str(timestamp)
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    except Exception:
        return str(timestamp)


# ==============================================================================
# STATISTICS VIEW
# ==============================================================================

def render_settings_statistics(
    settings: Dict[str, Any],
    container: Optional[Any] = None
):
    """Render settings statistics with charts
    
    Args:
        settings: Current settings dictionary
        container: NiceGUI container to render in
    """
    
    target = container or ui.column()
    
    with target:
        # Tax rate gauge
        tax_rate = safe_float(settings.get('DEFAULT_TAX_RATE', 0), 0)
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Tax Rate').classes('text-lg font-bold mb-2')
            
            # Simple progress bar representation
            with ui.row().classes('items-center gap-4'):
                ui.label(f'{tax_rate:.1f}%').classes('text-2xl font-bold text-blue-700')
                
                with ui.column().classes('flex-1'):
                    ui.linear_progress(
                        value=tax_rate / 100 if tax_rate <= 100 else 1,
                        show_value=False
                    ).classes('w-full')
                    ui.label(f'0% - 100%').classes('text-xs text-gray-500 text-center')
        
        # Markup statistics
        product_markup = safe_float(settings.get('PRODUCT_MARKUP_PERCENT', 15), 15)
        category_markup = safe_float(settings.get('CATEGORY_MARKUP_PERCENT', 20), 20)
        global_markup = safe_float(settings.get('DEFAULT_MARKUP_PERCENT', 20), 20)
        
        with ui.card().classes('w-full p-4'):
            ui.label('Markup Rates').classes('text-lg font-bold mb-4')
            
            # Create bar chart using Plotly
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[
                go.Bar(
                    name='Markup %',
                    x=['Product', 'Category', 'Global'],
                    y=[product_markup, category_markup, global_markup],
                    marker_color=['#3B82F6', '#10B981', '#F59E0B']
                )
            ])
            
            fig.update_layout(
                title='Markup Rates Comparison',
                yaxis_title='Percentage (%)',
                showlegend=False,
                height=300,
            )
            
            ui.plotly(fig).classes('w-full')


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    "render_settings_summary",
    "render_settings_summary_compact",
    "render_pending_requests_timeline",
    "render_settings_statistics",
    "handle_cancel_request",
    "show_cancel_confirmation",
    "execute_cancel",
    "format_timestamp",
]
