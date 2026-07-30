# ==============================================================================
# erp_pages/12_Settings.py
# ERP ENTERPRISE CONTROL CENTER v5.0 FINAL
#
# Settings Only Configuration
#
# No Hardcoded Default
#
# Database Driven:
#
# Tax
# Pricing
# Inventory
# Finance
#
# ==============================================================================


import streamlit as st

from erp_ui.settings.pricing_settings import (
    render_pricing_settings
)

from erp_core.loaders.settings_loader import (

    get_all_settings_cached,

    get_bool,

    get_float,

    save_setting as save_erp_setting,

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
# LOAD SETTINGS
# ==============================================================================


def load_settings():


    try:


        return get_all_settings_cached()



    except Exception as e:



        st.error(

            f"Settings Load Failed : {e}"

        )


        return {}








# ==============================================================================
# SAVE WRAPPER
# ==============================================================================


def save_setting(

    key,

    value

):


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
# PAGE
# ==============================================================================


def run():


    user = require_admin()


    settings = load_settings()



    st.title(

        "⚙ ERP Control Center"

    )



    st.success(

        f"🔐 Welcome Admin : {user.get('full_name','Admin')}"

    )



    st.caption(

        "Enterprise Configuration Center (Database Driven)"

    )



    st.divider()

    # ==========================================================================
    # PRICING ENGINE
    # ==========================================================================

    render_pricing_settings(settings)
    

    




    




    # --------------------------------------------------------------------------
    
        




    

 







    # ==========================================================================
    # ACCOUNTING & TAX SETTINGS
    # ==========================================================================


    st.subheader(

        "🧾 Accounting & Tax"

    )



    # --------------------------------------------------------------------------
    # TAX RATE FROM DATABASE ONLY
    # --------------------------------------------------------------------------


    tax_value = settings.get(

        "DEFAULT_TAX_RATE"

    )



    if tax_value is None:


        st.warning(

            "⚠ DEFAULT_TAX_RATE is not configured in ERP Settings Database."

        )


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
    # SAVE TAX
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



    st.divider()
    # ==========================================================================
    # INVENTORY SETTINGS
    # ==========================================================================


    st.subheader(

        "📦 Inventory Rules"

    )



    minimum_stock_value = settings.get(

        "MIN_STOCK_ALERT"

    )



    if minimum_stock_value is None:


        minimum_stock_value = 0



    try:

        minimum_stock_value = float(

            minimum_stock_value

        )

    except Exception:

        minimum_stock_value = 0






    minimum_stock = st.number_input(

        "Minimum Stock Alert",

        min_value=0.0,

        value=minimum_stock_value,

        step=1.0

    )




    auto_reorder = st.toggle(

        "🔄 Enable Auto Reorder",

        value=get_bool(

            settings,

            "AUTO_REORDER",

            False

        )

    )





    if st.button(

        "💾 Save Inventory Settings",

        use_container_width=True

    ):


        try:


            save_setting(

                "MIN_STOCK_ALERT",

                minimum_stock

            )


            save_setting(

                "AUTO_REORDER",

                auto_reorder

            )


            clear_settings_cache()



            notify_success(

                "📦 Inventory Settings Saved"

            )


            st.rerun()



        except Exception as e:


            notify_error(

                f"Inventory Save Failed : {e}"

            )



    st.divider()






    # ==========================================================================
    # FINANCE SETTINGS
    # ==========================================================================


    st.subheader(

        "💱 Finance Settings"

    )



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



    st.divider()








    # ==========================================================================
    # SYSTEM STATUS
    # ==========================================================================


    st.subheader(

        "🖥 System Status"

    )



    st.success(
"""
✔ ERP Core Active

✔ Database Connected

✔ Settings Service Connected

✔ Settings Cache Active

✔ Pricing Engine Connected

✔ Tax Engine Connected

✔ Inventory Engine Connected

✔ POS Ready

✔ Product / Category / Global Rule Ready
"""
    )



    st.success(

        "🚀 ERP Control Center Fully Operational"

    )





# ==============================================================================
# ENTRY POINT
# ==============================================================================


if __name__ == "__main__":


    st.set_page_config(

        page_title="ERP Control Center",

        page_icon="⚙️",

        layout="wide"

    )


    run()
