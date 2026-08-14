# ==============================================================================
# erp_core/rpc/refund_rpc.py
# ERP ENTERPRISE REFUND RPC WRAPPER
# ==============================================================================


from typing import (
    Optional,
    Dict,
    Any
)


from ..base_repo import (
    db,
)

from ..config import (
    log_error,
)

from ..services.refund_service import (
    RefundService,
)

def refund_sale_rpc(
    sale_id: int,
    refund_items: list,
    reason: str = "",
    cashier_id: Optional[str] = None

) -> Dict[str, Any]:


    try:

        service = RefundService(
            db()
        )


        return service.process_refund(

            sale_id,

            refund_items,

            reason,

            cashier_id

        )


    except Exception as e:

        log_error(
            f"refund_sale_rpc error: {e}"
        )


        return {

            "success": False,

            "message": str(e),

            "data": None

        }
