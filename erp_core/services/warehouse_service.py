# ==============================================================================
# erp_core/services/warehouse_service.py
# ERP ENTERPRISE WAREHOUSE SERVICE v1.0
# ==============================================================================


from ..base_repo import log_error
from ..config import Tables



class WarehouseService:


    def __init__(self, client):

        self.client = client



    # ==========================================================
    # DEFAULT WAREHOUSE FROM SETTINGS
    # ==========================================================

    def get_default_warehouse_id(self):


        try:


            setting = (

                self.client

                .table(
                    Tables.SETTINGS
                )

                .select(
                    "value"
                )

                .eq(
                    "key",
                    "DEFAULT_WAREHOUSE_ID"
                )

                .limit(1)

                .execute()

            )


            if setting.data:


                return int(
                    setting.data[0]["value"]
                )


        except Exception as e:


            log_error(

                message=
                "get_default_warehouse_id failed",

                exception=e

            )


        return None