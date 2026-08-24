# ==============================================================================
# erp_pages/inventory/stock_adjustment.py
# ERP ENTERPRISE STOCK ADJUSTMENT v1.0
# NICE GUI VERSION
#
# Maker Checker Approval Component
#
# Responsibilities:
# - Stock Adjustment
# - Approval Queue
# - Approve / Cancel
# - Adjustment History
#
# ==============================================================================

from typing import Dict, Any, Optional, List, Callable
from nicegui import ui, app

from database import db
from utils.ui import show_table
from auth import get_current_user


# ==============================================================================
# MAIN COMPONENT
# ==============================================================================

def render_stock_adjustment(
    products: List[Dict[str, Any]],
    warehouse_id: Any,
    warehouse_name: str,
    inventory_service: Any,
    container: Optional[Any] = None
):
    """Render stock adjustment component.
    
    Args:
        products: List of products
        warehouse_id: Warehouse ID
        warehouse_name: Warehouse name
        inventory_service: Inventory service instance
        container: NiceGUI container
    """
    target = container or ui.column()
    
    with target:
        ui.label('🔧 Enterprise Stock Adjustment').classes('text-xl font-bold mb-4')
        
        # No products check
        if not products:
            ui.notify('No products available', type='warning', position='top')
            return
        
        # Product selector
        product_map = {
            f"{p.get('id')} | {p.get('name')}": p
            for p in products
        }
        
        product_select = ui.select(
            list(product_map.keys()),
            label='📦 Select Product',
        ).classes('w-full mb-4')
        
        # Dynamic containers
        product_info_container = ui.column().classes('w-full mb-4')
        form_container = ui.column().classes('w-full mb-4')
        approval_container = ui.column().classes('w-full mb-4')
        history_container = ui.column().classes('w-full')
        
        def load_product_details():
            """Load selected product details."""
            product_info_container.clear()
            form_container.clear()
            
            selected_product = product_map.get(product_select.value)
            
            if not selected_product:
                return
            
            product_id = int(selected_product.get('id'))
            current_qty = (
                selected_product.get('available_qty')
                or selected_product.get('qty')
                or selected_product.get('stock')
                or 0
            )
            
            # Product info
            with product_info_container:
                with ui.card().classes('w-full p-4 bg-blue-50'):
                    ui.label(f'📦 Product: {selected_product.get("name")}').classes('font-semibold mb-1')
                    ui.label(f'🏭 Warehouse: {warehouse_name}').classes('mb-1')
                    ui.label(f'📊 Current Stock: {current_qty}').classes('font-bold text-lg')
            
            # Adjustment form
            with form_container:
                with ui.card().classes('w-full p-4'):
                    adjustment_type = ui.select(
                        ['DAMAGE', 'COUNT_CORRECTION', 'MANUAL_IN', 'MANUAL_OUT'],
                        label='Adjustment Type',
                        value='COUNT_CORRECTION',
                    ).classes('w-full mb-2')
                    
                    qty_input = ui.number(
                        'Quantity (+/-)',
                        value=0,
                        step=1,
                    ).classes('w-full mb-2')
                    
                    reason_input = ui.input(
                        'Reason',
                        value='Manual Adjustment',
                    ).classes('w-full mb-4')
                    
                    submit_btn = ui.button(
                        '💾 Submit Adjustment',
                        on_click=lambda: handle_submit_adjustment(
                            selected_product,
                            product_id,
                            warehouse_id,
                            adjustment_type.value,
                            qty_input.value,
                            reason_input.value,
                            inventory_service,
                            submit_btn,
                            load_approval_queue
                        )
                    ).classes('w-full bg-primary text-white')
        
        def load_approval_queue():
            """Load approval queue and history."""
            approval_container.clear()
            history_container.clear()
            
            try:
                history = inventory_service.get_stock_adjustments(
                    warehouse_id=int(warehouse_id)
                )
                
                current_user = str(get_current_user().get('id', ''))
                
                pending_rows = [
                    x for x in history
                    if str(x.get('status', '')).upper() == 'PENDING'
                ]
                
                # Pending queue
                with approval_container:
                    ui.label('⏳ Pending Approval Queue').classes('text-lg font-bold mb-2')
                    
                    if not pending_rows:
                        with ui.card().classes('w-full p-3 bg-green-50'):
                            ui.label('No pending adjustments').classes('text-green-700')
                    else:
                        for row in pending_rows:
                            build_pending_card(row, current_user, inventory_service, load_approval_queue)
                
                # History
                with history_container:
                    ui.separator().classes('my-4')
                    ui.label('📜 Adjustment History').classes('text-lg font-bold mb-2')
                    
                    if history:
                        show_table(history, serial=True, pagination=20)
                    else:
                        ui.label('No adjustment history').classes('text-gray-500')
            
            except Exception as e:
                with approval_container:
                    ui.notify(f'Approval Load Error: {e}', type='error', position='top')
        
        # Wire up events
        product_select.on_value_change(lambda e: load_product_details())
        
        # Initial load
        load_product_details()
        load_approval_queue()


