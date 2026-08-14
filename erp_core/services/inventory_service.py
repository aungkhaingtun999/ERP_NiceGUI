# ==============================================================================
# erp_core/services/inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE v38.0
#
# CLEAN RPC-DRIVEN VERSION
#
# Responsibilities:
# - Inventory health
# - Low stock alerts
# - Inventory KPI
# - Warehouse KPI
# - Inventory valuation
# - Inventory loss report
# - Stock card
# - Product batch settings
# - FEFO issue planning
# - Stock adjustment request
# - Stock adjustment history
# - FIFO COGS compatibility helper
#
# IMPORTANT
# ------------------------------------------------------------------------------
# FEFO calculation remains owned by PostgreSQL / Supabase.
#
# Python DOES NOT:
# - sort batches
# - calculate FEFO allocation
# - calculate shortage
# - calculate FEFO COGS
#
# Supabase remains the inventory source of truth.
#
# COMPATIBILITY
# ------------------------------------------------------------------------------
# erp_core.__init__ imports:
#
#     get_fifo_cogs
#
# Therefore this module provides a compatibility helper.
#
# The helper delegates inventory cost calculation to the existing
# get_fefo_issue_plan() RPC-driven flow instead of calculating cost in Python.
#
# ==============================================================================


from typing import (
    Any,
    Dict,
    List,
    Optional,
)


from ..base_repo import (
    log_error,
)


from .settings_service import (
    SettingsService,
)


# ==============================================================================
# CONSTANTS
# ==============================================================================

DEFAULT_MIN_STOCK_ALERT = 10


# ==============================================================================
# INTERNAL SAFE HELPERS
# ==============================================================================


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        return float(value)

    except Exception:

        return float(default)


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:

        return int(value)

    except Exception:

        return int(default)


def _normalize_rpc_data(
    data: Any,
) -> Any:
    """
    Normalize common Supabase RPC response shapes.

    PostgreSQL RPC may return:
        dict
        list[dict]
        scalar
        None
    """

    if isinstance(data, list):

        if len(data) == 1:

            return data[0]

        return data

    return data


# ==============================================================================
# INVENTORY SERVICE
# ==============================================================================


