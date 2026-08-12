# ==============================================================================
# erp_core/repositories/settings_repository.py
# ERP SETTINGS REPOSITORY v5.0
#
# Supabase Repository Layer
#
# Responsibilities:
# - Create Settings Change Request
# - Load Pending Requests
# - Approve via RPC
# - Reject via RPC
# - Cancel via RPC
#
# IMPORTANT:
# - This repository NEVER directly updates the `settings` table for approval.
# - All approval-side changes MUST pass through PostgreSQL RPC.
# - Maker-Checker enforcement belongs to the database RPC.
# ==============================================================================


from erp_core.base_repo import db


# ==============================================================================
# CONSTANTS
# ==============================================================================

SETTINGS_REQUEST_TABLE = "settings_change_requests"

APPROVE_RPC = "approve_setting_change_rpc"
REJECT_RPC = "reject_setting_change_rpc"
CANCEL_RPC = "cancel_setting_change_rpc"


# ==============================================================================
# INTERNAL VALIDATION
# ==============================================================================


def _require_value(value, field_name):

    if value is None:

        raise ValueError(
            f"{field_name} is required."
        )

    if isinstance(value, str) and not value.strip():

        raise ValueError(
            f"{field_name} is required."
        )

    return value


# ==============================================================================
# INTERNAL RPC RESULT NORMALIZER
# ==============================================================================


def _normalize_rpc_result(data):

    """
    Normalize Supabase RPC responses.

    Expected PostgreSQL result:

        {
            "success": true,
            "message": "Approved"
        }

    Some Supabase responses may return:

        [
            {
                "success": true,
                ...
            }
        ]
    """

    if isinstance(data, dict):

        return data


    if isinstance(data, list):

        if data and isinstance(data[0], dict):

            return data[0]


    return {

        "success": False,

        "message":
            "Unknown RPC response."

    }


# ==============================================================================
# CREATE CHANGE REQUEST
# MAKER
# ==============================================================================


def create_setting_request(

    setting_key,

    old_value,

    new_value,

    reason,

    requested_by

):

    """
    Create a new settings Maker request.

    IMPORTANT:
    This function only creates a PENDING request.

    It does NOT update the settings table.
    """

    _require_value(
        setting_key,
        "Setting key"
    )

    _require_value(
        requested_by,
        "Requested by"
    )


    if reason is None:

        reason = ""


    result = (

        db()

        .table(
            SETTINGS_REQUEST_TABLE
        )

        .insert({

            "setting_key":
                str(setting_key).strip(),

            "old_value":
                "" if old_value is None
                else str(old_value),

            "new_value":
                "" if new_value is None
                else str(new_value),

            "reason":
                str(reason),

            "requested_by":
                requested_by,

            "status":
                "PENDING"

        })

        .execute()

    )


    if not result.data:

        raise Exception(
            "Cannot create setting change request."
        )


    return result.data[0]["id"]


# ==============================================================================
# GET PENDING REQUESTS
# ==============================================================================


def get_pending_setting_requests():

    result = (

        db()

        .table(
            SETTINGS_REQUEST_TABLE
        )

        .select("*")

        .eq(
            "status",
            "PENDING"
        )

        .order(
            "created_at",
            desc=True
        )

        .execute()

    )


    return result.data or []


# ==============================================================================
# GET REQUEST BY ID
# OPTIONAL REPOSITORY HELPER
# ==============================================================================


def get_setting_request(
    request_id
):

    _require_value(
        request_id,
        "Request ID"
    )


    result = (

        db()

        .table(
            SETTINGS_REQUEST_TABLE
        )

        .select("*")

        .eq(
            "id",
            request_id
        )

        .maybe_single()

        .execute()

    )


    return result.data


# ==============================================================================
# APPROVE
# CHECKER
# ==============================================================================


def approve_setting_change(

    request_id,

    checker_id

):

    _require_value(
        request_id,
        "Request ID"
    )

    _require_value(
        checker_id,
        "Checker ID"
    )


    result = (

        db()

        .rpc(

            APPROVE_RPC,

            {

                "p_request_id":
                    request_id,

                "p_checker_id":
                    checker_id

            }

        )

        .execute()

    )


    return _normalize_rpc_result(
        result.data
    )


# ==============================================================================
# REJECT
# CHECKER
# ==============================================================================


def reject_setting_change(

    request_id,

    checker_id,

    reason

):

    _require_value(
        request_id,
        "Request ID"
    )

    _require_value(
        checker_id,
        "Checker ID"
    )


    if reason is None:

        reason = ""


    result = (

        db()

        .rpc(

            REJECT_RPC,

            {

                "p_request_id":
                    request_id,

                "p_checker_id":
                    checker_id,

                "p_reason":
                    str(reason)

            }

        )

        .execute()

    )


    return _normalize_rpc_result(
        result.data
    )


# ==============================================================================
# CANCEL
# MAKER
# ==============================================================================


def cancel_setting_change(

    request_id,

    user_id

):

    _require_value(
        request_id,
        "Request ID"
    )

    _require_value(
        user_id,
        "User ID"
    )


    result = (

        db()

        .rpc(

            CANCEL_RPC,

            {

                "p_request_id":
                    request_id,

                "p_user_id":
                    user_id

            }

        )

        .execute()

    )


    return _normalize_rpc_result(
        result.data
    )


# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "create_setting_request",

    "get_pending_setting_requests",

    "get_setting_request",

    "approve_setting_change",

    "reject_setting_change",

    "cancel_setting_change",

]
