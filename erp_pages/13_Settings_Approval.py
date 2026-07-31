# ==============================================================================
# erp_pages/13_Settings_Approval.py
# ERP ENTERPRISE SETTINGS APPROVAL CENTER v1.0
#
# Maker - Checker Approval Workflow
#
# Settings Change Approval
#
# ==============================================================================


import streamlit as st
import pandas as pd



from erp_core.services.settings_service import (
    SettingsService
)

from erp_core.loaders.settings_loader import (
    clear_settings_cache,
)

from utils.notification import (
    notify_success,
    notify_error,
)



# ==============================================================================
# SECURITY
# ==============================================================================


def require_admin():


    user = st.session_state.get("user")


    if not user:

        st.error(
            "⛔ Please login first"
        )

        st.stop()



    if user.get("role_id") != 1:

        st.error(
            "⛔ Admin Access Required"
        )

        st.stop()



    return user




# ==============================================================================
# LOAD REQUESTS
# ==============================================================================


def get_pending_requests():


    conn = get_connection()


    try:

        query = """

        SELECT

            id,
            setting_key,
            old_value,
            new_value,
            reason,
            status,
            requested_by,
            created_at

        FROM settings_change_requests

        WHERE status = 'PENDING'

        ORDER BY created_at DESC

        """


        return pd.read_sql(
            query,
            conn
        )


    finally:

        conn.close()




# ==============================================================================
# APPROVE RPC
# ==============================================================================


def approve_setting_change(

    request_id,

    checker_id

):


    conn = get_connection()


    try:


        cursor = conn.cursor()



        cursor.execute(

        """

        SELECT approve_setting_change_rpc(
            %s,
            %s
        )

        """,

        (

            request_id,

            checker_id

        )

        )



        result = cursor.fetchone()



        conn.commit()



        return result[0]



    except Exception as e:


        conn.rollback()

        raise e



    finally:

        conn.close()




# ==============================================================================
# PAGE
# ==============================================================================


def run():


    user = require_admin()


    st.title(
        "✅ Settings Approval Center"
    )


    st.caption(
        "Maker - Checker Configuration Approval Workflow"
    )


    st.divider()



    requests = get_pending_requests()



    if requests.empty:


        st.success(
            "✔ No Pending Setting Requests"
        )


        return



    st.subheader(
        "Pending Requests"
    )



    st.dataframe(

        requests,

        use_container_width=True

    )



    st.divider()



    for _, row in requests.iterrows():



        with st.container():


            st.markdown(
                f"""
### ⚙ {row['setting_key']}

Old Value:
`{row['old_value']}`

New Value:
`{row['new_value']}`

Reason:
{row['reason']}

Requested By:
`{row['requested_by']}`

"""
            )



            col1, col2 = st.columns(2)



            with col1:

    if st.button(

        "✅ Approve",

        key=f"approve_{row['id']}",

        use_container_width=True

    ):


        try:


            result = SettingsService.approve_request(

                row["id"],

                user["id"]

            )


            if result.get(

                "success",

                False

            ):


                # 🔥 IMPORTANT
                clear_settings_cache()


                notify_success(

                    "Setting Approved Successfully"

                )


                st.rerun()


            else:


                notify_error(

                    result.get(

                        "message",

                        "Approval Failed"

                    )

                )


        except Exception as e:


            notify_error(

                str(e)

            )
                            )


                            st.rerun()



                        else:


                            notify_error(

                                result.get(

                                    "message",

                                    "Approval Failed"

                                )

                            )



                    except Exception as e:


                        notify_error(

                            str(e)

                        )





            with col2:

    reject_reason = st.text_input(
        "Reject Reason",
        key=f"reason_{row['id']}"
    )

    if st.button(
        "❌ Reject",
        key=f"reject_{row['id']}",
        use_container_width=True
    ):

        result = SettingsService.reject_request(
            row["id"],
            user["id"],
            reject_reason
        )

        if result.get("success"):

            clear_settings_cache()

            notify_success(
                "Request Rejected"
            )

            st.rerun()

        else:

            notify_error(
                result.get("message")
            )





            st.divider()




# ==============================================================================
# ENTRY POINT
# ==============================================================================


if __name__ == "__main__":


    st.set_page_config(

        page_title="Settings Approval",

        page_icon="✅",

        layout="wide"

    )


    run()
