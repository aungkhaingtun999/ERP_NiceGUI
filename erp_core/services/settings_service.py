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


        # Local import to avoid circular import

        from erp_core.loaders.settings_loader import (
            get_all_settings_cached
        )



        settings = get_all_settings_cached()



        old_value = settings.get(
            setting_key
        )



        if old_value is None:

            old_value = ""



        old_value = str(old_value)

        new_value = str(new_value)



        # No change

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
