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
    # update_product_rpc removed from here


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
# CUSTOM UPDATE PRODUCT FUNCTION

# ==============================================================================
# CUSTOM UPDATE PRODUCT FUNCTION (FIXED)
# ==============================================================================

def update_product_rpc(
    product_id,
    name,
    sku,
    barcode,
    purchase_price,
    selling_price,
    minimum_stock,
    unit,
    notes,
    is_active=True
):

    try:

        client = db()

        # --------------------------------------------------------------
        # LOAD EXISTING PRODUCT
        # --------------------------------------------------------------

        old_result = (
            client
            .table("products")
            .select("id, sku, barcode, minimum_stock")
            .eq("id", int(product_id))
            .single()
            .execute()
        )

        old_data = old_result.data

        if not old_data:
            return {
                "success": False,
                "message": f"Product ID {product_id} not found"
            }

        # --------------------------------------------------------------
        # KEEP OLD VALUE IF INPUT EMPTY
        # --------------------------------------------------------------

        final_sku = (
            sku.strip()
            if sku and str(sku).strip()
            else old_data.get("sku")
        )

        final_barcode = (
            barcode.strip()
            if barcode and str(barcode).strip()
            else old_data.get("barcode")
        )

        final_min_stock = (
            int(minimum_stock)
            if minimum_stock is not None
            else int(old_data.get("minimum_stock", 0))
        )

        payload = {

            "name":
            str(name).strip(),

            "sku":
            final_sku,

            "barcode":
            final_barcode,

            "purchase_price":
            float(purchase_price),

            "selling_price":
            float(selling_price),

            "minimum_stock":
            final_min_stock,

            "unit":
            str(unit).strip() if unit else "pcs",

            "notes":
            notes,

            "is_active":
            bool(is_active),

        }

        print("ERP UPDATE PAYLOAD =", payload)

        # --------------------------------------------------------------
        # UPDATE PRODUCT
        # --------------------------------------------------------------
        print("UPDATE PRODUCT ID =", product_id)

        print("UPDATE PAYLOAD =", payload)
        result = (
            client
            .table("products")
            .update(payload)
            .eq("id", int(product_id))
            .execute()
        )
        print("UPDATE RESULT =", result.data)
        print("ERP UPDATE RESULT =", result.data)

        # --------------------------------------------------------------
        # VERIFY UPDATE
        # --------------------------------------------------------------

        verify = (
            client
            .table("products")
            .select("id, sku, barcode, minimum_stock")
            .eq("id", int(product_id))
            .single()
            .execute()
        )

        verify_data = verify.data or {}

        print("ERP VERIFY =", verify_data)

        return {
            "success": True,
            "message": "Product updated successfully",
            "data": verify_data
        }

    except Exception as e:

        print("ERP UPDATE ERROR =", e)

        return {
            "success": False,
            "message": str(e)
        }

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
    "update_product_rpc",



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
    "update_product_rpc",

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
