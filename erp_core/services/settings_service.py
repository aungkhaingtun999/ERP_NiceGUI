# ==============================================================================
# erp_core/services/settings_service.py
# ERP ENTERPRISE SETTINGS SERVICE v1.0
#
# Responsibilities:
#
# - ERP Settings Read
# - ERP Settings Write
# - Cache Control
# - Default Value Handling
# - Pricing / Tax / Inventory Config Support
#
# Flow:
#
# Supabase
#      ↓
# SettingsService
#      ↓
# Loader / UI / Engine
#
# ==============================================================================


from typing import (
    Any,
    Dict,
    List,
    Optional
)


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


    """
    ERP Central Settings Manager

    Table:

        erp_settings


    Schema:

        id
        key
        value
        created_at
        updated_at

    """



    # ==========================================================================
    # INIT
    # ==========================================================================


    def __init__(self, client):

        self.client = client





    # ==========================================================================
    # GET SINGLE SETTING
    # ==========================================================================


    def get_setting(

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

                .select("*")

                .eq(

                    "key",

                    key

                )

                .order(

                    "id",

                    desc=True

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

                message="Settings get failed",

                exception=e

            )



        return default







    # ==========================================================================
    # GET ALL SETTINGS
    # ==========================================================================


    def get_all_settings(

        self

    ) -> Dict[str, Any]:


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .select("*")

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

                message="Load all settings failed",

                exception=e

            )


            return {}








    # ==========================================================================
    # SAVE SETTING
    # ==========================================================================


    def save_setting(

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



            return {


                "success":

                    True,


                "data":

                    result.data

            }



        except Exception as e:


            log_error(

                message="Save setting failed",

                exception=e

            )


            return {


                "success":

                    False,


                "message":

                    str(e)

            }







    # ==========================================================================
    # SAVE MULTIPLE SETTINGS
    # ==========================================================================


    def save_settings(

        self,

        settings: Dict[str, Any]

    ):


        try:


            payload = [


                {


                    "key":

                        key,


                    "value":

                        str(value)


                }


                for key, value in settings.items()


            ]



            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .upsert(

                    payload,

                    on_conflict="key"

                )

                .execute()

            )



            return {


                "success":

                    True,


                "data":

                    result.data

            }



        except Exception as e:


            log_error(

                message="Bulk settings save failed",

                exception=e

            )


            return {


                "success":

                    False,


                "message":

                    str(e)

            }







    # ==========================================================================
    # DELETE SETTING
    # ==========================================================================


    def delete_setting(

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



            return {


                "success":

                    True,


                "data":

                    result.data

            }



        except Exception as e:


            log_error(

                message="Delete setting failed",

                exception=e

            )


            return {


                "success":

                    False,


                "message":

                    str(e)

            }







    # ==========================================================================
    # TYPE HELPERS
    # ==========================================================================


    def get_bool(

        self,

        key,

        default=False

    ):


        value = self.get_setting(

            key,

            default

        )


        return (

            str(value)

            .lower()

            ==

            "true"

        )





    def get_float(

        self,

        key,

        default=0.0

    ):


        try:


            return float(

                self.get_setting(

                    key,

                    default

                )

            )


        except Exception:


            return float(default)






    def get_int(

        self,

        key,

        default=0

    ):


        try:


            return int(

                self.get_setting(

                    key,

                    default

                )

            )


        except Exception:


            return int(default)







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

                .limit(1)

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


                "version":

                    "2.0",


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


            log_error(

                message=

                "Settings health check failed",

                exception=e

            )


            return {


                "service":

                    "SettingsService",


                "version":

                    "2.0",


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
