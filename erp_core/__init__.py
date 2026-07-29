# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE EXPORT HUB v30.8 FINAL
#
# Purpose:
# - Single import gateway
# - Prevent circular import
# - Public API export
#
# Usage:
#
# from erp_core import checkout_sale_rpc
# from erp_core import get_products
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
# DATABASE CORE
# ==============================================================================


from .base_repo import (

    db

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
# RECEIPT
# ==============================================================================


try:


    from .services.receipt_service import (

        ReceiptService

    )


except Exception:


    ReceiptService = None







# ==============================================================================
# CHECKOUT RPC
# ==============================================================================


from .rpc.checkout_rpc import (

    checkout_sale_rpc

)







# ==============================================================================
# INVENTORY
# ==============================================================================


try:


    from .services.inventory_service import (

        InventoryService

    )


except Exception:


    InventoryService = None







# ==============================================================================
# SALES
# ==============================================================================


try:


    from .services.sales_service import (

        SalesService

    )


except Exception:


    SalesService = None







# ==============================================================================
# PURCHASE
# ==============================================================================


try:


    from .services.purchase_service import (

        PurchaseService

    )


except Exception:


    PurchaseService = None







# ==============================================================================
# REFUND
# ==============================================================================


try:


    from .services.refund_service import (

        RefundService

    )


except Exception:


    RefundService = None







# ==============================================================================
# VERSION INFO
# ==============================================================================


__all__ = [



    # Core

    "ERP_VERSION",

    "Tables",

    "CACHE_KEYS",

    "DEFAULT_PAGE_SIZE",

    "db",

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



    # Checkout

    "checkout_sale_rpc",



    # Services

    "ReceiptService",

    "InventoryService",

    "SalesService",

    "PurchaseService",

    "RefundService"


]
