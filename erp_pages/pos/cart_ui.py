# ==============================================================================
# erp_pages/pos/cart_ui.py
# ERP ENTERPRISE POS CART UI v2.0 - NiceGUI Version
#
# - NiceGUI Components
# - Responsive Design
# - Real-time Updates
# - Button Styling Ready
# - Animation Support
# ==============================================================================

from typing import List, Dict, Any, Optional, Callable
from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from erp_pages.pos.cart import Cart, CartItem
from erp_pages.pos.engine import format_money
from erp_core.context import NiceGUISession


# ==============================================================================
# CART UI STYLE
# ==============================================================================

class CartUIStyle:
    """Cart UI styling configuration."""
    
    # Colors
    PRIMARY_COLOR = "#1976D2"
    SECONDARY_COLOR = "#26A69A"
    DANGER_COLOR = "#F44336"
    WARNING_COLOR = "#FF9800"
    SUCCESS_COLOR = "#4CAF50"
    
    # Button sizes
    BUTTON_SIZE = "sm"
    BUTTON_HEIGHT = "2.5rem"
    
    # Card styles
    CARD_CLASSES = "w-full q-pa-sm q-mb-xs"
    ITEM_CLASSES = "w-full items-center justify-between"
    
    # Animation
    ANIMATION_DURATION = 300  # milliseconds
    
    @classmethod
    def apply_style(cls):
        """Apply custom CSS styles."""
        ui.add_head_html('''
        <style>
            .pos-cart-item {
                transition: all 0.3s ease;
                border-radius: 8px;
                padding: 8px;
                margin-bottom: 4px;
            }
            .pos-cart-item:hover {
                background-color: #f5f5f5;
            }
            .pos-cart-item-removing {
                opacity: 0;
                transform: translateX(100px);
            }
            .pos-cart-total {
                font-size: 1.2rem;
                font-weight: bold;
                color: #1976D2;
            }
            .pos-cart-empty {
                text-align: center;
                color: #9E9E9E;
                padding: 2rem;
            }
            .pos-quantity-btn {
                min-width: 32px !important;
                min-height: 32px !important;
                padding: 4px !important;
            }
        </style>
        ''')


# ==============================================================================
# CART CONTROL
# ==============================================================================

