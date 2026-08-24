# ==============================================================================
# erp_pages/8_Transfer.py
# ERP ENTERPRISE WAREHOUSE TRANSFER v32
# NICE GUI VERSION
#
# MAKER-CHECKER ENABLED
# ==============================================================================

from typing import Dict, Any, Optional, List
from nicegui import ui, app

from erp_core.base_repo import db, log_error
from erp_core.loaders.warehouse_loader import get_warehouses

from auth import get_current_user


# ==============================================================================
# SESSION STATE
# ==============================================================================

class TransferState:
    """Session state for warehouse transfer."""
    
    def __init__(self):
        self.last_result: Optional[Dict[str, Any]] = None


def get_state() -> TransferState:
    """Get or create transfer state."""
    client_id = app.context.client.id if app.context.client else 'default'
    
    if not hasattr(app.storage, 'transfer_state'):
        app.storage.transfer_state = {}
    
    if client_id not in app.storage.transfer_state:
        app.storage.transfer_state[client_id] = TransferState()
    
    return app.storage.transfer_state[client_id]


# ==============================================================================
# REQUEST TRANSFER
# ==============================================================================

def create_transfer_request(
    client,
    current_user_id,
    source_warehouse_id,
    destination_warehouse_id,
    product_id,
    quantity,
    notes=None,
) -> bool:
    """Create warehouse transfer request."""
    try:
        response = (
            client.rpc(
                "create_warehouse_transfer_request_rpc",
                {
                    "p_source_warehouse_id": int(source_warehouse_id),
                    "p_destination_warehouse_id": int(destination_warehouse_id),
                    "p_product_id": int(product_id),
                    "p_quantity": float(quantity),
                    "p_maker_id": str(current_user_id),
                    "p_notes": notes,
                },
            )
            .execute()
        )
        
        result = response.data
        
        if isinstance(result, list):
            result = result[0] if result else None
        
        if not isinstance(result, dict):
            ui.notify('❌ Invalid transfer RPC response.', type='error', position='top')
            return False
        
        if not result.get("success"):
            ui.notify(result.get("message", "Transfer request failed."), type='error', position='top')
            return False
        
        # Store result
        state = get_state()
        state.last_result = {
            "success": True,
            "request_id": result.get("request_id", "-"),
            "status": result.get("status", "PENDING"),
            "quantity": result.get("quantity", quantity),
            "source_warehouse_id": result.get("source_warehouse_id", source_warehouse_id),
            "destination_warehouse_id": result.get("destination_warehouse_id", destination_warehouse_id),
            "product_id": result.get("product_id", product_id),
            "message": result.get("message", "Transfer request created."),
        }
        
        return True
    
    except Exception as e:
        log_error(message="Warehouse transfer request failed.", exception=e)
        ui.notify(f'❌ Failed to create transfer request: {e}', type='error', position='top')
        return False


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main warehouse transfer page."""
    
    target = container or ui.column()
    
    with target:
        ui.label('🔁 Enterprise Warehouse Transfer').classes('text-3xl font-bold mb-2')
        ui.label('Maker-Checker Controlled Warehouse Transfer').classes('text-gray-500 mb-4')
        
        current_user = get_current_user()
        
        if not current_user:
            ui.notify('🔒 Login required.', type='error', position='top')
            return
        
        current_user_id = current_user.get("id")
        
        if not current_user_id:
            ui.notify('Current user ID is missing.', type='error', position='top')
            return
        
        # Tabs
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_request = ui.tab('📤 Transfer Request', icon='send')
            tab_approval = ui.tab('🟡 Transfer Approval', icon='approval')
        
        with ui.tab_panels(tabs, value=tab_request).classes('w-full'):
            # Request tab
            with ui.tab_panel(tab_request):
                render_transfer_request(target, current_user_id)
                render_last_result(target)
            
            # Approval tab
            with ui.tab_panel(tab_approval):
                try:
                    from erp_pages.inventory.warehouse_transfer_approval import (
                        render_warehouse_transfer_approval_queue,
                    )
                    render_warehouse_transfer_approval_queue(target)
                except ImportError:
                    ui.label('Approval queue module not available').classes('text-gray-500')


def render_last_result(container: Any):
    """Render last transfer request result."""
    state = get_state()
    result = state.last_result
    
    if not result:
        return
    
    with container:
        ui.separator().classes('my-4')
        ui.label('📌 Latest Transfer Request').classes('text-xl font-bold mb-4')
        
        if result.get("success"):
            with ui.card().classes('w-full p-4 bg-green-50 border border-green-200 mb-4'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('check_circle').classes('text-green-500')
                    ui.label('✅ Transfer request created successfully.').classes('text-green-700 font-semibold')
            
            with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                    ui.label('Request ID').classes('text-sm text-gray-600')
                    ui.label(f"#{result.get('request_id')}").classes('text-xl font-bold')
                
                with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                    ui.label('Status').classes('text-sm text-gray-600')
                    ui.label(result.get("status", "PENDING")).classes('text-xl font-bold text-orange-600')
                
                with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                    ui.label('Quantity').classes('text-sm text-gray-600')
                    ui.label(str(result.get("quantity", 0))).classes('text-xl font-bold')
            
            with ui.card().classes('w-full p-4 bg-yellow-50 border border-yellow-200 mb-4'):
                ui.label('🟡 STATUS: PENDING').classes('font-bold text-yellow-700 mb-2')
                ui.label('Stock has NOT been moved yet.').classes('text-yellow-600')
                ui.label('This transfer is waiting for Checker approval.').classes('text-yellow-600')
            
            ui.label(f'Source Warehouse: {result.get("source_warehouse_id")}').classes('text-sm text-gray-600')
            ui.label(f'Destination Warehouse: {result.get("destination_warehouse_id")}').classes('text-sm text-gray-600')
            ui.label(f'Product ID: {result.get("product_id")}').classes('text-sm text-gray-600')
            
            ui.label('Maker → Pending → Checker Approval → Stock Movement').classes('text-xs text-gray-400 mt-2')


def render_transfer_request(container: Any, current_user_id: str):
    """Render transfer request form."""
    
    with container:
        ui.label('🚚 Create Warehouse Transfer').classes('text-xl font-bold mb-4')
        
        # Load warehouses
        try:
            warehouses = get_warehouses()
        except Exception as e:
            ui.notify('Warehouse loading failed.', type='error', position='top')
            return
        
        if not warehouses:
            ui.notify('No warehouses found.', type='warning', position='top')
            return
        
        warehouse_options = {}
        for warehouse in warehouses:
            try:
                warehouse_id = int(warehouse.get("id"))
            except Exception:
                continue
            
            code = warehouse.get("code") or "N/A"
            name = warehouse.get("name") or "Unknown"
            
            warehouse_options[warehouse_id] = f"[{warehouse_id}] {code} - {name}"
        
        if len(warehouse_options) < 2:
            ui.notify('At least two warehouses are required.', type='warning', position='top')
            return
        
        # Source/Destination selection
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.column().classes('flex-1 min-w-[250px]'):
                source_id = ui.select(
                    list(warehouse_options.keys()),
                    label='Source Warehouse',
                    format_func=lambda x: warehouse_options[x],
                ).classes('w-full')
            
            with ui.column().classes('flex-1 min-w-[250px]'):
                destination_list = [x for x in warehouse_options.keys() if x != source_id.value]
                destination_id = ui.select(
                    destination_list,
                    label='Destination Warehouse',
                    format_func=lambda x: warehouse_options[x],
                ).classes('w-full')
        
        # Update destination when source changes
        def update_destination():
            dest_list = [x for x in warehouse_options.keys() if x != source_id.value]
            destination_id.options = dest_list
            if destination_id.value not in dest_list and dest_list:
                destination_id.value = dest_list[0]
        
        source_id.on_value_change(lambda e: update_destination())
        
        # Load stock for source warehouse
        try:
            client = db()
            stock_rows = (
                client
                .table("warehouse_stock")
                .select("product_id, qty, available_qty")
                .eq("warehouse_id", int(source_id.value))
                .gt("available_qty", 0)
                .execute()
                .data
                or []
            )
        except Exception as e:
            ui.notify(f'Source stock loading failed: {e}', type='error', position='top')
            return
        
        if not stock_rows:
            ui.notify('Source warehouse has no available stock.', type='warning', position='top')
            return
        
        # Load products
        product_ids = []
        for row in stock_rows:
            try:
                product_ids.append(int(row["product_id"]))
            except Exception:
                pass
        
        if not product_ids:
            ui.notify('No valid products found.', type='warning', position='top')
            return
        
        try:
            products = (
                client
                .table("products")
                .select("id,name,sku")
                .in_("id", product_ids)
                .execute()
                .data
                or []
            )
        except Exception as e:
            ui.notify(f'Product loading failed: {e}', type='error', position='top')
            return
        
        product_options = {}
        for product in products:
            try:
                product_id = int(product["id"])
            except Exception:
                continue
            
            name = product.get("name") or "Unnamed Product"
            sku = product.get("sku") or "-"
            
            product_options[product_id] = f"{name} (SKU: {sku})"
        
        if not product_options:
            ui.notify('No products available for transfer.', type='warning', position='top')
            return
        
        # Product selection
        selected_product_id = ui.select(
            list(product_options.keys()),
            label='Select Product',
            format_func=lambda x: product_options[x],
        ).classes('w-full mb-4')
        
        # Dynamic stock display
        stock_display = ui.column().classes('w-full mb-4')
        
        def update_stock_display():
            stock_display.clear()
            
            # Source stock
            source_stock = next(
                (row for row in stock_rows if int(row["product_id"]) == int(selected_product_id.value)),
                None
            )
            
            if not source_stock:
                ui.notify('Source stock record not found.', type='error', position='top')
                return
            
            source_qty = float(source_stock.get("qty", 0) or 0)
            source_available = float(source_stock.get("available_qty", 0) or 0)
            
            # Destination stock
            try:
                dest_rows = (
                    client
                    .table("warehouse_stock")
                    .select("qty,available_qty")
                    .eq("warehouse_id", int(destination_id.value))
                    .eq("product_id", int(selected_product_id.value))
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                
                if dest_rows:
                    dest_qty = float(dest_rows[0].get("qty", 0) or 0)
                    dest_available = float(dest_rows[0].get("available_qty", 0) or 0)
                else:
                    dest_qty = 0
                    dest_available = 0
            except Exception:
                dest_qty = 0
                dest_available = 0
            
            with stock_display:
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    with ui.card().classes('p-4 flex-1 min-w-[250px] bg-blue-50'):
                        ui.label('📤 SOURCE STOCK').classes('font-bold mb-2')
                        ui.label(f'Warehouse: {warehouse_options[source_id.value]}').classes('text-sm')
                        ui.label(f'Product: {product_options[selected_product_id.value]}').classes('text-sm')
                        ui.label(f'Current Qty: {source_qty:g}').classes('text-sm')
                        ui.label(f'Available Qty: {source_available:g}').classes('text-sm font-bold')
                    
                    with ui.card().classes('p-4 flex-1 min-w-[250px] bg-green-50'):
                        ui.label('📥 DESTINATION STOCK').classes('font-bold mb-2')
                        ui.label(f'Warehouse: {warehouse_options[destination_id.value]}').classes('text-sm')
                        ui.label(f'Product: {product_options[selected_product_id.value]}').classes('text-sm')
                        ui.label(f'Current Qty: {dest_qty:g}').classes('text-sm')
                        ui.label(f'Available Qty: {dest_available:g}').classes('text-sm font-bold')
        
        selected_product_id.on_value_change(lambda e: update_stock_display())
        update_stock_display()
        
        # Transfer quantity
        source_stock = next(
            (row for row in stock_rows if int(row["product_id"]) == int(selected_product_id.value)),
            None
        )
        source_available = float(source_stock.get("available_qty", 0) or 0) if source_stock else 0
        
        transfer_qty = ui.number(
            'Transfer Quantity',
            min=1.0,
            max=float(source_available) if source_available > 0 else 1.0,
            value=1.0,
            step=1.0,
        ).classes('w-full mb-4')
        
        notes = ui.textarea(
            'Transfer Note (Optional)',
            placeholder='Reason / remark for warehouse transfer',
        ).classes('w-full mb-4')
        
        # Preview
        ui.label('📊 Transfer Preview').classes('font-bold mb-2')
        
        preview_container = ui.column().classes('w-full mb-4')
        
        def update_preview():
            preview_container.clear()
            
            source_stock = next(
                (row for row in stock_rows if int(row["product_id"]) == int(selected_product_id.value)),
                None
            )
            source_qty = float(source_stock.get("qty", 0) or 0) if source_stock else 0
            
            try:
                dest_rows = (
                    client
                    .table("warehouse_stock")
                    .select("qty")
                    .eq("warehouse_id", int(destination_id.value))
                    .eq("product_id", int(selected_product_id.value))
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                dest_qty = float(dest_rows[0].get("qty", 0) or 0) if dest_rows else 0
            except Exception:
                dest_qty = 0
            
            qty = transfer_qty.value or 0
            
            with preview_container:
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                        ui.label('After Approval - Source Stock').classes('text-sm text-gray-600')
                        ui.label(f'{source_qty - qty:g}').classes('text-2xl font-bold')
                        ui.label(f'-{qty:g}').classes('text-sm text-red-600')
                    
                    with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                        ui.label('After Approval - Destination Stock').classes('text-sm text-gray-600')
                        ui.label(f'{dest_qty + qty:g}').classes('text-2xl font-bold')
                        ui.label(f'+{qty:g}').classes('text-sm text-green-600')
        
        transfer_qty.on_value_change(lambda e: update_preview())
        update_preview()
        
        # Warning
        with ui.card().classes('w-full p-4 bg-orange-50 border border-orange-200 mb-4'):
            ui.label('⚠️ Maker-Checker Control').classes('font-bold text-orange-700 mb-2')
            ui.label('This action creates a PENDING transfer request only.').classes('text-orange-600')
            ui.label('Stock will NOT move now.').classes('text-orange-600')
            ui.label('Stock will move only after a different Checker approves the request.').classes('text-orange-600')
        
        # Submit button
        submit_btn = ui.button(
            '📤 Submit Transfer Request',
            on_click=lambda: handle_submit_transfer(
                client,
                current_user_id,
                source_id.value,
                destination_id.value,
                selected_product_id.value,
                transfer_qty.value,
                notes.value,
                submit_btn,
            )
        ).classes('w-full bg-primary text-white font-semibold py-2')


def handle_submit_transfer(
    client,
    current_user_id,
    source_warehouse_id,
    destination_warehouse_id,
    product_id,
    quantity,
    notes,
    submit_btn,
):
    """Handle transfer request submission."""
    try:
        if int(source_warehouse_id) == int(destination_warehouse_id):
            ui.notify('Source and destination warehouses must be different.', type='error', position='top')
            return
        
        if quantity <= 0:
            ui.notify('Transfer quantity must be greater than zero.', type='error', position='top')
            return
        
        submit_btn.disable()
        submit_btn.text = '⏳ Submitting...'
        
        success = create_transfer_request(
            client=client,
            current_user_id=current_user_id,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            product_id=product_id,
            quantity=quantity,
            notes=notes,
        )
        
        if success:
            ui.notify('Transfer request submitted successfully', type='positive', position='top')
    
    except Exception as e:
        ui.notify(f'Transfer error: {e}', type='error', position='top')
    
    finally:
        submit_btn.enable()
        submit_btn.text = '📤 Submit Transfer Request'


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
