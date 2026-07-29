# ==============================================================================
# erp_core/services/settings_service.py
# ERP ENTERPRISE SETTINGS SERVICE v3.0 FINAL
#
# Central Settings Engine
#
# Support:
#
# - Read Setting
# - Read All Settings
# - Save Setting
# - Delete Setting
# - Type Conversion
#
# Database:
#
# erp_settings
#
# Columns:
#
# id
# key
# value
# created_at
#
# ==============================================================================


from typing import (
    Any,
    Dict
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



    def __init__(

        self,

        client

    ):

        self.client = client







    # ==========================================================================
    # GET ONE
    # ==========================================================================


    def get_setting(

        self,

        key,

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

                .limit(1)

                .execute()

            )



            if result.data:

                return result.data[0].get(
                    "value"
                )


        except Exception as e:


            log_error(

                message="get_setting failed",

                exception=e

            )


        return default







    # ==========================================================================
    # GET ALL
    # ==========================================================================


    def get_all_settings(self):


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

                row.get("value")


                for row in rows

                if row.get("key")

            }



        except Exception as e:


            log_error(

                message="get_all_settings failed",

                exception=e

            )


            return {}







    # ==========================================================================
    # SAVE
    # ==========================================================================


    def save_setting(

        self,

        key,

        value

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

                message="save_setting failed",

                exception=e

            )


            return {

                "success":

                    False,


                "message":

                    str(e)

            }







    # ==========================================================================
    # SAVE MULTIPLE
    # ==========================================================================


    def save_settings(

        self,

        settings: Dict[str,Any]

    ):


        try:


            payload = []


            for key,value in settings.items():


                payload.append(

                    {

                        "key":

                            key,


                        "value":

                            str(value)

                    }

                )



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

                message="save_settings failed",

                exception=e

            )


            return {

                "success":

                    False,


                "message":

                    str(e)

            }
