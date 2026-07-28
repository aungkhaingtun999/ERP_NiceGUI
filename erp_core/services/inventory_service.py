# ==============================================================================
# erp_core/services/inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE
# Version: V1.1 Production FIX
#
# FIFO
# Inventory KPI
# Valuation
# Stock Card
# Loss Analytics
# Stock Adjustments
#
# Compatible:
#   erp_core.base_repo.db()
#   99_System_Test.py
#
# ==============================================================================

from typing import Any, Dict, List

from ..base_repo import db, log_error

# ==============================================================================
# Inventory Service
# ==============================================================================


class InventoryService:

    def __init__(self, client):
        self.client = client

    # ==========================================================================
    # Inventory KPI
    # ==========================================================================

    def get_inventory_kpi(self) -> Dict[str, Any]:
        try:
            result = (
                self.client.table("inventory_kpi_view")
                .select("*")
                .single()
                .execute()
            )

            data = result.data or {}

            return {
                "success": True,
                "total_products": data.get("total_products", 0),
                "total_warehouses": data.get("total_warehouses", 0),
                "total_stock_qty": data.get("total_stock_qty", 0),
                "total_inventory_value": data.get("total_inventory_value", 0),
                "average_unit_value": data.get("average_unit_value", 0),
                "low_stock_items": data.get("low_stock_items", 0),
            }

        except Exception as e:
            log_error(message="Inventory KPI failed", exception=e)
            return {"success": False, "message": str(e)}

    # ==========================================================================
    # Warehouse Inventory KPI
    # ==========================================================================

    def get_warehouse_inventory_kpi(self) -> List[Dict]:
        try:
            result = (
                self.client.table("warehouse_inventory_kpi_view")
                .select("*")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(message="Warehouse KPI failed", exception=e)
            return []

    # ==========================================================================
    # Inventory Valuation
    # ==========================================================================

    def get_inventory_valuation(self) -> List[Dict]:
        try:
            result = (
                self.client.table("inventory_valuation_view")
                .select("*")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(message="Inventory valuation failed", exception=e)
            return []

    # ==========================================================================
    # Inventory Loss Report
    # ==========================================================================

    def get_inventory_loss_report(self) -> List[Dict]:
        try:
            result = (
                self.client.table("inventory_loss_kpi_view")
                .select("*")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(message="Inventory loss report failed", exception=e)
            return []

    # ==========================================================================
    # Stock Card
    # ==========================================================================

    def get_stock_card(self, product_id: int, warehouse_id: int) -> List[Dict]:
        try:
            result = (
                self.client.table("stock_card_view")
                .select("*")
                .eq("product_id", product_id)
                .eq("warehouse_id", warehouse_id)
                .order("created_at")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(message="Stock card loading failed", exception=e)
            return []

    # ==========================================================================
    # Stock Adjustment Operations (Fixed for UUID, Schema & Unit Cost Compatibility)
    # ==========================================================================

    def adjust_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        reason: str,
        created_by: Any = None,
        unit_cost: float = 0.0,
    ) -> Dict[str, Any]:
        try:
            # Table Schema နှင့် ကိုက်ညီစေရန်နှင့် not-null constraint မတက်စေရန် payload တည်ဆောက်ခြင်း
            payload = {
                "product_id": int(product_id),
                "warehouse_id": int(warehouse_id),
                "qty": float(quantity),
                "reason": str(reason),
                "adjustment_type": "COUNT_CORRECTION",
                "status": "PENDING",
                "unit_cost": float(unit_cost),
            }

            # created_by / requested_by သည် uuid ဖြစ်နိုင်သဖြင့် int() မပြောင်းဘဲ string အနေဖြင့် ထည့်သွင်းခြင်း
            if created_by:
                payload["requested_by"] = str(created_by)

            res = self.client.table("stock_adjustments").insert(payload).execute()

            data = res.data
            if isinstance(data, list) and data:
                data = data[0]

            if data:
                return {"success": True, "data": data}
            else:
                return {
                    "success": False,
                    "message": "Stock adjustment insertion failed",
                }

        except Exception as e:
            log_error(message="Stock adjustment failed", exception=e)
            return {"success": False, "message": str(e)}

    def get_stock_adjustments(self, warehouse_id: int) -> List[Dict]:
        try:
            result = (
                self.client.table("stock_adjustments")
                .select("*")
                .eq("warehouse_id", int(warehouse_id))
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(message="Stock adjustment history loading failed", exception=e)
            return []

    # ==========================================================================
    # Inventory Health Check
    # ==========================================================================

    def health_check(self) -> Dict[str, Any]:
        try:
            result = (
                self.client.table("inventory_kpi_view")
                .select("*")
                .limit(1)
                .execute()
            )

            return {
                "service": "InventoryService",
                "status": "PASS",
                "database": "CONNECTED",
                "rows": len(result.data or []),
            }

        except Exception as e:
            return {
                "service": "InventoryService",
                "status": "FAIL",
                "message": str(e),
            }


# ==============================================================================
# Export
# ==============================================================================

__all__ = ["InventoryService"]
