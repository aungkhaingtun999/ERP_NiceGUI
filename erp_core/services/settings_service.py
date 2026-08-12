# ==============================================================================
# erp_core/services/settings_service.py
# ERP SETTINGS SERVICE v5.0
#
# ERP ENTERPRISE SETTINGS SERVICE
#
# Maker - Checker Approval Workflow
#
# Responsibilities:
# - Load settings
# - Read individual setting
# - Create Maker change request
# - Prevent duplicate pending requests
# - Detect no-change requests
# - Approve through RPC
# - Reject through RPC
# - Cancel by Maker
# - Direct save compatibility
#
# IMPORTANT:
# Normal configuration changes MUST use:
#
# Maker
#   ↓
# settings_change_requests
#   ↓
# PENDING
#   ↓
# Checker
#   ↓
# approve_setting_change_rpc
#   ↓
# settings
#
# Do NOT bypass Maker-Checker for normal UI changes.
# ==============================================================================


from erp_core.repositories.settings_repository import (

    create_setting_request,

    get_pending_setting_requests,

    approve_setting_change,

    reject_setting_change,

    cancel_setting_change,

)


# ==============================================================================
# VALUE NORMALIZATION
# ==============================================================================


def _normalize_value(value):

    """
    Normalize values for safe comparison.

    Examples:

        20
        20.0
        "20"
        "20.0"

    are considered equal.

    Boolean values are normalized as:

        True
        "true"
        "TRUE"

    -> "true"
    """

    if value is None:

        return ""


    # --------------------------------------------------------------------------
    # BOOLEAN
    # --------------------------------------------------------------------------

    if isinstance(value, bool):

        return "true" if value else "false"


    text = str(value).strip()


    if not text:

        return ""


    lower = text.lower()


    if lower in (
        "true",
        "false"
    ):

        return lower


    # --------------------------------------------------------------------------
    # NUMERIC
    # --------------------------------------------------------------------------

    try:

        number = float(text)


        if number.is_integer():

            return str(int(number))


        return str(number)


    except Exception:

        pass


    # --------------------------------------------------------------------------
    # TEXT
    # --------------------------------------------------------------------------

    return text


# ==============================================================================
# SETTINGS SERVICE
# ==============================================================================


