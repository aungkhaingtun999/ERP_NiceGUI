# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE EXPORT HUB v37.0
#
# DEBUG-SAFE PUBLIC API GATEWAY
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This file is the public export gateway of ERP Core.
#
# During debugging:
#
# - Core imports MUST NOT silently fail.
# - RPC imports MUST NOT be replaced by fallback functions.
# - Service imports MUST expose the real exception.
# - Loader imports MUST expose the real exception.
#
# The purpose of this version is to identify the exact broken module.
# ==============================================================================


print(
    "============================================================"
)

print(
    "ERP CORE START"
)

print(
    "============================================================"
)


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

print(
    "ERP CORE CONFIG: OK"
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

print(
    "ERP CORE DATABASE: OK"
)


# ==============================================================================
# CONTEXT
# ==============================================================================

from .context import (
    CacheManager,
)

print(
    "ERP CORE CONTEXT: OK"
)


# ==============================================================================
# PRODUCT LOADERS
# ==============================================================================

from .loaders.product_loader import (
    get_products,
    get_pos_products,
    get_active_products,
    refresh_products_cache,
)

print(
    "ERP CORE PRODUCT LOADER: OK"
)


# ==============================================================================
# INVENTORY LOADER
# ==============================================================================

from .loaders.inventory_loader import (
    get_inventory_view,
)

print(
    "ERP CORE INVENTORY LOADER: OK"
)


# ==============================================================================
# CUSTOMER LOADER
# ==============================================================================

from .loaders.customer_loader import (
    get_customers,
)

print(
    "ERP CORE CUSTOMER LOADER: OK"
)


# ==============================================================================
# SUPPLIER LOADER
# ==============================================================================

from .loaders.supplier_loader import (
    get_suppliers,
)

print(
    "ERP CORE SUPPLIER LOADER: OK"
)


# ==============================================================================
# CATEGORY LOADER
# ==============================================================================

from .loaders.category_loader import (
    get_categories,
)

print(
    "ERP CORE CATEGORY LOADER: OK"
)


# ==============================================================================
# SETTINGS LOADER
# ==============================================================================

from .loaders.settings_loader import (
    get_setting,
)

print(
    "ERP CORE SETTINGS LOADER: OK"
)


# ==============================================================================
# WAREHOUSE LOADER
# ==============================================================================

from .loaders.warehouse_loader import (
    get_default_warehouse_id,
    get_warehouses,
)

print(
    "ERP CORE WAREHOUSE LOADER: OK"
)


# ==============================================================================
# RECEIPT LOADER
# ==============================================================================

from .loaders.receipt_loader import (
    get_receipt,
    get_sale_items,
    get_full_receipt,
    search_receipts,
)

print(
    "ERP CORE RECEIPT LOADER: OK"
)


# ==============================================================================
# RPC
# ==============================================================================
#
# IMPORTANT
# ------------------------------------------------------------------------------
# RPC imports are intentionally separated.
#
# This allows deployment logs to identify the exact RPC wrapper that fails.
#
# Do NOT use:
#
#     from .rpc import (...)
#
# while debugging the RPC package.
#
# ==============================================================================


# ------------------------------------------------------------------------------
# CHECKOUT
# ------------------------------------------------------------------------------

try:

    from .rpc.checkout_rpc import (
        checkout_sale_rpc,
    )

except Exception as e:

    raise ImportError(
        "ERP CORE: checkout_rpc import failed: "
        f"{type(e).__name__}: {e}"
    ) from e


# ------------------------------------------------------------------------------
# PURCHASE
# ------------------------------------------------------------------------------

try:

    from .rpc.purchase_rpc import (
        purchase_receive_rpc,
    )

except Exception as e:

    raise ImportError(
        "ERP CORE: purchase_rpc import failed: "
        f"{type(e).__name__}: {e}"
    ) from e


# ------------------------------------------------------------------------------
# REFUND
# ------------------------------------------------------------------------------

try:

    from .rpc.refund_rpc import (
        refund_sale_rpc,
    )

except Exception as e:

    raise ImportError(
        "ERP CORE: refund_rpc import failed: "
        f"{type(e).__name__}: {e}"
    ) from e


# ------------------------------------------------------------------------------
# STOCK
# ------------------------------------------------------------------------------

try:

    from .rpc.stock_rpc import (
        stock_adjustment_rpc,
        update_product_rpc,
    )

except Exception as e:

    raise ImportError(
        "ERP CORE: stock_rpc import failed: "
        f"{type(e).__name__}: {e}"
    ) from e


# ------------------------------------------------------------------------------
# PRODUCT
# ------------------------------------------------------------------------------

try:

    from .rpc.product_rpc import (
        request_product_create_rpc,
        request_product_bulk_create_rpc,
        approve_product_create_rpc,
    )

except Exception as e:

    raise ImportError(
        "ERP CORE: product_rpc import failed: "
        f"{type(e).__name__}: {e}"
    ) from e


print("ERP CORE RPC IMPORT: OK")
# ==============================================================================
# SERVICES
# ==============================================================================

from .services.sales_service import (
    SalesService,
)

print(
    "ERP CORE SALES SERVICE: OK"
)


from .services.purchase_service import (
    PurchaseService,
)

print(
    "ERP CORE PURCHASE SERVICE: OK"
)


from .services.inventory_service import (
    InventoryService,
)

print(
    "ERP CORE INVENTORY SERVICE: OK"
)


from .services.refund_service import (
    RefundService,
)

print(
    "ERP CORE REFUND SERVICE: OK"
)


from .services.receipt_service import (
    ReceiptService,
)

print(
    "ERP CORE RECEIPT SERVICE: OK"
)


from .services.payment_service import (
    PaymentService,
)

print(
    "ERP CORE PAYMENT SERVICE: OK"
)


from .services.payment_qr_service import (
    PaymentQRService,
)

print(
    "ERP CORE PAYMENT QR SERVICE: OK"
)


# ==============================================================================
# HELPERS
# ==============================================================================

from .services.inventory_service import (
    get_fifo_cogs,
)

print(
    "ERP CORE FIFO COGS: OK"
)


from .services.audit_service import (
    create_audit_log,
)

print(
    "ERP CORE AUDIT SERVICE: OK"
)


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [

    # --------------------------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------------------------

    "db",
    "privileged_db",
    "get_supabase",
    "get_service_supabase",
    "get_connection",

    "DatabaseHealth",
    "database_health_check",


    # --------------------------------------------------------------------------
    # CONFIG
    # --------------------------------------------------------------------------

    "Tables",
    "CACHE_KEYS",
    "DEFAULT_PAGE_SIZE",
    "ERP_VERSION",
    "log_error",


    # --------------------------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------------------------

    "CacheManager",


    # --------------------------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------------------------

    "get_products",
    "get_pos_products",
    "get_active_products",
    "refresh_products_cache",


    # --------------------------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------------------------

    "get_inventory_view",


    # --------------------------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------------------------

    "get_customers",


    # --------------------------------------------------------------------------
    # SUPPLIER
    # --------------------------------------------------------------------------

    "get_suppliers",


    # --------------------------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------------------------

    "get_categories",


    # --------------------------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------------------------

    "get_setting",


    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    "get_default_warehouse_id",
    "get_warehouses",


    # --------------------------------------------------------------------------
    # RECEIPT
    # --------------------------------------------------------------------------

    "get_receipt",
    "get_sale_items",
    "get_full_receipt",
    "search_receipts",


    # --------------------------------------------------------------------------
    # RPC
    # --------------------------------------------------------------------------

    "checkout_sale_rpc",
    "purchase_receive_rpc",
    "refund_sale_rpc",
    "stock_adjustment_rpc",
    "update_product_rpc",

    "request_product_create_rpc",
    "request_product_bulk_create_rpc",
    "approve_product_create_rpc",


    # --------------------------------------------------------------------------
    # SERVICES
    # --------------------------------------------------------------------------

    "SalesService",
    "PurchaseService",
    "InventoryService",
    "RefundService",
    "ReceiptService",
    "PaymentService",
    "PaymentQRService",


    # --------------------------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------------------------

    "get_fifo_cogs",
    "create_audit_log",


    # --------------------------------------------------------------------------
    # UTILITIES
    # --------------------------------------------------------------------------

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

ERP_CORE_EXPORT_VERSION = "37.0"


print(
    "============================================================"
)

print(
    f"ERP CORE HUB v{ERP_CORE_EXPORT_VERSION} LOADED"
)

print(
    "============================================================"
)
