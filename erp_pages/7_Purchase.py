# ==============================================================================
# erp_pages/7_Purchase.py
# ERP ENTERPRISE PURCHASE RECEIVE v4.0
# NICE GUI VERSION
# ==============================================================================

from typing import Dict, Any, Optional, List
from decimal import Decimal
from nicegui import ui, app

from auth import is_authenticated, get_current_user
from database import create_audit_log
from erp_core import (
    get_products,
    get_suppliers,
    get_warehouses,
    purchase_receive_rpc
)
from utils.ui import show_table


# ==============================================================================
# SESSION STATE
# ==============================================================================

class PurchaseState:
    """Session state for purchase receive."""
    
    def __init__(self):
        self.cart: List[Dict[str, Any]] = []
        self.supplier_id: Optional[str] = None
        self.warehouse_id: Optional[str] = None
        self.message: Optional[str] = None


def get_state() -> PurchaseState:
    """Get or create purchase state."""
    client_id = app.context.client.id if app.context.client else 'default'
    
    if not hasattr(app.storage, 'purchase_state'):
        app.storage.purchase_state = {}
    
    if client_id not in app.storage.purchase_state:
        app.storage.purchase_state[client_id] = PurchaseState()
    
    return app.storage.purchase_state[client_id]


# ==============================================================================
# HELPERS
# ==============================================================================

def money(value: Any) -> str:
    """Format as MMK currency."""
    try:
        return f"{Decimal(str(value)):,.2f} MMK"
    except Exception:
        return "0.00 MMK"


def supplier_name(data: Dict[str, Any]) -> str:
    """Get supplier display name."""
    return (
        data.get("company_name")
        or data.get("name")
        or data.get("supplier_name")
        or f"Supplier #{data.get('id')}"
    )


def warehouse_name(data: Dict[str, Any]) -> str:
    """Get warehouse display name."""
    return (
        data.get("name")
        or data.get("warehouse_name")
        or data.get("code")
        or f"Warehouse #{data.get('id')}"
    )


