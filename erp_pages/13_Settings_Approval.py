# ==============================================================================
# erp_pages/13_Settings_Approval.py
# ERP ENTERPRISE SETTINGS APPROVAL CENTER v1.0 CLEAN
# NICE GUI VERSION
#
# Maker - Checker Workflow
# Approve / Reject / Cancel
#
# Compatible:
# app.py dynamic router
# sidebar.py navigation
# SettingsService
#
# ==============================================================================

from typing import Dict, Any, Optional, Callable, List
import pandas as pd
from datetime import datetime
from nicegui import ui

from erp_core.base_repo import db

from erp_core.services.settings_service import (
    SettingsService
)

from erp_core.loaders.settings_loader import (
    clear_settings_cache
)

from utils.notification import (
    notify_success,
    notify_error
)

from auth import (
    get_current_user,
)


# ==============================================================================
# SECURITY
# ==============================================================================

def require_admin() -> Optional[Dict[str, Any]]:
    """Check admin access."""
    user = get_current_user()
    
    if not user:
        ui.notify("⛔ Login Required", type='error', position='top')
        return None
    
    role_id = int(user.get("role_id", 0))
    
    if role_id != 1:
        ui.notify("⛔ Admin Access Required", type='error', position='top')
        return None
    
    return user


# ==============================================================================
# LOAD REQUESTS
# ==============================================================================

def get_pending_requests() -> pd.DataFrame:
    """Get pending settings change requests."""
    try:
        result = (
            db()
            .table("settings_change_requests")
            .select("""
                id,
                setting_key,
                old_value,
                new_value,
                reason,
                requested_by,
                status,
                created_at
            """)
            .eq("status", "PENDING")
            .order("created_at", desc=True)
            .execute()
        )
        
        return pd.DataFrame(result.data or [])
    
    except Exception as e:
        ui.notify(f"Load Request Error : {e}", type='error', position='top')
        return pd.DataFrame()


# ==============================================================================
# RESULT HELPER
# ==============================================================================

def get_result_value(result: Any, key: str) -> Any:
    """Extract value from result (dict or list)."""
    if isinstance(result, dict):
        return result.get(key)
    
    if isinstance(result, list) and result:
        if isinstance(result[0], dict):
            return result[0].get(key)
    
    return None


# ==============================================================================
# FORMAT HELPERS
# ==============================================================================

def format_timestamp(timestamp: Any) -> str:
    """Format timestamp for display."""
    if not timestamp:
        return "N/A"
    
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return str(timestamp)
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    except Exception:
        return str(timestamp)


# ==============================================================================
# REQUEST CARD COMPONENT
# ==============================================================================

