# ==============================================================================
# erp_ui/settings/accounting_settings.py
# ERP ACCOUNTING & TAX SETTINGS COMPONENT
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
# ACCOUNTING & TAX UI
# ==============================================================================


def render_accounting_settings(settings,
    user):


    st.subheader(
        "🧾 Accounting & Tax"
    )


    # --------------------------------------------------------------------------
    # TAX RATE
    # --------------------------------------------------------------------------


    tax_value = settings.get(

        "DEFAULT_TAX_RATE"

    )


    if tax_value is None:

        tax_value = 0



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
Controlled by ERP Settings Database
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

        "DISCOUNT_POLICY"

    )


    if discount_policy is None:

        discount_policy = "allowed"



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
    # SAVE
    # --------------------------------------------------------------------------


    if st.button(

        "💾 Save Accounting Settings",

        use_container_width=True

    ):


        try:


            save_setting(

                "DEFAULT_TAX_RATE",

                tax_rate

            )


            save_setting(

                "DISCOUNT_POLICY",

                discount_policy

            )



            clear_settings_cache()



            notify_success(

                f"🧾 Tax Settings Saved : {tax_rate:.2f}%"

            )



            st.rerun()



        except Exception as e:


            notify_error(

                f"Tax Save Failed : {e}"

            )
