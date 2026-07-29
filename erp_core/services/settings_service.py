# ==============================================================================
# erp_core/services/settings_service.py
# ERP ENTERPRISE SETTINGS SERVICE v1.0 FINAL
#
# Central Configuration Engine
#
# Database:
#       erp_settings
#
# Used By:
#       PricingService
#       InventoryService
#       SalesService
#       Dashboard
#
# Features:
#       - Safe Settings Read
#       - Type Conversion
#       - Cache Support
#       - Update Settings
#       - Delete Settings
#       - Health Check
#
# ==============================================================================


from typing import (
    Any,
    Dict,
    List
)


import streamlit as st


from ..base_repo import (
    log_error
)


from ..config import (
    Tables
)





# ==============================================================================
# SETTINGS SERVICE
# ==============================================================================


class SettingsService:


    # ==========================================================================
    # Constructor
    # ==========================================================================

    def __init__(
        self,
        client
    ):

        self.client = client





    # ==========================================================================
    # GET SINGLE SETTING
    # ==========================================================================


    def get(

        self,

        key: str,

        default=None

    ):


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .select(

                    "value"

                )

                .eq(

                    "key",

                    key

                )

                .limit(1)

                .execute()

            )



            if result.data:


                return result.data[0].get(

                    "value"

                )



        except Exception as e:


            log_error(

                message=

                f"Settings get failed: {key}",

                exception=e

            )



        return default






    # ==========================================================================
    # GET ALL SETTINGS
    # ==========================================================================


    def get_all(

        self

    ) -> Dict[str, Any]:


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .select(

                    "*"

                )

                .execute()

            )



            rows = result.data or []



            return {


                row["key"]:

                row.get(

                    "value"

                )

                for row in rows

            }



        except Exception as e:


            log_error(

                message="Settings get_all failed",

                exception=e

            )


            return {}






    # ==========================================================================
    # NUMBER
    # ==========================================================================


    def get_float(

        self,

        key,

        default=0.0

    ):


        try:


            return float(

                self.get(

                    key,

                    default

                )

            )


        except Exception:


            return float(

                default

            )







    # ==========================================================================
    # INTEGER
    # ==========================================================================


    def get_int(

        self,

        key,

        default=0

    ):


        try:


            return int(

                float(

                    self.get(

                        key,

                        default

                    )

                )

            )


        except Exception:


            return int(

                default

            )







    # ==========================================================================
    # BOOLEAN
    # ==========================================================================


    def get_bool(

        self,

        key,

        default=False

    ):


        value = str(

            self.get(

                key,

                default

            )

        ).lower()



        return value in (

            "true",

            "1",

            "yes",

            "on"

        )







    # ==========================================================================
    # SAVE / UPDATE
    # ==========================================================================


    def save(

        self,

        key: str,

        value: Any

    ):


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .upsert(

                    {

                        "key":

                            key,


                        "value":

                            str(value)

                    },

                    on_conflict="key"

                )

                .execute()

            )


            self.clear_cache()



            return {


                "success":

                    True,


                "data":

                    result.data

            }




        except Exception as e:


            log_error(

                message=

                f"Settings save failed: {key}",

                exception=e

            )


            return {


                "success":

                    False,


                "message":

                    str(e)

            }








    # ==========================================================================
    # DELETE
    # ==========================================================================


    def delete(

        self,

        key: str

    ):


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .delete()

                .eq(

                    "key",

                    key

                )

                .execute()

            )



            self.clear_cache()



            return True




        except Exception as e:


            log_error(

                message=

                f"Settings delete failed: {key}",

                exception=e

            )


            return False







    # ==========================================================================
    # CACHE
    # ==========================================================================


    @staticmethod
    def clear_cache():


        try:

            st.cache_data.clear()


        except Exception:

            pass







    # ==========================================================================
    # COMMON ERP SETTINGS
    # ==========================================================================


    def get_default_tax_rate(self):


        return self.get_float(

            "DEFAULT_TAX_RATE",

            0

        )





    def get_default_markup(self):


        return self.get_float(

            "DEFAULT_MARKUP_PERCENT",

            20

        )





    def get_min_stock_alert(self):


        return self.get_float(

            "MIN_STOCK_ALERT",

            10

        )





    def get_currency(self):


        return self.get(

            "CURRENCY",

            "MMK"

        )







    # ==========================================================================
    # HEALTH CHECK
    # ==========================================================================


    def health_check(self):


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .select(

                    "id"

                )

                .limit(

                    1

                )

                .execute()

            )


            return {


                "service":

                    "SettingsService",


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

                    "SettingsService",


                "status":

                    "FAIL",


                "message":

                    str(e)

            }







# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "SettingsService"

]
