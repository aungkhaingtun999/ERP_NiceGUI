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
#
# Compatible:
#   erp_core.base_repo.db()
#   99_System_Test.py
#
# ==============================================================================


from typing import Any, Dict, List


from ..base_repo import (
    db,
    log_error
)



# ==============================================================================
# Inventory Service
# ==============================================================================


class InventoryService:


    def __init__(
        self,
        client
    ):

        self.client = client


    # ==========================================================================
    # Inventory KPI
    # ==========================================================================

    @staticmethod
    def get_inventory_kpi() -> Dict[str, Any]:


        try:

            result = (

                self.client
                  .table()(
                    "inventory_kpi_view"
                )

                .select(
                    "*"
                )

                .single()

                .execute()

            )


            data = result.data or {}


            return {


                "success":
                    True,


                "total_products":
                    data.get(
                        "total_products",
                        0
                    ),


                "total_warehouses":
                    data.get(
                        "total_warehouses",
                        0
                    ),


                "total_stock_qty":
                    data.get(
                        "total_stock_qty",
                        0
                    ),


                "total_inventory_value":
                    data.get(
                        "total_inventory_value",
                        0
                    ),


                "average_unit_value":
                    data.get(
                        "average_unit_value",
                        0
                    ),


                "low_stock_items":
                    data.get(
                        "low_stock_items",
                        0
                    )

            }



        except Exception as e:


            log_error(

                message=
                "Inventory KPI failed",

                exception=e

            )


            return {

                "success":
                    False,

                "message":
                    str(e)

            }





    # ==========================================================================
    # Warehouse Inventory KPI
    # ==========================================================================

    @staticmethod
    def get_warehouse_inventory_kpi() -> List[Dict]:


        try:


            result = (

                self.client
                 .table()(
                    "warehouse_inventory_kpi_view"
                )

                .select(
                    "*"
                )

                .execute()

            )


            return result.data or []



        except Exception as e:


            log_error(

                message=
                "Warehouse KPI failed",

                exception=e

            )


            return []





    # ==========================================================================
    # Inventory Valuation
    # ==========================================================================

    @staticmethod
    def get_inventory_valuation() -> List[Dict]:


        try:


            result = (

                self.client
                  .table()(
                    "inventory_valuation_view"
                )

                .select(
                    "*"
                )

                .execute()

            )


            return result.data or []



        except Exception as e:


            log_error(

                message=
                "Inventory valuation failed",

                exception=e

            )


            return []





    # ==========================================================================
    # Inventory Loss Report
    # ==========================================================================

    @staticmethod
    def get_inventory_loss_report() -> List[Dict]:


        try:


            result = (

                self.client
                  .table()(
                    "inventory_loss_kpi_view"
                )

                .select(
                    "*"
                )

                .execute()

            )


            return result.data or []



        except Exception as e:


            log_error(

                message=
                "Inventory loss report failed",

                exception=e

            )


            return []





    # ==========================================================================
    # Stock Card
    # ==========================================================================

    @staticmethod
    def get_stock_card(

        product_id: int,

        warehouse_id: int

    ) -> List[Dict]:


        try:


            result = (

                self.client
                  .table()(
                    "stock_card_view"
                )

                .select(
                    "*"
                )

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



        except Exception as e:


            log_error(

                message=
                "Stock card loading failed",

                exception=e

            )


            return []





    # ==========================================================================
    # Inventory Health Check
    # ==========================================================================

    @staticmethod
    def health_check() -> Dict[str, Any]:


        try:


            result = (

                self.client
                  .table()(
                    "inventory_kpi_view"
                )

                .select(
                    "*"
                )

                .limit(
                    1
                )

                .execute()

            )


            return {


                "service":
                    "InventoryService",


                "status":
                    "PASS",


                "database":
                    "CONNECTED",


                "rows":
                    len(
                        result.data or []
                    )

            }



        except Exception as e:


            return {


                "service":
                    "InventoryService",


                "status":
                    "FAIL",


                "message":
                    str(e)

            }





# ==============================================================================
# Export Instance
# ==============================================================================


# Export helper only
inventory_service = None()
