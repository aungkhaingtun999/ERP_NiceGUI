# ==============================================================================
# erp_pages/13_Settings_Approval.py
# ERP ENTERPRISE SETTINGS APPROVAL CENTER v4.0
#
# Maker - Checker Workflow
#
# Admin Only
#
# ==============================================================================


import streamlit as st
import pandas as pd


from erp_core.base_repo import db


from erp_core.services.settings_service import (
    SettingsService
)


from erp_core.loaders.settings_loader import (
    clear_settings_cache
)


from utils.notification import (
    notify_success,
    notify_error
)



# ==============================================================================
# SECURITY
# ==============================================================================


def require_admin():


    user = st.session_state.get(
        "user"
    )


    if not user:

        st.error(
            "⛔ Login Required"
        )

        st.stop()



    if int(user.get("role_id",0)) != 1:

        st.error(
            "⛔ Admin Access Required"
        )

        st.stop()



    return user




# ==============================================================================
# LOAD PENDING
# ==============================================================================


def get_pending_requests():


    try:


        result = (

            db()

            .table(
                "settings_change_requests"
            )

            .select(
                """
                id,
                setting_key,
                old_value,
                new_value,
                reason,
                requested_by,
                created_at,
                status
                """
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


        return pd.DataFrame(
            result.data or []
        )



    except Exception as e:


        st.error(
            f"Pending Load Error : {e}"
        )


        return pd.DataFrame()




# ==============================================================================
# RESULT CHECK
# ==============================================================================


def rpc_success(result):


    if isinstance(result,dict):

        return result.get(
            "success",
            False
        )


    return False




# ==============================================================================
# PAGE
# ==============================================================================


def run():


    user = require_admin()


    current_user_id = str(
        user["id"]
    )



    st.title(
        "✅ Settings Approval Center"
    )


    st.caption(
        "Maker - Checker Workflow | Admin Only"
    )


    st.divider()



    pending_df = get_pending_requests()



    if pending_df.empty:


        st.success(
            "✔ No Pending Requests"
        )

        return




    st.warning(

        f"⏳ Pending Changes : {len(pending_df)}"

    )



    st.divider()



    for _, row in pending_df.iterrows():



        request_id = row["id"]


        maker_id = str(
            row["requested_by"]
        )



        with st.container():



            st.subheader(

                f"⚙ {row['setting_key']}"

            )



           
