# ==============================================================================
# erp_core/services/settings_service.py
# ERP ENTERPRISE SETTINGS SERVICE v2.0 FINAL
#
# Responsibility:
#
# - Central ERP Settings Management
# - Read / Write Settings
# - Type Conversion
# - Cache Friendly
# - Pricing Engine Support
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



    # ==========================================================================
    # INIT
    # ==========================================================================


    def __init__(

        self,

        client

    ):


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

                .limit(1)

                .execute()

            )



            if result.data:


                return result.data[0].get(

                    "value"

                )



        except Exception as e:


            log_error(

                message="Get setting failed",

                exception=e

            )



        return default







    # ==========================================================================
    # GET ALL SETTINGS
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


                row.get("key"):

                row.get("value")


                for row in rows


                if row.get("key")

            }



        except Exception as e:


            log_error(

                message="Get all settings failed",

                exception=e

            )


            return {}







    # ==========================================================================
    # SAVE SINGLE SETTING
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

        settings: Dict[str,Any]

    ):


        try:


            payload = [


                {


                    "key":

                        key,


                    "value":

                        str(value)

                }


                for key,value in settings.items()


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

                message="Bulk save settings failed",

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

        key:str

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


        return str(value).lower() == "true"







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







    def get_text(

        self,

        key,

        default=""

    ):


        value = self.get_setting(

            key,

            default

        )


        return str(value)








    # ==========================================================================
    # HEALTH CHECK
    # ==========================================================================


    def health_check(self):


        try:


            self.client.table(

                Tables.SETTINGS

            ).select(

                "id"

            ).limit(

                1

            ).execute()



            return {


                "service":

                    "SettingsService",


                "status":

                    "PASS"

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
