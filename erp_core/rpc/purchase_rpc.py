# ==============================================================================
# erp_core/rpc/purchase_rpc.py
# ERP ENTERPRISE PURCHASE RPC WRAPPER
# ==============================================================================


from typing import Optional, Dict, Any

from ..base_repo import (
    db,
)

from ..config import (
    log_error,
)

def purchase_receive_rpc(
    product_id: int,
    supplier_id: int,
    warehouse_id: int,
    qty,
    cost,
    remarks: str = "",
    user_id: Optional[str] = None

) -> Dict[str, Any]:


    try:

        response = (
            db()
            .rpc(
                "purchase_receive_rpc",
                {
                    "p_product_id": product_id,
                    "p_supplier_id": supplier_id,
                    "p_warehouse_id": warehouse_id,
                    "p_qty": qty,
                    "p_cost": cost,
                    "p_remarks": remarks,
                    "p_user_id": user_id
                }
            )
            .execute()
        )


        return response.data



    except Exception as e:


        log_error(
            f"purchase_receive_rpc error: {e}"
        )


        return {

            "success": False,

            "message": str(e),

            "data": None

        }
