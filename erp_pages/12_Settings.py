# ==============================================================================
# erp_pages/12_Settings.py
# ERP ENTERPRISE CONTROL CENTER v5.0 FINAL
#
# Settings Management UI
#
# Connected:
#
# settings_loader
# SettingsService
# Pricing Engine
#
# NO DEFAULT TAX
# NO GLOBAL MARKUP
#
# ==============================================================================


import streamlit as st



from erp_core.loaders.settings_loader import (

    get_all_settings_cached,

    get_bool,

    save_setting,

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

            "⛔ Admin Access Only"

        )

        st.stop()



    return user







# ==============================================================================
# SAVE WRAPPER
# ==============================================================================


def save_value(

    key,

    value

):


    result = save_setting(

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
# MAIN
# ==============================================================================


def run():


    user = require_admin()


    settings = get_all_settings_cached()





    # ==========================================================================
    # HEADER
    # ==========================================================================


    st.title(

        "⚙ ERP Control Center"

    )


    st.success(

        f"🔐 Welcome Admin : {user.get('full_name','Admin')}"

    )


    st.caption(

        "Enterprise Configuration Center"

    )


    st.divider()





    # ==========================================================================
    # PRICING ENGINE
    # ==========================================================================


    st.subheader(

        "💰 Pricing Engine"

    )


    st.info(

"""
Pricing Rule Priority


Product Markup

        ↓

Category Markup

        ↓

Current Selling Price


System uses the first available pricing rule.
"""

    )



    st.divider()



    # --------------------------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------------------------


    priority_list = [

        "PRODUCT_FIRST",

        "CATEGORY_FIRST",

        "CURRENT_PRICE"

    ]



    priority_name = {


        "PRODUCT_FIRST":

            "Product → Category → Current Price",


        "CATEGORY_FIRST":

            "Category → Product → Current Price",


        "CURRENT_PRICE":

            "Use Current Price"

    }



    current_priority = settings.get(

        "PRICING_PRIORITY",

        "PRODUCT_FIRST"

    )



    pricing_priority = st.selectbox(

        "⚙ Pricing Priority",

        priority_list,

        index=(

            priority_list.index(

                current_priority

            )

            if current_priority in priority_list

            else 0

        ),

        format_func=lambda x:

            priority_name.get(

                x,

                x

            )

    )







    # --------------------------------------------------------------------------
    # MARKUP CONTROL
    # --------------------------------------------------------------------------


    col1,col2 = st.columns(2)



    with col1:


        enable_product = st.toggle(

            "☑ Enable Product Markup",

            value=get_bool(

                settings,

                "ENABLE_PRODUCT_MARKUP",

                True

            )

        )




    with col2:


        enable_category = st.toggle(

            "☑ Enable Category Markup",

            value=get_bool(

                settings,

                "ENABLE_CATEGORY_MARKUP",

                True

            )

        )







    # --------------------------------------------------------------------------
    # PRICE METHOD
    # --------------------------------------------------------------------------


    pricing_method = st.selectbox(

        "📊 Price Calculation Method",

        [

            "MARKUP",

            "MARGIN"

        ],

        index=(

            0

            if settings.get(

                "PRICING_METHOD",

                "MARKUP"

            )

            == "MARKUP"

            else 1

        )

    )







    col3,col4 = st.columns(2)



    with col3:


        auto_update = st.toggle(

            "🔄 Auto Update Selling Price",

            value=get_bool(

                settings,

                "AUTO_UPDATE_SELLING_PRICE",

                True

            )

        )





    with col4:


        manual_override = st.toggle(

            "✏ Allow Manual Price Override",

            value=get_bool(

                settings,

                "ALLOW_MANUAL_PRICE_OVERRIDE",

                True

            )

        )








    if st.button(

        "💾 Save Pricing Settings",

        use_container_width=True

    ):


        try:


            save_value(

                "PRICING_PRIORITY",

                pricing_priority

            )


            save_value(

                "ENABLE_PRODUCT_MARKUP",

                enable_product

            )


            save_value(

                "ENABLE_CATEGORY_MARKUP",

                enable_category

            )


            save_value(

                "PRICING_METHOD",

                pricing_method

            )


            save_value(

                "AUTO_UPDATE_SELLING_PRICE",

                auto_update

            )


            save_value(

                "ALLOW_MANUAL_PRICE_OVERRIDE",

                manual_override

            )



            clear_settings_cache()



            notify_success(

                "💰 Pricing settings saved"

            )


            st.rerun()



        except Exception as e:


            notify_error(

                str(e)

            )