class SettingsService:


    # ==========================================================================
    # INIT
    # ==========================================================================

    def __init__(

        self,

        db

    ):

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

                key = row.get("key")


                if not key:

                    continue


                settings[key] = row.get(
                    "value"
                )


            return settings


        except Exception as e:

            print(
                "SETTINGS LOAD ERROR:",
                e
            )

            return {}


    # ==========================================================================
    # GET SINGLE SETTING
    # ==========================================================================

    def get_setting(

        self,

        key,

        default=None

    ):

        if not key:

            return default


        try:

            result = (

                self.db

                .table("settings")

                .select("value")

                .eq(
                    "key",
                    key
                )

                .maybe_single()

                .execute()

            )


            if result.data:

                return result.data.get(
                    "value",
                    default
                )


            return default


        except Exception as e:

            print(
                "SETTING READ ERROR:",
                e
            )

            return default


    # ==========================================================================
    # SAVE SETTING
    #
    # COMPATIBILITY METHOD
    #
    # IMPORTANT:
    # This method is NOT intended for normal Maker-Checker UI changes.
    #
    # Normal settings changes should use request_change().
    #
    # This method exists because older code / loaders may call:
    #
    #     service.save_setting(key, value)
    #
    # ==========================================================================

    def save_setting(

        self,

        key,

        value

    ):

        if not key:

            return {

                "success": False,

                "message":
                    "Setting key is required"

            }


        try:

            result = (

                self.db

                .table("settings")

                .update({

                    "value": str(value)

                })

                .eq(
                    "key",
                    key
                )

                .execute()

            )


            if not result.data:

                return {

                    "success": False,

                    "message":
                        f"Setting not found: {key}"

                }


            return {

                "success": True,

                "message":
                    "Setting saved",

                "setting_key":
                    key,

                "value":
                    str(value)

            }


        except Exception as e:

            return {

                "success": False,

                "message":
                    str(e)

            }


    # ==========================================================================
    # CREATE CHANGE REQUEST
    # MAKER
    # ==========================================================================

    @staticmethod
    def request_change(

        setting_key,

        new_value,

        reason,

        requested_by

    ):

        # ----------------------------------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------------------------------

        if not setting_key:

            return {

                "success": False,

                "message":
                    "Setting key is required"

            }


        if not requested_by:

            return {

                "success": False,

                "message":
                    "Requester ID is required"

            }


        # ----------------------------------------------------------------------
        # DUPLICATE PENDING CHECK
        # ----------------------------------------------------------------------

        try:

            pending = (
                get_pending_setting_requests()
            )

        except Exception as e:

            return {

                "success": False,

                "message":
                    f"Unable to check pending requests: {e}"

            }


        for req in pending or []:

            if (
                str(
                    req.get("setting_key", "")
                ).strip()
                ==
                str(setting_key).strip()
            ):

                return {

                    "success": False,

                    "message":
                        (
                            f"⏳ {setting_key} "
                            "already waiting approval"
                        ),

                    "request_id":
                        req.get("id")

                }


        # ----------------------------------------------------------------------
        # LOAD CURRENT VALUE
        #
        # Use a fresh DB read instead of cached settings.
        # This prevents stale approval values.
        # ----------------------------------------------------------------------

        try:

            from erp_core.base_repo import db

            client = db()


            result = (

                client

                .table("settings")

                .select("value")

                .eq(
                    "key",
                    setting_key
                )

                .maybe_single()

                .execute()

            )


            if result.data:

                old_value = result.data.get(
                    "value"
                )

            else:

                old_value = ""


        except Exception as e:

            return {

                "success": False,

                "message":
                    (
                        "Unable to read current "
                        f"setting value: {e}"
                    )

            }


        # ----------------------------------------------------------------------
        # NORMALIZE VALUES
        # ----------------------------------------------------------------------

        old_normalized = _normalize_value(
            old_value
        )


        new_normalized = _normalize_value(
            new_value
        )


        # ----------------------------------------------------------------------
        # NO CHANGE
        # ----------------------------------------------------------------------

        if old_normalized == new_normalized:

            return {

                "success": False,

                "message":
                    "No change detected",

                "setting_key":
                    setting_key,

                "current_value":
                    str(old_value)

            }


        # ----------------------------------------------------------------------
        # CREATE REQUEST
        # ----------------------------------------------------------------------

        try:

            request_id = create_setting_request(

                setting_key,

                str(old_value)
                if old_value is not None
                else "",

                str(new_value),

                reason,

                requested_by

            )


        except Exception as e:

            return {

                "success": False,

                "message":
                    (
                        "Failed to create setting "
                        f"change request: {e}"
                    )

            }


        # ----------------------------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------------------------

        return {

            "success": True,

            "message":
                (
                    "Change request created. "
                    "Waiting for Checker approval."
                ),

            "request_id":
                request_id,

            "setting_key":
                setting_key,

            "old_value":
                str(old_value)
                if old_value is not None
                else "",

            "new_value":
                str(new_value),

            "status":
                "PENDING"

        }


    # ==========================================================================
    # GET PENDING REQUESTS
    # ==========================================================================

    @staticmethod
    def get_pending_requests():

        try:

            return (
                get_pending_setting_requests()
                or []
            )

        except Exception as e:

            return []


    # ==========================================================================
    # APPROVE
    # CHECKER
    # ==========================================================================

    @staticmethod
    def approve_request(

        request_id,

        checker_id

    ):

        if not request_id:

            return {

                "success": False,

                "message":
                    "Request ID is required"

            }


        if not checker_id:

            return {

                "success": False,

                "message":
                    "Checker ID is required"

            }


        try:

            return approve_setting_change(

                request_id,

                checker_id

            )

        except Exception as e:

            return {

                "success": False,

                "message":
                    str(e)

            }


    # ==========================================================================
    # REJECT
    # CHECKER
    # ==========================================================================

    @staticmethod
    def reject_request(

        request_id,

        checker_id,

        reason

    ):

        if not request_id:

            return {

                "success": False,

                "message":
                    "Request ID is required"

            }


        if not checker_id:

            return {

                "success": False,

                "message":
                    "Checker ID is required"

            }


        reason = (
            str(reason).strip()
            if reason is not None
            else ""
        )


        if not reason:

            reason = "Rejected by Checker"


        try:

            return reject_setting_change(

                request_id,

                checker_id,

                reason

            )

        except Exception as e:

            return {

                "success": False,

                "message":
                    str(e)

            }


    # ==========================================================================
    # CANCEL
    # MAKER ONLY
    # ==========================================================================

    @staticmethod
    def cancel_request(

        request_id,

        user_id

    ):

        if not request_id:

            return {

                "success": False,

                "message":
                    "Request ID is required"

            }


        if not user_id:

            return {

                "success": False,

                "message":
                    "User ID is required"

            }


        try:

            return cancel_setting_change(

                request_id,

                user_id

            )

        except Exception as e:

            return {

                "success": False,

                "message":
                    str(e)

            }


# ==============================================================================
# END
# ==============================================================================
