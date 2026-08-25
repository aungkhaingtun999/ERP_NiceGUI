# ==============================================================================
# erp_pages/pos/__init__.py
# ERP ENTERPRISE POS MODULE PACKAGE - NiceGUI Version
# Version v13.0
#
# POS Components
# - engine
# - product
# - cart
# - payment
# - receipt
# - cache
# - NiceGUI UI components
# ==============================================================================

"""
ERP Enterprise POS Package - NiceGUI Version

Modular POS Architecture for NiceGUI

Modules:

engine.py
    - Price engine with owner priority
    - Money formatting
    - Tax calculation
    - Discount management

product.py
    - Product loader with caching
    - Search with autocomplete
    - Barcode scanning
    - Product variants

cart.py
    - Cart state management
    - Add/remove/update quantity
    - Cart calculation with discounts
    - Cart persistence

payment.py
    - Checkout RPC
    - Payment validation
    - Multiple payment methods
    - Payment splitting

receipt.py
    - Receipt rendering
    - PDF generation
    - Thermal printer support
    - Email receipt
    - Receipt templates

cache.py
    - Inventory cache refresh
    - Price cache
    - Product cache
    - Real-time updates

ui.py
    - NiceGUI POS UI components
    - Product grid
    - Cart panel
    - Payment dialog
    - Receipt viewer
"""

# ==============================================================================
# VERSION
# ==============================================================================

POS_VERSION = "13.0"
POS_NAME = "ERP Enterprise POS"
POS_DESCRIPTION = "Point of Sale System for NiceGUI"

# ==============================================================================
# EXPORTS - Core Modules
# ==============================================================================

from .engine import (
    PriceEngine,
    MoneyFormatter,
    TaxCalculator,
    DiscountEngine,
    PriceSource,
    format_money,
    calculate_tax,
    calculate_discount,
)

from .product import (
    ProductLoader,
    ProductSearch,
    ProductScanner,
    BarcodeScanner,
    ProductVariant,
    get_product_by_barcode,
    search_products,
)

from .cart import (
    Cart,
    CartItem,
    CartManager,
    CartCalculator,
    CartPersistence,
    create_cart,
    get_cart_manager,
)

from .payment import (
    PaymentProcessor,
    PaymentMethod,
    PaymentResult,
    CheckoutService,
    PaymentValidator,
    process_payment,
    validate_payment,
)

from .receipt import (
    ReceiptGenerator,
    ReceiptTemplate,
    ReceiptPrinter,
    PDFReceipt,
    EmailReceipt,
    generate_receipt,
    print_receipt,
)

from .cache import (
    POSCacheManager,
    CacheInvalidator,
    InventoryCache,
    PriceCache,
    refresh_cache,
    invalidate_cache,
)

# ==============================================================================
# EXPORTS - UI Components (NiceGUI)
# ==============================================================================

from .ui import (
    POSUI,
    ProductGrid,
    CartPanel,
    PaymentDialog,
    ReceiptViewer,
    CustomerSelector,
    create_pos_ui,
    POSLayout,
)

# ==============================================================================
# EXPORTS - Utilities
# ==============================================================================

from .utils import (
    POSConfig,
    POSError,
    POSValidationError,
    POSPermissionError,
    POSSettings,
    validate_pos_settings,
    get_pos_config,
)

# ==============================================================================
# PACKAGE METADATA
# ==============================================================================

__all__ = [
    # Version
    "POS_VERSION",
    "POS_NAME",
    "POS_DESCRIPTION",
    
    # Engine
    "PriceEngine",
    "MoneyFormatter",
    "TaxCalculator",
    "DiscountEngine",
    "PriceSource",
    "format_money",
    "calculate_tax",
    "calculate_discount",
    
    # Product
    "ProductLoader",
    "ProductSearch",
    "ProductScanner",
    "BarcodeScanner",
    "ProductVariant",
    "get_product_by_barcode",
    "search_products",
    
    # Cart
    "Cart",
    "CartItem",
    "CartManager",
    "CartCalculator",
    "CartPersistence",
    "create_cart",
    "get_cart_manager",
    
    # Payment
    "PaymentProcessor",
    "PaymentMethod",
    "PaymentResult",
    "CheckoutService",
    "PaymentValidator",
    "process_payment",
    "validate_payment",
    
    # Receipt
    "ReceiptGenerator",
    "ReceiptTemplate",
    "ReceiptPrinter",
    "PDFReceipt",
    "EmailReceipt",
    "generate_receipt",
    "print_receipt",
    
    # Cache
    "POSCacheManager",
    "CacheInvalidator",
    "InventoryCache",
    "PriceCache",
    "refresh_cache",
    "invalidate_cache",
    
    # UI
    "POSUI",
    "ProductGrid",
    "CartPanel",
    "PaymentDialog",
    "ReceiptViewer",
    "CustomerSelector",
    "create_pos_ui",
    "POSLayout",
    
    # Utils
    "POSConfig",
    "POSError",
    "POSValidationError",
    "POSPermissionError",
    "POSSettings",
    "validate_pos_settings",
    "get_pos_config",
]

# ==============================================================================
# OPTIONAL MODULE LOADER
# ==============================================================================

def load_pos_module(name: str):
    """
    Safe POS module loader
    
    Example:
        load_pos_module("product")
    """
    import importlib
    return importlib.import_module(f"erp_pages.pos.{name}")


def get_module_info(name: str) -> dict:
    """Get information about a POS module."""
    module_info = {
        "engine": {
            "description": "Price engine and money formatting",
            "version": "2.0",
            "dependencies": [],
        },
        "product": {
            "description": "Product loading and searching",
            "version": "2.0",
            "dependencies": ["cache"],
        },
        "cart": {
            "description": "Shopping cart management",
            "version": "2.0",
            "dependencies": ["product", "engine"],
        },
        "payment": {
            "description": "Payment processing",
            "version": "2.0",
            "dependencies": ["cart", "engine"],
        },
        "receipt": {
            "description": "Receipt generation and printing",
            "version": "2.0",
            "dependencies": ["payment"],
        },
        "cache": {
            "description": "POS cache management",
            "version": "2.0",
            "dependencies": [],
        },
        "ui": {
            "description": "NiceGUI UI components",
            "version": "2.0",
            "dependencies": ["engine", "product", "cart", "payment", "receipt"],
        },
    }
    return module_info.get(name, {})


def get_pos_status() -> dict:
    """Get POS system status."""
    from erp_core.context import ERPContext
    from erp_core.base_repo import database_health_check
    
    context = ERPContext.get_current()
    
    return {
        "version": POS_VERSION,
        "name": POS_NAME,
        "description": POS_DESCRIPTION,
        "database_healthy": database_health_check(),
        "user_id": context.user_id,
        "warehouse_id": context.warehouse_id,
        "modules_loaded": __all__,
    }

# ==============================================================================
# INITIALIZATION
# ==============================================================================

print(f"ERP POS PACKAGE READY - {POS_NAME} v{POS_VERSION}")
print(f"Available modules: {', '.join(__all__[:10])}...")
