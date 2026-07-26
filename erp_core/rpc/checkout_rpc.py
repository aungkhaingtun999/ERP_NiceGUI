# ==============================================================================
# erp_core/rpc/checkout_rpc.py
# ERP ENTERPRISE CHECKOUT RPC
# ==============================================================================

from typing import Optional, Dict, Any

from ..base_repo import (
    db,
    log_error
)


def checkout_sale_rpc(
    cart: list,
    paid_amount: Any = 0,
    warehouse_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    cashier_id: Optional[str] = None,
    counter_id: int = 1,
    payment_method: str = "cash",
    tax_rate: Any = 0,
    discount: Any = 0

) -> Dict[str, Any]:


    try:

        payload = {

            "p_cart": cart,

            "p_warehouse_id": warehouse_id,

            "p_user_id": cashier_id,

            "p_customer_id": customer_id,

            "p_payment_method": payment_method,

            "p_discount": discount,

            "p_tax": (
                float(tax_rate)
                * sum(
                    float(i["qty"]) *
                    float(i["selling_price"])
                    for i in cart
                )
                / 100
            )

        }


        response = (
            db()
            .rpc(
                "checkout_sale_rpc",
                payload
            )
            .execute()
        )


        return response.data


    except Exception as e:

        log_error(
            f"checkout_sale_rpc error: {e}"
        )


        return {

            "success": False,

            "message": str(e)

        }
