# ==============================================================================
# erp_core/services/purchase_service.py
# ERP ENTERPRISE PURCHASE SERVICE
# ==============================================================================

from typing import Any, Dict, Optional

from ..base_repo import money, validate_uuid
from ..context import CacheManager, ERPContext
from ..rpc.engine import RPCEngine


class PurchaseService:

    def __init__(self, client):
        self.client = client
        self.pricing = PricingService(client)

    def receive_stock(
        self,
        product_id: int,
        supplier_id: int,
        warehouse_id: int,
        qty: int,
        cost: Any,
        payment_method: str = "credit",
        remarks: str = "",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = ERPContext.get_current()
        context.rotate_transaction()

        selling_price = self.pricing.calculate_selling_price(cost)

        result = RPCEngine.execute(
            self.client,
            "purchase_receive_rpc",
            {
                "p_product_id": int(product_id),
                "p_supplier_id": int(supplier_id),
                "p_warehouse_id": int(warehouse_id),
                "p_qty": int(qty),
                "p_price": float(money(cost)),
                "p_selling_price": float(selling_price),
                "p_notes": str(remarks),
                "p_created_by": validate_uuid(user_id),
            },
        )

        if result.get("success"):
            CacheManager.bump_version("inventory_version")

        return result
