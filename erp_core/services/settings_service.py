# ==============================================================================
# erp_core/services/settings_service.py
# ERP SETTINGS SERVICE
# Maker - Checker Workflow
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


            for row in result.data:


                settings[
                    row["key"]
                ] = row["value"]



            return settings



        except Exception as e:


            print(
                "GET SETTINGS ERROR:",
                e
            )


            return {}



    # --------------------------------------------------------------------------
    # CREATE CHANGE REQUEST
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


        request_id = create_setting_request(

            setting_key,

            str(old_value),

            str(new_value),

            reason,

            requested_by

        )


        return {

            "success": True,

            "request_id": request_id

        }



    # --------------------------------------------------------------------------
    # PENDING LIST
    # --------------------------------------------------------------------------

    @staticmethod
    def get_pending_requests():

        return get_pending_setting_requests()



    # --------------------------------------------------------------------------
    # APPROVE REQUEST
    # --------------------------------------------------------------------------

    @staticmethod
    def approve_request(
        request_id,
        checker_id
    ):


        return approve_setting_change(

            request_id,

            checker_id

        )
