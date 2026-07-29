# ==============================================================================
# erp_core/rpc/__init__.py
# ERP ENTERPRISE RPC PACKAGE v34 SAFE EXPORT
# ==============================================================================


print("RPC PACKAGE START")



from .checkout_rpc import (
    checkout_sale_rpc
)



try:

    from .purchase_rpc import (
        purchase_receive_rpc
    )

except Exception:


    def purchase_receive_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "purchase_receive_rpc unavailable"
        }




try:

    from .refund_rpc import (
        refund_sale_rpc
    )

except Exception:


    def refund_sale_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "refund_sale_rpc unavailable"
        }




try:

    from .stock_rpc import (
        stock_adjustment_rpc
    )

except Exception:


    def stock_adjustment_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "stock_adjustment_rpc unavailable"
        }




try:

    from .product_rpc import (
        update_product_rpc
    )

except Exception:


    def update_product_rpc(*args, **kwargs):

        return {
            "success": False,
            "message": "update_product_rpc unavailable"
        }





__all__ = [

    "checkout_sale_rpc",

    "purchase_receive_rpc",

    "refund_sale_rpc",

    "stock_adjustment_rpc",

    "update_product_rpc"

]


print("RPC PACKAGE READY")
