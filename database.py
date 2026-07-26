"""
==============================================================================
database.py
ERP ENTERPRISE DATABASE GATEWAY v33
Legacy Compatibility Bridge
==============================================================================

Legacy pages:
    from database import ...

New architecture:
    erp_core/

This module only re-exports ERP Core APIs.
==============================================================================
"""


# ==============================================================================
# ERP CORE IMPORT
# ==============================================================================

from erp_core import (

    # ------------------------------------------------------------------
    # DATABASE
    # ------------------------------------------------------------------

    db,

    get_supabase,

    get_connection,

    DatabaseHealth,

    database_health_check,


    # ------------------------------------------------------------------
    # LOADERS
    # ------------------------------------------------------------------

    get_setting,

    get_products,

    get_inventory_view,

    get_warehouses,

    get_default_warehouse_id,

    get_suppliers,

    get_customers,


    # ------------------------------------------------------------------
    # RECEIPT
    # ------------------------------------------------------------------

    get_receipt,

    get_sale_items,

    search_receipts,


    # ------------------------------------------------------------------
    # RPC
    # ------------------------------------------------------------------

    checkout_sale_rpc,

    purchase_receive_rpc,

    refund_sale_rpc,

    stock_adjustment_rpc,

    update_product_rpc,


    # ------------------------------------------------------------------
    # SERVICES
    # ------------------------------------------------------------------

    SalesService,

    PurchaseService,

    InventoryService,

    RefundService,

    ReceiptService,


    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    get_fifo_cogs,

    create_audit_log,


    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------

    money,

    money_float,

    validate_uuid,

    serialize_json,

    safe_execute,

)



ERP_DATABASE_VERSION = "33.0 Legacy Gateway"



# ==============================================================================
# SERVICE FACTORIES
# ==============================================================================


def get_sales_service():

    return SalesService(
        db()
    )



def get_purchase_service():

    return PurchaseService(
        db()
    )



def get_inventory_service():

    return InventoryService(
        db()
    )



def get_refund_service():

    return RefundService(
        db()
    )



# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================


__all__ = [


    # ------------------------------------------------------------------
    # DATABASE
    # ------------------------------------------------------------------

    "db",

    "get_supabase",

    "get_connection",

    "DatabaseHealth",

    "database_health_check",



    # ------------------------------------------------------------------
    # LOADERS
    # ------------------------------------------------------------------

    "get_setting",

    "get_products",

    "get_inventory_view",

    "get_warehouses",

    "get_default_warehouse_id",

    "get_suppliers",

    "get_customers",



    # ------------------------------------------------------------------
    # RECEIPT
    # ------------------------------------------------------------------

    "get_receipt",

    "get_sale_items",

    "search_receipts",



    # ------------------------------------------------------------------
    # RPC
    # ------------------------------------------------------------------

    "checkout_sale_rpc",

    "purchase_receive_rpc",

    "refund_sale_rpc",

    "stock_adjustment_rpc",

    "update_product_rpc",



    # ------------------------------------------------------------------
    # SERVICES
    # ------------------------------------------------------------------

    "SalesService",

    "PurchaseService",

    "InventoryService",

    "RefundService",

    "ReceiptService",



    # ------------------------------------------------------------------
    # SERVICE FACTORIES
    # ------------------------------------------------------------------

    "get_sales_service",

    "get_purchase_service",

    "get_inventory_service",

    "get_refund_service",



    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    "get_fifo_cogs",

    "create_audit_log",



    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------

    "money",

    "money_float",

    "validate_uuid",

    "serialize_json",

    "safe_execute",


]


print(
    "ERP DATABASE GATEWAY v33 LOADED"
)