def product_name(data: Dict[str, Any]) -> str:
    """Get product display name."""
    return (
        data.get("name")
        or data.get("product_name")
        or f"Product #{data.get('id')}"
    )


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main purchase receive page."""
    
    # Auth check
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            ui.label('ကျေးဇူးပြု၍ Login အရင်ဝင်ပါ။').classes('text-orange-700')
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        # Show success message if exists
        if state.message:
            ui.notify(state.message, type='positive', position='top', timeout=5000)
            state.message = None
        
        ui.label('📦 Enterprise Purchase Receive').classes('text-3xl font-bold mb-4')
        
        # Load data
        try:
            suppliers = get_suppliers()
            warehouses = get_warehouses()
            products = get_products()
        except Exception as e:
            ui.notify(f'Data Loading Error: {e}', type='error', position='top')
            return
        
        if not suppliers:
            ui.notify('Supplier မရှိပါ', type='warning', position='top')
            return
        
        if not warehouses:
            ui.notify('Warehouse မရှိပါ', type='warning', position='top')
            return
        
        if not products:
            ui.notify('Product မရှိပါ', type='warning', position='top')
            return
        
        cart_exists = len(state.cart) > 0
        
        # ======================================================================
        # PURCHASE INFORMATION
        # ======================================================================
        
        ui.label('🏭 Purchase Information').classes('text-xl font-bold mb-4')
        
        # Supplier selection
        supplier_options = {
            supplier_name(s): s
            for s in suppliers
        }
        
        supplier_select = ui.select(
            list(supplier_options.keys()),
            label='Supplier',
            value=next((k for k, v in supplier_options.items() if v.get("id") == state.supplier_id), None) if state.supplier_id else None,
        ).classes('w-full mb-4')
        
        if cart_exists:
            supplier_select.disable()
        
        # Warehouse selection
        warehouse_options = {
            warehouse_name(w): w
            for w in warehouses
        }
        
        warehouse_select = ui.select(
            list(warehouse_options.keys()),
            label='Warehouse',
            value=next((k for k, v in warehouse_options.items() if v.get("id") == state.warehouse_id), None) if state.warehouse_id else None,
        ).classes('w-full mb-4')
        
        if cart_exists:
            warehouse_select.disable()
        
        # Update state if cart empty
        if not cart_exists:
            if supplier_select.value:
                state.supplier_id = supplier_options[supplier_select.value]["id"]
            if warehouse_select.value:
                state.warehouse_id = warehouse_options[warehouse_select.value]["id"]
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # ADD PRODUCT SECTION
        # ======================================================================
        
        ui.label('➕ Add Product').classes('text-xl font-bold mb-4')
        
        with ui.card().classes('w-full p-4 mb-4'):
            # Product selection
            product_options = {
                f"{product_name(p)} ({p.get('sku','')})": p
                for p in products
            }
            
            product_select = ui.select(
                list(product_options.keys()),
                label='Product',
            ).classes('w-full mb-4')
            
            with ui.row().classes('w-full gap-4 flex-wrap'):
                with ui.column().classes('flex-1 min-w-[200px]'):
                    quantity_input = ui.number(
                        'Quantity',
                        min=0.01,
                        value=1.00,
                        step=1.00,
                    ).classes('w-full')
                
                with ui.column().classes('flex-1 min-w-[200px]'):
                    cost_input = ui.number(
                        'Cost Price',
                        min=0.0,
                        value=0.0,
                        step=0.01,
                    ).classes('w-full')
            
            add_btn = ui.button(
                '➕ Add To Cart',
                on_click=lambda: handle_add_to_cart(
                    product_options[product_select.value],
                    quantity_input.value,
                    cost_input.value,
                    state,
                    add_btn
                )
            ).classes('w-full bg-primary text-white mt-4')
        
        # ======================================================================
        # PURCHASE CART
        # ======================================================================
        
        ui.label('🛒 Purchase Cart').classes('text-xl font-bold mb-4')
        
        cart_container = ui.column().classes('w-full')
        
        def render_cart():
            """Render purchase cart."""
            cart_container.clear()
            
            cart = state.cart
            
            if not cart:
                with cart_container:
                    ui.label('Purchase Cart is empty.').classes('text-gray-500')
                return
            
            with cart_container:
                # Cart table
                cart_display = []
                total_amount = Decimal("0.00")
                
                for idx, item in enumerate(cart):
                    total_amount += item["total"]
                    cart_display.append({
                        "No": idx + 1,
                        "Product": item["product_name"],
                        "SKU": item.get("sku", ""),
                        "Quantity": f"{item['qty']:,.2f}",
                        "Cost": money(item["cost"]),
                        "Total": money(item["total"]),
                    })
                
                columns = [
                    {'name': col, 'label': col, 'field': col, 'sortable': True}
                    for col in cart_display[0].keys()
                ]
                
                ui.table(
                    columns=columns,
                    rows=cart_display,
                    row_key='No',
                ).classes('w-full mb-4')
                
                # Total
                with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                    with ui.card().classes('p-4 flex-1 min-w-[200px] bg-blue-50'):
                        ui.label('Total Purchase Amount').classes('text-sm text-gray-600')
                        ui.label(money(total_amount)).classes('text-xl font-bold text-blue-700')
                    
                    with ui.card().classes('p-4 flex-1 min-w-[150px] bg-green-50'):
                        ui.label('Total Items').classes('text-sm text-gray-600')
                        ui.label(str(len(cart))).classes('text-xl font-bold text-green-700')
                
                # Remove item
                ui.label('🗑 Remove Item').classes('font-bold mb-2')
                
                remove_options = {
                    f"{i+1}. {item['product_name']}": i
                    for i, item in enumerate(cart)
                }
                
                with ui.row().classes('w-full gap-2 items-end'):
                    remove_select = ui.select(
                        list(remove_options.keys()),
                        label='Select item to remove',
                    ).classes('flex-1')
                    
                    remove_btn = ui.button(
                        'Remove Selected Item',
                        on_click=lambda: handle_remove(
                            remove_options[remove_select.value],
                            state,
                            render_cart
                        )
                    ).classes('bg-red-500 text-white')
                
                ui.separator().classes('my-4')
                
                # Preview
                ui.label('📊 Stock Receive Preview').classes('font-bold mb-2')
                
                preview_rows = []
                for item in cart:
                    preview_rows.append({
                        "Product": item["product_name"],
                        "Receive Qty": f"{item['qty']:,.2f}",
                        "Warehouse": warehouse_select.value or "N/A",
                        "New Stock": f"+{item['qty']:,.2f}",
                    })
                
                preview_columns = [
                    {'name': col, 'label': col, 'field': col}
                    for col in preview_rows[0].keys()
                ]
                
                ui.table(
                    columns=preview_columns,
                    rows=preview_rows,
                    row_key='Product',
                ).classes('w-full mb-4')
        
        # Initial render
        render_cart()
        
        # ======================================================================
        # COMPLETE PURCHASE
        # ======================================================================
        
        if state.cart:
            ui.separator().classes('my-4')
            
            complete_btn = ui.button(
                '💾 Complete Purchase',
                on_click=lambda: handle_complete_purchase(state, complete_btn, render_cart)
            ).classes('w-full bg-green-500 text-white font-semibold py-2 mb-2')
        
        # Clear cart button
        clear_btn = ui.button(
            '🗑 Clear Purchase Cart',
            on_click=lambda: handle_clear_cart(state, render_cart)
        ).classes('w-full bg-gray-500 text-white')


def handle_add_to_cart(product: Dict, qty_val: float, cost_val: float, state: PurchaseState, add_btn: Any):
    """Handle add to cart."""
    try:
        qty = Decimal(str(qty_val))
        cost = Decimal(str(cost_val))
        
        found = False
        
        for item in state.cart:
            if item["product_id"] == product["id"]:
                item["qty"] += qty
                item["total"] = item["qty"] * item["cost"]
                found = True
                break
        
        if not found:
            state.cart.append({
                "product_id": product["id"],
                "product_name": product_name(product),
                "sku": product.get("sku", ""),
                "qty": qty,
                "cost": cost,
                "total": qty * cost,
            })
        
        ui.notify('Product added to purchase cart', type='positive', position='top')
    
    except Exception as e:
        ui.notify(f'Error adding product: {e}', type='error', position='top')


def handle_remove(index: int, state: PurchaseState, render_cart: callable):
    """Handle remove item from cart."""
    try:
        if 0 <= index < len(state.cart):
            state.cart.pop(index)
            ui.notify('Item removed', type='positive', position='top')
            render_cart()
    except Exception as e:
        ui.notify(f'Error removing item: {e}', type='error', position='top')


def handle_complete_purchase(state: PurchaseState, complete_btn: Any, render_cart: callable):
    """Handle complete purchase."""
    try:
        complete_btn.disable()
        complete_btn.text = '⏳ Processing...'
        
        success = []
        errors = []
        
        supplier_id = state.supplier_id
        warehouse_id = state.warehouse_id
        
        if not supplier_id or not warehouse_id:
            ui.notify('Supplier or Warehouse missing.', type='error', position='top')
            return
        
        user = get_current_user()
        user_id = user.get("id") if user else None
        
        for item in state.cart:
            try:
                result = purchase_receive_rpc(
                    product_id=int(item["product_id"]),
                    supplier_id=int(supplier_id),
                    warehouse_id=int(warehouse_id),
                    qty=int(item["qty"]),
                    cost=float(item["cost"]),
                    remarks="Purchase Receive",
                    user_id=user_id,
                )
                
                if isinstance(result, dict):
                    if result.get("success"):
                        success.append(item["product_name"])
                    else:
                        errors.append(f"{item['product_name']} : {result.get('message', 'Failed')}")
                elif result is True:
                    success.append(item["product_name"])
                else:
                    errors.append(f"{item['product_name']} : RPC Failed")
            
            except Exception as e:
                errors.append(f"{item['product_name']} : {e}")
        
        if success:
            try:
                create_audit_log(
                    action="PURCHASE_RECEIVE",
                    details="Purchase received products: " + ", ".join(success)
                )
            except Exception:
                pass
            
            state.message = "✅ Purchase Completed Successfully - " + ", ".join(success)
            state.cart = []
            state.supplier_id = None
            state.warehouse_id = None
            
            ui.notify(state.message, type='positive', position='top', timeout=5000)
            render_cart()
        
        if errors:
            ui.notify('❌ Purchase Errors: ' + " | ".join(errors), type='error', position='top', timeout=10000)
    
    except Exception as e:
        ui.notify(f'Purchase error: {e}', type='error', position='top')
    
    finally:
        complete_btn.enable()
        complete_btn.text = '💾 Complete Purchase'


def handle_clear_cart(state: PurchaseState, render_cart: callable):
    """Handle clear cart."""
    state.cart = []
    state.supplier_id = None
    state.warehouse_id = None
    
    ui.notify('Cart cleared', type='info', position='top')
    render_cart()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
