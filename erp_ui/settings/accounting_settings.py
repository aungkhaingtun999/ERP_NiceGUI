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



    st.markdown(
f"""
<div style="
padding:18px;
border-radius:12px;
border:1px solid #999;
">

<div>
📌 Current Tax Rate
</div>

<h2>
{active_tax_rate:.2f} %
</h2>

<div>
Approval Controlled Setting
</div>

</div>
""",
unsafe_allow_html=True
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
