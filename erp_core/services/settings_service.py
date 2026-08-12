# ==============================================================================
# erp_core/services/settings_service.py
# ERP SETTINGS SERVICE v6.0
#
# ERP ENTERPRISE SETTINGS SERVICE
#
# Canonical Settings Source:
#     public.settings
#
# Approval Queue:
#     public.settings_change_requests
#
# Maker - Checker Approval Workflow
#
# Responsibilities:
# - Load settings
# - Read individual setting
# - Create Maker change request
# - Prevent duplicate pending requests
# - Detect no-change requests
# - Approve through PostgreSQL RPC
# - Reject through PostgreSQL RPC
# - Cancel by Maker
# - Legacy direct-save compatibility
#
# IMPORTANT:
#
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
# public.settings
#
# erp_settings is NOT used.
#
# ==============================================================================


from typing import Any, Dict, List


from erp_core.repositories.settings_repository import (

    get_all_settings,

    get_setting,

    create_setting_request,

    get_pending_setting_requests,

    approve_setting_change,

    reject_setting_change,

    cancel_setting_change,

)


# ==============================================================================
# VALUE NORMALIZATION
# ==============================================================================


def _normalize_value(value: Any) -> str:
    """
    Normalize values for safe comparison.

    Examples:

        20
        20.0
        "20"
        "20.0"

    become:

        "20"

    Boolean values:

        True
        "true"
        "TRUE"

    become:

        "true"

    Text remains case-sensitive.
    """

    if value is None:

        return ""


    # --------------------------------------------------------------------------
    # BOOLEAN
    # --------------------------------------------------------------------------

    if isinstance(value, bool):

        return (
            "true"
            if value
            else "false"
        )


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

            return str(
                int(number)
            )


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

        db=None

    ):

        self.db = db


    # ==========================================================================
    # LOAD ALL SETTINGS
    # ==========================================================================

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Load all settings from canonical public.settings.
        """

        try:

            return get_all_settings()


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

        key: str,

        default: Any = None

    ) -> Any:
        """
        Read one setting from canonical public.settings.
        """

        if not key:

            return default


        try:

            return get_setting(

                key,

                default

            )


        except Exception as e:

            print(
                "SETTING READ ERROR:",
                e
            )

            return default


    # ==========================================================================
    # DIRECT SAVE
    #
    # LEGACY COMPATIBILITY ONLY
    #
    # IMPORTANT:
    #
    # Normal Settings UI MUST NOT use this method.
    #
    # It exists only because older modules may still call:
    #
    #     service.save_setting(key, value)
    #
    # Future code should migrate those callers to request_change().
    # ==========================================================================

    def save_setting(

        self,

        key: str,

        value: Any

    ) -> Dict[str, Any]:

        if not key:

            return {

                "success":
                    False,

                "message":
                    "Setting key is required."

            }


        try:

            from erp_core.base_repo import db

            client = db()


            result = (

                client

                .table("settings")

                .update({

                    "value":
                        str(value),

                    "updated_at":
                        "now()"

                })

                .eq(
                    "key",
                    key
                )

                .execute()

            )


            if not result.data:

                return {

                    "success":
                        False,

                    "message":
                        f"Setting not found: {key}"

                }


            return {

                "success":
                    True,

                "message":
                    "Setting saved directly.",

                "setting_key":
                    key,

                "value":
                    str(value)

            }


        except Exception as e:

            return {

                "success":
                    False,

                "message":
                    str(e)

            }


    # ==========================================================================
    # CREATE CHANGE REQUEST
    # MAKER
    # ==========================================================================

    @staticmethod
    def request_change(

        setting_key: str,

        new_value: Any,

        reason: str,

        requested_by: str

    ) -> Dict[str, Any]:
        """
        Create a Maker change request.

        Does NOT modify public.settings.

        Workflow:

            current value
                ↓
            compare
                ↓
            create PENDING request
        """

        # ----------------------------------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------------------------------

        setting_key = (
            str(setting_key).strip()
            if setting_key is not None
            else ""
        )


        if not setting_key:

            return {

                "success":
                    False,

                "message":
                    "Setting key is required."

            }


        if not requested_by:

            return {

                "success":
                    False,

                "message":
                    "Requester ID is required."

            }


        reason = (

            str(reason).strip()

            if reason is not None

            else ""

        )


        if not reason:

            reason = "Setting change request"


        # ----------------------------------------------------------------------
        # DUPLICATE PENDING CHECK
        # ----------------------------------------------------------------------

        try:

            pending = (
                get_pending_setting_requests()
                or []
            )


        except Exception as e:

            return {

                "success":
                    False,

                "message":
                    (
                        "Unable to check pending "
                        f"setting requests: {e}"
                    )

            }


        for request in pending:

            existing_key = str(

                request.get(
                    "setting_key",
                    ""
                )

            ).strip()


            if existing_key == setting_key:

                return {

                    "success":
                        False,

                    "message":
                        (
                            f"⏳ {setting_key} "
                            "already waiting approval."
                        ),

                    "request_id":
                        request.get("id"),

                    "status":
                        request.get("status")

                }


        # ----------------------------------------------------------------------
        # LOAD CURRENT VALUE
        #
        # IMPORTANT:
        # Repository reads public.settings directly.
        #
        # We deliberately DO NOT use cached settings here.
        #
        # This prevents stale values when another approval has just occurred.
        # ----------------------------------------------------------------------

        try:

            old_value = get_setting(

                setting_key,

                ""

            )


        except Exception as e:

            return {

                "success":
                    False,

                "message":
                    (
                        "Unable to read current "
                        f"setting value: {e}"
                    )

            }


        # ----------------------------------------------------------------------
        # NORMALIZE
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

                "success":
                    False,

                "message":
                    "No change detected.",

                "setting_key":
                    setting_key,

                "current_value":
                    str(old_value)
                    if old_value is not None
                    else ""

            }


        # ----------------------------------------------------------------------
        # CREATE PENDING REQUEST
        # ----------------------------------------------------------------------

        try:

            request_id = create_setting_request(

                setting_key,

                (
                    str(old_value)
                    if old_value is not None
                    else ""
                ),

                str(new_value),

                reason,

                requested_by

            )


        except Exception as e:

            return {

                "success":
                    False,

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

            "success":
                True,

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
                (
                    str(old_value)
                    if old_value is not None
                    else ""
                ),

            "new_value":
                str(new_value),

            "status":
                "PENDING"

        }


    # ==========================================================================
    # GET PENDING REQUESTS
    # ==========================================================================

    @staticmethod
    def get_pending_requests() -> List[Dict[str, Any]]:
        """
        Return all pending setting requests.
        """

        try:

            return (
                get_pending_setting_requests()
                or []
            )


        except Exception as e:

            print(
                "PENDING SETTINGS LOAD ERROR:",
                e
            )

            return []


    # ==========================================================================
    # APPROVE
    # CHECKER
    # ==========================================================================

    @staticmethod
    def approve_request(

        request_id,

        checker_id

    ) -> Dict[str, Any]:
        """
        Approve setting change through PostgreSQL RPC.

        Python never directly marks the request APPROVED.
        """

        if request_id is None:

            return {

                "success":
                    False,

                "message":
                    "Request ID is required."

            }


        if not checker_id:

            return {

                "success":
                    False,

                "message":
                    "Checker ID is required."

            }


        try:

            return approve_setting_change(

                request_id,

                checker_id

            )


        except Exception as e:

            return {

                "success":
                    False,

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

        reason=None

    ) -> Dict[str, Any]:
        """
        Reject setting change through PostgreSQL RPC.
        """

        if request_id is None:

            return {

                "success":
                    False,

                "message":
                    "Request ID is required."

            }


        if not checker_id:

            return {

                "success":
                    False,

                "message":
                    "Checker ID is required."

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

                "success":
                    False,

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

    ) -> Dict[str, Any]:
        """
        Cancel a pending request through PostgreSQL RPC.
        """

        if request_id is None:

            return {

                "success":
                    False,

                "message":
                    "Request ID is required."

            }


        if not user_id:

            return {

                "success":
                    False,

                "message":
                    "User ID is required."

            }


        try:

            return cancel_setting_change(

                request_id,

                user_id

            )


        except Exception as e:

            return {

                "success":
                    False,

                "message":
                    str(e)

            }


# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "SettingsService"

]


# ==============================================================================
# END
# ==============================================================================
