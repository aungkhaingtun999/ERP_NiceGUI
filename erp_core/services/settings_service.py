# ==============================================================================
# erp_core/services/settings_service.py
# ERP SETTINGS SERVICE
# Maker - Checker Workflow v2.0
# ==============================================================================


from erp_core.repositories.settings_repository import (
    create_setting_request,
    get_pending_setting_requests,
    approve_setting_change,
)



class SettingsService:


    def __init__(self, db):

        self.db = db



    # --------------------------------------------------------------------------
    # LOAD ALL SETTINGS
    # --------------------------------------------------------------------------

    def get_all_settings(self):

        try:

            result = (
                self.db
                .table("settings")
                .select("*")
                .execute()
            )


            settings = {}


            for row in result.data or []:

                settings[row["key"]] = row["value"]


            return settings


        except Exception as e:

            print(
                "GET SETTINGS ERROR:",
                e
            )

            return {}



    # --------------------------------------------------------------------------
    # CREATE CHANGE REQUEST
    # Maker
    # --------------------------------------------------------------------------

    @staticmethod
    def request_change(
        setting_key,
        new_value,
        reason,
        requested_by
    ):


        from erp_core.loaders.settings_loader import (
            get_all_settings_cached
        )


        settings = get_all_settings_cached()



        old_value = settings.get(
            setting_key,
            ""
        )



        old_value = str(old_value)

        new_value = str(new_value)



        # --------------------------------------------------
        # DUPLICATE PENDING CHECK
        # --------------------------------------------------

        pending_requests = (
            get_pending_setting_requests()
        )



        for req in pending_requests:


            if req["setting_key"] == setting_key:


                return {

                    "success": False,

                    "message":
                    "A pending request already exists for this setting"

                }




        # --------------------------------------------------
        # NO CHANGE CHECK
        # --------------------------------------------------

        if old_value == new_value:


            return {

                "success": False,

                "message":
                "No change detected"

            }



        request_id = create_setting_request(

            setting_key,

            old_value,

            new_value,

            reason,

            requested_by

        )



        return {

            "success": True,

            "message":
            "Setting change request created",

            "request_id":
            request_id

        }





    # --------------------------------------------------------------------------
    # PENDING REQUESTS
    # --------------------------------------------------------------------------

    @staticmethod
    def get_pending_requests():

        return get_pending_setting_requests()




    # --------------------------------------------------------------------------
    # APPROVE REQUEST
    # Checker Only
    # --------------------------------------------------------------------------

    @staticmethod
    def approve_request(
        request_id,
        checker_id
    ):


        result = approve_setting_change(

            request_id,

            checker_id

        )


        return result





    # --------------------------------------------------------------------------
    # REJECT REQUEST
    # Checker Only
    # --------------------------------------------------------------------------

    @staticmethod
    def reject_request(
        request_id,
        checker_id,
        reason
    ):


        from erp_core.repositories.settings_repository import (
            reject_setting_change
        )


        return reject_setting_change(

            request_id,

            checker_id,

            reason

        )





    # --------------------------------------------------------------------------
    # CANCEL REQUEST
    # Maker Only
    # --------------------------------------------------------------------------

    @staticmethod
    def cancel_request(
        request_id,
        user_id
    ):


        from erp_core.repositories.settings_repository import (
            cancel_setting_change
        )


        return cancel_setting_change(

            request_id,

            user_id

        )
