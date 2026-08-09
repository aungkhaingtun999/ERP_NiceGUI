
# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE EXPORT HUB v35.0
#
# PUBLIC API GATEWAY
# ------------------------------------------------------------------------------
# Legacy database.py Compatible
# Circular Import Safe
#
# MAKER / CHECKER SUPPORT
# ------------------------------------------------------------------------------
# db()
#     -> Normal Supabase client
#
# privileged_db()
#     -> Server-side service_role client
#     -> NEVER exposed to browser
#
# create_product_full()
#     -> Direct authenticated access remains disabled
#
# request_product_create_rpc()
# approve_product_create_rpc()
#     -> Called through protected server-side RPC flow
# ==============================================================================


# ==============================================================================
# CONFIG
# ==============================================================================

from .config import (
    Tables,
    CACHE_KEYS,
    DEFAULT_PAGE_SIZE,
    ERP_VERSION,
    log_error,
)


# ==============================================================================
# DATABASE & UTILITIES
# ------------------------------------------------------------------------------
# base_repo.py
# ==============================================================================

from .base_repo import (
    # Normal database
    db,
    get_supabase,
    get_connection,

    # Privileged server database
    privileged_db,
    get_service_supabase,

    # Health
    DatabaseHealth,
    database_health_check,

    # Money
    money,
    money_float,
    safe_float,

    # UUID
    validate_uuid,

    # JSON
    serialize_json,

    # Safe execution
    safe_execute,
)


# ==============================================================================
# CONTEXT
# ==============================================================================

from .context import (
    CacheManager,
)


# ==============================================================================
# INVENTORY / PRODUCT
# ==============================================================================

try:

    from .loaders.product_loader import (
        get_products,
        get_pos_products,
        get_active_products,
        refresh_products_cache,
    )

except Exception:

    def get_products(*args, **kwargs):
        return []


    def get_pos_products(*args, **kwargs):
        return []


    def get_active_products(*args, **kwargs):
        return []


    def refresh_products_cache():
        pass


# ==============================================================================
# INVENTORY VIEW
# ==============================================================================

try:

    from .loaders.inventory_loader import (
        get_inventory_view,
    )

except Exception:

    def get_inventory_view(*args, **kwargs):
        return []


# ==============================================================================
# CUSTOMER
# ==============================================================================

try:

    from .loaders.customer_loader import (
        get_customers,
    )

except Exception:

    def get_customers(*args, **kwargs):
        return []


# ==============================================================================
# SUPPLIER
# ==============================================================================

try:

    from .loaders.supplier_loader import (
        get_suppliers,
    )

except Exception:

    def get_suppliers(*args, **kwargs):
        return []


# ==============================================================================
# CATEGORY
# ==============================================================================

try:

    from .loaders.category_loader import (
        get_categories,
    )

except Exception:

    def get_categories(*args, **kwargs):
        return []


# ==============================================================================
# SETTINGS
# ==============================================================================

try:

    from .loaders.settings_loader import (
        get_setting,
    )

except Exception:

    def get_setting(
        key,
        default=None,
    ):
        return default


# ==============================================================================
# WAREHOUSE
# ==============================================================================

try:

    from .loaders.warehouse_loader import (
        get_default_warehouse_id,
        get_warehouses,
    )

except Exception:

    def get_default_warehouse_id():
        return None


    def get_warehouses():
        return []


# ==============================================================================
# RECEIPT
# ==============================================================================

try:

    from .loaders.receipt_loader import (
        get_receipt,
        get_sale_items,
        get_full_receipt,
        search_receipts,
    )

except Exception:

    def get_receipt(*args, **kwargs):
        return None


    def get_sale_items(*args, **kwargs):
        return []


    def get_full_receipt(*args, **kwargs):

        return {
            "success": False,
            "sale": {},
            "items": [],
        }


    def search_receipts(*args, **kwargs):
        return []


# ==============================================================================
# RPC
# ==============================================================================

# ------------------------------------------------------------------------------
# CHECKOUT
# ------------------------------------------------------------------------------

try:

    from .rpc.checkout_rpc import (
        checkout_sale_rpc,
    )

except Exception:

    def checkout_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "Checkout RPC unavailable",
        }


# ------------------------------------------------------------------------------
# PURCHASE
# ------------------------------------------------------------------------------

try:

    from .rpc.purchase_rpc import (
        purchase_receive_rpc,
    )

except Exception:

    purchase_receive_rpc = None


# ------------------------------------------------------------------------------
# REFUND
# ------------------------------------------------------------------------------

try:

    from .rpc.refund_rpc import (
        refund_sale_rpc,
    )

except Exception:

    refund_sale_rpc = None


# ------------------------------------------------------------------------------
# INVENTORY
# ------------------------------------------------------------------------------

