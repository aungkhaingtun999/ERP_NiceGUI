# ==============================================================================
# ERP SETTINGS REPOSITORY
# Supabase Version
# ==============================================================================


from erp_core.base_repo import get_connection
from erp_core.base_repo import db


def reject_setting_change(
    request_id,
    checker_id,
    reason
):

    result = db().rpc(
        "reject_setting_change_rpc",
        {
            "p_request_id": request_id,
            "p_checker_id": checker_id,
            "p_reason": reason
        }
    ).execute()

    return result.data


def cancel_setting_change(
    request_id,
    user_id
):

    result = db().rpc(
        "cancel_setting_change_rpc",
        {
            "p_request_id": request_id,
            "p_user_id": user_id
        }
    ).execute()

    return result.data


# --------------------------------------------------------------------------
# CREATE REQUEST
# --------------------------------------------------------------------------

def create_setting_request(
    setting_key,
    old_value,
    new_value,
    reason,
    requested_by
):

    db = get_connection()


    result = db.table(
        "settings_change_requests"
    ).insert({
        "setting_key": setting_key,
        "old_value": str(old_value),
        "new_value": str(new_value),
        "reason": reason,
        "requested_by": requested_by,
    }).execute()


    return result.data[0]["id"]




# --------------------------------------------------------------------------
# PENDING LIST
# --------------------------------------------------------------------------

def get_pending_setting_requests():

    db = get_connection()


    result = db.table(
        "settings_change_requests"
    ).select(
        "*"
    ).eq(
        "status",
        "PENDING"
    ).order(
        "created_at",
        desc=True
    ).execute()


    return result.data




# --------------------------------------------------------------------------
# APPROVE REQUEST
# --------------------------------------------------------------------------

def approve_setting_change(
    request_id,
    checker_id
):

    db = get_connection()


    result = db.rpc(
        "approve_setting_change_rpc",
        {
            "p_request_id": request_id,
            "p_checker_id": checker_id,
        }
    ).execute()


    return result.data
