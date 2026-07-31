# ==============================================================================
# erp_ui/settings/accounting_settings.py
# ERP ACCOUNTING & TAX SETTINGS COMPONENT v2.0
#
# Approval Workflow Enabled
#
# Request -> Approval -> Apply
#
# ==============================================================================


import streamlit as st


from erp_core.services.settings_service import (
    SettingsService,
)


from utils.notification import (
    notify_success,
    notify_error,
)



# ==============================================================================
# ACCOUNTING SETTINGS UI
# ==============================================================================


def render_accounting_settings(
    settings,
    user
):


    st.subheader(
        "🧾 Accounting & Tax"
    )


    # --------------------------------------------------------------------------
    # TAX RATE
    # --------------------------------------------------------------------------

    tax_value = settings.get(
        "DEFAULT_TAX_RATE",
        0
    )


    try:

        active_tax_rate = float(
            tax_value
        )

    except Exception:

        active_tax_rate = 0



    st.caption(
    f"Current Tax Rate : {active_tax_rate:.2f}%"
)


    tax_rate = st.number_input(

        "Change Tax Rate (%)",

        min_value=0.0,

        max_value=100.0,

        value=active_tax_rate,

        step=0.1

    )



    # --------------------------------------------------------------------------
    # DISCOUNT POLICY
    # --------------------------------------------------------------------------

    discount_policy = settings.get(
        "DISCOUNT_POLICY",
        "allowed"
    )



    discount_policy = st.selectbox(

        "Discount Policy",

        [
            "allowed",
            "restricted"
        ],

        index=(
            0
            if discount_policy == "allowed"
            else 1
        )

    )



    # --------------------------------------------------------------------------
    # REQUEST CHANGE
    # --------------------------------------------------------------------------

    if st.button(

        "📤 Submit Accounting Change Request",

        use_container_width=True

    ):


        try:


            SettingsService.request_change(

                "DEFAULT_TAX_RATE",

                str(tax_rate),

                "Accounting Tax Rate Change",

                user["id"]

            )


            SettingsService.request_change(

                "DISCOUNT_POLICY",

                discount_policy,

                "Discount Policy Change",

                user["id"]

            )



            notify_success(

                "🧾 Accounting Change Request Submitted. Waiting Approval."

            )


            st.rerun()



        except Exception as e:


            notify_error(

                f"Accounting Request Failed : {e}"

            )
