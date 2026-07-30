# ==============================================================================
# erp_ui/settings/finance_settings.py
# ERP FINANCE SETTINGS COMPONENT v2.0
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
# FINANCE SETTINGS UI
# ==============================================================================


def render_finance_settings(
    settings,
    user
):


    st.subheader(
        "💱 Finance Settings"
    )



    # --------------------------------------------------------------------------
    # CURRENCY
    # --------------------------------------------------------------------------

    currency_list = [

        "MMK",
        "USD",
        "THB",
        "SGD"

    ]


    current_currency = settings.get(
        "CURRENCY",
        "MMK"
    )


    if current_currency not in currency_list:

        current_currency = "MMK"



    currency = st.selectbox(

        "Base Currency",

        currency_list,

        index=currency_list.index(
            current_currency
        )

    )



    # --------------------------------------------------------------------------
    # PAYMENT METHODS
    # --------------------------------------------------------------------------

    payment_default = settings.get(

        "PAYMENT_METHODS",

        "Cash"

    )


    payment_methods = st.multiselect(

        "Payment Methods",

        [

            "Cash",

            "Bank Transfer",

            "Mobile Pay",

            "Credit"

        ],

        default=payment_default.split(",")

    )



    # --------------------------------------------------------------------------
    # SUBMIT REQUEST
    # --------------------------------------------------------------------------

    if st.button(

        "📤 Submit Finance Change Request",

        use_container_width=True

    ):


        try:


            SettingsService.request_change(

                "CURRENCY",

                currency,

                "Finance Currency Change",

                user["id"]

            )



            SettingsService.request_change(

                "PAYMENT_METHODS",

                ",".join(payment_methods),

                "Payment Methods Change",

                user["id"]

            )



            notify_success(

                "💱 Finance Change Request Submitted. Waiting Approval."

            )


            st.rerun()



        except Exception as e:


            notify_error(

                f"Finance Request Failed : {e}"

            )
