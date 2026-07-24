# ==============================================================================
# erp_core/rpc/stock_rpc.py
# ERP ENTERPRISE STOCK ADJUSTMENT RPC WRAPPER
# ==============================================================================


from typing import (
    Optional,
    Dict,
    Any
)


from ..base_repo import (
    db,
    log_error
)


from ..services import (
    InventoryService
)





def stock_adjustment_rpc(
    product_id: int,
    warehouse_id: int,
    quantity: int,
    reason: str,
    user_id: Optional[str] = None,
    created_by: Optional[str] = None

) -> Dict[str, Any]:


    # Compatibility
    if created_by and not user_id:
        user_id = created_by


    try:

        service = InventoryService(
            db()
        )


        return service.adjust_stock(

            product_id,

            warehouse_id,

            quantity,

            reason,

            user_id

        )


    except Exception as e:

        log_error(
            f"stock_adjustment_rpc error: {e}"
        )


        return {

            "success": False,

            "message": str(e),

            "data": None

        }


# ==============================================================================
# PRODUCT UPDATE RPC
# ==============================================================================


def update_product_rpc(
    product_id: int,
    name: str,
    sku: str,
    barcode: str,
    purchase_price: float,
    selling_price: float,
    minimum_stock: int,
    unit: str,
    notes: str,
    is_active: bool

) -> Dict[str, Any]:


    try:

        service = InventoryService(
            db()
        )


        return service.update_product(

            product_id,

            {
                "name": name,
                "sku": sku,
                "barcode": barcode,
                "purchase_price": purchase_price,
                "selling_price": selling_price,
                "minimum_stock": minimum_stock,
                "unit": unit,
                "notes": notes,
                "is_active": is_active
            }

        )


    except Exception as e:

        log_error(
            f"update_product_rpc error: {e}"
        )


        return {

            "success": False,

            "message": str(e),

            "data": None

        }