class InventoryService:

    # ==========================================================================
    # INIT
    # ==========================================================================

    def __init__(
        self,
        client,
    ):

        self.client = client

        self.settings = SettingsService(
            client
        )

    # ==========================================================================
    # HEALTH CHECK
    # ==========================================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:
        """
        Simple database connectivity check.
        """

        try:

            response = (
                self.client
                .table("warehouses")
                .select("id")
                .limit(1)
                .execute()
            )

            rows = response.data or []

            return {
                "success": True,
                "message":
                    "Inventory service is healthy",
                "rows":
                    len(rows),
            }

        except Exception as e:

            log_error(
                message=
                    "Inventory health check failed.",
                exception=e,
            )

            return {
                "success": False,
                "message": str(e),
                "rows": 0,
            }

    # ==========================================================================
    # LOW STOCK RULE
    # ==========================================================================

    def get_min_stock_alert(
        self,
    ) -> int:
        """
        Read minimum stock alert from canonical settings.

        IMPORTANT:
        SettingsService v6.0 exposes get_setting(), not get_int().
        Therefore we normalize the value here.
        """

        try:

            value = self.settings.get_setting(
                "MIN_STOCK_ALERT",
                DEFAULT_MIN_STOCK_ALERT,
            )

            return _safe_int(
                value,
                DEFAULT_MIN_STOCK_ALERT,
            )

        except Exception as e:

            log_error(
                message=
                    "Minimum stock setting load failed.",
                exception=e,
            )

            return DEFAULT_MIN_STOCK_ALERT

    # ==========================================================================
    # LOW STOCK CHECK
    # ==========================================================================

    def get_low_stock_alerts(
        self,
        warehouse_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:

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
                    int(warehouse_id),
                )

            result = query.execute()

            rows = result.data or []

            alerts = []

            for item in rows:

                qty = _safe_float(
                    item.get(
                        "qty",
                        0,
                    ),
                    0,
                )

                if qty <= minimum_stock:

                    alerts.append(
                        item
                    )

            return alerts

        except Exception as e:

            log_error(
                message=
                    "Low stock alert check failed.",
                exception=e,
            )

            return []

    # ==========================================================================
    # INVENTORY KPI
    # ==========================================================================

    def get_inventory_kpi(
        self,
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

            if isinstance(data, list):

                data = (
                    data[0]
                    if data
                    else {}
                )

            if not isinstance(data, dict):

                return {
                    "success": False,
                    "message":
                        "Invalid inventory KPI response.",
                }

            return {
                "success": True,

                "total_products":
                    data.get(
                        "total_products",
                        0,
                    ),

                "total_warehouses":
                    data.get(
                        "total_warehouses",
                        0,
                    ),

                "total_stock_qty":
                    data.get(
                        "total_stock_qty",
                        0,
                    ),

                "total_inventory_value":
                    data.get(
                        "total_inventory_value",
                        0,
                    ),

                "average_unit_value":
                    data.get(
                        "average_unit_value",
                        0,
                    ),

                "low_stock_items":
                    data.get(
                        "low_stock_items",
                        0,
                    ),
            }

        except Exception as e:

            log_error(
                message=
                    "Inventory KPI retrieval failed.",
                exception=e,
            )

            return {
                "success": False,
                "message": str(e),
            }

    # ==========================================================================
    # WAREHOUSE INVENTORY KPI
    # ==========================================================================

    def get_warehouse_inventory_kpi(
        self,
    ) -> List[Dict[str, Any]]:

        try:

            result = (
                self.client
                .table(
                    "warehouse_inventory_kpi_view"
                )
                .select("*")
                .execute()
            )

            return result.data or []

        except Exception as e:

            log_error(
                message=
                    "Warehouse KPI retrieval failed.",
                exception=e,
            )

            return []

    # ==========================================================================
    # INVENTORY VALUATION
    # ==========================================================================

    def get_inventory_valuation(
        self,
    ) -> List[Dict[str, Any]]:

        try:

            result = (
                self.client
                .table(
                    "inventory_valuation_view"
                )
                .select("*")
                .execute()
            )

            return result.data or []

        except Exception as e:

            log_error(
                message=
                    "Inventory valuation retrieval failed.",
                exception=e,
            )

            return []

    # ==========================================================================
    # INVENTORY LOSS REPORT
    # ==========================================================================

    def get_inventory_loss_report(
        self,
    ) -> List[Dict[str, Any]]:

        try:

            result = (
                self.client
                .table(
                    "inventory_loss_kpi_view"
                )
                .select("*")
                .execute()
            )

            return result.data or []

        except Exception as e:

            log_error(
                message=
                    "Inventory loss report retrieval failed.",
                exception=e,
            )

            return []

    # ==========================================================================
    # STOCK CARD
    # ==========================================================================

    def get_stock_card(
        self,
        product_id: int,
        warehouse_id: int,
    ) -> List[Dict[str, Any]]:

        try:

            result = (
                self.client
                .table("stock_card_view")
                .select("*")
                .eq(
                    "product_id",
                    int(product_id),
                )
                .eq(
                    "warehouse_id",
                    int(warehouse_id),
                )
                .order(
                    "created_at"
                )
                .execute()
            )

            return result.data or []

        except Exception as e:

            log_error(
                message=
                    "Stock card loading failed.",
                exception=e,
            )

            return []

    # ==========================================================================
    # PRODUCT BATCH SETTINGS
    # ==========================================================================

    def get_product_batch_settings(
        self,
        product_id: int,
    ) -> Dict[str, Any]:

        product_id = int(product_id)

        try:

            result = (
                self.client
                .table("products")
                .select(
                    """
                    id,
                    name,
                    track_batches,
                    track_expiry,
                    shelf_life_days
                    """
                )
                .eq(
                    "id",
                    product_id,
                )
                .single()
                .execute()
            )

            data = result.data

            if isinstance(data, list):

                if not data:

                    return {
                        "success": False,
                        "message":
                            "Product batch settings not found.",
                        "product_id":
                            product_id,
                    }

                data = data[0]

            if not isinstance(data, dict):

                return {
                    "success": False,
                    "message":
                        "Invalid product batch settings response.",
                    "product_id":
                        product_id,
                }

            return {
                "success": True,

                "product_id":
                    data.get(
                        "id"
                    ),

                "product_name":
                    data.get(
                        "name"
                    ),

                "track_batches":
                    bool(
                        data.get(
                            "track_batches",
                            False,
                        )
                    ),

                "track_expiry":
                    bool(
                        data.get(
                            "track_expiry",
                            False,
                        )
                    ),

                "shelf_life_days":
                    data.get(
                        "shelf_life_days",
                        0,
                    ),
            }

        except Exception as e:

            log_error(
                message=
                    "Product batch settings load failed.",
                exception=e,
            )

            return {
                "success": False,
                "message": str(e),
                "product_id":
                    product_id,
            }

    # ==========================================================================
    # FEFO ISSUE PLAN
    #
    # IMPORTANT
    # --------------------------------------------------------------------------
    # Python does NOT calculate FEFO.
    #
    # Supabase owns:
    # - batch ordering
    # - allocation
    # - shortage
    # - cost
    # ==========================================================================

    def get_fefo_issue_plan(
        self,
        product_id: int,
        warehouse_id: int,
        issue_quantity: float,
    ) -> Dict[str, Any]:

        product_id = int(product_id)
        warehouse_id = int(warehouse_id)

        requested_qty = _safe_float(
            issue_quantity,
            0,
        )

        try:

            if requested_qty <= 0:

                return {
                    "success": False,
                    "method": "FEFO",
                    "message":
                        "Issue quantity must be greater than zero.",

                    "product_id":
                        product_id,

                    "warehouse_id":
                        warehouse_id,

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

            response = (
                self.client
                .rpc(
                    "get_fefo_issue_plan",
                    {
                        "p_product_id":
                            product_id,

                        "p_warehouse_id":
                            warehouse_id,

                        "p_issue_quantity":
                            requested_qty,
                    },
                )
                .execute()
            )

            result = _normalize_rpc_data(
                response.data
            )

            if isinstance(result, list):

                if not result:

                    return {
                        "success": False,
                        "method": "FEFO",
                        "message":
                            "Empty FEFO RPC response.",

                        "product_id":
                            product_id,

                        "warehouse_id":
                            warehouse_id,

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

            if not isinstance(
                result,
                dict,
            ):

                return {
                    "success": False,
                    "method": "FEFO",
                    "message":
                        "Invalid FEFO RPC response.",

                    "product_id":
                        product_id,

                    "warehouse_id":
                        warehouse_id,

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

            return result

        except Exception as e:

            log_error(
                message=
                    "FEFO RPC call failed.",
                exception=e,
            )

            return {
                "success": False,
                "method": "FEFO",
                "message": str(e),

                "product_id":
                    product_id,

                "warehouse_id":
                    warehouse_id,

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

    # ==========================================================================
    # FIFO COGS COMPATIBILITY
    #
    # IMPORTANT
    # --------------------------------------------------------------------------
    # This function exists because erp_core.__init__.py publicly imports:
    #
    #     get_fifo_cogs
    #
    # It does NOT perform FIFO calculations in Python.
    #
    # The database remains responsible for inventory cost allocation.
    #
    # Current inventory architecture uses get_fefo_issue_plan().
    # Therefore this compatibility helper obtains total_cost from that
    # database-owned issue plan.
    # ==========================================================================

    def calculate_fifo_cogs(
        self,
        product_id: int,
        warehouse_id: int,
        issue_quantity: float,
    ) -> float:

        try:

            result = self.get_fefo_issue_plan(
                product_id=product_id,
                warehouse_id=warehouse_id,
                issue_quantity=issue_quantity,
            )

            if not result.get(
                "success",
                False,
            ):

                return 0.0

            return _safe_float(
                result.get(
                    "total_cost",
                    0,
                ),
                0,
            )

        except Exception as e:

            log_error(
                message=
                    "FIFO COGS compatibility calculation failed.",
                exception=e,
            )

            return 0.0

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

            if isinstance(
                data,
                list,
            ) and data:

                data = data[0]

            if data:

                return {
                    "success": True,
                    "data": data,
                }

            return {
                "success": False,
                "message":
                    "Stock adjustment insertion failed.",
            }

        except Exception as e:

            log_error(
                message=
                    "Stock adjustment failed.",
                exception=e,
            )

            return {
                "success": False,
                "message": str(e),
            }

    # ==========================================================================
    # STOCK ADJUSTMENT HISTORY
    # ==========================================================================

    def get_stock_adjustments(
        self,
        warehouse_id: int,
    ) -> List[Dict[str, Any]]:

        try:

            result = (
                self.client
                .table("stock_adjustments")
                .select(
                    """
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
                    """
                )
                .eq(
                    "warehouse_id",
                    int(warehouse_id),
                )
                .order(
                    "created_at",
                    desc=True,
                )
                .execute()
            )

            rows = result.data or []

            for row in rows:

                product_id = row.get(
                    "product_id"
                )

                if product_id is None:

                    row["product_name"] = (
                        "Unknown"
                    )

                    continue

                try:

                    product_result = (
                        self.client
                        .table("products")
                        .select("name")
                        .eq(
                            "id",
                            product_id,
                        )
                        .single()
                        .execute()
                    )

                    product_data = (
                        product_result.data
                    )

                    if isinstance(
                        product_data,
                        list,
                    ):

                        product_data = (
                            product_data[0]
                            if product_data
                            else {}
                        )

                    if isinstance(
                        product_data,
                        dict,
                    ):

                        row["product_name"] = (
                            product_data.get(
                                "name",
                                "Unknown",
                            )
                        )

                    else:

                        row["product_name"] = (
                            "Unknown"
                        )

                except Exception:

                    row["product_name"] = (
                        "Unknown"
                    )

            return rows

        except Exception as e:

            log_error(
                message=
                    "Stock adjustment history load failed.",
                exception=e,
            )

            return []


# ==============================================================================
# MODULE-LEVEL FIFO COGS COMPATIBILITY FUNCTION
#
# Required by:
#
#     from erp_core.services.inventory_service import get_fifo_cogs
#
# ==============================================================================


def get_fifo_cogs(
    product_id: int,
    warehouse_id: int,
    issue_quantity: float,
    client=None,
) -> float:
    """
    Public compatibility helper.

    IMPORTANT:
    No FIFO/FEFO calculation is performed in Python.

    If a database client is supplied, use it.

    Otherwise obtain the standard ERP database client lazily.

    The actual inventory cost remains database-driven.
    """

    try:

        if client is None:

            from ..base_repo import db

            client = db()

        service = InventoryService(
            client
        )

        return service.calculate_fifo_cogs(
            product_id=product_id,
            warehouse_id=warehouse_id,
            issue_quantity=issue_quantity,
        )

    except Exception as e:

        log_error(
            message=
                "get_fifo_cogs failed.",
            exception=e,
        )

        return 0.0


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    "InventoryService",
    "get_fifo_cogs",
]


# ==============================================================================
# END
# ==============================================================================