class CartUI:
    """
    POS Cart UI component for NiceGUI.
    """
    
    def __init__(
        self,
        cart: Optional[Cart] = None,
        on_update: Optional[Callable] = None,
        on_checkout: Optional[Callable] = None,
        on_clear: Optional[Callable] = None,
    ):
        """
        Initialize Cart UI.
        
        Args:
            cart: Cart instance
            on_update: Callback when cart is updated
            on_checkout: Callback when checkout is clicked
            on_clear: Callback when cart is cleared
        """
        self.cart = cart or Cart()
        self.on_update = on_update
        self.on_checkout = on_checkout
        self.on_clear = on_clear
        
        # UI elements
        self.cart_container = None
        self.items_container = None
        self.summary_container = None
        self.empty_label = None
        
        # Apply styles
        CartUIStyle.apply_style()
    
    def create(self) -> ui.element:
        """
        Create the cart UI.
        
        Returns:
            The main cart container element
        """
        with ui.card().classes('w-full h-full') as self.cart_container:
            # Header
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('🛒 Shopping Cart').classes('text-h6')
                
                with ui.row().classes('gap-1'):
                    # Clear button
                    ui.button(
                        icon='delete_sweep',
                        on_click=self._clear_cart,
                        color='negative',
                        size='sm'
                    ).tooltip('Clear cart')
                    
                    # Refresh button
                    ui.button(
                        icon='refresh',
                        on_click=self._refresh,
                        size='sm'
                    ).tooltip('Refresh cart')
            
            ui.separator()
            
            # Items container (scrollable)
            with ui.scroll_area().classes('w-full h-96'):
                self.items_container = ui.column().classes('w-full gap-1')
                self._render_items()
            
            ui.separator()
            
            # Summary and actions
            self.summary_container = ui.column().classes('w-full')
            self._render_summary()
            
            # Checkout button
            with ui.row().classes('w-full gap-2 mt-2'):
                ui.button(
                    'Checkout',
                    on_click=self._checkout,
                    color='primary',
                    icon='payment'
                ).classes('w-full').bind_visibility_from(
                    self.cart, 'items', lambda items: bool(items)
                )
        
        return self.cart_container
    
    def _render_items(self):
        """Render cart items."""
        self.items_container.clear()
        
        with self.items_container:
            if not self.cart.items:
                with ui.column().classes('pos-cart-empty w-full'):
                    ui.icon('shopping_cart_off', size='3rem')
                    ui.label('Cart is empty').classes('text-h6')
                    ui.label('Add products to get started').classes('text-caption')
                return
            
            for idx, item in enumerate(self.cart.items):
                self._render_item(item, idx)
    
    def _render_item(self, item: CartItem, index: int):
        """
        Render a single cart item.
        
        Args:
            item: Cart item
            index: Item index
        """
        with ui.card().classes('pos-cart-item w-full').props('flat'):
            with ui.row().classes('pos-cart-item w-full'):
                # Product info
                with ui.column().classes('flex-1'):
                    ui.label(item.product_name).classes('text-weight-bold')
                    with ui.row().classes('gap-2 items-center'):
                        ui.label(f'SKU: {item.sku}').classes('text-caption text-grey-5')
                        ui.label(f'Qty: {item.quantity}').classes('text-caption')
                
                # Price and quantity controls
                with ui.row().classes('items-center gap-2'):
                    # Quantity controls
                    with ui.row().classes('gap-1'):
                        ui.button(
                            icon='remove',
                            size='sm',
                            on_click=lambda i=index: self._decrease_quantity(i),
                        ).classes('pos-quantity-btn')
                        
                        ui.label(str(int(item.quantity))).classes('q-px-sm')
                        
                        ui.button(
                            icon='add',
                            size='sm',
                            on_click=lambda i=index: self._increase_quantity(i),
                        ).classes('pos-quantity-btn')
                    
                    # Price
                    ui.label(format_money(item.total)).classes('text-weight-bold')
                    
                    # Remove button
                    ui.button(
                        icon='delete',
                        size='sm',
                        color='negative',
                        on_click=lambda i=index: self._remove_item(i),
                    ).classes('pos-quantity-btn')
    
    def _render_summary(self):
        """Render cart summary."""
        self.summary_container.clear()
        
        with self.summary_container:
            # Summary details
            with ui.column().classes('w-full gap-1'):
                # Subtotal
                with ui.row().classes('w-full justify-between'):
                    ui.label('Subtotal:')
                    ui.label(format_money(self.cart.get_subtotal()))
                
                # Tax
                with ui.row().classes('w-full justify-between'):
                    ui.label('Tax:')
                    ui.label(format_money(self.cart.get_tax_total()))
                
                # Discount
                discount = self.cart.get_total_discount()
                if discount > 0:
                    with ui.row().classes('w-full justify-between text-negative'):
                        ui.label('Discount:')
                        ui.label(f'-{format_money(discount)}')
                
                ui.separator()
                
                # Total
                with ui.row().classes('w-full justify-between pos-cart-total'):
                    ui.label('Total:')
                    ui.label(format_money(self.cart.get_total()))
                
                # Item count
                with ui.row().classes('w-full justify-end text-caption text-grey-5'):
                    ui.label(f'{self.cart.get_item_count()} items')
    
    def _increase_quantity(self, index: int):
        """Increase item quantity."""
        if index < len(self.cart.items):
            item = self.cart.items[index]
            self.cart.update_quantity(item.product_id, item.quantity + 1)
            self._update_cart()
    
    def _decrease_quantity(self, index: int):
        """Decrease item quantity."""
        if index < len(self.cart.items):
            item = self.cart.items[index]
            if item.quantity > 1:
                self.cart.update_quantity(item.product_id, item.quantity - 1)
            else:
                self.cart.remove_item(item.product_id)
            self._update_cart()
    
    def _remove_item(self, index: int):
        """Remove item from cart."""
        if index < len(self.cart.items):
            item = self.cart.items[index]
            self.cart.remove_item(item.product_id)
            self._update_cart()
    
    def _clear_cart(self):
        """Clear cart with confirmation."""
        if self.cart.items:
            ui.dialog(
                ui.card()
                .classes('w-96')
                .add(
                    ui.label('Clear Cart?').classes('text-h6'),
                    ui.label('This will remove all items from your cart.'),
                    ui.row().classes('justify-end gap-2').add(
                        ui.button('Cancel', on_click=lambda d: d.close()),
                        ui.button(
                            'Clear',
                            color='negative',
                            on_click=lambda d: [
                                self.cart.clear(),
                                self._update_cart(),
                                d.close(),
                                ui.notify('Cart cleared', type='warning')
                            ]
                        )
                    )
                )
            ).open()
        else:
            ui.notify('Cart is already empty', type='info')
    
    def _checkout(self):
        """Handle checkout."""
        if not self.cart.items:
            ui.notify('Cart is empty', type='warning')
            return
        
        if self.on_checkout:
            self.on_checkout(self.cart)
        else:
            ui.notify('Checkout handler not set', type='warning')
    
    def _refresh(self):
        """Refresh cart display."""
        self._update_cart()
        ui.notify('Cart refreshed', type='info')
    
    def _update_cart(self):
        """Update cart UI."""
        self._render_items()
        self._render_summary()
        
        if self.on_update:
            self.on_update(self.cart)
    
    def set_cart(self, cart: Cart):
        """Set new cart instance."""
        self.cart = cart
        self._update_cart()
    
    def get_cart(self) -> Cart:
        """Get current cart instance."""
        return self.cart


