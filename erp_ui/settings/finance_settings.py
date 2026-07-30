# ==============================================================================
# erp_ui/settings/finance_settings.py
# ERP FINANCE SETTINGS COMPONENT
# ==============================================================================


import streamlit as st


from erp_core.loaders.settings_loader import (
    clear_settings_cache,
    save_setting as save_erp_setting,
)


from utils.notification import (
    notify_success,
    notify_error,
)



# ==============================================================================
# SAVE WRAPPER
# ==============================================================================


def save_setting(key, value):

    result = save_erp_setting(
        key,
        value
    )


    if not result.get(
        "success",
        False
    ):

        raise Exception(

            result.get(

                "message",

                "Save failed"

            )

        )



# ==============================================================================
# FINANCE SETTINGS UI
# ==============================================================================


def render_finance_settings(settings,
    user):


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

        "CURRENCY"

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

        "PAYMENT_METHODS"

    )


    if not payment_default:

        payment_default = "Cash"



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
    # SAVE
    # --------------------------------------------------------------------------


    if st.button(

        "💾 Save Finance Settings",

        use_container_width=True

    ):


        try:


            save_setting(

                "CURRENCY",

                currency

            )


            save_setting(

                "PAYMENT_METHODS",

                ",".join(

                    payment_methods

                )

            )



            clear_settings_cache()



            notify_success(

                "💱 Finance Settings Saved"

            )



            st.rerun()



        except Exception as e:


            notify_error(

                f"Finance Save Failed : {e}"

            )