def build_request_card(
    row: Dict[str, Any],
    current_user_id: str,
    on_change: Optional[Callable] = None
):
    """Build individual request card."""
    request_id = row["id"]
    maker_id = str(row["requested_by"])
    
    with ui.card().classes('w-full p-4 mb-4 border border-gray-200'):
        # Setting key
        ui.label(f"⚙ {row['setting_key']}").classes('text-xl font-bold mb-3')
        
        # Values comparison
        with ui.row().classes('w-full gap-4 flex-wrap mb-3'):
            # Old value
            with ui.card().classes('p-3 flex-1 min-w-[150px] bg-gray-50'):
                ui.label('Current Value').classes('text-sm text-gray-600')
                ui.label(str(row["old_value"])).classes('font-semibold text-gray-700')
            
            # New value
            with ui.card().classes('p-3 flex-1 min-w-[150px] bg-blue-50'):
                ui.label('Pending Value').classes('text-sm text-gray-600')
                ui.label(str(row["new_value"])).classes('font-semibold text-blue-700')
        
        # Reason
        if row.get("reason"):
            with ui.row().classes('items-start gap-2 mb-2'):
                ui.icon('description').classes('text-gray-500')
                ui.label('Reason:').classes('font-semibold')
                ui.label(str(row["reason"])).classes('text-gray-600')
        
        # Request info
        with ui.row().classes('w-full gap-4 flex-wrap mb-3'):
            with ui.column().classes('flex-1 min-w-[150px]'):
                ui.label('Requested By:').classes('text-sm text-gray-500')
                ui.label(maker_id).classes('font-mono text-sm')
            
            with ui.column().classes('flex-1 min-w-[150px]'):
                ui.label('Created:').classes('text-sm text-gray-500')
                ui.label(format_timestamp(row.get("created_at"))).classes('text-sm')
        
        ui.separator().classes('my-3')
        
        # ======================================================================
        # MAKER CANNOT APPROVE OWN REQUEST
        # ======================================================================
        
        if maker_id == current_user_id:
            with ui.card().classes('w-full p-3 bg-orange-50 border border-orange-200'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('warning').classes('text-orange-500')
                    ui.label('⚠ This is your request. Waiting for another Admin.').classes(
                        'text-orange-700'
                    )
                
                cancel_btn = ui.button(
                    '🗑 Cancel Request',
                    on_click=lambda: show_cancel_dialog(row, cancel_btn, on_change)
                ).classes('w-full bg-red-500 text-white')
        
        # ======================================================================
        # CHECKER ACTIONS
        # ======================================================================
        
        else:
            with ui.row().classes('w-full gap-2'):
                # Approve button
                approve_btn = ui.button(
                    '✅ Approve',
                    on_click=lambda: handle_approve(row, approve_btn, on_change)
                ).classes('flex-1 bg-green-500 text-white')
                
                # Reject button
                reject_btn = ui.button(
                    '❌ Reject',
                    on_click=lambda: show_reject_dialog(row, reject_btn, on_change)
                ).classes('flex-1 bg-red-500 text-white')


def show_cancel_dialog(
    row: Dict[str, Any],
    cancel_btn: Any,
    on_change: Optional[Callable] = None
):
    """Show cancel confirmation dialog."""
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
        ui.label('Confirm Cancellation').classes('text-xl font-bold mb-4')
        
        ui.label('Are you sure you want to cancel this request?').classes('mb-4')
        
        with ui.card().classes('w-full p-3 bg-gray-50 mb-4'):
            ui.label(f"Setting: {row['setting_key']}").classes('font-semibold')
            ui.label(f"New Value: {row['new_value']}").classes('text-blue-600')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('No, Keep Request', on_click=dialog.close).props('flat')
            
            ui.button(
                'Yes, Cancel',
                on_click=lambda: handle_cancel(row, dialog, cancel_btn, on_change)
            ).classes('bg-red-500 text-white')
    
    dialog.open()


def handle_cancel(
    row: Dict[str, Any],
    dialog: Any,
    cancel_btn: Any,
    on_change: Optional[Callable] = None
):
    """Handle request cancellation."""
    try:
        cancel_btn.disable()
        cancel_btn.text = '⏳ Cancelling...'
        
        user = get_current_user()
        current_user_id = str(user.get("id") or user.get("user_id"))
        
        result = SettingsService.cancel_request(
            row["id"],
            current_user_id
        )
        
        if get_result_value(result, "success"):
            clear_settings_cache()
            notify_success("Request Cancelled")
            dialog.close()
            
            if on_change:
                on_change()
        else:
            notify_error(str(result))
            dialog.close()
    
    except Exception as e:
        notify_error(str(e))
        dialog.close()
    
    finally:
        cancel_btn.enable()
        cancel_btn.text = '🗑 Cancel Request'


def handle_approve(
    row: Dict[str, Any],
    approve_btn: Any,
    on_change: Optional[Callable] = None
):
    """Handle request approval."""
    try:
        approve_btn.disable()
        approve_btn.text = '⏳ Approving...'
        
        user = get_current_user()
        current_user_id = str(user.get("id") or user.get("user_id"))
        
        result = SettingsService.approve_request(
            row["id"],
            current_user_id
        )
        
        if get_result_value(result, "success"):
            clear_settings_cache()
            notify_success("Setting Approved")
            
            if on_change:
                on_change()
        else:
            notify_error(str(result))
    
    except Exception as e:
        notify_error(str(e))
    
    finally:
        approve_btn.enable()
        approve_btn.text = '✅ Approve'


def show_reject_dialog(
    row: Dict[str, Any],
    reject_btn: Any,
    on_change: Optional[Callable] = None
):
    """Show reject dialog with reason input."""
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
        ui.label('Reject Request').classes('text-xl font-bold mb-4')
        
        ui.label(f"Setting: {row['setting_key']}").classes('mb-2')
        ui.label(f"New Value: {row['new_value']}").classes('mb-4')
        
        # Rejection reason
        reason_input = ui.textarea(
            'Reject Reason',
            placeholder='Enter reason for rejection...'
        ).classes('w-full mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            ui.button(
                'Confirm Reject',
                on_click=lambda: handle_reject(
                    row,
                    reason_input.value,
                    dialog,
                    reject_btn,
                    on_change
                )
            ).classes('bg-red-500 text-white')
    
    dialog.open()


def handle_reject(
    row: Dict[str, Any],
    reason: str,
    dialog: Any,
    reject_btn: Any,
    on_change: Optional[Callable] = None
):
    """Handle request rejection."""
    try:
        if not reason:
            ui.notify("Reject reason required", type='error', position='top')
            return
        
        reject_btn.disable()
        reject_btn.text = '⏳ Rejecting...'
        
        user = get_current_user()
        current_user_id = str(user.get("id") or user.get("user_id"))
        
        result = SettingsService.reject_request(
            row["id"],
            current_user_id,
            reason
        )
        
        if get_result_value(result, "success"):
            clear_settings_cache()
            notify_success("Request Rejected")
            dialog.close()
            
            if on_change:
                on_change()
        else:
            notify_error(str(result))
            dialog.close()
    
    except Exception as e:
        notify_error(str(e))
        dialog.close()
    
    finally:
        reject_btn.enable()
        reject_btn.text = '❌ Reject'


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point."""
    
    user = require_admin()
    
    if not user:
        return
    
    current_user_id = str(
        user.get("id") or user.get("user_id")
    )
    
    target = container or ui.column()
    
    with target:
        # Header
        ui.label("✅ Settings Approval Center").classes('text-3xl font-bold mb-2')
        ui.label("Maker - Checker Workflow | Admin Only").classes('text-gray-500 mb-4')
        
        # Session info
        with ui.expansion('🔍 Session Info', icon='info').classes('w-full mb-4'):
            with ui.column().classes('w-full gap-2 p-2'):
                ui.label(f"User ID: {current_user_id}").classes('font-mono')
                ui.label(f"Role: {user.get('role', 'Unknown')}").classes('font-mono')
                ui.label(f"Name: {user.get('full_name', 'Unknown')}").classes('font-mono')
        
        ui.separator().classes('my-4')
        
        # Load requests
        requests = get_pending_requests()
        
        if requests.empty:
            with ui.card().classes('w-full p-4 bg-green-50'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('check_circle').classes('text-green-500')
                    ui.label("✔ No Pending Setting Requests").classes('text-green-700 font-semibold')
            return
        
        # Pending warning
        with ui.card().classes('w-full p-4 bg-orange-50 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning').classes('text-orange-500')
                ui.label(f"⏳ Pending Changes : {len(requests)}").classes(
                    'text-orange-700 font-semibold'
                )
        
        ui.separator().classes('my-4')
        
        # Requests container
        requests_container = ui.column().classes('w-full')
        
        def refresh_requests():
            """Refresh pending requests."""
            requests_container.clear()
            
            new_requests = get_pending_requests()
            
            if new_requests.empty:
                with requests_container:
                    with ui.card().classes('w-full p-4 bg-green-50'):
                        ui.label("✔ No Pending Setting Requests").classes('text-green-700')
                return
            
            with requests_container:
                for _, row in new_requests.iterrows():
                    build_request_card(
                        row.to_dict(),
                        current_user_id,
                        refresh_requests
                    )
        
        # Initial render
        refresh_requests()


# ==============================================================================
# ADVANCED VIEW WITH STATISTICS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced view with statistics."""
    
    user = require_admin()
    
    if not user:
        return
    
    current_user_id = str(user.get("id") or user.get("user_id"))
    
    target = container or ui.column()
    
    with target:
        ui.label("✅ Settings Approval Center").classes('text-3xl font-bold mb-4')
        
        requests = get_pending_requests()
        
        # Statistics
        total_requests = len(requests)
        
        if total_requests > 0:
            # Count by setting type
            setting_counts = requests['setting_key'].value_counts()
            
            with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                with ui.card().classes('p-4 flex-1 min-w-[150px] bg-blue-50'):
                    ui.label('Total Pending').classes('text-sm text-gray-600')
                    ui.label(str(total_requests)).classes('text-2xl font-bold text-blue-700')
                
                with ui.card().classes('p-4 flex-1 min-w-[150px] bg-green-50'):
                    ui.label('Your Requests').classes('text-sm text-gray-600')
                    your_count = sum(
                        1 for _, r in requests.iterrows()
                        if str(r['requested_by']) == current_user_id
                    )
                    ui.label(str(your_count)).classes('text-2xl font-bold text-green-700')
                
                with ui.card().classes('p-4 flex-1 min-w-[150px] bg-orange-50'):
                    ui.label('To Review').classes('text-sm text-gray-600')
                    review_count = total_requests - your_count
                    ui.label(str(review_count)).classes('text-2xl font-bold text-orange-700')
            
            # Setting type breakdown
            with ui.card().classes('w-full p-4 mb-4'):
                ui.label('Requests by Setting Type').classes('font-bold mb-2')
                
                for setting_key, count in setting_counts.items():
                    with ui.row().classes('w-full justify-between items-center py-1'):
                        ui.label(setting_key).classes('font-mono')
                        ui.badge(str(count)).classes('bg-blue-100 text-blue-700')
        
        # Requests list
        requests_container = ui.column().classes('w-full')
        
        def refresh_requests():
            requests_container.clear()
            
            new_requests = get_pending_requests()
            
            if new_requests.empty:
                with requests_container:
                    with ui.card().classes('w-full p-4 bg-green-50'):
                        ui.label("✔ No Pending Setting Requests").classes('text-green-700')
                return
            
            with requests_container:
                for _, row in new_requests.iterrows():
                    build_request_card(
                        row.to_dict(),
                        current_user_id,
                        refresh_requests
                    )
        
        refresh_requests()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
