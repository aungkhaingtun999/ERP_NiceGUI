# ==============================================================================
# erp_core/services/inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE (Integration Layer Updated)
# ==============================================================================

from typing import Any, Dict, List

from ..base_repo import db, log_error
from ..config import Tables
from .settings_service import SettingsService

# ==============================================================================
# Inventory Service
# ==============================================================================


class InventoryService:

    def __init__(self, client):
        self.client = client
        self.settings = SettingsService(client)

    # ==========================================================================
    # LOW STOCK RULE
    # ==========================================================================

    def get_min_stock_alert(self) -> int:
        try:
            return self.settings.get_int("MIN_STOCK_ALERT", 10)
        except Exception as e:
            log_error(message="Minimum stock setting load failed", exception=e)
            return 10

    # ==========================================================================
    # LOW STOCK CHECK
    # ==========================================================================

    def get_low_stock_alerts(self, warehouse_id=None):
        try:
            minimum_stock = float(self.get_min_stock_alert())

            query = self.client.table("warehouse_stock").select("*")

            if warehouse_id:
                query = query.eq("warehouse_id", warehouse_id)

            result = query.execute()
            rows = result.data or []

            return [
                item
                for item in rows
                if float(item.get("qty", 0)) <= minimum_stock
            ]

        except Exception as e:
            log_error(message="Low stock alert failed", exception=e)
            return []

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
    # Stock Adjustment Operations
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
            payload = {
                "product_id": int(product_id),
                "warehouse_id": int(warehouse_id),
                "qty": float(quantity),
                "reason": str(reason),
                "adjustment_type": "COUNT_CORRECTION",
                "status": "PENDING",
                "unit_cost": float(unit_cost),
            }

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
    # Stock Adjustment Approval
    # ==========================================================================

    def approve_stock_adjustment(
        self, adjustment_id: int, manager_id: Any
    ) -> Dict[str, Any]:
        try:
            response = (
                self.client.rpc(
                    "approve_stock_adjustment_rpc",
                    {
                        "p_adjustment_id": int(adjustment_id),
                        "p_manager_id": str(manager_id),
                    },
                )
                .execute()
            )
            result = response.data
            if isinstance(result, list):
                result = result[0]
            return result or {"success": False, "message": "No response data"}

        except Exception as e:
            log_error(message="Stock adjustment RPC approval failed", exception=e)
            return {"success": False, "message": str(e)}

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
