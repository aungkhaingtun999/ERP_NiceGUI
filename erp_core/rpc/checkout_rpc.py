# ==============================================================================
# erp_core/rpc/checkout_rpc.py
# ERP ENTERPRISE CHECKOUT RPC
# ==============================================================================

from typing import Any, Dict, List, Optional

from ..base_repo import db, log_error
from ..context import CacheManager


def checkout_sale_rpc(
    cart: List[Dict[str, Any]],
    paid_amount: Any = 0,
    warehouse_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    cashier_id: Optional[str] = None,
    counter_id: int = 1,
    payment_method: str = "cash",
    tax_rate: Any = 0,
    discount: Any = 0,
) -> Dict[str, Any]:
    """Executes the checkout sale RPC procedure safely with error handling."""
    try:
        # Calculate tax amount safely
        subtotal = sum(
            float(item.get("qty", 0)) * float(item.get("selling_price", 0))
            for item in cart
        )
        calculated_tax = (float(tax_rate) * subtotal) / 100

        payload = {
            "p_cart": cart,
            "p_warehouse_id": warehouse_id,
            "p_user_id": cashier_id,
            "p_customer_id": customer_id,
            "p_payment_method": payment_method,
            "p_discount": discount,
            "p_tax": calculated_tax,
            "p_paid_amount": paid_amount,
            "p_counter_id": counter_id,
        }

        response = db().rpc("checkout_sale_rpc", payload).execute()
        
        result = response.data if response and hasattr(response, "data") else response

        # Check if sale is successful and refresh cache
        if isinstance(result, dict):
            if result.get("success"):
                CacheManager.refresh_inventory()
                CacheManager.refresh_products()
                
            return result

        return {
            "success": True, 
            "data": result
        }

    except Exception as e:
        log_error(f"checkout_sale_rpc error: {e}")

        return {
            "success": False,
            "message": str(e),
        }