# ==============================================================================
# COMPACT CART UI
# ==============================================================================

class CompactCartUI(CartUI):
    """
    Compact version of cart UI for smaller screens.
    """
    
    def _render_item(self, item: CartItem, index: int):
        """Render item in compact form."""
        with ui.row().classes('pos-cart-item w-full'):
            # Product name and quantity
            with ui.column().classes('flex-1'):
                ui.label(item.product_name).classes('text-weight-bold text-sm')
                ui.label(f'x{item.quantity}').classes('text-caption')
            
            # Price and actions
            with ui.row().classes('items-center gap-1'):
                ui.label(format_money(item.total)).classes('text-sm')
                
                ui.button(
                    icon='add',
                    size='xs',
                    on_click=lambda i=index: self._increase_quantity(i),
                ).classes('pos-quantity-btn')
                
                ui.button(
                    icon='remove',
                    size='xs',
                    on_click=lambda i=index: self._decrease_quantity(i),
                ).classes('pos-quantity-btn')
                
                ui.button(
                    icon='delete',
                    size='xs',
                    color='negative',
                    on_click=lambda i=index: self._remove_item(i),
                ).classes('pos-quantity-btn')


# ==============================================================================
# CART WITH ANIMATIONS
# ==============================================================================

class AnimatedCartUI(CartUI):
    """
    Cart UI with animations.
    """
    
    def _render_item(self, item: CartItem, index: int):
        """Render item with animation."""
        with ui.card().classes('pos-cart-item w-full').props('flat'):
            with ui.row().classes('pos-cart-item w-full'):
                # Product info
                with ui.column().classes('flex-1'):
                    ui.label(item.product_name).classes('text-weight-bold')
                    with ui.row().classes('gap-2 items-center'):
                        ui.label(f'Qty: {item.quantity}').classes('text-caption')
                
                # Price and controls
                with ui.row().classes('items-center gap-2'):
                    # Quantity controls
                    with ui.row().classes('gap-1'):
                        ui.button(
                            icon='remove',
                            size='sm',
                            on_click=lambda i=index: self._decrease_quantity(i),
                            color='grey',
                        ).classes('pos-quantity-btn')
                        
                        # Animated quantity label
                        with ui.element('span').classes('q-px-sm transition-all'):
                            ui.label(str(int(item.quantity))).bind_text_from(
                                item, 'quantity',
                                lambda q: str(int(q))
                            )
                        
                        ui.button(
                            icon='add',
                            size='sm',
                            on_click=lambda i=index: self._increase_quantity(i),
                            color='primary',
                        ).classes('pos-quantity-btn')
                    
                    ui.label(format_money(item.total)).classes('text-weight-bold')
                    
                    ui.button(
                        icon='delete',
                        size='sm',
                        color='negative',
                        on_click=lambda i=index: self._remove_item(i),
                    ).classes('pos-quantity-btn')


