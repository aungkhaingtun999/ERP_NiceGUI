# ==============================================================================
# erp_core/rpc/__init__.py
# ERP ENTERPRISE RPC PACKAGE v36.0 FINAL
#
# SAFE RPC EXPORT HUB
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
        e,
    )

    def checkout_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "checkout_sale_rpc unavailable",
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
        e,
    )

    def purchase_receive_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "purchase_receive_rpc unavailable",
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
        e,
    )

    def refund_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "refund_sale_rpc unavailable",
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
        e,
    )

    def stock_adjustment_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "stock_adjustment_rpc unavailable",
        }


# ==============================================================================
# PRODUCT
# ==============================================================================

try:

    from .product_rpc import (

        update_product_rpc,

        request_product_create_rpc,

        request_product_bulk_create_rpc,

        approve_product_create_rpc,

    )

except Exception as e:

    print(
        "RPC product_rpc import failed:",
        e,
    )

    def update_product_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "update_product_rpc unavailable",
        }

    def request_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "request_product_create_rpc unavailable",
        }

    def request_product_bulk_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "request_product_bulk_create_rpc unavailable",
        }

    def approve_product_create_rpc(*args, **kwargs):

        return {
            "success": False,
            "message":
                "approve_product_create_rpc unavailable",
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

    "request_product_create_rpc",

    "request_product_bulk_create_rpc",

    "approve_product_create_rpc",

]


print(
    "ERP RPC PACKAGE READY"
)