try:

    from .rpc.inventory_rpc import (
        stock_adjustment_rpc,
    )

except Exception:

    stock_adjustment_rpc = None


# ------------------------------------------------------------------------------
# PRODUCT
# ------------------------------------------------------------------------------

try:

    from .rpc.product_rpc import (
        update_product_rpc,
    )

except Exception:

    update_product_rpc = None


# ==============================================================================
# SERVICES
# ==============================================================================

# ------------------------------------------------------------------------------
# SALES
# ------------------------------------------------------------------------------

try:

    from .services.sales_service import (
        SalesService,
    )

except Exception:

    SalesService = None


# ------------------------------------------------------------------------------
# PURCHASE
# ------------------------------------------------------------------------------

try:

    from .services.purchase_service import (
        PurchaseService,
    )

except Exception:

    PurchaseService = None


# ------------------------------------------------------------------------------
# INVENTORY
# ------------------------------------------------------------------------------

try:

    from .services.inventory_service import (
        InventoryService,
    )

except Exception:

    InventoryService = None


# ------------------------------------------------------------------------------
# REFUND
# ------------------------------------------------------------------------------

try:

    from .services.refund_service import (
        RefundService,
    )

except Exception:

    RefundService = None


# ------------------------------------------------------------------------------
# RECEIPT
# ------------------------------------------------------------------------------

try:

    from .services.receipt_service import (
        ReceiptService,
    )

except Exception:

    ReceiptService = None


# ------------------------------------------------------------------------------
# PAYMENT
# ------------------------------------------------------------------------------

try:

    from .services.payment_service import (
        PaymentService,
    )

except Exception:

    PaymentService = None


# ------------------------------------------------------------------------------
# PAYMENT QR
# ------------------------------------------------------------------------------

try:

    from .services.payment_qr_service import (
        PaymentQRService,
    )

except Exception:

    PaymentQRService = None


# ==============================================================================
# HELPERS
# ==============================================================================

# ------------------------------------------------------------------------------
# FIFO COGS
# ------------------------------------------------------------------------------

try:

    from .services.inventory_service import (
        get_fifo_cogs,
    )

except Exception:

    def get_fifo_cogs(*args, **kwargs):
        return 0


# ------------------------------------------------------------------------------
# AUDIT LOG
# ------------------------------------------------------------------------------

try:

    from .services.audit_service import (
        create_audit_log,
    )

except Exception:

    def create_audit_log(*args, **kwargs):
        return None


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [

    # ==========================================================================
    # DATABASE
    # ==========================================================================

    "db",
    "privileged_db",

    "get_supabase",
    "get_service_supabase",

    "get_connection",

    "DatabaseHealth",
    "database_health_check",


    # ==========================================================================
    # CONFIG
    # ==========================================================================

    "Tables",
    "CACHE_KEYS",
    "DEFAULT_PAGE_SIZE",
    "ERP_VERSION",
    "log_error",


    # ==========================================================================
    # CONTEXT
    # ==========================================================================

    "CacheManager",


    # ==========================================================================
    # PRODUCT
    # ==========================================================================

    "get_products",
    "get_pos_products",
    "get_active_products",
    "refresh_products_cache",
    "get_inventory_view",


    # ==========================================================================
    # SUPPLIER
    # ==========================================================================

    "get_suppliers",


    # ==========================================================================
    # CATEGORY
    # ==========================================================================

    "get_categories",


    # ==========================================================================
    # CUSTOMER
    # ==========================================================================

    "get_customers",


    # ==========================================================================
    # SETTINGS
    # ==========================================================================

    "get_setting",


    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================

    "get_default_warehouse_id",
    "get_warehouses",


    # ==========================================================================
    # RECEIPT
    # ==========================================================================

    "get_receipt",
    "get_sale_items",
    "get_full_receipt",
    "search_receipts",


    # ==========================================================================
    # RPC
    # ==========================================================================

    "checkout_sale_rpc",
    "purchase_receive_rpc",
    "refund_sale_rpc",
    "stock_adjustment_rpc",
    "update_product_rpc",


    # ==========================================================================
    # SERVICES
    # ==========================================================================

    "SalesService",
    "PurchaseService",
    "InventoryService",
    "RefundService",
    "ReceiptService",
    "PaymentService",
    "PaymentQRService",


    # ==========================================================================
    # HELPERS
    # ==========================================================================

    "get_fifo_cogs",
    "create_audit_log",


    # ==========================================================================
    # UTILITIES
    # ==========================================================================

    "money",
    "money_float",
    "safe_float",
    "validate_uuid",
    "serialize_json",
    "safe_execute",
]


# ==============================================================================
# VERSION
# ==============================================================================

ERP_CORE_EXPORT_VERSION = "35.0"


print(
    f"ERP CORE HUB v{ERP_CORE_EXPORT_VERSION} LOADED"
)

