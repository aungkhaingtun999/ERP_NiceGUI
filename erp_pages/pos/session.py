# ==============================================================================
# erp_pages/pos/session_nicegui.py
# ERP ENTERPRISE POS SESSION MANAGER v12.9 FINAL
# NiceGUI Version
#
# Responsibilities:
# - Initialize POS session
# - Load system settings
# - Manage checkout state
# - Reset transaction safely
#
# Flow:
#
# ERP Settings
#      |
#      ↓
# POS Session
#      |
#      ↓
# Checkout
#      |
#      ↓
# Receipt
#
# ==============================================================================

from nicegui import app
from typing import Dict, Any, Optional
import asyncio

from erp_core.loaders.settings_loader import (
    clear_settings_cache,
)

# ==============================================================================
# DEFAULT STATE
# ==============================================================================

def default_pos_state() -> Dict[str, Any]:
    """Get default POS state"""
    return {
        # --------------------------------------------------
        # CART
        # --------------------------------------------------
        "cart": [],
        
        # --------------------------------------------------
        # SALE
        # --------------------------------------------------
        "sale_data": None,
        "show_receipt": False,
        
        # --------------------------------------------------
        # PROCESS LOCK
        # --------------------------------------------------
        "processing": False,
        
        # --------------------------------------------------
        # TAX
        # --------------------------------------------------
        "tax_rate": 0.0,
        
        # --------------------------------------------------
        # DISCOUNT
        # --------------------------------------------------
        "discount": 0.0,
        "discount_policy": "allowed",
        
        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------
        "selected_product": None,
        "product_search": "",
        
        # --------------------------------------------------
        # PAYMENT
        # --------------------------------------------------
        "payment_method": "CASH",
        "received_amount": 0.0,
    }

# ==============================================================================
# LOAD SYSTEM SETTINGS
# ==============================================================================

def load_pos_settings() -> Dict[str, Any]:
    """Load POS settings from ERP system"""
    try:
        tax_rate = float(
            get_setting("DEFAULT_TAX_RATE", 0)
        )
    except Exception:
        tax_rate = 0.0
    
    try:
        discount_policy = str(
            get_setting("DISCOUNT_POLICY", "allowed")
        )
    except Exception:
        discount_policy = "allowed"
    
    return {
        "tax_rate": tax_rate,
        "discount_policy": discount_policy
    }

# ==============================================================================
# INIT SESSION
# ==============================================================================

def init_pos_session():
    """Initialize POS session state"""
    # Clear settings cache
    try:
        clear_settings_cache()
    except Exception:
        pass
    
    # Initialize default state
    defaults = default_pos_state()
    
    for key, value in defaults.items():
        if key not in app.storage.user:
            app.storage.user[key] = value
    
    # Load ERP Settings if not loaded
    if not app.storage.user.get('_pos_settings_loaded', False):
        settings = load_pos_settings()
        
        app.storage.user['tax_rate'] = settings.get('tax_rate', 0)
        app.storage.user['discount_policy'] = settings.get('discount_policy', 'allowed')
        app.storage.user['_pos_settings_loaded'] = True

# ==============================================================================
# RESET SALE
# ==============================================================================

def reset_sale():
    """Reset sale transaction state"""
    reset_values = {
        "cart": [],
        "sale_data": None,
        "show_receipt": False,
        "processing": False,
        "selected_product": None,
        "product_search": "",
        "payment_method": "CASH",
        "received_amount": 0.0,
        "discount": 0.0,
    }
    
    for key, value in reset_values.items():
        app.storage.user[key] = value

# ==============================================================================
# CART CHECK
# ==============================================================================

def has_cart() -> bool:
    """Check if cart has items"""
    return bool(app.storage.user.get('cart', []))

# ==============================================================================
# RECEIPT MODE
# ==============================================================================

def is_receipt_mode() -> bool:
    """Check if in receipt mode"""
    return bool(app.storage.user.get('show_receipt', False))

# ==============================================================================
# PROCESS LOCK
# ==============================================================================

def start_processing():
    """Start processing lock"""
    app.storage.user['processing'] = True