def build_pending_card(
    row: Dict[str, Any],
    current_user: str,
    inventory_service: Any,
    refresh_callback: Callable
):
    """Build individual pending adjustment card."""
    
    with ui.card().classes('w-full p-4 mb-2 border border-orange-200'):
        # Info
        ui.label(f"ID: {row['id']}").classes('font-semibold')
        ui.label(f"Product: {row.get('product_name', 'N/A')}").classes('text-sm')
        ui.label(f"Qty: {row.get('qty', 0)}").classes('text-sm')
        ui.label(f"Reason: {row.get('reason', 'N/A')}").classes('text-sm')
        ui.label(f"Requested By: {row.get('requested_by', 'N/A')}").classes('text-sm text-gray-500 mb-2')
        
        maker = str(row.get('requested_by', ''))
        
        with ui.row().classes('w-full gap-2'):
            # Approve button
            if current_user == maker:
                with ui.column().classes('flex-1'):
                    ui.label('🚫 Maker cannot approve').classes('text-sm text-orange-600 text-center')
            else:
                approve_btn = ui.button(
                    '✅ Approve',
                    on_click=lambda: handle_approve(
                        row.get('id'),
                        current_user,
                        inventory_service,
                        approve_btn,
                        refresh_callback
                    )
                ).classes('flex-1 bg-green-500 text-white')
            
            # Cancel button
            cancel_btn = ui.button(
                '❌ Cancel',
                on_click=lambda: handle_cancel(
                    row.get('id'),
                    current_user,
                    cancel_btn,
                    refresh_callback
                )
            ).classes('flex-1 bg-red-500 text-white')


def handle_submit_adjustment(
    selected_product: Dict,
    product_id: int,
    warehouse_id: Any,
    adjustment_type: str,
    qty: float,
    reason: str,
    inventory_service: Any,
    submit_btn: Any,
    refresh_callback: Callable
):
    """Handle adjustment submission."""
    try:
        if qty == 0:
            ui.notify('Quantity cannot be zero', type='warning', position='top')
            return
        
        submit_btn.disable()
        submit_btn.text = '⏳ Submitting...'
        
        user = get_current_user()
        
        result = inventory_service.adjust_stock(
            product_id=product_id,
            warehouse_id=int(warehouse_id),
            quantity=int(qty),
            reason=reason,
            created_by=user.get('id') if user else None,
            unit_cost=float(selected_product.get('purchase_price', 0)),
        )
        
        if result.get('success'):
            ui.notify('✅ Adjustment Submitted (PENDING)', type='positive', position='top')
            refresh_callback()
        else:
            ui.notify(result.get('message', 'Adjustment Failed'), type='error', position='top')
    
    except Exception as e:
        ui.notify(f'Adjustment Error: {e}', type='error', position='top')
    
    finally:
        submit_btn.enable()
        submit_btn.text = '💾 Submit Adjustment'


def handle_approve(
    adjustment_id: Any,
    manager_id: str,
    inventory_service: Any,
    approve_btn: Any,
    refresh_callback: Callable
):
    """Handle adjustment approval."""
    try:
        approve_btn.disable()
        approve_btn.text = '⏳ Approving...'
        
        result = inventory_service.approve_stock_adjustment(
            adjustment_id=int(adjustment_id),
            manager_id=manager_id,
        )
        
        if result.get('success'):
            ui.notify('Approved Successfully', type='positive', position='top')
            refresh_callback()
        else:
            ui.notify(result.get('message', 'Approve Failed'), type='error', position='top')
    
    except Exception as e:
        ui.notify(f'Approval Error: {e}', type='error', position='top')
    
    finally:
        approve_btn.enable()
        approve_btn.text = '✅ Approve'


