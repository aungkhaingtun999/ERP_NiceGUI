# ==============================================================================
# erp_pages/13_Settings_Approval.py
# ERP ENTERPRISE SETTINGS APPROVAL CENTER v2.0
#
# Maker - Checker Workflow
#
# Admin Only Checker
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
            "⛔ Please login first"
        )

        st.stop()



    if user.get(
        "role_id"
    ) != 1:


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
                status,
                requested_by,
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
            f"Load Pending Failed : {e}"
        )


        return pd.DataFrame()



# ==============================================================================
# PAGE
# ==============================================================================


def run():


    user = require_admin()


    st.title(
        "✅ Settings Approval Center"
    )


    st.caption(
        "Maker - Checker Workflow (Admin Only)"
    )


    st.divider()



    pending_df = get_pending_requests()



    if pending_df.empty:


        st.success(
            "✔ No Pending Setting Requests"
        )

        return



    st.warning(
        f"⏳ Pending Requests : {len(pending_df)}"
    )



    st.dataframe(

        pending_df[
            [
                "setting_key",
                "old_value",
                "new_value",
                "requested_by",
                "created_at"
            ]
        ],

        use_container_width=True,

        hide_index=True

    )



    st.divider()



    for _, row in pending_df.iterrows():


        request_id = row["id"]



        with st.container():


            st.subheader(

                f"⚙ {row['setting_key']}"

            )


            st.write(
                f"""
Current Value :
`{row['old_value']}`


New Value :
`{row['new_value']}`


Reason :
{row.get('reason','')}


Requested By :
`{row['requested_by']}`
"""
            )



            # ==============================================================
            # SELF APPROVAL BLOCK
            # ==============================================================


            if str(row["requested_by"]) == str(user["id"]):


                st.warning(
                    "⚠ You cannot approve your own request. Another Admin must approve."
                )



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

                                user["id"]

                            )



                            if result.get(
                                "success",
                                False
                            ):


                                clear_settings_cache()


                                notify_success(
                                    "✅ Setting Approved Successfully"
                                )


                                st.rerun()



                            else:


                                notify_error(

                                    result.get(
                                        "message",
                                        "Approve Failed"
                                    )

                                )



                        except Exception as e:


                            notify_error(
                                str(e)
                            )



            # ==============================================================
            # REJECT
            # ==============================================================


            reject_reason = st.text_input(

                "Reject Reason",

                key=f"reason_{request_id}"

            )



            if st.button(

                "❌ Reject",

                key=f"reject_{request_id}",

                use_container_width=True

            ):


                try:


                    result = SettingsService.reject_request(

                        request_id,

                        user["id"],

                        reject_reason

                    )



                    if result.get(
                        "success",
                        False
                    ):


                        clear_settings_cache()


                        notify_success(
                            "❌ Request Rejected"
                        )


                        st.rerun()



                    else:


                        notify_error(

                            result.get(
                                "message",
                                "Reject Failed"
                            )

                        )



                except Exception as e:


                    notify_error(
                        str(e)
                    )



            st.divider()



# ==============================================================================
# ENTRY
# ==============================================================================


if __name__ == "__main__":


    st.set_page_config(

        page_title="Settings Approval",

        page_icon="✅",

        layout="wide"

    )


    run()
