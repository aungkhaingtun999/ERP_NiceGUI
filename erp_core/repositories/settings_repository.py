# ==============================================================================
# erp_core/repositories/settings_repository.py
# ERP SETTINGS REPOSITORY v4.0
#
# Supabase Repository Layer
#
# Maker - Checker Workflow
# ==============================================================================


from erp_core.base_repo import db



# ==============================================================================
# CREATE CHANGE REQUEST
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

            "requested_by": requested_by,

            "status": "PENDING"

        })

        .execute()

    )



    if not result.data:


        raise Exception(
            "Cannot create setting request"
        )



    return result.data[0]["id"]




# ==============================================================================
# GET PENDING REQUESTS
# ==============================================================================


def get_pending_setting_requests():


    result = (

        db()

        .table(
            "settings_change_requests"
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
# APPROVE
# CHECKER
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


    result = (

        db()

        .rpc(

            "reject_setting_change_rpc",

            {

                "p_request_id":
                request_id,


                "p_checker_id":
                checker_id,


                "p_reason":
                reason

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


    result = (

        db()

        .rpc(

            "cancel_setting_change_rpc",

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
# RPC RESULT FORMAT
# ==============================================================================


def _normalize_rpc_result(data):


    if isinstance(data, dict):

        return data



    if isinstance(data, list) and data:


        if isinstance(data[0], dict):

            return data[0]



    return {

        "success": False,

        "message":
        "Unknown RPC response"

    }
