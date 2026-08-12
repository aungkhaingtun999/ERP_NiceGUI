# ==============================================================================
# erp_core/repositories/settings_repository.py
# ERP SETTINGS REPOSITORY v5.0
#
# Supabase Repository Layer
#
# Canonical Settings Table:
#     public.settings
#
# Approval Queue:
#     public.settings_change_requests
#
# Maker - Checker Workflow
#
# Responsibilities:
# - Create setting change request
# - Read pending requests
# - Read setting
# - Read all settings
# - Approve through RPC
# - Reject through RPC
# - Cancel through RPC
# - Normalize RPC responses
#
# IMPORTANT:
# - public.settings is the ONLY active settings source.
# - erp_settings is NOT used here.
# - Actual approval/update is performed by PostgreSQL RPC.
# ==============================================================================


from typing import Any, Dict, List, Optional


from erp_core.base_repo import db


# ==============================================================================
# CONSTANTS
# ==============================================================================

SETTINGS_TABLE = "settings"
CHANGE_REQUESTS_TABLE = "settings_change_requests"

STATUS_PENDING = "PENDING"


# ==============================================================================
# INTERNAL HELPERS
# ==============================================================================


def _client():
    """
    Return the active ERP database client.
    """
    return db()


def _normalize_rpc_result(data: Any) -> Dict[str, Any]:
    """
    Normalize Supabase RPC responses.

    PostgreSQL functions returning json/jsonb may arrive as:
        dict
        list[dict]
        None

    Always return a predictable dictionary.
    """

    if isinstance(data, dict):

        return data


    if isinstance(data, list):

        if data and isinstance(data[0], dict):

            return data[0]


    return {
        "success": False,
        "message": "Unknown RPC response"
    }


# ==============================================================================
# SETTINGS READ
# ==============================================================================


def get_all_settings() -> Dict[str, Any]:
    """
    Load all active settings from public.settings.

    Returns:
        {
            "SETTING_KEY": "value",
            ...
        }
    """

    result = (
        _client()
        .table(SETTINGS_TABLE)
        .select("key,value")
        .order("key")
        .execute()
    )


    settings = {}


    for row in result.data or []:

        key = row.get("key")

        if key is None:
            continue

        settings[str(key)] = row.get("value")


    return settings


# ==============================================================================
# GET SINGLE SETTING
# ==============================================================================


def get_setting(
    setting_key: str,
    default: Any = None
) -> Any:
    """
    Read one setting from public.settings.
    """

    if not setting_key:

        return default


    result = (
        _client()
        .table(SETTINGS_TABLE)
        .select("key,value")
        .eq("key", setting_key)
        .limit(1)
        .execute()
    )


    rows = result.data or []


    if not rows:

        return default


    return rows[0].get(
        "value",
        default
    )


# ==============================================================================
# CREATE CHANGE REQUEST
# MAKER
# ==============================================================================


def create_setting_request(
    setting_key: str,
    old_value: Any,
    new_value: Any,
    reason: str,
    requested_by: str
) -> int:
    """
    Create a Maker setting change request.

    IMPORTANT:
    This function DOES NOT modify public.settings.

    It only creates a PENDING request.

    Actual setting modification occurs only after
    approve_setting_change_rpc().
    """

    if not setting_key:

        raise ValueError(
            "Setting key is required."
        )


    if not requested_by:

        raise ValueError(
            "Requester ID is required."
        )


    # --------------------------------------------------------------------------
    # Duplicate pending protection
    #
    # Do this at repository level as an early protection.
    # The database/RPC layer should still enforce the final rule.
    # --------------------------------------------------------------------------

    pending = get_pending_setting_requests()


    for request in pending:

        if request.get("setting_key") == setting_key:

            raise ValueError(
                f"{setting_key} already has a pending approval request."
            )


    payload = {

        "setting_key":
            str(setting_key),

        "old_value":
            str(old_value),

        "new_value":
            str(new_value),

        "reason":
            str(reason or ""),

        "requested_by":
            requested_by,

        "status":
            STATUS_PENDING

    }


    result = (
        _client()
        .table(CHANGE_REQUESTS_TABLE)
        .insert(payload)
        .execute()
    )


    rows = result.data or []


    if not rows:

        raise RuntimeError(
            "Cannot create setting change request."
        )


    request_id = rows[0].get("id")


    if request_id is None:

        raise RuntimeError(
            "Setting change request created without request ID."
        )


    return int(request_id)


# ==============================================================================
# GET PENDING REQUESTS
# ==============================================================================


def get_pending_setting_requests() -> List[Dict[str, Any]]:
    """
    Return all PENDING setting change requests.

    Newest requests first.
    """

    result = (
        _client()
        .table(CHANGE_REQUESTS_TABLE)
        .select("*")
        .eq(
            "status",
            STATUS_PENDING
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
# ==============================================================================


def get_setting_change_request(
    request_id: int
) -> Optional[Dict[str, Any]]:
    """
    Load one setting change request.
    """

    if request_id is None:

        return None


    result = (
        _client()
        .table(CHANGE_REQUESTS_TABLE)
        .select("*")
        .eq("id", request_id)
        .limit(1)
        .execute()
    )


    rows = result.data or []


    if not rows:

        return None


    return rows[0]


# ==============================================================================
# APPROVE
# CHECKER
# ==============================================================================


def approve_setting_change(
    request_id: int,
    checker_id: str
) -> Dict[str, Any]:
    """
    Approve a setting change.

    IMPORTANT:
    Python does NOT directly update public.settings.

    PostgreSQL RPC performs the atomic approval:

        PENDING
           ↓
        validation
           ↓
        settings update
           ↓
        APPROVED

    RPC:
        approve_setting_change_rpc
    """

    if request_id is None:

        return {
            "success": False,
            "message": "Request ID is required."
        }


    if not checker_id:

        return {
            "success": False,
            "message": "Checker ID is required."
        }


    result = (
        _client()
        .rpc(
            "approve_setting_change_rpc",
            {
                "p_request_id":
                    int(request_id),

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
    request_id: int,
    checker_id: str,
    reason: str
) -> Dict[str, Any]:
    """
    Reject a pending setting change.
    """

    if request_id is None:

        return {
            "success": False,
            "message": "Request ID is required."
        }


    if not checker_id:

        return {
            "success": False,
            "message": "Checker ID is required."
        }


    result = (
        _client()
        .rpc(
            "reject_setting_change_rpc",
            {
                "p_request_id":
                    int(request_id),

                "p_checker_id":
                    checker_id,

                "p_reason":
                    str(reason or "")
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
    request_id: int,
    user_id: str
) -> Dict[str, Any]:
    """
    Cancel a pending setting change.

    Only the original Maker should be allowed to cancel.
    PostgreSQL RPC performs the final authorization check.
    """

    if request_id is None:

        return {
            "success": False,
            "message": "Request ID is required."
        }


    if not user_id:

        return {
            "success": False,
            "message": "User ID is required."
        }


    result = (
        _client()
        .rpc(
            "cancel_setting_change_rpc",
            {
                "p_request_id":
                    int(request_id),

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

    "get_all_settings",

    "get_setting",

    "create_setting_request",

    "get_pending_setting_requests",

    "get_setting_change_request",

    "approve_setting_change",

    "reject_setting_change",

    "cancel_setting_change",

]
        
