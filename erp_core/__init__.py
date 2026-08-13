# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE EXPORT HUB v36.0
#
# PUBLIC API GATEWAY
#
# Legacy:
#     from database import ...
#
# New:
#     from erp_core import ...
#
# Maker / Checker:
#     request_product_create_rpc
#     request_product_bulk_create_rpc
#     approve_product_create_rpc
#
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
# PRODUCT LOADER
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
        message="Product loader import failed",
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
# INVENTORY LOADER
# ==============================================================================

try:

    from .loaders.inventory_loader import (
        get_inventory_view,
    )

except Exception as e:

    log_error(
        message="Inventory loader import failed",
        exception=e,
    )

    def get_inventory_view(*args, **kwargs):
        return []


# ==============================================================================
# CUSTOMER LOADER
# ==============================================================================

try:

    from .loaders.customer_loader import (
        get_customers,
    )

except Exception as e:

    log_error(
        message="Customer loader import failed",
        exception=e,
    )

    def get_customers(*args, **kwargs):
        return []


# ==============================================================================
# SUPPLIER LOADER
# ==============================================================================

try:

    from .loaders.supplier_loader import (
        get_suppliers,
    )

except Exception as e:

    log_error(
        message="Supplier loader import failed",
        exception=e,
    )

    def get_suppliers(*args, **kwargs):
        return []


# ==============================================================================
# CATEGORY LOADER
# ==============================================================================

try:

    from .loaders.category_loader import (
        get_categories,
    )

except Exception as e:

    log_error(
        message="Category loader import failed",
        exception=e,
    )

    def get_categories(*args, **kwargs):
        return []


# ==============================================================================
# SETTINGS LOADER
# ==============================================================================

try:

    from .loaders.settings_loader import (
        get_setting,
    )

except Exception as e:

    log_error(
        message="Settings loader import failed",
        exception=e,
    )

    def get_setting(
        key,
        default=None,
    ):
        return default


# ==============================================================================
# WAREHOUSE LOADER
# ==============================================================================

try:

    from .loaders.warehouse_loader import (
        get_default_warehouse_id,
        get_warehouses,
    )

except Exception as e:

    log_error(
        message="Warehouse loader import failed",
        exception=e,
    )

    def get_default_warehouse_id():
        return None

    def get_warehouses():
        return []


# ==============================================================================
# RECEIPT LOADER
# ==============================================================================

try:

    from .loaders.receipt_loader import (
        get_receipt,
        get_sale_items,
        get_full_receipt,
        search_receipts,
    )

except Exception as e:

    log_error(
        message="Receipt loader import failed",
        exception=e,
    )

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
# RPC PACKAGE
#
# IMPORTANT
# ------------------------------------------------------------------------------
# All public RPC functions come from erp_core.rpc
#
# DO NOT import the same RPC again from individual modules below.
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

    # --------------------------------------------------------------------------
    # SAFE FALLBACKS
    # --------------------------------------------------------------------------

    def checkout_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "checkout_sale_rpc unavailable",
        }


    def purchase_receive_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "purchase_receive_rpc unavailable",
        }


    def refund_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "refund_sale_rpc unavailable",
        }


    def stock_adjustment_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "stock_adjustment_rpc unavailable",
        }


    def update_product_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "update_product_rpc unavailable",
        }


    def request_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "request_product_create_rpc unavailable",
        }


    def request_product_bulk_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "request_product_bulk_create_rpc unavailable",
        }


    def approve_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "approve_product_create_rpc unavailable",
        }


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

except Exception as e:

    log_error(
        message="SalesService import failed",
        exception=e,
    )

    SalesService = None


# ------------------------------------------------------------------------------
# PURCHASE
# ------------------------------------------------------------------------------

try:

    from .services.purchase_service import (
        PurchaseService,
    )

except Exception as e:

    log_error(
        message="PurchaseService import failed",
        exception=e,
    )

    PurchaseService = None


# ------------------------------------------------------------------------------
# INVENTORY
# ------------------------------------------------------------------------------

try:

    from .services.inventory_service import (
        InventoryService,
    )

except Exception as e:

    log_error(
        message="InventoryService import failed",
        exception=e,
    )

    InventoryService = None


# ------------------------------------------------------------------------------
# REFUND
# ------------------------------------------------------------------------------

try:

    from .services.refund_service import (
        RefundService,
    )

except Exception as e:

    log_error(
        message="RefundService import failed",
        exception=e,
    )

    RefundService = None


# ------------------------------------------------------------------------------
# RECEIPT
# ------------------------------------------------------------------------------

try:

    from .services.receipt_service import (
        ReceiptService,
    )

except Exception as e:

    log_error(
        message="ReceiptService import failed",
        exception=e,
    )

    ReceiptService = None


# ------------------------------------------------------------------------------
# PAYMENT
# ------------------------------------------------------------------------------

try:

    from .services.payment_service import (
        PaymentService,
    )

except Exception as e:

    log_error(
        message="PaymentService import failed",
        exception=e,
    )

    PaymentService = None


# ------------------------------------------------------------------------------
# PAYMENT QR
# ------------------------------------------------------------------------------

try:

    from .services.payment_qr_service import (
        PaymentQRService,
    )

except Exception as e:

    log_error(
        message="PaymentQRService import failed",
        exception=e,
    )

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

    "request_product_create_rpc",
    "request_product_bulk_create_rpc",
    "approve_product_create_rpc",


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

ERP_CORE_EXPORT_VERSION = "36.0"


print(
    f"ERP CORE HUB v{ERP_CORE_EXPORT_VERSION} LOADED"
)
