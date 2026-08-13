# ==============================================================================
# erp_core/rpc/__init__.py
# ERP ENTERPRISE RPC PACKAGE v35.1
#
# SAFE RPC EXPORT HUB
#
# Architecture:
#
# ERP Core
#    ↓
# RPC Package
#    ↓
# Individual RPC Modules
#
# ==============================================================================


print("ERP RPC PACKAGE START")


# ==============================================================================
# CHECKOUT
# ==============================================================================

try:

    from .checkout_rpc import (
        checkout_sale_rpc,
    )

except Exception as e:

    print(
        "RPC checkout_rpc import failed:",
        e
    )

    def checkout_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "checkout_sale_rpc unavailable"
        }


# ==============================================================================
# PURCHASE
# ==============================================================================

try:

    from .purchase_rpc import (
        purchase_receive_rpc,
    )

except Exception as e:

    print(
        "RPC purchase_rpc import failed:",
        e
    )

    def purchase_receive_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "purchase_receive_rpc unavailable"
        }


# ==============================================================================
# REFUND
# ==============================================================================

try:

    from .refund_rpc import (
        refund_sale_rpc,
    )

except Exception as e:

    print(
        "RPC refund_rpc import failed:",
        e
    )

    def refund_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "refund_sale_rpc unavailable"
        }


# ==============================================================================
# STOCK
# ==============================================================================

try:

    from .stock_rpc import (
        stock_adjustment_rpc,
    )

except Exception as e:

    print(
        "RPC stock_rpc import failed:",
        e
    )

    def stock_adjustment_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "stock_adjustment_rpc unavailable"
        }


# ==============================================================================
# PRODUCT
# ------------------------------------------------------------------------------
# IMPORTANT:
#
# update_product_rpc lives in:
#
#     erp_core/rpc/product_rpc.py
#
# NOT stock_rpc.py
# ==============================================================================

try:

    from .product_rpc import (
        update_product_rpc,
    )

except Exception as e:

    print(
        "RPC product_rpc import failed:",
        e
    )

    def update_product_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "update_product_rpc unavailable"
        }


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [

    "checkout_sale_rpc",

    "purchase_receive_rpc",

    "refund_sale_rpc",

    "stock_adjustment_rpc",

    "update_product_rpc",

]


print(
    "ERP RPC PACKAGE READY"
)
