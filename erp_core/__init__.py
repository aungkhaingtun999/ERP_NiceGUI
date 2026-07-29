# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE EXPORT HUB v30.9 FINAL
#
# Public API Gateway
# Legacy database.py compatible
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

    log_error

)





# ==============================================================================
# DATABASE
# ==============================================================================

from .base_repo import (

    db

)





# ==============================================================================
# SUPABASE COMPATIBILITY
# ==============================================================================


def get_supabase():

    """
    Legacy compatibility wrapper

    Old modules:
        from erp_core import get_supabase

    New architecture:
        from erp_core.base_repo import db
    """

    return db()







# ==============================================================================
# CONTEXT
# ==============================================================================

from .context import (

    CacheManager

)





# ==============================================================================
# PRODUCT
# ==============================================================================

from .loaders.product_loader import (

    get_products,

    get_pos_products,

    get_active_products,

    refresh_products_cache

)





# ==============================================================================
# SETTINGS
# ==============================================================================

from .loaders.settings_loader import (

    get_setting

)





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
# CHECKOUT
# ==============================================================================


from .rpc.checkout_rpc import (

    checkout_sale_rpc

)







# ==============================================================================
# SERVICES
# ==============================================================================


try:

    from .services.receipt_service import (

        ReceiptService

    )


except Exception:

    ReceiptService = None





try:

    from .services.inventory_service import (

        InventoryService

    )


except Exception:

    InventoryService = None





try:

    from .services.sales_service import (

        SalesService

    )


except Exception:

    SalesService = None





try:

    from .services.purchase_service import (

        PurchaseService

    )


except Exception:

    PurchaseService = None





try:

    from .services.refund_service import (

        RefundService

    )


except Exception:

    RefundService = None







# ==============================================================================
# EXPORT LIST
# ==============================================================================


__all__ = [


    # Core

    "ERP_VERSION",

    "Tables",

    "CACHE_KEYS",

    "DEFAULT_PAGE_SIZE",

    "log_error",



    # Database

    "db",

    "get_supabase",



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



    # RPC

    "checkout_sale_rpc",



    # Services

    "ReceiptService",

    "InventoryService",

    "SalesService",

    "PurchaseService",

    "RefundService"

]
