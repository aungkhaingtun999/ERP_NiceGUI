# ==============================================================================
# erp_core/services/inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE
# Version: V1.0 Production
#
# FIFO
# Valuation
# Stock Card
# KPI
# Loss Analytics
# ==============================================================================


from typing import Any, Dict, List

from ..base_repo import db


# ==============================================================================
# Inventory Service
# ==============================================================================


class InventoryService:


    # --------------------------------------------------------------------------
    # Inventory KPI
    # --------------------------------------------------------------------------

    @staticmethod
    def get_inventory_kpi() -> Dict[str, Any]:

        try:

            result = (
                db
                .table("inventory_kpi_view")
                .select("*")
                .single()
                .execute()
            )


            return result.data or {}


        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }



    # --------------------------------------------------------------------------
    # Warehouse Inventory KPI
    # --------------------------------------------------------------------------

    @staticmethod
    def get_warehouse_inventory_kpi() -> List[Dict]:


        try:

            result = (
                db
                .table("warehouse_inventory_kpi_view")
                .select("*")
                .execute()
            )


            return result.data or []


        except Exception:

            return []



    # --------------------------------------------------------------------------
    # Inventory Valuation
    # --------------------------------------------------------------------------

    @staticmethod
    def get_inventory_valuation() -> List[Dict]:


        try:

            result = (
                db
                .table("inventory_valuation_view")
                .select("*")
                .execute()
            )


            return result.data or []


        except Exception:

            return []



    # --------------------------------------------------------------------------
    # Inventory Loss Report
    # --------------------------------------------------------------------------

    @staticmethod
    def get_inventory_loss_report() -> List[Dict]:


        try:

            result = (
                db
                .table("inventory_loss_kpi_view")
                .select("*")
                .execute()
            )


            return result.data or []


        except Exception:

            return []



    # --------------------------------------------------------------------------
    # Stock Card
    # --------------------------------------------------------------------------

    @staticmethod
    def get_stock_card(
        product_id: int,
        warehouse_id: int
    ) -> List[Dict]:


        try:

            result = (
                db
                .table("stock_card_view")
                .select("*")
                .eq(
                    "product_id",
                    product_id
                )
                .eq(
                    "warehouse_id",
                    warehouse_id
                )
                .order(
                    "created_at"
                )
                .execute()
            )


            return result.data or []


        except Exception:

            return []



# ==============================================================================
# Export Instance
# ==============================================================================

inventory_service = InventoryService()
