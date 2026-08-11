# ==============================================================================
# erp_core/services/inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE
# CLEAN RPC-DRIVEN VERSION
#
# Architecture:
#
# Streamlit
#     ↓
# InventoryService
#     ↓
# Supabase RPC
#     ↓
# get_fefo_issue_plan()
#     ↓
# inventory_batches
#
# FEFO calculation is owned by Supabase.
#
# Python DOES NOT:
# - sort batches
# - calculate allocation
# - calculate shortage
# - calculate FEFO COGS
#
# Supabase is the source of truth.
# ==============================================================================

from typing import Any, Dict, List, Optional

from ..base_repo import log_error
from .settings_service import SettingsService


# ==============================================================================
# INVENTORY SERVICE
# ==============================================================================

class InventoryService:

    def __init__(self, client):

        self.client = client

        self.settings = SettingsService(
            client
        )

    # ==========================================================================
    # LOW STOCK RULE
    # ==========================================================================

    def get_min_stock_alert(self) -> int:

        try:

            return self.settings.get_int(
                "MIN_STOCK_ALERT",
                10
            )

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
        self,
        warehouse_id: Optional[int] = None
    ) -> List[Dict]:

        try:

            minimum_stock = float(
                self.get_min_stock_alert()
            )

            query = (
                self.client
                .table("warehouse_stock")
                .select("*")
            )

            if warehouse_id is not None:

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id)
                )

            result = query.execute()

            rows = result.data or []

            return [
                item
                for item in rows
                if float(
                    item.get("qty", 0) or 0
                ) <= minimum_stock
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

    def get_inventory_kpi(
        self
    ) -> Dict[str, Any]:

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
                "total_products":
                    data.get("total_products", 0),
                "total_warehouses":
                    data.get("total_warehouses", 0),
                "total_stock_qty":
                    data.get("total_stock_qty", 0),
                "total_inventory_value":
                    data.get("total_inventory_value", 0),
                "average_unit_value":
                    data.get("average_unit_value", 0),
                "low_stock_items":
                    data.get("low_stock_items", 0),
            }

        except Exception as e:

            log_error(
                message="Inventory KPI retrieval failed.",
                exception=e
            )

            return {
                "success": False,
                "message": str(e)
            }

    # ==========================================================================
    # WAREHOUSE INVENTORY KPI
    # ==========================================================================

    def get_warehouse_inventory_kpi(
        self
    ) -> List[Dict]:

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

    def get_inventory_valuation(
        self
    ) -> List[Dict]:

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

    def get_inventory_loss_report(
        self
    ) -> List[Dict]:

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
        self,
        product_id: int,
        warehouse_id: int
    ) -> List[Dict]:

        try:

            result = (
                self.client
                .table("stock_card_view")
                .select("*")
                .eq(
                    "product_id",
                    int(product_id)
                )
                .eq(
                    "warehouse_id",
                    int(warehouse_id)
                )
                .order(
                    "created_at"
                )
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
    # PRODUCT BATCH SETTINGS
    # ==========================================================================

    def get_product_batch_settings(
        self,
        product_id: int
    ) -> Dict[str, Any]:

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
                .eq(
                    "id",
                    int(product_id)
                )
                .single()
                .execute()
            )

            data = result.data

            # ------------------------------------------------------------------
            # Normalize Supabase / test response
            # ------------------------------------------------------------------

            if isinstance(data, list):

                if not data:

                    return {
                        "success": False,
                        "message":
                            "Product batch settings not found.",
                        "product_id":
                            int(product_id),
                    }

                data = data[0]

            if not isinstance(data, dict):

                return {
                    "success": False,
                    "message":
                        "Invalid product batch settings response.",
                    "product_id":
                        int(product_id),
                }

            return {
                "success": True,
                "product_id":
                    data.get("id"),
                "product_name":
                    data.get("name"),
                "track_batches":
                    bool(
                        data.get(
                            "track_batches",
                            False
                        )
                    ),
                "track_expiry":
                    bool(
                        data.get(
                            "track_expiry",
                            False
                        )
                    ),
                "shelf_life_days":
                    data.get(
                        "shelf_life_days",
                        0
                    ),
            }

        except Exception as e:

            log_error(
                message="Product batch settings load failed.",
                exception=e
            )

            return {
                "success": False,
                "message": str(e),
                "product_id": int(product_id),
            }

    # ==========================================================================
    # FEFO ISSUE PLAN
    #
    # IMPORTANT:
    # FEFO calculation is NOT performed in Python.
    #
    # Supabase RPC:
    #
    #     get_fefo_issue_plan(
    #         p_product_id,
    #         p_warehouse_id,
    #         p_issue_quantity
    #     )
    #
    # owns:
    # - batch ordering
    # - allocation
    # - shortage
    # - total COGS
    # ==========================================================================

    def get_fefo_issue_plan(
        self,
        product_id: int,
        warehouse_id: int,
        issue_quantity: float
    ) -> Dict[str, Any]:

        try:

            requested_qty = float(
                issue_quantity
            )

            if requested_qty <= 0:

                return {
                    "success": False,
                    "method": "FEFO",
                    "message":
                        "Issue quantity must be greater than zero.",
                    "product_id":
                        int(product_id),
                    "warehouse_id":
                        int(warehouse_id),
                    "requested_qty":
                        requested_qty,
                    "allocated_qty":
                        0,
                    "shortage_qty":
                        requested_qty,
                    "total_cost":
                        0,
                    "allocations":
                        [],
                }

            # ------------------------------------------------------------------
            # SUPABASE RPC
            # ------------------------------------------------------------------

            response = (
                self.client
                .rpc(
                    "get_fefo_issue_plan",
                    {
                        "p_product_id":
                            int(product_id),

                        "p_warehouse_id":
                            int(warehouse_id),

                        "p_issue_quantity":
                            requested_qty,
                    }
                )
                .execute()
            )

            result = response.data

            # ------------------------------------------------------------------
            # Normalize RPC response
            #
            # Supabase normally returns JSON object.
            # Some mocks may return a list.
            # ------------------------------------------------------------------

            if isinstance(result, list):

                if not result:

                    return {
                        "success": False,
                        "method": "FEFO",
                        "message":
                            "Empty FEFO RPC response.",
                        "product_id":
                            int(product_id),
                        "warehouse_id":
                            int(warehouse_id),
                        "requested_qty":
                            requested_qty,
                        "allocated_qty":
                            0,
                        "shortage_qty":
                            requested_qty,
                        "total_cost":
                            0,
                        "allocations":
                            [],
                    }

                result = result[0]

            # ------------------------------------------------------------------
            # Validate response
            # ------------------------------------------------------------------

            if not isinstance(result, dict):

                return {
                    "success": False,
                    "method": "FEFO",
                    "message":
                        "Invalid FEFO RPC response.",
                    "product_id":
                        int(product_id),
                    "warehouse_id":
                        int(warehouse_id),
                    "requested_qty":
                        requested_qty,
                    "allocated_qty":
                        0,
                    "shortage_qty":
                        requested_qty,
                    "total_cost":
                        0,
                    "allocations":
                        [],
                }

            # ------------------------------------------------------------------
            # Return Supabase result directly
            #
            # Database remains source of truth.
            # ------------------------------------------------------------------

            return result

        except Exception as e:

            log_error(
                message="FEFO RPC call failed.",
                exception=e
            )

            return {
                "success": False,
                "method": "FEFO",
                "message": str(e),
                "product_id":
                    int(product_id),
                "warehouse_id":
                    int(warehouse_id),
                "requested_qty":
                    float(issue_quantity),
                "allocated_qty":
                    0,
                "shortage_qty":
                    float(issue_quantity),
                "total_cost":
                    0,
                "allocations":
                    [],
            }

    # ==========================================================================
    # STOCK ADJUSTMENT
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
                "product_id":
                    int(product_id),

                "warehouse_id":
                    int(warehouse_id),

                "qty":
                    float(quantity),

                "reason":
                    str(reason),

                "adjustment_type":
                    "COUNT_CORRECTION",

                "status":
                    "PENDING",

                "unit_cost":
                    float(unit_cost),
            }

            if created_by:

                payload["requested_by"] = str(
                    created_by
                )

            response = (
                self.client
                .table("stock_adjustments")
                .insert(payload)
                .execute()
            )

            data = response.data

            if isinstance(data, list) and data:

                data = data[0]

            if data:

                return {
                    "success": True,
                    "data": data
                }

            return {
                "success": False,
                "message":
                    "Stock adjustment insertion failed."
            }

        except Exception as e:

            log_error(
                message="Stock adjustment failed.",
                exception=e
            )

            return {
                "success": False,
                "message": str(e)
            }

    # ==========================================================================
    # STOCK ADJUSTMENT HISTORY
    # ==========================================================================

    def get_stock_adjustments(
        self,
        warehouse_id: int
    ) -> List[Dict]:

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
                .eq(
                    "warehouse_id",
                    int(warehouse_id)
                )
                .order(
                    "created_at",
                    desc=True
                )
                .execute()
            )

            rows = result.data or []

            for row in rows:

                product_result = (
                    self.client
                    .table("products")
                    .select("name")
                    .eq(
                        "id",
                        row["product_id"]
                    )
                    .single()
                    .execute()
                )

                product_data = (
                    product_result.data
                )

                if isinstance(
                    product_data,
                    list
                ):

                    product_data = (
                        product_data[0]
                        if product_data
                        else {}
                    )

                row["product_name"] = (
                    product_data.get(
                        "name",
                        "Unknown"
                    )
                    if isinstance(
                        product_data,
                        dict
                    )
                    else "Unknown"
                )

            return rows

        except Exception as e:

            log_error(
                message="Stock adjustment history load failed.",
                exception=e
            )

            return []
