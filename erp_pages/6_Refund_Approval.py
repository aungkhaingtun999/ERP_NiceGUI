# ==============================================================================
# ERP ENTERPRISE REFUND APPROVAL CENTER
# NICE GUI VERSION
#
# FINAL REFUND WORKFLOW
#
# RPC ONLY:
#   approve_refund_rpc
#   reject_refund_rpc
#
# STATUS FLOW:
#   PENDING -> APPROVED
#   PENDING -> REJECTED
#
# IMPORTANT:
#   Approve = restore stock + inventory log + FIFO layer
#   Reject  = status only
# ==============================================================================

from typing import Dict, Any, Optional, List
from nicegui import ui

from database import db
from auth import require_login


# ==============================================================================
# ALLOWED ROLES
# ==============================================================================

ALLOWED_ROLE_IDS = {
    1,  # Admin
    2,  # Manager
}


# ==============================================================================
# SAFE NUMBER
# ==============================================================================

def safe_float(value: Any) -> float:
    """Safely convert value to float."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


# ==============================================================================
# APPROVE
# ==============================================================================

def handle_approval(
    refund_id: Any,
    approver_id: Any,
    approve_btn: Optional[Any] = None,
    on_success: Optional[callable] = None
):
    """Handle refund approval."""
    try:
        if approve_btn:
            approve_btn.disable()
            approve_btn.text = '⏳ Approving...'
        
        result = (
            db()
            .rpc(
                "approve_refund_rpc",
                {
                    "p_refund_id": int(refund_id),
                    "p_manager_id": approver_id,
                },
            )
            .execute()
        )
        
        data = result.data
        
        if isinstance(data, dict) and data.get("success") is True:
            ui.notify(f'Refund ID {refund_id} approved successfully.', type='positive', position='top')
            
            if on_success:
                on_success()
        else:
            message = data.get("message") if isinstance(data, dict) else str(data)
            ui.notify(f'Approval failed: {message}', type='error', position='top')
    
    except Exception as e:
        ui.notify(f'Approval error: {e}', type='error', position='top')
    
    finally:
        if approve_btn:
            approve_btn.enable()
            approve_btn.text = '✅ Approve Refund'


# ==============================================================================
# REJECT
# ==============================================================================

def handle_rejection(
    refund_id: Any,
    approver_id: Any,
    reason: str,
    reject_btn: Optional[Any] = None,
    on_success: Optional[callable] = None
):
    """Handle refund rejection."""
    reason = (reason or "").strip()
    
    if not reason:
        ui.notify('Reject reason is required.', type='warning', position='top')
        return
    
    try:
        if reject_btn:
            reject_btn.disable()
            reject_btn.text = '⏳ Rejecting...'
        
        result = (
            db()
            .rpc(
                "reject_refund_rpc",
                {
                    "p_refund_id": int(refund_id),
                    "p_manager_id": approver_id,
                    "p_reason": reason,
                },
            )
            .execute()
        )
        
        data = result.data
        
        if isinstance(data, dict) and data.get("success") is True:
            ui.notify(f'Refund ID {refund_id} rejected successfully.', type='positive', position='top')
            
            if on_success:
                on_success()
        else:
            message = data.get("message") if isinstance(data, dict) else str(data)
            ui.notify(f'Rejection failed: {message}', type='error', position='top')
    
    except Exception as e:
        ui.notify(f'Rejection error: {e}', type='error', position='top')
    
    finally:
        if reject_btn:
            reject_btn.enable()
            reject_btn.text = '❌ Reject Refund'


# ==============================================================================
# REJECT DIALOG
# ==============================================================================

def show_reject_dialog(
    refund: Dict[str, Any],
    approver_id: Any,
    on_success: Optional[callable] = None
):
    """Show reject confirmation dialog with reason input."""
    refund_id = refund.get("id")
    
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
        ui.label('Reject Refund').classes('text-xl font-bold mb-4')
        
        ui.label(f'Refund ID: {refund_id}').classes('font-semibold mb-2')
        ui.label(f'Amount: {safe_float(refund.get("refund_amount")):,.0f} MMK').classes('mb-4')
        
        reason_input = ui.textarea(
            'Reject Reason',
            placeholder='Enter reason for rejection...'
        ).classes('w-full mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            ui.button(
                'Confirm Reject',
                on_click=lambda: handle_rejection_with_dialog(
                    refund_id,
                    approver_id,
                    reason_input.value,
                    dialog,
                    on_success
                )
            ).classes('bg-red-500 text-white')
    
    dialog.open()


def handle_rejection_with_dialog(
    refund_id: Any,
    approver_id: Any,
    reason: str,
    dialog: Any,
    on_success: Optional[callable] = None
):
    """Handle rejection from dialog."""
    reason = (reason or "").strip()
    
    if not reason:
        ui.notify('Reject reason is required.', type='warning', position='top')
        return
    
    try:
        result = (
            db()
            .rpc(
                "reject_refund_rpc",
                {
                    "p_refund_id": int(refund_id),
                    "p_manager_id": approver_id,
                    "p_reason": reason,
                },
            )
            .execute()
        )
        
        data = result.data
        
        if isinstance(data, dict) and data.get("success") is True:
            ui.notify(f'Refund ID {refund_id} rejected successfully.', type='positive', position='top')
            dialog.close()
            
            if on_success:
                on_success()
        else:
            message = data.get("message") if isinstance(data, dict) else str(data)
            ui.notify(f'Rejection failed: {message}', type='error', position='top')
            dialog.close()
    
    except Exception as e:
        ui.notify(f'Rejection error: {e}', type='error', position='top')
        dialog.close()


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main refund approval page."""
    
    # Auth check
    user = require_login()
    
    if not user:
        ui.notify('Authentication required.', type='error', position='top')
        return
    
    # Role check
    try:
        role_id = int(user.get("role_id"))
    except (TypeError, ValueError):
        role_id = None
    
    if role_id not in ALLOWED_ROLE_IDS:
        ui.notify('⛔ Access Denied. Admin or Manager permission required.', type='error', position='top')
        return
    
    target = container or ui.column()
    
    with target:
        ui.label('✅ Refund Approval Center').classes('text-3xl font-bold mb-2')
        
        role_name = "Admin" if role_id == 1 else "Manager"
        ui.label(f'Authorized Approver: {role_name}').classes('text-gray-500 mb-4')
        
        # Load pending refunds
        try:
            response = (
                db()
                .table("refunds")
                .select("*")
                .eq("status", "PENDING")
                .order("id", desc=True)
                .execute()
            )
            
            refunds = response.data if response and hasattr(response, "data") and response.data else []
        
        except Exception as e:
            ui.notify(f'Error loading pending refunds: {e}', type='error', position='top')
            return
        
        # Empty state
        if not refunds:
            with ui.card().classes('w-full p-4 bg-green-50'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('check_circle').classes('text-green-500')
                    ui.label('✅ No Pending Refunds').classes('text-green-700 font-semibold')
            return
        
        # Summary
        total_pending = len(refunds)
        total_amount = sum(safe_float(refund.get("refund_amount")) for refund in refunds)
        
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-orange-50'):
                ui.label('Pending Refunds').classes('text-sm text-gray-600')
                ui.label(str(total_pending)).classes('text-3xl font-bold text-orange-700')
            
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-blue-50'):
                ui.label('Pending Amount').classes('text-sm text-gray-600')
                ui.label(f'{total_amount:,.0f} MMK').classes('text-3xl font-bold text-blue-700')
        
        ui.separator().classes('my-4')
        
        # Refund queue container
        queue_container = ui.column().classes('w-full')
        
        def refresh_queue():
            """Refresh refund queue."""
            queue_container.clear()
            
            # Reload refunds
            try:
                response = (
                    db()
                    .table("refunds")
                    .select("*")
                    .eq("status", "PENDING")
                    .order("id", desc=True)
                    .execute()
                )
                
                current_refunds = response.data if response and hasattr(response, "data") and response.data else []
            
            except Exception as e:
                ui.notify(f'Error loading refunds: {e}', type='error', position='top')
                return
            
            if not current_refunds:
                with queue_container:
                    with ui.card().classes('w-full p-4 bg-green-50'):
                        ui.label('✅ No Pending Refunds').classes('text-green-700 font-semibold')
                return
            
            with queue_container:
                for refund in current_refunds:
                    build_refund_card(refund, user["id"], refresh_queue)
        
        def build_refund_card(refund: Dict[str, Any], approver_id: Any, on_success: callable):
            """Build individual refund card."""
            refund_id = refund.get("id")
            sale_id = refund.get("sale_id")
            refund_amount = safe_float(refund.get("refund_amount"))
            refund_date = refund.get("refund_date") or "-"
            reason = refund.get("reason") or "-"
            
            with ui.card().classes('w-full p-4 mb-4 border border-orange-200'):
                # Header info
                with ui.row().classes('w-full gap-4 flex-wrap mb-3'):
                    with ui.column().classes('flex-1 min-w-[100px]'):
                        ui.label('Refund ID').classes('text-sm text-gray-500')
                        ui.label(str(refund_id)).classes('font-bold')
                    
                    with ui.column().classes('flex-1 min-w-[100px]'):
                        ui.label('Sale ID').classes('text-sm text-gray-500')
                        ui.label(str(sale_id)).classes('font-bold')
                    
                    with ui.column().classes('flex-1 min-w-[150px]'):
                        ui.label('Refund Amount').classes('text-sm text-gray-500')
                        ui.label(f'{refund_amount:,.0f} MMK').classes('font-bold text-orange-600')
                    
                    with ui.column().classes('flex-1 min-w-[150px]'):
                        ui.label('Refund Date').classes('text-sm text-gray-500')
                        ui.label(str(refund_date)).classes('text-sm')
                
                # Reason
                ui.label('Reason:').classes('text-sm text-gray-500')
                ui.label(reason).classes('mb-3 text-gray-700')
                
                # Status
                with ui.card().classes('w-full p-3 bg-orange-50 mb-3'):
                    ui.label('⏳ PENDING — Waiting for Manager Approval').classes('text-orange-700')
                
                ui.separator().classes('my-2')
                
                # Actions
                with ui.row().classes('w-full gap-2'):
                    approve_btn = ui.button(
                        '✅ Approve Refund',
                        on_click=lambda: handle_approval(
                            refund_id,
                            approver_id,
                            approve_btn,
                            on_success
                        )
                    ).classes('flex-1 bg-green-500 text-white')
                    
                    reject_btn = ui.button(
                        '❌ Reject Refund',
                        on_click=lambda: show_reject_dialog(
                            refund,
                            approver_id,
                            on_success
                        )
                    ).classes('flex-1 bg-red-500 text-white')
        
        # Initial render
        refresh_queue()


# ==============================================================================
# ADVANCED VIEW WITH TABS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced view with tabs for pending and history."""
    
    user = require_login()
    
    if not user:
        return
    
    try:
        role_id = int(user.get("role_id"))
    except:
        role_id = None
    
    if role_id not in ALLOWED_ROLE_IDS:
        ui.notify('⛔ Access Denied', type='error', position='top')
        return
    
    target = container or ui.column()
    
    with target:
        ui.label('✅ Refund Approval Center').classes('text-3xl font-bold mb-4')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_pending = ui.tab('⏳ Pending', icon='pending')
            tab_approved = ui.tab('✅ Approved', icon='check_circle')
            tab_rejected = ui.tab('❌ Rejected', icon='cancel')
        
        with ui.tab_panels(tabs, value=tab_pending).classes('w-full'):
            with ui.tab_panel(tab_pending):
                run(target)
            
            with ui.tab_panel(tab_approved):
                render_refund_history(target, "APPROVED")
            
            with ui.tab_panel(tab_rejected):
                render_refund_history(target, "REJECTED")


def render_refund_history(container: Any, status: str):
    """Render refund history by status."""
    container.clear()
    
    try:
        response = (
            db()
            .table("refunds")
            .select("*")
            .eq("status", status)
            .order("id", desc=True)
            .limit(50)
            .execute()
        )
        
        refunds = response.data if response and hasattr(response, "data") and response.data else []
    
    except Exception as e:
        ui.notify(f'Error loading history: {e}', type='error', position='top')
        return
    
    if not refunds:
        with container:
            ui.label(f'No {status.lower()} refunds').classes('text-gray-500')
        return
    
    with container:
        rows = []
        for refund in refunds:
            rows.append({
                "Refund ID": refund.get("id"),
                "Sale ID": refund.get("sale_id"),
                "Amount": f"{safe_float(refund.get('refund_amount')):,.0f} MMK",
                "Date": refund.get("refund_date") or "-",
                "Reason": refund.get("reason") or "-",
            })
        
        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in rows[0].keys()
        ]
        
        ui.table(columns=columns, rows=rows, row_key='Refund ID', pagination=10).classes('w-full')


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
