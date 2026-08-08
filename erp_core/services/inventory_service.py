# ==============================================================================
# erp_core/services/inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE
#
# Version:
# - Existing Inventory Operations
# - Warehouse Support
# - Stock Adjustment / Approval
# - Mobile Inventory
# - Batch + Expiry Support
# - FEFO Allocation Engine v1
#
# NOTE:
# FEFO v1 only calculates the issue plan.
# It DOES NOT deduct stock yet.
# Actual deduction will be handled by a transaction-safe RPC in the next step.
# ==============================================================================

from typing import Any, Dict, List, Optional

from ..base_repo import db, log_error
from ..config import Tables
from .settings_service import SettingsService

# ==============================================================================
# INVENTORY SERVICE
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
            log_error(
                message="Minimum stock setting load failed.",
                exception=e
            )
            return 10

    # ==========================================================================
    # LOW STOCK CHECK
    # ==========================================================================

    def get_low_stock_alerts(
        self, warehouse_id: Optional[int] = None
    ) -> List[Dict]:
        try:
            minimum_stock = float(self.get_min_stock_alert())

            query = (
                self.client
                .table("warehouse_stock")
                .select("*")
            )

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
            log_error(
                message="Low stock alert check failed.",
                exception=e
            )
            return []

    # ==========================================================================
    # INVENTORY KPI
    # ==========================================================================

    def get_inventory_kpi(self) -> Dict[str, Any]:
        try:
            result = (
                self.client
                .table("inventory_kpi_view")
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
            log_error(
                message="Inventory KPI retrieval failed.",
                exception=e
            )
            return {"success": False, "message": str(e)}

    # ==========================================================================
    # WAREHOUSE INVENTORY KPI
    # ==========================================================================

    def get_warehouse_inventory_kpi(self) -> List[Dict]:
        try:
            result = (
                self.client
                .table("warehouse_inventory_kpi_view")
                .select("*")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(
                message="Warehouse KPI retrieval failed.",
                exception=e
            )
            return []

    # ==========================================================================
    # INVENTORY VALUATION
    # ==========================================================================

    def get_inventory_valuation(self) -> List[Dict]:
        try:
            result = (
                self.client
                .table("inventory_valuation_view")
                .select("*")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(
                message="Inventory valuation retrieval failed.",
                exception=e
            )
            return []

    # ==========================================================================
    # INVENTORY LOSS REPORT
    # ==========================================================================

    def get_inventory_loss_report(self) -> List[Dict]:
        try:
            result = (
                self.client
                .table("inventory_loss_kpi_view")
                .select("*")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(
                message="Inventory loss report retrieval failed.",
                exception=e
            )
            return []

    # ==========================================================================
    # STOCK CARD
    # ==========================================================================

    def get_stock_card(
        self, product_id: int, warehouse_id: int
    ) -> List[Dict]:
        try:
            result = (
                self.client
                .table("stock_card_view")
                .select("*")
                .eq("product_id", product_id)
                .eq("warehouse_id", warehouse_id)
                .order("created_at")
                .execute()
            )
            return result.data or []

        except Exception as e:
            log_error(
                message="Stock card loading failed.",
                exception=e
            )
            return []

    # ==========================================================================
    # BATCH / EXPIRY CONFIGURATION
    # ==========================================================================

    def get_product_batch_settings(self, product_id: int) -> Dict[str, Any]:
        try:
            result = (
                self.client
                .table("products")
                .select("""
                    id,
                    name,
                    track_batches,
                    track_expiry,
                    shelf_life_days
                """)
                .eq("id", int(product_id))
                .single()
                .execute()
            )

            data = result.data or {}

            return {
                "success": True,
                "product_id": data.get("id"),
                "product_name": data.get("name"),
                "track_batches": bool(data.get("track_batches", False)),
                "track_expiry": bool(data.get("track_expiry", False)),
                "shelf_life_days": data.get("shelf_life_days", 0),
            }

        except Exception as e:
            log_error(
                message="Product batch settings load failed.",
                exception=e
            )
            return {"success": False, "message": str(e)}

    # ==========================================================================
    # FEFO BATCH LOADER
    #
    # Returns only batches with:
    # - positive quantity
    # - expiry date
    #
    # IMPORTANT:
    # - No stock is changed.
    # - Final FEFO ordering is enforced in Python.
    # ==========================================================================

    def get_fefo_batches(
        self,
        product_id: int,
        warehouse_id: int
    ) -> List[Dict]:

        try:

            result = (
                self.client
                .table("inventory_batches")
                .select("""
                    id,
                    product_id,
                    warehouse_id,
                    batch_no,
                    manufacturing_date,
                    expiry_date,
                    quantity,
                    unit_cost
                """)
                .eq(
                    "product_id",
                    int(product_id)
                )
                .eq(
                    "warehouse_id",
                    int(warehouse_id)
                )
                .gt(
                    "quantity",
                    0
                )
                .order(
                    "expiry_date",
                    desc=False
                )
                .order(
                    "id",
                    desc=False
                )
                .execute()
            )

            rows = result.data or []

            # --------------------------------------------------------------
            # Remove batches without expiry date
            # --------------------------------------------------------------

            rows = [
                row
                for row in rows
                if row.get("expiry_date") not in (None, "")
            ]

            # --------------------------------------------------------------
            # Enforce FEFO ordering at service level
            # Earliest expiry first
            # ID = deterministic tie breaker
            # --------------------------------------------------------------

            rows.sort(
                key=lambda row: (
                    row.get("expiry_date") or "",
                    int(row.get("id", 0) or 0),
                )
            )

            return rows

        except Exception as e:

            log_error(
                message="FEFO batch loading failed.",
                exception=e
            )

            return []

    # ==========================================================================
    # FEFO ISSUE PLAN
    #
    # Example:
    #
    # Batch 001 = 50 @ 1000
    # Batch 002 = 80 @ 1050
    # Request   = 60
    #
    # Allocation:
    # Batch 001 = 50
    # Batch 002 = 10
    #
    # Total COGS = 60,500
    #
    # IMPORTANT:
    # This method DOES NOT deduct stock.
    # ==========================================================================

    def get_fefo_issue_plan(
        self,
        product_id: int,
        warehouse_id: int,
        issue_quantity: float
    ) -> Dict[str, Any]:

        try:

            requested_qty = float(issue_quantity)

            if requested_qty <= 0:

                return {
                    "success": False,
                    "method": "FEFO",
                    "message": "Issue quantity must be greater than zero.",
                    "product_id": int(product_id),
                    "warehouse_id": int(warehouse_id),
                    "requested_qty": requested_qty,
                    "allocated_qty": 0,
                    "shortage_qty": requested_qty,
                    "total_cost": 0,
                    "allocations": [],
                }

            # --------------------------------------------------------------
            # PRODUCT BATCH SETTINGS
            # --------------------------------------------------------------

            settings = self.get_product_batch_settings(
                product_id
            )

            if not settings.get("success"):

                return {
                    "success": False,
                    "method": "FEFO",
                    "message": settings.get(
                        "message",
                        "Unable to load product batch settings."
                    ),
                    "product_id": int(product_id),
                    "warehouse_id": int(warehouse_id),
                    "requested_qty": requested_qty,
                    "allocated_qty": 0,
                    "shortage_qty": requested_qty,
                    "total_cost": 0,
                    "allocations": [],
                }

            track_batches = bool(
                settings.get("track_batches", False)
            )

            track_expiry = bool(
                settings.get("track_expiry", False)
            )

            # --------------------------------------------------------------
            # BATCH TRACKING CHECK
            # --------------------------------------------------------------

            if not track_batches:

                return {
                    "success": False,
                    "method": "SIMPLE_OR_FIFO",
                    "message": (
                        "Product is not configured "
                        "for batch tracking."
                    ),
                    "product_id": int(product_id),
                    "warehouse_id": int(warehouse_id),
                    "requested_qty": requested_qty,
                    "allocated_qty": 0,
                    "shortage_qty": requested_qty,
                    "total_cost": 0,
                    "allocations": [],
                }

            # --------------------------------------------------------------
            # EXPIRY TRACKING CHECK
            # --------------------------------------------------------------

            if not track_expiry:

                return {
                    "success": False,
                    "method": "BATCH_FIFO",
                    "message": (
                        "Product has batch tracking but "
                        "expiry tracking is disabled."
                    ),
                    "product_id": int(product_id),
                    "warehouse_id": int(warehouse_id),
                    "requested_qty": requested_qty,
                    "allocated_qty": 0,
                    "shortage_qty": requested_qty,
                    "total_cost": 0,
                    "allocations": [],
                }

            # --------------------------------------------------------------
            # LOAD BATCHES
            # --------------------------------------------------------------

            batches = self.get_fefo_batches(
                product_id=product_id,
                warehouse_id=warehouse_id
            )

            # --------------------------------------------------------------
            # FINAL FEFO SORT
            # --------------------------------------------------------------

            batches = sorted(
                batches,
                key=lambda batch: (
                    batch.get("expiry_date") is None,
                    batch.get("expiry_date") or "",
                    int(batch.get("id", 0) or 0),
                )
            )

            if not batches:

                return {
                    "success": False,
                    "method": "FEFO",
                    "message": (
                        "No available FEFO batches found."
                    ),
                    "product_id": int(product_id),
                    "warehouse_id": int(warehouse_id),
                    "requested_qty": requested_qty,
                    "allocated_qty": 0,
                    "shortage_qty": requested_qty,
                    "total_cost": 0,
                    "allocations": [],
                }

            # --------------------------------------------------------------
            # ALLOCATION
            # --------------------------------------------------------------

            remaining_qty = requested_qty

            allocations = []

            total_cost = 0.0

            for batch in batches:

                if remaining_qty <= 0:
                    break

                available_qty = float(
                    batch.get("quantity", 0) or 0
                )

                if available_qty <= 0:
                    continue

                issue_qty = min(
                    available_qty,
                    remaining_qty
                )

                unit_cost = float(
                    batch.get("unit_cost", 0) or 0
                )

                line_cost = (
                    issue_qty * unit_cost
                )

                allocations.append({

                    "batch_id": batch.get("id"),

                    "batch_no": batch.get("batch_no"),

                    "manufacturing_date":
                        batch.get("manufacturing_date"),

                    "expiry_date":
                        batch.get("expiry_date"),

                    "available_qty":
                        available_qty,

                    "issue_qty":
                        issue_qty,

                    "remaining_qty":
                        available_qty - issue_qty,

                    "unit_cost":
                        unit_cost,

                    "line_cost":
                        line_cost,
                })

                total_cost += line_cost

                remaining_qty -= issue_qty

            # --------------------------------------------------------------
            # FINAL QUANTITIES
            # --------------------------------------------------------------

            allocated_qty = (
                requested_qty - remaining_qty
            )

            shortage_qty = max(
                remaining_qty,
                0
            )

            # --------------------------------------------------------------
            # INSUFFICIENT STOCK
            # --------------------------------------------------------------

            if shortage_qty > 0:

                return {
                    "success": False,
                    "method": "FEFO",
                    "message": (
                        "Insufficient FEFO batch stock."
                    ),
                    "product_id": int(product_id),
                    "warehouse_id": int(warehouse_id),
                    "requested_qty": requested_qty,
                    "allocated_qty": allocated_qty,
                    "shortage_qty": shortage_qty,
                    "total_cost": total_cost,
                    "allocations": allocations,
                }

            # --------------------------------------------------------------
            # SUCCESS
            # --------------------------------------------------------------

            return {
                "success": True,
                "method": "FEFO",
                "product_id": int(product_id),
                "warehouse_id": int(warehouse_id),
                "requested_qty": requested_qty,
                "allocated_qty": allocated_qty,
                "shortage_qty": 0,
                "total_cost": total_cost,
                "allocations": allocations,
            }

        except Exception as e:

            log_error(
                message="FEFO issue plan calculation failed.",
                exception=e
            )

            return {
                "success": False,
                "method": "FEFO",
                "message": str(e),
                "product_id": int(product_id),
                "warehouse_id": int(warehouse_id),
                "requested_qty": float(
                    issue_quantity
                ),
                "allocated_qty": 0,
                "shortage_qty": float(
                    issue_quantity
                ),
                "total_cost": 0,
                "allocations": [],
            }
            # --------------------------------------------------------------
            # SUCCESS
            # --------------------------------------------------------------
            return {
                "success": True,
                "method": "FEFO",
                "product_id": int(product_id),
                "warehouse_id": int(warehouse_id),
                "requested_qty": requested_qty,
                "allocated_qty": allocated_qty,
                "shortage_qty": 0,
                "total_cost": total_cost,
                "allocations": allocations,
            }

        except Exception as e:
            log_error(
                message="FEFO issue plan calculation failed.",
                exception=e
            )
            return {
                "success": False,
                "message": str(e),
                "allocations": []
            }

    # ==========================================================================
    # STOCK ADJUSTMENT OPERATIONS
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

            res = (
                self.client
                .table("stock_adjustments")
                .insert(payload)
                .execute()
            )

            data = res.data
            if isinstance(data, list) and data:
                data = data[0]

            if data:
                return {"success": True, "data": data}
            else:
                return {
                    "success": False,
                    "message": "Stock adjustment insertion failed.",
                }

        except Exception as e:
            log_error(
                message="Stock adjustment failed.",
                exception=e
            )
            return {"success": False, "message": str(e)}

    # ==========================================================================
    # STOCK ADJUSTMENT HISTORY
    # ==========================================================================

    def get_stock_adjustments(self, warehouse_id: int) -> List[Dict]:
        try:
            result = (
                self.client
                .table("stock_adjustments")
                .select("""
                    id,
                    product_id,
                    warehouse_id,
                    adjustment_type,
                    qty,
                    reason,
                    status,
                    requested_by,
                    approved_by,
                    approved_at,
                    created_at
                """)
                .eq("warehouse_id", int(warehouse_id))
                .order("created_at", desc=True)
                .execute()
            )

            rows = result.data or []

            for row in rows:
                product = (
                    self.client
                    .table("products")
                    .select("name")
                    .eq("id", row["product_id"])
                    .single()
                    .execute()
                )

                row["product_name"] = (
                    product.data.get("name")
                    if product.data
                    else "Unknown"
                )

            return rows

        except Exception as e:
            log_error(
                message="Stock adjustment history loading failed.",
                exception=e
            )
            return []

    # ==========================================================================
    # STOCK ADJUSTMENT APPROVAL
    # ==========================================================================

    def approve_stock_adjustment(
        self, adjustment_id: int, manager_id: Any
    ) -> Dict[str, Any]:
        try:
            response = (
                self.client
                .rpc(
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
            return result or {"success": False, "message": "No response data found."}

        except Exception as e:
            log_error(
                message="Stock adjustment RPC approval failed.",
                exception=e
            )
            return {"success": False, "message": str(e)}

    # ==========================================================================
    # INVENTORY HEALTH CHECK
    # ==========================================================================

    def health_check(self) -> Dict[str, Any]:
        try:
            result = (
                self.client
                .table("inventory_kpi_view")
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

    # ==========================================================================
    # MOBILE INVENTORY
    # CREATE PRODUCT + OPENING STOCK
    # ==========================================================================

    def create_product_with_stock(
        self,
        product_data: Dict[str, Any],
        opening_stock: int = 0,
        warehouse_id: Optional[int] = None,
        created_by: Any = None,
    ):
        try:
            barcode = product_data.get("barcode")

            if barcode:
                existing = (
                    self.client
                    .table("products")
                    .select("id")
                    .eq("barcode", barcode)
                    .execute()
                )

                if existing.data:
                    return {
                        "success": False,
                        "message": "Barcode already exists."
                    }

            product_data["stock"] = opening_stock
            product_data.setdefault("is_active", True)

            result = (
                self.client
                .table("products")
                .insert(product_data)
                .execute()
            )

            product = result.data[0]
            product_id = product["id"]

            if opening_stock > 0:
                self.create_inventory_log(
                    product_id=product_id,
                    quantity=opening_stock,
                    balance_after=opening_stock,
                    warehouse_id=warehouse_id,
                    created_by=created_by
                )

            return {
                "success": True,
                "data": product
            }

        except Exception as e:
            log_error(
                message="Mobile product creation failed.",
                exception=e
            )
            return {
                "success": False,
                "message": str(e)
            }

    # ==========================================================================
    # MOBILE INVENTORY LOG
    # ==========================================================================

    def create_inventory_log(
        self,
        product_id: int,
        quantity: float,
        balance_after: float,
        warehouse_id: Optional[int] = None,
        created_by: Any = None,
    ):
        payload = {
            "product_id": product_id,
            "reference_type": "OPENING",
            "quantity": quantity,
            "balance_after": balance_after,
            "remarks": "Mobile Inventory Opening Stock",
            "warehouse_id": warehouse_id,
            "created_by": created_by
        }

        return (
            self.client
            .table("inventory_logs")
            .insert(payload)
            .execute()
        )


# ==============================================================================
# EXPORT
# ==============================================================================
__all__ = ["InventoryService"]
