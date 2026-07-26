# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE PACKAGE v31.0
# CLEAN LAZY IMPORT ARCHITECTURE
# ==============================================================================


"""
ERP CORE

Structure:

Pages
 |
 └── erp_core
        |
        ├── config
        ├── context
        ├── base_repo
        ├── repositories
        ├── services
        ├── loaders
        └── rpc


"""



# ==============================================================================
# CONFIG
# ==============================================================================

from .config import (
    Tables,
    TABLE_PRODUCT_VIEW,
    DEFAULT_PAGE_SIZE,
    log_error
)



# ==============================================================================
# CONTEXT
# ==============================================================================

from .context import (
    ERPContext,
    CacheManager,
    get_cache_version,
    bump_cache,
    bump_inventory_version,
    bump_product_version,
    bump_sales_version
)



# ==============================================================================
# DATABASE CORE
# ==============================================================================

from .base_repo import (

    db,

    get_supabase,

    get_connection,

    DatabaseHealth,

    database_health_check,

    money,

    money_float,

    validate_uuid,

    serialize_json,

    safe_execute

)



# ==============================================================================
# REPOSITORIES
# ==============================================================================

from .repositories import (

    RepositoryCoordinator,

    BaseRepository,

    ProductRepository,

    WarehouseRepository,

    CustomerRepository,

    SupplierRepository,

    SalesRepository

)



# ==============================================================================
# RPC ENGINE
# ==============================================================================

from .rpc.engine import RPCEngine




ERP_CORE_VERSION = "31.0 CLEAN LAZY ARCHITECTURE"



# ==============================================================================
# LAZY EXPORT MAP
# ==============================================================================


_EXPORTS = {


    # ----------------------------------------------------------
    # LOADERS
    # ----------------------------------------------------------

    "get_setting":
        ("loaders", "get_setting"),


    "get_products":
        ("loaders", "get_products"),


    "get_inventory_view":
        ("loaders", "get_inventory_view"),


    "get_default_warehouse_id":
        ("loaders", "get_default_warehouse_id"),


    "get_warehouses":
        ("loaders", "get_warehouses"),


    "get_customers":
        ("loaders", "get_customers"),


    "get_suppliers":
        ("loaders", "get_suppliers"),



    # ----------------------------------------------------------
    # RECEIPT
    # ----------------------------------------------------------

    "get_receipt":
        ("loaders", "get_receipt"),


    "get_sale_items":
        ("loaders", "get_sale_items"),


    "search_receipts":
        ("loaders", "search_receipts"),



    # ----------------------------------------------------------
    # SERVICES
    # ----------------------------------------------------------

    "SalesService":
        ("services", "SalesService"),


    "InventoryService":
        ("services", "InventoryService"),


    "PurchaseService":
        ("services", "PurchaseService"),


    "RefundService":
        ("services", "RefundService"),


    "CustomerService":
        ("services", "CustomerService"),


    "ReceiptService":
        ("services", "ReceiptService"),


    "DashboardService":
        ("services", "DashboardService"),



    # ----------------------------------------------------------
    # RPC
    # ----------------------------------------------------------

    "checkout_sale_rpc":
        (
            "rpc.checkout_rpc",
            "checkout_sale_rpc"
        ),


    "purchase_receive_rpc":
        (
            "rpc.purchase_rpc",
            "purchase_receive_rpc"
        ),


    "refund_sale_rpc":
        (
            "rpc.refund_rpc",
            "refund_sale_rpc"
        ),


    "stock_adjustment_rpc":
        (
            "rpc.stock_rpc",
            "stock_adjustment_rpc"
        ),


    "update_product_rpc":
        (
            "rpc.stock_rpc",
            "update_product_rpc"
        ),



    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------

    "get_fifo_cogs":
        (
            "services",
            "get_fifo_cogs"
        )

}





# ==============================================================================
# LAZY IMPORT FUNCTION
# ==============================================================================


def __getattr__(name):


    if name not in _EXPORTS:

        raise AttributeError(
            f"erp_core has no attribute '{name}'"
        )



    module_name, object_name = _EXPORTS[name]



    # RPC

    if module_name.startswith("rpc."):


        module = __import__(

            f"erp_core.{module_name}",

            fromlist=[object_name]

        )


        return getattr(
            module,
            object_name
        )



    # SERVICES

    if module_name == "services":


        from . import services


        return getattr(
            services,
            object_name
        )



    # LOADERS

    if module_name == "loaders":


        from . import loaders


        return getattr(
            loaders,
            object_name
        )



    raise AttributeError(name)





# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================


__all__ = [


    "ERP_CORE_VERSION",


    # DATABASE

    "db",
    "get_supabase",
    "get_connection",


    # MONEY

    "money",
    "money_float",


    # CONFIG

    "Tables",
    "TABLE_PRODUCT_VIEW",


    # CACHE

    "CacheManager",
    "get_cache_version",
    "bump_cache",
    "bump_inventory_version",
    "bump_product_version",
    "bump_sales_version",


    # REPOSITORY

    "RepositoryCoordinator",
    "BaseRepository",
    "ProductRepository",


    # LOADERS

    "get_setting",
    "get_products",
    "get_inventory_view",
    "get_default_warehouse_id",
    "get_warehouses",
    "get_customers",
    "get_suppliers",
    "get_receipt",
    "get_sale_items",
    "search_receipts",


    # RPC

    "checkout_sale_rpc",
    "purchase_receive_rpc",
    "refund_sale_rpc",
    "stock_adjustment_rpc",
    "update_product_rpc",


    # SERVICES

    "SalesService",
    "InventoryService",
    "PurchaseService",
    "RefundService",
    "CustomerService",
    "ReceiptService",
    "DashboardService",


    # RPC ENGINE

    "RPCEngine"

]




print(
    "ERP_CORE v31.0 CLEAN LAZY ARCHITECTURE LOADED"
)
