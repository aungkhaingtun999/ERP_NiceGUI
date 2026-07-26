# ==============================================================================
# erp_core/__init__.py
# ERP ENTERPRISE CORE PACKAGE v30.13
# SAFE LAZY IMPORT ARCHITECTURE
# ==============================================================================


"""
ERP CORE PACKAGE

Architecture:

Pages
 |
 └── erp_core
        |
        ├── base_repo
        ├── repositories
        ├── services
        ├── loaders
        └── rpc
              |
              ├── checkout_rpc
              ├── purchase_rpc
              ├── refund_rpc
              └── stock_rpc


"""



# ==============================================================================
# EXCEPTIONS
# ==============================================================================

from .exceptions import *



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
from .context import (
    CacheManager,
)



# ==============================================================================
# DATABASE
# ==============================================================================

from .base_repo import (

    get_supabase,

    db,

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
# RPC ENGINE ONLY
# ==============================================================================
# IMPORTANT:
# DO NOT IMPORT RPC FUNCTIONS HERE
# ==============================================================================

from .rpc.engine import RPCEngine




ERP_CORE_VERSION = "30.13 SAFE RPC LAZY ARCHITECTURE"





# ==============================================================================
# EXPORT MAP
# ==============================================================================


_EXPORTS = {



    # ==========================================================
    # LOADERS
    # ==========================================================


    "get_setting":
        ("loaders", "get_setting"),


    "get_products":
        ("loaders", "get_products"),


    "get_inventory_view":
        ("loaders", "get_inventory_view"),


    "get_warehouses":
        ("loaders", "get_warehouses"),


    "get_default_warehouse_id":
        ("loaders", "get_default_warehouse_id"),


    "get_suppliers":
        ("loaders", "get_suppliers"),


    "get_customers":
        ("loaders", "get_customers"),
    
    "get_receipt":
        ("loaders", "get_receipt"),
    "get_sale_items":
    ("loaders", "get_sale_items"),
    "search_receipts":
    ("loaders", "search_receipts"),




    # ==========================================================
    # SERVICES
    # ==========================================================


    "AccountingLedgerService":
        ("services", "AccountingLedgerService"),


    "CustomerService":
        ("services", "CustomerService"),


    "SalesService":
        ("services", "SalesService"),


    "InventoryService":
        ("services", "InventoryService"),


    "PurchaseService":
        ("services", "PurchaseService"),


    "RefundService":
        ("services", "RefundService"),


    "DashboardService":
        ("services", "DashboardService"),


    "AuditService":
        ("services", "AuditService"),
     "ReceiptService":
    ("services", "ReceiptService"),




    # ==========================================================
    # RPC DIRECT MODULE
    # ==========================================================


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




    # ==========================================================
    # HELPERS
    # ==========================================================


    "get_fifo_cogs":
        (
            "services",
            "get_fifo_cogs"
        ),



    "create_audit_log":
        (
            "services",
            "create_audit_log"
        )

}







# ==============================================================================
# LAZY LOADER
# ==============================================================================


def __getattr__(name):


    if name not in _EXPORTS:

        raise AttributeError(

            f"module 'erp_core' has no attribute '{name}'"

        )



    module_name, object_name = _EXPORTS[name]



    # ----------------------------------------------------------
    # RPC DIRECT IMPORT
    # ----------------------------------------------------------

    if module_name.startswith("rpc."):


        module = __import__(

            f"erp_core.{module_name}",

            fromlist=[object_name]

        )


        return getattr(

            module,

            object_name

        )




    # ----------------------------------------------------------
    # SERVICES
    # ----------------------------------------------------------

    if module_name == "services":


        from . import services


        return getattr(

            services,

            object_name

        )




    # ----------------------------------------------------------
    # LOADERS
    # ----------------------------------------------------------

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



    # CONTEXT

    "ERPContext",

    "CacheManager",



    # RPC ENGINE

    "RPCEngine",



    # LOADERS

    "get_setting",

    "get_products",

    "get_inventory_view",

    "get_warehouses",

    "get_default_warehouse_id",

    "get_suppliers",

    "get_customers",
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

    "AccountingLedgerService",

    "CustomerService",

    "SalesService",

    "InventoryService",

    "PurchaseService",

    "RefundService",

    "DashboardService",

    "AuditService",
    "ReceiptService",
    



    # HELPERS

    "get_fifo_cogs",

    "create_audit_log"

]





print(
    "ERP_CORE v30.13 SAFE RPC LAZY ARCHITECTURE LOADED"
)
