# ==============================================================================
# erp_pages/13_Settings_Approval.py
# ERP ENTERPRISE SETTINGS APPROVAL CENTER v1.0 CLEAN
#
# Maker - Checker Workflow
# Approve / Reject / Cancel
#
# Compatible:
# app.py dynamic router
# sidebar.py navigation
# SettingsService
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


    role_id = int(
        user.get(
            "role_id",
            0
        )
    )


    if role_id != 1:

        st.error(
            "⛔ Admin Access Required"
        )

        st.stop()


    return user



# ==============================================================================
# LOAD REQUESTS
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
                status,
                created_at
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
            f"Load Request Error : {e}"
        )

        return pd.DataFrame()



# ==============================================================================
# RESULT HELPER
# ==============================================================================

def get_result_value(result, key):

    if isinstance(result, dict):

        return result.get(
            key
        )


    if isinstance(result, list) and result:

        if isinstance(result[0], dict):

            return result[0].get(
                key
            )


    return None



# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run():


    user = require_admin()



    current_user_id = str(
        user.get(
            "id"
        )
        or
        user.get(
            "user_id"
        )
    )



    st.title(
        "✅ Settings Approval Center"
    )


    st.caption(
        "Maker - Checker Workflow | Admin Only"
    )



    # DEBUG

    with st.expander(
        "🔍 Session Debug"
    ):

        st.json(
            user
        )

        st.write(
            "Current User ID:",
            current_user_id
        )



    st.divider()



    requests = get_pending_requests()



    if requests.empty:

        st.success(
            "✔ No Pending Setting Requests"
        )

        return



    st.warning(
        f"⏳ Pending Changes : {len(requests)}"
    )



    st.divider()



    for _, row in requests.iterrows():


        request_id = row["id"]


        maker_id = str(
            row["requested_by"]
        )



        with st.container():



            st.subheader(
                f"⚙ {row['setting_key']}"
            )


            st.write(
                "Current Value:",
                row["old_value"]
            )


            st.write(
                "Pending Value:",
                row["new_value"]
            )


            st.write(
                "Reason:",
                row["reason"]
            )


            st.write(
                "Requested By:",
                maker_id
            )


            st.write(
                "Created:",
                row["created_at"]
            )



            st.divider()



            # ==============================================================
            # MAKER CANNOT APPROVE OWN REQUEST
            # ==============================================================

            if maker_id == current_user_id:


                st.warning(
                    "⚠ This is your request. Waiting for another Admin."
                )


                if st.button(
                    "🗑 Cancel Request",
                    key=f"cancel_{request_id}"
                ):


                    try:

                        result = SettingsService.cancel_request(
                            request_id,
                            current_user_id
                        )


                        if get_result_value(
                            result,
                            "success"
                        ):


                            clear_settings_cache()


                            notify_success(
                                "Request Cancelled"
                            )


                            st.rerun()


                        else:

                            notify_error(
                                str(result)
                            )


                    except Exception as e:

                        notify_error(
                            str(e)
                        )



            # ==============================================================
            # CHECKER
            # ==============================================================

            else:


                col1, col2 = st.columns(2)



                with col1:


                    if st.button(
                        "✅ Approve",
                        key=f"approve_{request_id}",
                        use_container_width=True
                    ):


                        try:


                            result = SettingsService.approve_request(
                                request_id,
                                current_user_id
                            )


                            if get_result_value(
                                result,
                                "success"
                            ):


                                clear_settings_cache()


                                notify_success(
                                    "Setting Approved"
                                )


                                st.rerun()


                            else:

                                notify_error(
                                    str(result)
                                )



                        except Exception as e:

                            notify_error(
                                str(e)
                            )



                with col2:


                    reason = st.text_input(
                        "Reject Reason",
                        key=f"reason_{request_id}"
                    )


                    if st.button(
                        "❌ Reject",
                        key=f"reject_{request_id}",
                        use_container_width=True
                    ):


                        if not reason:

                            notify_error(
                                "Reject reason required"
                            )

                            st.stop()



                        try:


                            result = SettingsService.reject_request(
                                request_id,
                                current_user_id,
                                reason
                            )



                            if get_result_value(
                                result,
                                "success"
                            ):


                                clear_settings_cache()


                                notify_success(
                                    "Request Rejected"
                                )


                                st.rerun()


                            else:

                                notify_error(
                                    str(result)
                                )



                        except Exception as e:

                            notify_error(
                                str(e)
                            )


            st.divider()
