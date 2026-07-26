# ==============================================================================
# erp_core/rpc/checkout_rpc.py
# ERP ENTERPRISE CHECKOUT RPC
# FINAL PRODUCTION v12
# PART 1/2
# ==============================================================================

from typing import Any, Dict, List, Optional

from ..base_repo import db, log_error
from ..context import CacheManager


def checkout_sale_rpc(
    cart: List[Dict[str, Any]],
    paid_amount: Any = 0,
    warehouse_id: Optional[int] = None,
    cashier_id: Optional[str] = None,
    counter_id: int = 1,
    payment_method: str = "CASH",
    tax_rate: Any = 0,
    discount: Any = 0,
) -> Dict[str, Any]:
    """
    ERP Enterprise POS Checkout RPC Wrapper

    Database RPC Signature

    checkout_sale_rpc(
        p_cart,
        p_paid_amount,
        p_warehouse_id,
        p_cashier_id,
        p_counter_id,
        p_payment_method,
        p_tax_rate,
        p_discount
    )
    """

    try:

        # ==========================================================
        # VALIDATION
        # ==========================================================

        if not cart:

            return {
                "success": False,
                "message": "Cart is empty."
            }

        if warehouse_id is None:

            return {
                "success": False,
                "message": "Warehouse not selected."
            }

        if cashier_id is None:

            return {
                "success": False,
                "message": "Cashier not found."
            }

        # ==========================================================
        # NORMALIZE CART
        # ==========================================================

        rpc_cart = []

        for item in cart:

            rpc_cart.append({

                "id": int(item["id"]),

                "qty": int(item["qty"]),

                "selling_price": float(
                    item["selling_price"]
                )

            })

        # ==========================================================
        # RPC PAYLOAD
        # ==========================================================

        payload = {

            "p_cart": rpc_cart,

            "p_paid_amount": float(
                paid_amount
            ),

            "p_warehouse_id": int(
                warehouse_id
            ),

            "p_cashier_id": cashier_id,

            "p_counter_id": int(
                counter_id
            ),

            "p_payment_method": str(
                payment_method
            ).upper(),

            "p_tax_rate": float(
                tax_rate
            ),

            "p_discount": float(
                discount
            ),

        }

        # ==========================================================
        # EXECUTE RPC
        # ==========================================================

        response = (
            db()
            .rpc(
                "checkout_sale_rpc",
                payload
            )
            .execute()
        )
                # ==========================================================
        # RESPONSE
        # ==========================================================

        result = (
            response.data
            if hasattr(response, "data")
            else response
        )

        # ----------------------------------------------------------
        # RPC returned JSON object
        # ----------------------------------------------------------

        if isinstance(result, dict):

            if result.get("success", False):

                try:
                    CacheManager.refresh_inventory()
                except Exception:
                    pass

                try:
                    CacheManager.refresh_products()
                except Exception:
                    pass

            return result

        # ----------------------------------------------------------
        # RPC returned list
        # ----------------------------------------------------------

        if isinstance(result, list):

            if len(result) == 1 and isinstance(result[0], dict):

                if result[0].get("success", False):

                    try:
                        CacheManager.refresh_inventory()
                    except Exception:
                        pass

                    try:
                        CacheManager.refresh_products()
                    except Exception:
                        pass

                return result[0]

            return {
                "success": True,
                "data": result
            }

        # ----------------------------------------------------------
        # Empty response
        # ----------------------------------------------------------

        if result is None:

            return {
                "success": False,
                "message": "RPC returned empty response."
            }

        # ----------------------------------------------------------
        # Primitive response
        # ----------------------------------------------------------

        return {
            "success": True,
            "data": result
        }

    # ==============================================================
    # ERROR
    # ==============================================================

    except Exception as e:

        log_error(f"checkout_sale_rpc : {e}")

        return {
            "success": False,
            "message": str(e)
        }
