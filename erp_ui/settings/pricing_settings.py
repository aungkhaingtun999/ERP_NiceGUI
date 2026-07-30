# ==============================================================================
# erp_ui/settings/pricing_settings.py
# ERP PRICING SETTINGS COMPONENT
# ==============================================================================


import streamlit as st


from erp_core.loaders.settings_loader import (
    get_bool,
)


from erp_core.services.settings_service import (
    SettingsService,
)


from utils.notification import (
    notify_success,
    notify_error,
)

priority_labels = {

    "OWNER_FIRST":
        "Owner Price → Product → Category → Global",

    "PRODUCT_FIRST":
        "Product → Category → Global",

    "CATEGORY_FIRST":
        "Category → Product → Global",

    "GLOBAL_FIRST":
        "Global Only"

}


# ==============================================================================
# PRICING UI
# ==============================================================================


def render_pricing_settings(settings, user):

    st.subheader(
        "💰 Pricing Engine"
    )


    st.info(
"""
Pricing Priority

① Product Markup

        ↓

② Category Markup

        ↓

③ Global Markup


All values are controlled by ERP Settings Database.
"""
    )


    st.divider()



    # --------------------------------------------------------------------------
    # GLOBAL MARKUP
    # --------------------------------------------------------------------------


    global_markup_value = settings.get(
        "DEFAULT_MARKUP_PERCENT",
        0
    )


    try:

        global_markup_value = float(
            global_markup_value
        )

    except Exception:

        global_markup_value = 0



    default_markup = st.number_input(

        "🌍 Global Markup (%)",

        min_value=0.0,

        max_value=500.0,

        value=global_markup_value,

        step=1.0

    )



    # --------------------------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------------------------


    priority_options = [

        "OWNER_FIRST",

        "PRODUCT_FIRST",

        "CATEGORY_FIRST",

        "GLOBAL_FIRST"

]

priority_labels = {

    "OWNER_FIRST":
        "Owner Price → Product → Category → Global",

    "PRODUCT_FIRST":
        "Product → Category → Global",

    "CATEGORY_FIRST":
        "Category → Product → Global",

    "GLOBAL_FIRST":
        "Global Only"

}



    current_priority = settings.get(

        "PRICING_PRIORITY",

        "PRODUCT_FIRST"

    )


    pricing_priority = st.selectbox(

        "⚙ Pricing Priority",

        priority_options,

        index=(

            priority_options.index(

                current_priority

            )

            if current_priority in priority_options

            else 0

        ),

        format_func=lambda x:

            priority_labels.get(

                x,

                x

            )

    )



    # --------------------------------------------------------------------------
    # ENABLE RULES
    # --------------------------------------------------------------------------


    col1, col2 = st.columns(2)



    with col1:

        enable_product_markup = st.toggle(

            "☑ Product Markup Override",

            value=get_bool(

                settings,

                "ENABLE_PRODUCT_MARKUP",

                False

            )

        )



    with col2:

        enable_category_markup = st.toggle(

            "☑ Category Markup",

            value=get_bool(

                settings,

                "ENABLE_CATEGORY_MARKUP",

                False

            )

        )



    # --------------------------------------------------------------------------
    # METHOD
    # --------------------------------------------------------------------------


    pricing_method = st.selectbox(

        "📊 Calculation Method",

        [

            "MARKUP",

            "MARGIN"

        ],

        index=(

            0

            if settings.get(

                "PRICING_METHOD",

                "MARKUP"

            ) == "MARKUP"

            else 1

        )

    )



    col3, col4 = st.columns(2)



    with col3:

        auto_update_price = st.toggle(

            "🔄 Auto Update Selling Price",

            value=get_bool(

                settings,

                "AUTO_UPDATE_SELLING_PRICE",

                False

            )

        )



    with col4:

        allow_manual_override = st.toggle(

            "✏ Manual Price Override",

            value=get_bool(

                settings,

                "ALLOW_MANUAL_PRICE_OVERRIDE",

                False

            )

        )



    # --------------------------------------------------------------------------
    # SAVE
    # --------------------------------------------------------------------------
# SAVE REQUEST
# --------------------------------------------------------------------------


if st.button(

    "📨 Submit Pricing Change Request",

    use_container_width=True

):


    try:


        changes = [


            ("DEFAULT_MARKUP_PERCENT", default_markup),

            ("PRICING_PRIORITY", pricing_priority),

            ("ENABLE_PRODUCT_MARKUP", enable_product_markup),

            ("ENABLE_CATEGORY_MARKUP", enable_category_markup),

            ("PRICING_METHOD", pricing_method),

            ("AUTO_UPDATE_SELLING_PRICE", auto_update_price),

            ("ALLOW_MANUAL_PRICE_OVERRIDE", allow_manual_override),

        ]



        created = 0



        for key, value in changes:


            result = SettingsService.request_change(

                setting_key=key,

                new_value=value,

                reason="Pricing settings updated from ERP Control Center",

                requested_by=user["id"]

            )


            if result.get("success"):

                created += 1



        if created > 0:


            notify_success(

                f"📨 {created} pricing change request(s) submitted for approval."

            )


            st.rerun()


        else:


            st.info("No pricing changes detected.")



    except Exception as e:


        notify_error(

            f"Pricing Request Failed : {e}"

        )


            clear_settings_cache()


            notify_success(
                "💰 Pricing Engine settings saved."
            )


            st.rerun()



        except Exception as e:


            notify_error(

                f"Pricing Save Failed : {e}"

            )
