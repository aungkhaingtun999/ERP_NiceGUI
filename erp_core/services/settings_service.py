# ==============================================================================
# erp_core/services/settings_service.py
# ERP SETTINGS SERVICE v4.0
#
# Maker - Checker Approval Workflow
#
# Features:
# - Create Setting Request
# - Duplicate Pending Block
# - Approve
# - Reject
# - Cancel
# ==============================================================================


from erp_core.repositories.settings_repository import (

    create_setting_request,

    get_pending_setting_requests,

    approve_setting_change,

    reject_setting_change,

    cancel_setting_change,

)



class SettingsService:



    def __init__(self, db):

        self.db = db



    # ==========================================================================
    # LOAD ALL SETTINGS
    # ==========================================================================

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
                "SETTINGS LOAD ERROR:",
                e
            )


            return {}




    # ==========================================================================
    # CREATE REQUEST
    # MAKER
    # ==========================================================================


    @staticmethod
    def request_change(

        setting_key,

        new_value,

        reason,

        requested_by

    ):


        # --------------------------------------------------
        # DUPLICATE PENDING CHECK
        # --------------------------------------------------

        pending = get_pending_setting_requests()



        for req in pending:


            if req.get("setting_key") == setting_key:


                return {

                    "success": False,

                    "message":
                    f"⏳ {setting_key} already waiting approval"

                }




        # --------------------------------------------------
        # CURRENT VALUE
        # --------------------------------------------------


        from erp_core.loaders.settings_loader import (

            get_all_settings_cached

        )


        settings = get_all_settings_cached()



        old_value = str(

            settings.get(

                setting_key,

                ""

            )

        )



        new_value = str(new_value)



        # --------------------------------------------------
        # NO CHANGE
        # --------------------------------------------------


        if old_value == new_value:


            return {

                "success": False,

                "message":
                "No change detected"

            }




        # --------------------------------------------------
        # CREATE REQUEST
        # --------------------------------------------------


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
            "Change request created. Waiting approval.",

            "request_id":
            request_id

        }




    # ==========================================================================
    # PENDING
    # ==========================================================================


    @staticmethod
    def get_pending_requests():

        return get_pending_setting_requests()




    # ==========================================================================
    # APPROVE
    # CHECKER ONLY
    # ==========================================================================


    @staticmethod
    def approve_request(

        request_id,

        checker_id

    ):


        return approve_setting_change(

            request_id,

            checker_id

        )




    # ==========================================================================
    # REJECT
    # CHECKER ONLY
    # ==========================================================================


    @staticmethod
    def reject_request(

        request_id,

        checker_id,

        reason

    ):


        return reject_setting_change(

            request_id,

            checker_id,

            reason

        )




    # ==========================================================================
    # CANCEL
    # MAKER ONLY
    # ==========================================================================


    @staticmethod
    def cancel_request(

        request_id,

        user_id

    ):


        return cancel_setting_change(

            request_id,

            user_id

        )
