# ==============================================================================
# erp_core/services/settings_service.py
# ERP ENTERPRISE SETTINGS SERVICE v2.0 FINAL
#
# Central ERP Configuration Manager
#
# Table:
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


    """
    Central ERP Settings Engine

    Responsible:

    - Read settings
    - Save settings
    - Bulk update
    - Type conversion

    """


    # ==========================================================================
    # INIT
    # ==========================================================================


    def __init__(
        self,
        client
    ):

        self.client = client



    # ==========================================================================
    # GET SINGLE
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

                .select(

                    "*"

                )

                .eq(

                    "key",

                    key

                )

                .limit(

                    1

                )

                .execute()

            )



            if result.data:

                return result.data[0].get(
                    "value"
                )



        except Exception as e:


            log_error(

                message="Get setting error",

                exception=e

            )


        return default




    # ==========================================================================
    # GET ALL SETTINGS
    # ==========================================================================


    def get_all_settings(
        self
    ) -> Dict[str,Any]:


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

                row.get("value")


                for row in rows


                if row.get("key")

            }



        except Exception as e:


            log_error(

                message="Load all settings error",

                exception=e

            )


            return {}





    # ==========================================================================
    # SAVE SINGLE
    # ==========================================================================


    def save_setting(

        self,

        key,

        value

    ):


        try:


            if not key:


                return {

                    "success":False,

                    "message":
                    "Setting key required"

                }



            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .upsert(

                    {

                        "key":

                            str(key),


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

                message="Save setting error",

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

        settings:dict

    ):


        try:


            if not settings:


                return {


                    "success":

                    False,


                    "message":

                    "No settings supplied"

                }




            payload = []


            for key,value in settings.items():


                payload.append(

                    {

                        "key":

                        str(key),


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

                message="Bulk save settings error",

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


    def delete_setting(

        self,

        key

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

                message="Delete setting error",

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

        key

    ):


        value = self.get_setting(

            key

        )


        return (

            str(value)

            .lower()

            ==

            "true"

        )





    def get_float(

        self,

        key

    ):


        try:


            value = self.get_setting(

                key

            )


            if value is None:

                return None



            return float(value)



        except Exception:


            return None





    def get_int(

        self,

        key

    ):


        try:


            value = self.get_setting(

                key

            )


            if value is None:

                return None



            return int(value)



        except Exception:


            return None





    def get_text(

        self,

        key

    ):


        value = self.get_setting(

            key

        )


        return value





    # ==========================================================================
    # HEALTH CHECK
    # ==========================================================================


    def health_check(

        self

    ):


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
