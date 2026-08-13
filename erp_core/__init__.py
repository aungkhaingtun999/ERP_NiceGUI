# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE EXPORT HUB v36.0 FINAL
#
# PUBLIC API GATEWAY
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
# DATABASE
# ==============================================================================

from .base_repo import (
    db,
    privileged_db,
    get_supabase,
    get_service_supabase,
    get_connection,
    DatabaseHealth,
    database_health_check,
    money,
    money_float,
    safe_float,
    validate_uuid,
    serialize_json,
    safe_execute,
)


# ==============================================================================
# CONTEXT
# ==============================================================================

from .context import (
    CacheManager,
)


# ==============================================================================
# PRODUCT LOADERS
# ==============================================================================

try:

    from .loaders.product_loader import (
        get_products,
        get_pos_products,
        get_active_products,
        refresh_products_cache,
    )

except Exception as e:

    log_error(
        message=
            "Product loader import failed",
        exception=e,
    )

    def get_products(*args, **kwargs):
        return []

    def get_pos_products(*args, **kwargs):
        return []

    def get_active_products(*args, **kwargs):
        return []

    def refresh_products_cache():
        pass


# ==============================================================================
# INVENTORY
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

except Exception as e:

    log_error(
        message=
            "Warehouse loader import failed",
        exception=e,
    )

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

try:

    from .rpc import (

        checkout_sale_rpc,

        purchase_receive_rpc,

        refund_sale_rpc,

        stock_adjustment_rpc,

        update_product_rpc,

        request_product_create_rpc,

        request_product_bulk_create_rpc,

        approve_product_create_rpc,

    )

except Exception as e:

    log_error(
        message="ERP RPC package import failed",
        exception=e,
    )


    def checkout_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "checkout_sale_rpc unavailable",
        }


    def purchase_receive_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "purchase_receive_rpc unavailable",
        }


    def refund_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "refund_sale_rpc unavailable",
        }


    def stock_adjustment_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "stock_adjustment_rpc unavailable",
        }


    def update_product_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "update_product_rpc unavailable",
        }


    def request_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "request_product_create_rpc unavailable",
        }


    def request_product_bulk_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "request_product_bulk_create_rpc unavailable",
        }


    def approve_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "approve_product_create_rpc unavailable",
        }
# ==============================================================================
# SERVICES
# ==============================================================================

try:

    from .services.sales_service import (
        SalesService,
    )

except Exception:

    SalesService = None


try:

    from .services.purchase_service import (
        PurchaseService,
    )

except Exception:

    PurchaseService = None


try:

    from .services.inventory_service import (
        InventoryService,
    )

except Exception:

    InventoryService = None


try:

    from .services.refund_service import (
        RefundService,
    )

except Exception:

    RefundService = None


try:

    from .services.receipt_service import (
        ReceiptService,
    )

except Exception:

    ReceiptService = None


try:

    from .services.payment_service import (
        PaymentService,
    )

except Exception:

    PaymentService = None


try:

    from .services.payment_qr_service import (
        PaymentQRService,
    )

except Exception:

    PaymentQRService = None


# ==============================================================================
# HELPERS
# ==============================================================================

try:

    from .services.inventory_service import (
        get_fifo_cogs,
    )

except Exception:

    def get_fifo_cogs(*args, **kwargs):
        return 0


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

    # DATABASE

    "db",
    "privileged_db",
    "get_supabase",
    "get_service_supabase",
    "get_connection",
    "DatabaseHealth",
    "database_health_check",

    # CONFIG

    "Tables",
    "CACHE_KEYS",
    "DEFAULT_PAGE_SIZE",
    "ERP_VERSION",
    "log_error",

    # CONTEXT

    "CacheManager",

    # PRODUCT

    "get_products",
    "get_pos_products",
    "get_active_products",
    "refresh_products_cache",
    "get_inventory_view",

    # SUPPLIER

    "get_suppliers",

    # CATEGORY

    "get_categories",

    # CUSTOMER

    "get_customers",

    # SETTINGS

    "get_setting",

    # WAREHOUSE

    "get_default_warehouse_id",
    "get_warehouses",

    # RECEIPT

    "get_receipt",
    "get_sale_items",
    "get_full_receipt",
    "search_receipts",

    # RPC

    "checkout_sale_rpc",
    "purchase_receive_rpc",
    "refund_sale_rpc",
    "stock_adjustment_rpc",
    "update_product_rpc",

    "request_product_create_rpc",
    "request_product_bulk_create_rpc",
    "approve_product_create_rpc",

    # SERVICES

    "SalesService",
    "PurchaseService",
    "InventoryService",
    "RefundService",
    "ReceiptService",
    "PaymentService",
    "PaymentQRService",

    # HELPERS

    "get_fifo_cogs",
    "create_audit_log",

    # UTILITIES

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

ERP_CORE_EXPORT_VERSION = "36.0"


print(
    f"ERP CORE HUB v{ERP_CORE_EXPORT_VERSION} LOADED"
)
