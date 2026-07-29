# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE EXPORT HUB v31.0 FINAL FIX
#
# Public API Gateway
# Legacy database.py Compatible
# Circular Import Safe
# ==============================================================================


# ==============================================================================
# CONFIG
# ==============================================================================

from .config import (
    Tables,
    CACHE_KEYS,
    DEFAULT_PAGE_SIZE,
    ERP_VERSION,
    log_error
)



# ==============================================================================
# DATABASE
# ==============================================================================

from .base_repo import (

    db,

    get_supabase,

    get_connection,

    DatabaseHealth,

    database_health_check,

    money,

    money_float,

    safe_float,

    validate_uuid,

    serialize_json,

    safe_execute

)



# ==============================================================================
# CONTEXT
# ==============================================================================

from .context import (

    CacheManager

)



# ==============================================================================
# PRODUCT
# ==============================================================================

try:

    from .loaders.product_loader import (

        get_products,

        get_pos_products,

        get_active_products,

        refresh_products_cache

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
# SETTINGS
# ==============================================================================

try:

    from .loaders.settings_loader import (

        get_setting

    )

except Exception:


    def get_setting(
        key,
        default=None
    ):

        return default





# ==============================================================================
# WAREHOUSE
# ==============================================================================


try:

    from .loaders.warehouse_loader import (

        get_default_warehouse_id,

        get_warehouses

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

        search_receipts

    )

except Exception:


    def get_receipt(*args, **kwargs):

        return None



    def get_sale_items(*args, **kwargs):

        return []



    def search_receipts(*args, **kwargs):

        return []





# ==============================================================================
# RPC
# ==============================================================================


try:

    from .rpc.checkout_rpc import (

        checkout_sale_rpc

    )

except Exception:


    def checkout_sale_rpc(*args, **kwargs):

        return {

            "success":False,

            "message":"Checkout RPC unavailable"

        }





try:

    from .rpc.purchase_rpc import (

        purchase_receive_rpc

    )

except Exception:


    purchase_receive_rpc = None





try:

    from .rpc.refund_rpc import (

        refund_sale_rpc

    )

except Exception:


    refund_sale_rpc = None





try:

    from .rpc.inventory_rpc import (

        stock_adjustment_rpc

    )

except Exception:


    stock_adjustment_rpc = None





try:

    from .rpc.product_rpc import (

        update_product_rpc

    )

except Exception:


    update_product_rpc = None






# ==============================================================================
# SERVICES
# ==============================================================================


try:

    from .services.sales_service import SalesService

except Exception:

    SalesService = None



try:

    from .services.purchase_service import PurchaseService

except Exception:

    PurchaseService = None



try:

    from .services.inventory_service import InventoryService

except Exception:

    InventoryService = None



try:

    from .services.refund_service import RefundService

except Exception:

    RefundService = None



try:

    from .services.receipt_service import ReceiptService

except Exception:

    ReceiptService = None





# ==============================================================================
# HELPERS
# ==============================================================================


try:

    from .services.inventory_service import (

        get_fifo_cogs

    )

except Exception:


    def get_fifo_cogs(*args, **kwargs):

        return 0





try:

    from .services.audit_service import (

        create_audit_log

    )

except Exception:


    def create_audit_log(*args, **kwargs):

        return None





# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    # Database

    "db",

    "get_supabase",

    "get_connection",

    "DatabaseHealth",

    "database_health_check",


    # Config

    "Tables",

    "CACHE_KEYS",

    "DEFAULT_PAGE_SIZE",

    "ERP_VERSION",

    "log_error",


    # Context

    "CacheManager",


    # Product

    "get_products",

    "get_pos_products",

    "get_active_products",

    "refresh_products_cache",


    # Settings

    "get_setting",


    # Warehouse

    "get_default_warehouse_id",

    "get_warehouses",


    # Receipt

    "get_receipt",

    "get_sale_items",

    "search_receipts",


    # RPC

    "checkout_sale_rpc",

    "purchase_receive_rpc",

    "refund_sale_rpc",

    "stock_adjustment_rpc",

    "update_product_rpc",


    # Services

    "SalesService",

    "PurchaseService",

    "InventoryService",

    "RefundService",

    "ReceiptService",


    # Utils

    "money",

    "money_float",

    "safe_float",

    "validate_uuid",

    "serialize_json",

    "safe_execute",


    # Helpers

    "get_fifo_cogs",

    "create_audit_log"

]


print(
    "ERP CORE HUB v31.0 LOADED"
)
