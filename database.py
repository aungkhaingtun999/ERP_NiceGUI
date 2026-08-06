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
    get_categories,

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
    # (update_product_rpc ကို ဤနေရာမှ ဖယ်ရှားပြီးပါပြီ)


    # ------------------------------------------------------------------
    # SERVICES
    # ------------------------------------------------------------------

    SalesService,

    PurchaseService,

    InventoryService,

    RefundService,

    ReceiptService,
    PaymentService,
    PaymentQRService,

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
# PAYMENT HELPERS
# ==============================================================================

def create_mobile_payment(
    sale_id,
    provider,
    transaction_id,
    amount,
    cashier_id=None
):

    return PaymentService.create_mobile_payment(
        sale_id=sale_id,
        provider=provider,
        transaction_id=transaction_id,
        amount=amount,
        cashier_id=cashier_id
    )


def verify_payment(
    payment_id,
    verified_by
):

    return PaymentService.verify_payment(
        payment_id,
        verified_by
    )


def reject_payment(
    payment_id,
    verified_by,
    reason
):

    return PaymentService.reject_payment(
        payment_id,
        verified_by,
        reason
    )


def get_pending_payments():

    return PaymentService.pending_payments()


def generate_payment_qr(
    provider="",
    account_name="",
    account_no="",
    amount=0,
    sale_id="",
    raw_payload=None
):

    return PaymentQRService.generate_qr(
        provider=provider,
        account_name=account_name,
        account_no=account_no,
        amount=amount,
        sale_id=sale_id,
        raw_payload=raw_payload
    )


# ==============================================================================
# CUSTOM UPDATE PRODUCT FUNCTION (Added)
# ==============================================================================

def update_product_rcp(...):
    # လိုအပ်သော logic ကို ဤနေရာတွင် ထည့်သွင်းရန်
    pass


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
    "get_categories",
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
    "update_product_rpc", # __all__ ထဲတွင် ဆက်လက် ထည့်သွင်းထားသည်



    # ------------------------------------------------------------------
    # SERVICES
    # ------------------------------------------------------------------

    "SalesService",

    "PurchaseService",

    "InventoryService",

    "RefundService",

    "ReceiptService",
    "PaymentService",
    "PaymentQRService",
    "generate_payment_qr",

    # ------------------------------------------------------------------
    # SERVICE FACTORIES
    # ------------------------------------------------------------------

    "get_sales_service",

    "get_purchase_service",

    "get_inventory_service",

    "get_refund_service",

    "create_mobile_payment",
    "verify_payment",
    "reject_payment",
    "get_pending_payments",

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
