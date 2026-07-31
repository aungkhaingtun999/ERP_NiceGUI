# ==============================================================================
# erp_pages/13_Settings_Approval.py
# ERP ENTERPRISE SETTINGS APPROVAL CENTER v5.0
#
# Maker - Checker Workflow
# Admin Only
#
# Approve / Reject / Cancel
# Cache Refresh
# Debug Ready
#
# ==============================================================================
import streamlit as st

st.set_page_config(8
    page_title="Settings Approval",
    page_icon="✅",
    layout="wide"
)

st.write("PAGE LOADED")



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



    if int(user.get("role_id", 0)) != 1:

        st.error(
            "⛔ Admin Access Required"
        )

        st.stop()



    return user





# ==============================================================================
# LOAD PENDING REQUESTS
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
            f"Pending Load Error : {e}"
        )


        return pd.DataFrame()





# ==============================================================================
# RPC RESULT CHECK
# ==============================================================================


def rpc_success(result):


    if isinstance(result, dict):

        return result.get(
            "success",
            False
        )


    if isinstance(result, list) and result:


        if isinstance(result[0], dict):

            return result[0].get(
                "success",
                False
            )


    return False




def rpc_message(result):


    if isinstance(result, dict):

        return result.get(
            "message",
            ""
        )


    if isinstance(result, list) and result:


        if isinstance(result[0], dict):

            return result[0].get(
                "message",
                ""
            )


    return str(result)




# ==============================================================================
# PAGE
# ==============================================================================

def run():

    user = st.session_state.get("user")


    # ================= DEBUG =================

    st.write("===== SESSION DEBUG =====")

    st.json(user)

    st.write("=========================")


    user = require_admin()


    current_user_id = user.get("id")


    if not current_user_id:

        current_user_id = user.get("user_id")


    current_user_id = str(current_user_id)


    st.info(
        f"👤 Login User: {user.get('username')} | ID: {current_user_id}"
    )

    # ================= DEBUG =================

    with st.expander(
        "🔍 Debug Session User"
    ):

        st.write(user)

        st.write(
            "Current ID:",
            current_user_id
        )

        st.write(
            "Role:",
            user.get("role_id")
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
            "✔ No Pending Setting Requests"
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



            st.markdown(
f"""
**Current Value**

`{row['old_value']}`


**Pending Value**

`{row['new_value']}`


**Reason**

{row.get('reason','')}


**Requested By**

`{maker_id}`


**Created**

{row['created_at']}
"""
            )



            # ==============================================================
            # MAKER
            # ==============================================================


            if str(maker_id).strip() == str(current_user_id).strip():


                st.warning(
                    "⚠ Your request. Waiting for another Admin approval."
                )


                if st.button(

                    "🗑 Cancel Request",

                    key=f"cancel_{request_id}",

                    use_container_width=True

                ):


                    try:


                        result = SettingsService.cancel_request(

                            request_id,

                            current_user_id

                        )


                        if rpc_success(result):


                            clear_settings_cache()


                            notify_success(
                                "Request Cancelled"
                            )


                            st.rerun()


                        else:


                            notify_error(
                                rpc_message(result)
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


                            if rpc_success(result):


                                clear_settings_cache()


                                notify_success(
                                    "Setting Approved"
                                )


                                st.rerun()



                            else:


                                notify_error(
                                    rpc_message(result)
                                )



                        except Exception as e:


                            notify_error(
                                str(e)
                            )



                with col2:


                    reject_reason = st.text_input(

                        "Reject Reason",

                        key=f"reject_reason_{request_id}"

                    )



                    if st.button(

                        "❌ Reject",

                        key=f"reject_{request_id}",

                        use_container_width=True

                    ):


                        if not reject_reason:


                            notify_error(
                                "Please enter reject reason"
                            )

                            st.stop()



                        try:


                            result = SettingsService.reject_request(

                                request_id,

                                current_user_id,

                                reject_reason

                            )


                            if rpc_success(result):


                                clear_settings_cache()


                                notify_success(
                                    "Request Rejected"
                                )


                                st.rerun()



                            else:


                                notify_error(
                                    rpc_message(result)
                                )


                        except Exception as e:


                            notify_error(
                                str(e)
                            )



            st.divider()




# ==============================================================================
# STREAMLIT PAGE ENTRY
# ==============================================================================


st.set_page_config(

    page_title="Settings Approval",

    page_icon="✅",

    layout="wide"

)


run()
