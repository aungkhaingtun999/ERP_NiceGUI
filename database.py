"""
==============================================================================
database.py
ERP ENTERPRISE DATABASE GATEWAY v32
Legacy Compatibility Bridge
==============================================================================

Legacy bridge.
Old pages:
from database import ...
New architecture:
erp_core/
This file only re-exports ERP Core APIs.
"""

from erp_core import (
    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    db,
    get_supabase,
    get_connection,
    DatabaseHealth,
    database_health_check,
    search_receipts,  # Added to match __all__
    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------
    get_setting,
    get_products,
    get_inventory_view,
    get_warehouses,
    get_default_warehouse_id,
    get_suppliers,
    get_customers,
    get_receipt,
    get_sale_items,
    # ------------------------------------------------------------------
    # RPC
    # ------------------------------------------------------------------
    checkout_sale_rpc,
    purchase_receive_rpc,
    refund_sale_rpc,
    stock_adjustment_rpc,
    update_product_rpc,
    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------
    SalesService,
    PurchaseService,
    InventoryService,
    RefundService,
    ReceiptService,
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    get_fifo_cogs,
    create_audit_log,
    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    money,
    money_float,
    validate_uuid,
    serialize_json,
    safe_execute,
)

ERP_DATABASE_VERSION = "32.0 Legacy Gateway"


# ==============================================================================
# SERVICE FACTORIES
# ==============================================================================

def get_sales_service():
    return SalesService(db())


def get_purchase_service():
    return PurchaseService(db())


def get_inventory_service():
    return InventoryService(db())


def get_refund_service():
    return RefundService(db())


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [  # Fixed from 'all =' to '__all__ ='
    # Database
    "db",
    "get_supabase",
    "get_connection",
    "DatabaseHealth",
    "database_health_check",
    "search_receipts",
    # Loaders
    "get_setting",
    "get_products",
    "get_inventory_view",
    "get_warehouses",
    "get_default_warehouse_id",
    "get_suppliers",
    "get_customers",
    "get_receipt",
    "get_sale_items",
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
    # Factories
    "get_sales_service",
    "get_purchase_service",
    "get_inventory_service",
    "get_refund_service",
    # Helpers
    "get_fifo_cogs",
    "create_audit_log",
    # Utils
    "money",
    "money_float",
    "validate_uuid",
    "serialize_json",
    "safe_execute",
]

print(
    "stock_adjustment_rpc loaded from:",
    stock_adjustment_rpc.__module__
)

print(
    "signature:",
    stock_adjustment_rpc.__code__.co_varnames
)
