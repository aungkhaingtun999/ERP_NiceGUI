# ==============================================================================
# erp_core/rpc/__init__.py
# ERP ENTERPRISE RPC PACKAGE v36.1
#
# RPC PUBLIC EXPORT HUB
#
# Responsibilities:
# - Export all public RPC wrappers
# - Keep import failures visible
# - Never silently hide broken RPC modules
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This file MUST export every RPC function imported by:
#
#     erp_core/__init__.py
#
# ==============================================================================


print("============================================================")
print("ERP RPC PACKAGE START")
print("============================================================")


# ==============================================================================
# CHECKOUT
# ==============================================================================

try:

    from .checkout_rpc import (
        checkout_sale_rpc,
    )

    print(
        "ERP RPC CHECKOUT: OK"
    )

except Exception as e:

    print(
        "============================================================"
    )

    print(
        "ERP RPC CHECKOUT IMPORT FAILED"
    )

    print(
        "ERROR TYPE:",
        type(e).__name__
    )

    print(
        "ERROR:",
        str(e)
    )

    print(
        "============================================================"
    )

    def checkout_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "checkout_sale_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }


# ==============================================================================
# PURCHASE
# ==============================================================================

try:

    from .purchase_rpc import (
        purchase_receive_rpc,
    )

    print(
        "ERP RPC PURCHASE: OK"
    )

except Exception as e:

    print(
        "ERP RPC PURCHASE IMPORT FAILED:",
        type(e).__name__,
        str(e)
    )

    def purchase_receive_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "purchase_receive_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }


# ==============================================================================
# REFUND
# ==============================================================================

try:

    from .refund_rpc import (
        refund_sale_rpc,
    )

    print(
        "ERP RPC REFUND: OK"
    )

except Exception as e:

    print(
        "ERP RPC REFUND IMPORT FAILED:",
        type(e).__name__,
        str(e)
    )

    def refund_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "refund_sale_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }


# ==============================================================================
# STOCK + PRODUCT UPDATE
# ==============================================================================
#
# IMPORTANT:
#
# update_product_rpc is defined in stock_rpc.py
# together with stock_adjustment_rpc.
#
# Therefore BOTH functions must be imported here.
#
# ==============================================================================

try:

    from .stock_rpc import (
        stock_adjustment_rpc,
        update_product_rpc,
    )

    print(
        "ERP RPC STOCK: OK"
    )

    print(
        "ERP RPC PRODUCT UPDATE: OK"
    )

except Exception as e:

    print(
        "ERP RPC STOCK IMPORT FAILED:",
        type(e).__name__,
        str(e)
    )

    def stock_adjustment_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "stock_adjustment_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }

    def update_product_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "update_product_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }


# ==============================================================================
# PRODUCT CREATION / MAKER-CHECKER
# ==============================================================================

try:

    from .product_rpc import (

        request_product_create_rpc,

        request_product_bulk_create_rpc,

        approve_product_create_rpc,

    )

    print(
        "ERP RPC PRODUCT MAKER-CHECKER: OK"
    )

except Exception as e:

    print(
        "ERP RPC PRODUCT IMPORT FAILED:",
        type(e).__name__,
        str(e)
    )

    def request_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "request_product_create_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }


    def request_product_bulk_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "request_product_bulk_create_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }


    def approve_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": (
                "approve_product_create_rpc import failed: "
                f"{type(e).__name__}: {e}"
            ),
        }


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [

    # --------------------------------------------------------------------------
    # CHECKOUT
    # --------------------------------------------------------------------------

    "checkout_sale_rpc",


    # --------------------------------------------------------------------------
    # PURCHASE
    # --------------------------------------------------------------------------

    "purchase_receive_rpc",


    # --------------------------------------------------------------------------
    # REFUND
    # --------------------------------------------------------------------------

    "refund_sale_rpc",


    # --------------------------------------------------------------------------
    # STOCK
    # --------------------------------------------------------------------------

    "stock_adjustment_rpc",


    # --------------------------------------------------------------------------
    # PRODUCT UPDATE
    # --------------------------------------------------------------------------

    "update_product_rpc",


    # --------------------------------------------------------------------------
    # PRODUCT MAKER-CHECKER
    # --------------------------------------------------------------------------

    "request_product_create_rpc",

    "request_product_bulk_create_rpc",

    "approve_product_create_rpc",

]


print("============================================================")
print("ERP RPC PACKAGE READY")
print("============================================================")
