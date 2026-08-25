# ==============================================================================
# erp_pages/pos/main_nicegui.py
# 
# ERP ENTERPRISE POS MAIN CONTROLLER v13.2 STABLE
# NiceGUI Version
# 
# Stable POS Layout
# - Product + Cart Side Layout
# - Existing Payment Engine
# - Existing Pricing Engine
# - Existing Checkout Engine
# ==============================================================================

from nicegui import ui, app
from typing import Optional, List, Dict, Any
import pandas as pd

from erp_core import get_default_warehouse_id

from .session import init_pos_session
from .product import render_products
from .cart import get_cart_rows
from .cart_ui import render_cart_control
from .payment import render_payment
from .receipt import render_receipt
from .styles import load_pos_style

from auth import is_authenticated
from language import language_selector

# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def money(value) -> str:
    """Format money value to MMK"""
    try:
        return f"{float(value):,.0f} MMK"
    except Exception:
        return "0 MMK"

# ==============================================================================
# POS MAIN PAGE
# ==============================================================================

class POSPage:
    """POS Main Page Controller for NiceGUI"""
    
    def __init__(self):
        self.cart_container: Optional[ui.element] = None
        self.product_container: Optional[ui.element] = None
        self.payment_container: Optional[ui.element] = None
        self.cart_table: Optional[ui.table] = None
        self.cart_control_container: Optional[ui.element] = None
        
    def create_header(self):
        """Create POS header section"""
        with ui.row().classes('w-full items-center justify-between mb-4'):
            with ui.column().classes('gap-0'):
                ui.label('🛒 ERP Enterprise POS').classes('text-2xl font-bold')
                ui.label('Fast Compact Sales System').classes('text-sm text-gray-500')
            
            # Language selector
            with ui.row().classes('items-center gap-2'):
                self.create_language_selector()
                
    def create_language_selector(self):
        """Create language selector dropdown"""
        try:
            from language import get_languages, set_language
            
            languages = get_languages()
            current_lang = app.storage.user.get('language', 'en')
            
            def on_language_change(e):
                set_language(e.value)
                ui.notify(f'Language changed to {e.value}', type='positive')
                self.refresh_page()
            
            ui.select(
                options=languages,
                value=current_lang,
                on_change=on_language_change
            ).classes('w-32').props('outlined dense')
            
        except Exception:
            # Fallback if language module not available
            pass
    
    def create_product_panel(self, warehouse_id: str):
        """Create products panel"""
        with ui.column().classes('w-3/5 gap-4'):
            ui.label('📦 Products').classes('text-xl font-semibold mb-2')
            self.product_container = ui.column().classes('w-full')
            
            with self.product_container:
                try:
                    render_products(warehouse_id, container=self.product_container)
                except Exception as e:
                    ui.label(f'Error loading products: {str(e)}').classes('text-red-500')
    
    def create_cart_panel(self):
        """Create cart panel"""
        with ui.column().classes('w-2/5 gap-4'):
            ui.label('🛒 Cart').classes('text-xl font-semibold mb-2')
            
            self.cart_container = ui.column().classes('w-full gap-2')
            self.cart_control_container = ui.column().classes('w-full')
            
            with self.cart_container:
                self.update_cart_display()
    
    def update_cart_display(self):
        """Update cart display"""
        if self.cart_container is None:
            return
            
        # Clear existing cart content
        self.cart_container.clear()
        
        with self.cart_container:
            cart = app.storage.user.get('cart', [])
            
            if not cart:
                ui.label('Cart is empty').classes('text-gray-500 italic p-4')
            else:
                try:
                    rows = get_cart_rows(cart)
                    if rows:
                        # Create cart table
                        columns = [
                            {'name': 'product', 'label': 'Product', 'field': 'Product', 'align': 'left'},
                            {'name': 'qty', 'label': 'Qty', 'field': 'Qty', 'align': 'center'},
                            {'name': 'unit_price', 'label': 'Unit Price', 'field': 'Unit Price', 'align': 'right'},
                            {'name': 'amount', 'label': 'Amount', 'field': 'Amount', 'align': 'right'},
                        ]
                        
                        # Format money values
                        formatted_rows = []
                        for row in rows:
                            formatted_row = row.copy()
                            formatted_row['Unit Price'] = money(row.get('Unit Price', 0))
                            formatted_row['Amount'] = money(row.get('Amount', 0))
                            formatted_rows.append(formatted_row)
                        
                        self.cart_table = ui.table(
                            columns=columns,
                            rows=formatted_rows,
                            row_key='product'
                        ).classes('w-full').props('dense flat bordered')
                        
                        # Cart controls
                        with self.cart_control_container:
                            self.cart_control_container.clear()
                            with self.cart_control_container:
                                try:
                                    render_cart_control(cart, container=self.cart_control_container)
                                except Exception as e:
                                    ui.label(f'Error loading cart controls: {str(e)}').classes('text-red-500')
                except Exception as e:
                    ui.label(f'Error displaying cart: {str(e)}').classes('text-red-500')
    
    def create_payment_panel(self, warehouse_id: str):
        """Create payment panel"""
        self.payment_container = ui.column().classes('w-full mt-4')
        
        with self.payment_container:
            cart = app.storage.user.get('cart', [])
            if cart:
                try:
                    render_payment(warehouse_id, container=self.payment_container)
                except Exception as e:
                    ui.label(f'Error loading payment: {str(e)}').classes('text-red-500')
    
    def refresh_page(self):
        """Refresh the entire POS page"""
        # Clear all containers
        if self.product_container:
            self.product_container.clear()
        if self.cart_container:
            self.cart_container.clear()
        if self.payment_container:
            self.payment_container.clear()
        if self.cart_control_container:
            self.cart_control_container.clear()
            
        # Re-render products and cart
        warehouse_id = get_default_warehouse_id()
        if warehouse_id:
            with self.product_container:
                try:
                    render_products(warehouse_id, container=self.product_container)
                except Exception:
                    pass
            
            self.update_cart_display()
            self.create_payment_panel(warehouse_id)
    
    def check_receipt_mode(self) -> bool:
        """Check if receipt should be shown"""
        return app.storage.user.get('show_receipt', False)
    
    def render_receipt_page(self):
        """Render receipt page"""
        try:
            render_receipt()
        except Exception as e:
            ui.label(f'Error loading receipt: {str(e)}').classes('text-red-500')
    
    def build(self):
        """Build the POS page"""
        # Load custom styles
        try:
            load_pos_style()
        except Exception:
            pass
        
        # Check authentication
        if not is_authenticated():
            with ui.column().classes('w-full items-center justify-center p-8'):
                ui.icon('warning', size='48px').classes('text-yellow-500')
                ui.label('Please login first.').classes('text-xl font-semibold')
                ui.label('Authentication required to access POS system').classes('text-gray-500')
            return
        
        # Initialize POS session
        init_pos_session()
        
        # Get warehouse
        warehouse_id = get_default_warehouse_id()
        if not warehouse_id:
            with ui.column().classes('w-full items-center justify-center p-8'):
                ui.icon('error', size='48px').classes('text-red-500')
                ui.label('Default warehouse not configured.').classes('text-xl font-semibold')
                ui.label('Please configure warehouse in settings').classes('text-gray-500')
            return
        
        # Check receipt mode
        if self.check_receipt_mode():
            self.render_receipt_page()
            return
        
        # Main POS layout
        with ui.column().classes('w-full p-4 gap-4'):
            # Header
            self.create_header()
            
            # Main content area (Product + Cart)
            with ui.row().classes('w-full gap-4 items-start'):
                # Product panel (60%)
                self.create_product_panel(warehouse_id)
                
                # Cart panel (40%)
                self.create_cart_panel()
            
            # Payment section
            self.create_payment_panel(warehouse_id)

# ==============================================================================
# PAGE ROUTER
# ==============================================================================

def create_pos_page():
    """Create and return POS page"""
    page = POSPage()
    return page

# ==============================================================================
# MAIN RUN (NiceGUI Version)
# ==============================================================================

def run():
    """Main POS page runner for NiceGUI"""
    pos_page = POSPage()
    pos_page.build()
    return pos_page

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

@ui.page('/pos')
def pos_page():
    """POS page route"""
    with ui.header().classes('items-center justify-between'):
        ui.label('ERP Enterprise POS').classes('text-xl font-bold')
    
    with ui.column().classes('w-full'):
        run()

# ==============================================================================
# INITIALIZATION
# ==============================================================================

def init_pos_module():
    """Initialize POS module for NiceGUI"""
    # Register page
    app.add_static_files('/pos/static', 'erp_pages/pos/static')
    
    # Initialize any required storage
    if 'cart' not in app.storage.user:
        app.storage.user['cart'] = []
    if 'show_receipt' not in app.storage.user:
        app.storage.user['show_receipt'] = False
    
    # Return the page function
    return pos_page

# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'POSPage',
    'create_pos_page',
    'run',
    'pos_page',
    'init_pos_module',
    'money'
]