# ==============================================================================
# CART WITH PERSISTENCE
# ==============================================================================

class PersistentCartUI(CartUI):
    """
    Cart UI with session persistence.
    """
    
    SESSION_KEY = "pos_cart_data"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_from_session()
    
    def _load_from_session(self):
        """Load cart from session."""
        cart_data = NiceGUISession.get(self.SESSION_KEY)
        if cart_data:
            try:
                self.cart = Cart.from_dict(cart_data)
            except Exception as e:
                print(f"Error loading cart from session: {e}")
    
    def _save_to_session(self):
        """Save cart to session."""
        if self.cart:
            NiceGUISession.set(self.SESSION_KEY, self.cart.to_dict())
    
    def _update_cart(self):
        """Update cart and save to session."""
        super()._update_cart()
        self._save_to_session()


# ==============================================================================
# CART UTILITY FUNCTIONS
# ==============================================================================

def create_cart_ui(
    cart: Optional[Cart] = None,
    compact: bool = False,
    animated: bool = False,
    persistent: bool = False,
    on_update: Optional[Callable] = None,
    on_checkout: Optional[Callable] = None,
    on_clear: Optional[Callable] = None,
) -> CartUI:
    """
    Create a cart UI with specified options.
    
    Args:
        cart: Cart instance
        compact: Use compact layout
        animated: Enable animations
        persistent: Enable session persistence
        on_update: Callback on update
        on_checkout: Callback on checkout
        on_clear: Callback on clear
    
    Returns:
        CartUI instance
    """
    ui_class = CartUI
    
    if compact:
        ui_class = CompactCartUI
    elif animated:
        ui_class = AnimatedCartUI
    elif persistent:
        ui_class = PersistentCartUI
    
    return ui_class(
        cart=cart,
        on_update=on_update,
        on_checkout=on_checkout,
        on_clear=on_clear,
    )


# ==============================================================================
# LEGACY COMPATIBILITY
# ==============================================================================

# For backward compatibility with Streamlit version
def render_cart_control(cart: List[Dict[str, Any]]):
    """
    Legacy function for Streamlit compatibility.
    Now returns a NiceGUI component.
    """
    from erp_pages.pos.cart import create_cart_from_list
    
    # Convert list to Cart object
    cart_obj = create_cart_from_list(cart)
    
    # Create UI
    cart_ui = create_cart_ui(
        cart=cart_obj,
        compact=True
    )
    
    return cart_ui.create()


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # UI Classes
    "CartUI",
    "CompactCartUI",
    "AnimatedCartUI",
    "PersistentCartUI",
    
    # Style
    "CartUIStyle",
    
    # Factory
    "create_cart_ui",
    
    # Legacy
    "render_cart_control",
]

print("ERP POS CART UI READY - NiceGUI Version")
