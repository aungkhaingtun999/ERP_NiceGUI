# ==============================================================================
# erp_core/repositories/settings_repository.py
# ERP SETTINGS REPOSITORY
# Supabase Version
#
# Maker - Checker Workflow
# ==============================================================================


from erp_core.base_repo import db



# ==============================================================================
# CREATE REQUEST
# ==============================================================================


def create_setting_request(
    setting_key,
    old_value,
    new_value,
    reason,
    requested_by
):


    result = (

        db()

        .table(
            "settings_change_requests"
        )

        .insert({

            "setting_key": setting_key,

            "old_value": str(old_value),

            "new_value": str(new_value),

            "reason": reason,

            "requested_by": requested_by

        })

        .execute()

    )


    return result.data[0]["id"]




# ==============================================================================
# PENDING REQUESTS
# ==============================================================================


def get_pending_setting_requests():


    result = (

        db()

        .table(
            "settings_change_requests"
        )

        .select(
            "*"
        )

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
# APPROVE
# ==============================================================================


def approve_setting_change(
    request_id,
    checker_id
):


    result = (

        db()

        .rpc(

            "approve_setting_change_rpc",

            {

                "p_request_id": request_id,

                "p_checker_id": checker_id

            }

        )

        .execute()

    )


    return result.data[0] if result.data else {
        "success": False,
        "message": "No response"
    }




# ==============================================================================
# REJECT
# ==============================================================================


def reject_setting_change(
    request_id,
    checker_id,
    reason
):


    result = (

        db()

        .rpc(

            "reject_setting_change_rpc",

            {

                "p_request_id": request_id,

                "p_checker_id": checker_id,

                "p_reason": reason

            }

        )

        .execute()

    )


    return result.data[0] if result.data else {
        "success": False,
        "message": "No response"
    }




# ==============================================================================
# CANCEL
# ==============================================================================


def cancel_setting_change(
    request_id,
    user_id
):


    result = (

        db()

        .rpc(

            "cancel_setting_change_rpc",

            {

                "p_request_id": request_id,

                "p_user_id": user_id

            }

        )

        .execute()

    )


    return result.data[0] if result.data else {
        "success": False,
        "message": "No response"
    }