def handle_cancel(
    adjustment_id: Any,
    user_id: str,
    cancel_btn: Any,
    refresh_callback: Callable
):
    """Handle adjustment cancellation."""
    try:
        cancel_btn.disable()
        cancel_btn.text = '⏳ Cancelling...'
        
        db().rpc(
            'cancel_stock_adjustment_rpc',
            {
                'p_adjustment_id': int(adjustment_id),
                'p_user_id': user_id,
            }
        ).execute()
        
        ui.notify('Cancelled', type='positive', position='top')
        refresh_callback()
    
    except Exception as e:
        ui.notify(f'Cancel Error: {e}', type='error', position='top')
    
    finally:
        cancel_btn.enable()
        cancel_btn.text = '❌ Cancel'


# ==============================================================================
# ADVANCED VIEW WITH TABS
# ==============================================================================

def render_stock_adjustment_advanced(
    products: List[Dict[str, Any]],
    warehouse_id: Any,
    warehouse_name: str,
    inventory_service: Any,
    container: Optional[Any] = None
):
    """Render stock adjustment with tabs."""
    
    target = container or ui.column()
    
    with target:
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_adjust = ui.tab('🔧 Adjust', icon='tune')
            tab_pending = ui.tab('⏳ Pending', icon='pending')
            tab_history = ui.tab('📜 History', icon='history')
        
        with ui.tab_panels(tabs, value=tab_adjust).classes('w-full'):
            with ui.tab_panel(tab_adjust):
                render_adjustment_form(products, warehouse_id, warehouse_name, inventory_service)
            
            with ui.tab_panel(tab_pending):
                render_pending_queue(warehouse_id, inventory_service)
            
            with ui.tab_panel(tab_history):
                render_history(warehouse_id, inventory_service)


def render_adjustment_form(products, warehouse_id, warehouse_name, inventory_service):
    """Render adjustment form only."""
    if not products:
        ui.label('No products available').classes('text-gray-500')
        return
    
    product_map = {
        f"{p.get('id')} | {p.get('name')}": p
        for p in products
    }
    
    product_select = ui.select(list(product_map.keys()), label='Product').classes('w-full mb-2')
    
    form_container = ui.column().classes('w-full')
    
    def load_form():
        form_container.clear()
        product = product_map.get(product_select.value)
        
        if not product:
            return
        
        with form_container:
            with ui.card().classes('w-full p-4'):
                ui.label(f'Current Stock: {product.get("available_qty", 0)}').classes('font-bold mb-2')
                
                adjustment_type = ui.select(
                    ['DAMAGE', 'COUNT_CORRECTION', 'MANUAL_IN', 'MANUAL_OUT'],
                    label='Type',
                ).classes('w-full mb-2')
                
                qty = ui.number('Quantity', value=0, step=1).classes('w-full mb-2')
                reason = ui.input('Reason', value='Manual Adjustment').classes('w-full mb-4')
                
                submit_btn = ui.button(
                    'Submit',
                    on_click=lambda: handle_submit_adjustment(
                        product,
                        int(product.get('id')),
                        warehouse_id,
                        adjustment_type.value,
                        qty.value,
                        reason.value,
                        inventory_service,
                        submit_btn,
                        load_form
                    )
                ).classes('w-full bg-primary text-white')
    
    product_select.on_value_change(lambda e: load_form())
    load_form()


def render_pending_queue(warehouse_id, inventory_service):
    """Render pending approval queue only."""
    try:
        history = inventory_service.get_stock_adjustments(warehouse_id=int(warehouse_id))
        current_user = str(get_current_user().get('id', ''))
        
        pending = [x for x in history if str(x.get('status', '')).upper() == 'PENDING']
        
        if not pending:
            ui.label('No pending adjustments').classes('text-gray-500')
            return
        
        for row in pending:
            build_pending_card(row, current_user, inventory_service, lambda: render_pending_queue(warehouse_id, inventory_service))
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')


def render_history(warehouse_id, inventory_service):
    """Render adjustment history only."""
    try:
        history = inventory_service.get_stock_adjustments(warehouse_id=int(warehouse_id))
        
        if history:
            show_table(history, serial=True, pagination=20)
        else:
            ui.label('No adjustment history').classes('text-gray-500')
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Test with mock data if needed
    pass