def stop_processing():
    """Stop processing lock"""
    app.storage.user['processing'] = False

def is_processing() -> bool:
    """Check if processing"""
    return bool(app.storage.user.get('processing', False))

# ==============================================================================
# TAX HELPER
# ==============================================================================

def get_tax_rate() -> float:
    """Get current tax rate"""
    return float(app.storage.user.get('tax_rate', 0))

# ==============================================================================
# DISCOUNT HELPER
# ==============================================================================

def get_discount_policy() -> str:
    """Get discount policy"""
    return app.storage.user.get('discount_policy', 'allowed')

# ==============================================================================
# SESSION MANAGER CLASS (OPTIONAL)
# ==============================================================================

class POSSessionManager:
    """POS Session Manager Class for NiceGUI"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize POS session asynchronously"""
        if self._initialized:
            return
        
        # Clear settings cache
        try:
            await asyncio.to_thread(clear_settings_cache)
        except Exception:
            pass
        
        # Initialize default state
        defaults = default_pos_state()
        
        for key, value in defaults.items():
            if key not in app.storage.user:
                app.storage.user[key] = value
        
        # Load ERP settings
        if not app.storage.user.get('_pos_settings_loaded', False):
            settings = await asyncio.to_thread(load_pos_settings)
            
            app.storage.user['tax_rate'] = settings.get('tax_rate', 0)
            app.storage.user['discount_policy'] = settings.get('discount_policy', 'allowed')
            app.storage.user['_pos_settings_loaded'] = True
        
        self._initialized = True
    
    def reset(self):
        """Reset POS session"""
        reset_sale()
    
    def start_processing(self):
        """Start processing lock"""
        start_processing()
    
    def stop_processing(self):
        """Stop processing lock"""
        stop_processing()
    
    def is_processing(self) -> bool:
        """Check if processing"""
        return is_processing()
    
    def get_cart(self) -> list:
        """Get current cart"""
        return app.storage.user.get('cart', [])
    
    def set_cart(self, cart: list):
        """Set cart items"""
        app.storage.user['cart'] = cart
    
    def clear_cart(self):
        """Clear cart"""
        app.storage.user['cart'] = []
    
    def add_to_cart(self, item: Dict):
        """Add item to cart"""
        cart = self.get_cart()
        cart.append(item)
        self.set_cart(cart)
    
    def get_tax_rate(self) -> float:
        """Get tax rate"""
        return get_tax_rate()
    
    def get_discount_policy(self) -> str:
        """Get discount policy"""
        return get_discount_policy()
    
    def get_payment_method(self) -> str:
        """Get payment method"""
        return app.storage.user.get('payment_method', 'CASH')
    
    def set_payment_method(self, method: str):
        """Set payment method"""
        app.storage.user['payment_method'] = method
    
    def get_received_amount(self) -> float:
        """Get received amount"""
        return float(app.storage.user.get('received_amount', 0.0))
    
    def set_received_amount(self, amount: float):
        """Set received amount"""
        app.storage.user['received_amount'] = amount
    
    def is_receipt_mode(self) -> bool:
        """Check if in receipt mode"""
        return is_receipt_mode()
    
    def show_receipt(self, sale_data: Optional[Dict] = None):
        """Show receipt with sale data"""
        if sale_data:
            app.storage.user['sale_data'] = sale_data
        app.storage.user['show_receipt'] = True
    
    def hide_receipt(self):
        """Hide receipt"""
        app.storage.user['show_receipt'] = False
    
    def get_sale_data(self) -> Optional[Dict]:
        """Get sale data"""
        return app.storage.user.get('sale_data', None)

# ==============================================================================
# GLOBAL SESSION MANAGER INSTANCE
# ==============================================================================

# Create singleton instance
session_manager = POSSessionManager()

# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'default_pos_state',
    'load_pos_settings',
    'init_pos_session',
    'reset_sale',
    'has_cart',
    'is_receipt_mode',
    'start_processing',
    'stop_processing',
    'is_processing',
    'get_tax_rate',
    'get_discount_policy',
    'POSSessionManager',
    'session_manager'
]
