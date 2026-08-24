# ==============================================================================
# erp_pages/5_Refund.py
# ERP ENTERPRISE REFUND SYSTEM
# NICE GUI VERSION
#
# Maker-Checker Refund Workflow
# ==============================================================================

from typing import Dict, Any, Optional, List
from nicegui import ui, app

from auth import require_login
from database import db


# ==============================================================================
# SAFE NUMBER HELPERS
# ==============================================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer."""
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def normalize_status(value: Any) -> str:
    """Normalize status string."""
    return str(value or "").strip().upper()


# ==============================================================================
# SESSION STATE
# ==============================================================================

class RefundState:
    """Session state for refund system."""
    
    def __init__(self):
        self.selected_sale: Optional[Dict[str, Any]] = None
        self.refund_cart: List[Dict[str, Any]] = []
        self.refund_reason: str = ""


def get_state() -> RefundState:
    """Get or create refund state."""
    client_id = app.context.client.id if app.context.client else 'default'
    
    if not hasattr(app.storage, 'refund_state'):
        app.storage.refund_state = {}
    
    if client_id not in app.storage.refund_state:
        app.storage.refund_state[client_id] = RefundState()
    
    return app.storage.refund_state[client_id]


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main refund system page."""
    
    user = require_login()
    
    if not user:
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        ui.label('↩️ Refund System').classes('text-3xl font-bold mb-2')
        ui.label('ERP Enterprise Maker-Checker Refund Workflow').classes('text-gray-500 mb-4')
        
        # ======================================================================
        # SEARCH SECTION
        # ======================================================================
        
        ui.label('🔍 Search Sale').classes('text-xl font-bold mb-2')
        
        with ui.row().classes('w-full gap-2 items-end mb-4'):
            sale_input = ui.input(
                'Enter Sale ID',
                placeholder='Enter Sale ID',
            ).classes('flex-1')
            
            search_btn = ui.button(
                '🔎 Search Sale',
                on_click=lambda: handle_search(sale_input.value, state, search_btn)
            ).classes('bg-primary text-white')
            
            clear_btn = ui.button(
                '🧹 Clear',
                on_click=lambda: clear_state(state)
            ).classes('bg-gray-500 text-white')
        
        # ======================================================================
        # DYNAMIC CONTAINERS
        # ======================================================================
        
        content_container = ui.column().classes('w-full')
        
        def handle_search(sale_id_str: str, state: RefundState, search_btn: Any):
            """Handle sale search."""
            try:
                if not sale_id_str or not sale_id_str.isdigit():
                    ui.notify('Please enter a valid numeric Sale ID.', type='warning', position='top')
                    return
                
                sale_id = int(sale_id_str)
                search_btn.disable()
                search_btn.text = '⏳ Searching...'
                
                # Load sale
                sale_response = (
                    db()
                    .table("sales")
                    .select("*")
                    .eq("id", sale_id)
                    .execute()
                )
                
                sale_data = sale_response.data if sale_response else []
                
                if not sale_data:
                    ui.notify(f'Sale ID {sale_id} not found.', type='error', position='top')
                    state.selected_sale = None
                    return
                
                sale = sale_data[0]
                
                # Load sale items
                items_response = (
                    db()
                    .table("sale_items")
                    .select("*")
                    .eq("sale_id", sale_id)
                    .order("id")
                    .execute()
                )
                
                sale_items = items_response.data if items_response else []
                sale["items"] = sale_items
                
                # Load refunds
                refunds_response = (
                    db()
                    .table("refunds")
                    .select("id,sale_id,status,refund_amount,reason,cashier_id,approved_by,approved_at")
                    .eq("sale_id", sale_id)
                    .execute()
                )
                
                refunds = refunds_response.data if refunds_response else []
                
                # Load refund items
                refund_items = []
                if refunds:
                    refund_ids = [r.get("id") for r in refunds if r.get("id") is not None]
                    if refund_ids:
                        refund_items_response = (
                            db()
                            .table("refund_items")
                            .select("refund_id,sale_item_id,product_id,quantity,unit_price,total")
                            .in_("refund_id", refund_ids)
                            .execute()
                        )
                        refund_items = refund_items_response.data if refund_items_response else []
                
                # Build refund history
                refund_map = {r.get("id"): r for r in refunds if r.get("id") is not None}
                refund_history = []
                
                for refund_item in refund_items:
                    refund_id = refund_item.get("refund_id")
                    refund_master = refund_map.get(refund_id, {})
                    
                    refund_history.append({
                        "refund_id": refund_id,
                        "sale_item_id": refund_item.get("sale_item_id"),
                        "product_id": refund_item.get("product_id"),
                        "quantity": safe_int(refund_item.get("quantity")),
                        "status": normalize_status(refund_master.get("status")),
                        "refund_amount": safe_float(refund_master.get("refund_amount")),
                        "reason": refund_master.get("reason"),
                    })
                
                sale["refund_history"] = refund_history
                
                # Load product names
                product_ids = [item.get("product_id") for item in sale_items if item.get("product_id") is not None]
                product_map = {}
                
                if product_ids:
                    unique_ids = list(dict.fromkeys(product_ids))
                    products_response = (
                        db()
                        .table("products")
                        .select("id,name")
                        .in_("id", unique_ids)
                        .execute()
                    )
                    
                    products_data = products_response.data if products_response else []
                    for product in products_data:
                        product_map[product.get("id")] = product.get("name")
                
                # Attach product names
                for item in sale_items:
                    product_id = item.get("product_id")
                    item["display_product_name"] = (
                        product_map.get(product_id)
                        or item.get("product_name")
                        or f"Product #{product_id}"
                    )
                
                state.selected_sale = sale
                state.refund_cart = []
                
                render_sale_details(content_container, state, user)
                
            except Exception as e:
                ui.notify(f'Database Query Error: {e}', type='error', position='top')
            
            finally:
                search_btn.enable()
                search_btn.text = '🔎 Search Sale'
        
        def clear_state(state: RefundState):
            """Clear refund state."""
            state.selected_sale = None
            state.refund_cart = []
            state.refund_reason = ""
            content_container.clear()
            sale_input.value = ""
            ui.notify('Cleared', type='info', position='top')
        
        # Initial state
        if state.selected_sale:
            render_sale_details(content_container, state, user)


def render_sale_details(container: Any, state: RefundState, user: Dict[str, Any]):
    """Render sale details and refund selection."""
    container.clear()
    
    sale = state.selected_sale
    
    if not sale:
        return
    
    sale_id = sale.get("id")
    invoice_no = sale.get("invoice_no") or sale.get("invoice") or "-"
    sale_date = sale.get("created_at") or "-"
    original_total = safe_float(sale.get("total", sale.get("total_amount", 0)))
    
    with container:
        ui.separator().classes('my-4')
        ui.label('🧾 Sale Information').classes('text-xl font-bold mb-4')
        
        # Sale info cards
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                ui.label('Sale ID').classes('text-sm text-gray-600')
                ui.label(str(sale_id)).classes('text-lg font-bold')
            
            with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                ui.label('Invoice No').classes('text-sm text-gray-600')
                ui.label(str(invoice_no)).classes('text-lg font-bold')
            
            with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                ui.label('Sale Date').classes('text-sm text-gray-600')
                ui.label(str(sale_date)).classes('text-sm')
            
            with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                ui.label('Original Total').classes('text-sm text-gray-600')
                ui.label(f'{original_total:,.0f} MMK').classes('text-lg font-bold text-green-700')
        
        # Refund history warnings
        refund_history = sale.get("refund_history", [])
        pending_refunds = [r for r in refund_history if normalize_status(r.get("status")) == "PENDING"]
        approved_refunds = [r for r in refund_history if normalize_status(r.get("status")) in ("APPROVED", "COMPLETED")]
        
        if pending_refunds:
            with ui.card().classes('w-full p-3 bg-orange-50 mb-2'):
                ui.label(f'⏳ This sale has {len(pending_refunds)} pending refund item(s).').classes('text-orange-700')
        
        if approved_refunds:
            with ui.card().classes('w-full p-3 bg-blue-50 mb-4'):
                ui.label(f'✅ {len(approved_refunds)} refund item(s) approved.').classes('text-blue-700')
        
        ui.separator().classes('my-4')
        ui.label('📦 Select Refund Items').classes('text-xl font-bold mb-4')
        
        # Items selection
        items_container = ui.column().classes('w-full')
        cart = []
        estimated_total = 0.0
        selected_qty_total = 0
        
        for item in sale.get("items", []):
            item_id = item.get("id")
            product_id = item.get("product_id")
            qty_sold = safe_int(item.get("quantity", item.get("qty", 0)))
            price = safe_float(item.get("unit_price", item.get("selling_price", 0)))
            product_name = item.get("display_product_name") or f"Product #{product_id}"
            
            # Calculate refunded quantities
            completed_qty = 0
            pending_qty = 0
            
            for refund in refund_history:
                refund_sale_item_id = refund.get("sale_item_id")
                
                if refund_sale_item_id is not None:
                    if safe_int(refund_sale_item_id) != safe_int(item_id):
                        continue
                else:
                    if refund.get("product_id") != product_id:
                        continue
                
                status = normalize_status(refund.get("status"))
                refund_qty = safe_int(refund.get("quantity"))
                
                if status in ("APPROVED", "COMPLETED"):
                    completed_qty += refund_qty
                elif status == "PENDING":
                    pending_qty += refund_qty
            
            available_qty = max(0, qty_sold - completed_qty - pending_qty)
            
            with items_container:
                with ui.card().classes('w-full p-3 mb-2'):
                    with ui.row().classes('w-full items-center gap-4 flex-wrap'):
                        # Product name
                        with ui.column().classes('flex-1 min-w-[200px]'):
                            ui.label(product_name).classes('font-bold')
                            
                            if completed_qty > 0:
                                ui.label(f'Approved: {completed_qty}').classes('text-sm text-green-600')
                            if pending_qty > 0:
                                ui.label(f'Pending: {pending_qty}').classes('text-sm text-orange-600')
                        
                        # Sold qty
                        with ui.column().classes('min-w-[80px]'):
                            ui.label('Sold').classes('text-sm text-gray-500')
                            ui.label(str(qty_sold)).classes('font-semibold')
                        
                        # Price
                        with ui.column().classes('min-w-[100px]'):
                            ui.label('Price').classes('text-sm text-gray-500')
                            ui.label(f'{price:,.0f}').classes('font-semibold')
                        
                        # Refund qty input
                        with ui.column().classes('min-w-[150px]'):
                            if available_qty <= 0:
                                if completed_qty >= qty_sold:
                                    ui.badge('✅ Already Refunded').classes('bg-green-100 text-green-700')
                                elif pending_qty >= qty_sold:
                                    ui.badge('⏳ Refund Pending').classes('bg-orange-100 text-orange-700')
                                else:
                                    ui.badge('No Refund Available').classes('bg-gray-100 text-gray-700')
                                
                                qty = 0
                            else:
                                qty_input = ui.number(
                                    'Refund Qty',
                                    min=0,
                                    max=available_qty,
                                    value=0,
                                    step=1,
                                ).classes('w-full')
                                qty = qty_input.value or 0
                        
                        # Add to cart
                        if qty > 0:
                            selected_qty_total += int(qty)
                            estimated_total += float(qty) * price
                            cart.append({"sale_item_id": int(item_id), "qty": int(qty)})
        
        state.refund_cart = cart
        
        # Summary
        ui.separator().classes('my-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap items-center mb-4'):
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-blue-50'):
                ui.label('Estimated Refund').classes('text-sm text-gray-600')
                ui.label(f'{estimated_total:,.0f} MMK').classes('text-2xl font-bold text-blue-700')
            
            with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                ui.label('Selected Qty').classes('text-sm text-gray-600')
                ui.label(str(selected_qty_total)).classes('text-xl font-bold')
            
            with ui.card().classes('p-4 flex-1 min-w-[150px]'):
                ui.label('Items').classes('text-sm text-gray-600')
                ui.label(str(len(cart))).classes('text-xl font-bold')
        
        # Reason input
        reason_input = ui.input(
            'Reason for Refund',
            placeholder='Enter refund reason...',
            value=state.refund_reason,
        ).classes('w-full mb-4')
        
        # Submit button
        submit_btn = ui.button(
            '↩️ Submit Refund Request',
            on_click=lambda: handle_submit_refund(
                state, reason_input.value, user, submit_btn
            )
        ).classes('w-full bg-primary text-white font-semibold py-2')


def handle_submit_refund(state: RefundState, reason: str, user: Dict[str, Any], submit_btn: Any):
    """Handle refund request submission."""
    try:
        if not state.refund_cart:
            ui.notify('No items selected for refund.', type='error', position='top')
            return
        
        reason_clean = str(reason or "").strip()
        
        if not reason_clean:
            ui.notify('Please enter a refund reason.', type='error', position='top')
            return
        
        submit_btn.disable()
        submit_btn.text = '⏳ Submitting...'
        
        result = (
            db()
            .rpc(
                "refund_sale_rpc",
                {
                    "p_sale_id": int(state.selected_sale["id"]),
                    "p_items": state.refund_cart,
                    "p_reason": reason_clean,
                    "p_cashier_id": user["id"],
                },
            )
            .execute()
        )
        
        res_data = result.data
        
        # Parse response
        success = False
        refund_id = None
        refund_total = None
        message = None
        
        if isinstance(res_data, dict):
            success = bool(res_data.get("success"))
            refund_id = res_data.get("refund_id")
            refund_total = res_data.get("refund_total")
            message = res_data.get("message")
        elif isinstance(res_data, list) and res_data:
            first = res_data[0]
            if isinstance(first, dict):
                success = bool(first.get("success"))
                refund_id = first.get("refund_id")
                refund_total = first.get("refund_total")
                message = first.get("message")
        
        if success:
            ui.notify('✅ Refund Request Created Successfully', type='positive', position='top')
            
            if refund_id is not None:
                ui.notify(f'Refund ID: {refund_id}', type='info', position='top')
            
            if refund_total is not None:
                ui.notify(f'Refund Total: {safe_float(refund_total):,.0f} MMK', type='info', position='top')
            
            # Clear state
            state.refund_cart = []
            state.selected_sale = None
            state.refund_reason = ""
            
        else:
            ui.notify(f'Refund failed: {message or res_data}', type='error', position='top')
    
    except Exception as e:
        ui.notify(f'Refund RPC Error: {e}', type='error', position='top')
    
    finally:
        submit_btn.enable()
        submit_btn.text = '↩️ Submit Refund Request'


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
