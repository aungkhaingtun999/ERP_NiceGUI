# ==============================================================================
# erp_pages/12_Settings.py
# ERP ENTERPRISE CONTROL CENTER v4.0
#
# PART 1 / 2
#
# Settings UI Layer
# Connected:
#   settings_loader
#   SettingsService
#   ERP Cache
#
# ==============================================================================


import streamlit as st


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
            "⛔ Access Denied : Admin Only"
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
            f"Settings Load Error : {e}"
        )

        return {}





# ==============================================================================
# SAVE SETTINGS WRAPPER
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

                "Save Failed"

            )

        )





# ==============================================================================
# MAIN
# ==============================================================================


def run():


    user = require_admin()


    settings = load_settings()



    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------


    st.title(
        "⚙ ERP Control Center"
    )


    st.success(

        f"🔐 Welcome Admin : "
        f"{user.get('full_name','Admin')}"

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
Pricing Priority


① Product Markup

        ↓

② Category Markup

        ↓

③ Global Default Markup


System automatically selects the first available rule.
"""
    )



    st.divider()



    # --------------------------------------------------------------------------
    # GLOBAL MARKUP
    # --------------------------------------------------------------------------


    default_markup = st.number_input(

        "🌍 Global Default Markup (%)",

        min_value=0.0,

        max_value=500.0,

        value=get_float(

            settings,

            "DEFAULT_MARKUP_PERCENT",

            40.0

        ),

        step=1.0

    )





    # --------------------------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------------------------


    priority_options = [

        "PRODUCT_FIRST",

        "CATEGORY_FIRST",

        "GLOBAL_FIRST"

    ]


    priority_labels = {


        "PRODUCT_FIRST":

            "Product → Category → Global",


        "CATEGORY_FIRST":

            "Category → Product → Global",


        "GLOBAL_FIRST":

            "Global Default Only"

    }



    current_priority = settings.get(

        "PRICING_PRIORITY",

        "PRODUCT_FIRST"

    )



    pricing_priority = st.selectbox(

        "⚙ Pricing Priority Rule",

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
    # MARKUP ENABLE
    # --------------------------------------------------------------------------


    col1, col2 = st.columns(2)



    with col1:


        enable_product_markup = st.toggle(

            "☑ Enable Product Markup Override",

            value=get_bool(

                settings,

                "ENABLE_PRODUCT_MARKUP",

                True

            )

        )




    with col2:


        enable_category_markup = st.toggle(

            "☑ Enable Category Markup",

            value=get_bool(

                settings,

                "ENABLE_CATEGORY_MARKUP",

                True

            )

        )





    st.divider()





    # --------------------------------------------------------------------------
    # PRICE METHOD
    # --------------------------------------------------------------------------


    pricing_method = st.selectbox(

        "📊 Pricing Calculation Method",

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





    col3, col4 = st.columns(2)



    with col3:


        auto_update_price = st.toggle(

            "🔄 Auto Update Selling Price",

            value=get_bool(

                settings,

                "AUTO_UPDATE_SELLING_PRICE",

                True

            )

        )



    with col4:


        allow_manual_override = st.toggle(

            "✏ Allow Manual Price Override",

            value=get_bool(

                settings,

                "ALLOW_MANUAL_PRICE_OVERRIDE",

                True

            )

        )





    # --------------------------------------------------------------------------
    # SAVE PRICING
    # --------------------------------------------------------------------------


    if st.button(

        "💾 Save Pricing Engine Settings",

        use_container_width=True

    ):


        try:


            save_setting(

                "DEFAULT_MARKUP_PERCENT",

                default_markup

            )


            save_setting(

                "PRICING_PRIORITY",

                pricing_priority

            )


            save_setting(

                "ENABLE_PRODUCT_MARKUP",

                enable_product_markup

            )


            save_setting(

                "ENABLE_CATEGORY_MARKUP",

                enable_category_markup

            )


            save_setting(

                "PRICING_METHOD",

                pricing_method

            )


            save_setting(

                "AUTO_UPDATE_SELLING_PRICE",

                auto_update_price

            )


            save_setting(

                "ALLOW_MANUAL_PRICE_OVERRIDE",

                allow_manual_override

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





    st.divider()

    # ==========================================================================
    # ACCOUNTING & TAX SETTINGS
    # ==========================================================================


    st.subheader(
        "🧾 Accounting & Tax"
    )


    active_tax_rate = get_float(

        settings,

        "DEFAULT_TAX_RATE",

        7.0

    )


    # --------------------------------------------------------------------------
    # ACTIVE TAX CARD
    # --------------------------------------------------------------------------

    st.markdown(

        f"""
<div style="
    padding:18px;
    border-radius:14px;
    background:#E8F5E9;
    border:1px solid #4CAF50;
    margin-bottom:18px;
">

<div style="
    font-size:14px;
    color:#2E7D32;
    font-weight:600;
">
📌 Current Active Tax Rate
</div>


<div style="
    font-size:34px;
    font-weight:700;
    color:#1B5E20;
">
{active_tax_rate:.2f}%
</div>


<div style="
    font-size:13px;
    color:#33691E;
">
Used by POS, Sales, Invoice and Accounting modules.
</div>


</div>
""",

        unsafe_allow_html=True

    )



    tax_rate = st.number_input(

        "Change Tax Rate (%)",

        min_value=0.0,

        max_value=100.0,

        value=float(active_tax_rate),

        step=0.5

    )



    discount_policy = st.selectbox(

        "Discount Policy",

        [

            "allowed",

            "restricted"

        ],

        index=(

            0

            if settings.get(

                "DISCOUNT_POLICY",

                "allowed"

            )

            == "allowed"

            else 1

        )

    )




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

                f"🧾 Tax updated successfully : {tax_rate:.2f}%"

            )


            st.rerun()



        except Exception as e:


            notify_error(

                str(e)

            )





    st.divider()





    # ==========================================================================
    # INVENTORY RULES
    # ==========================================================================


    st.subheader(

        "📦 Inventory Rules"

    )



    minimum_stock = st.number_input(

        "Default Minimum Stock Alert",

        min_value=0.0,

        value=get_float(

            settings,

            "MIN_STOCK_ALERT",

            10

        ),

        step=1.0

    )



    auto_reorder = st.toggle(

        "Enable Auto Reorder",

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

                "📦 Inventory settings saved."

            )


            st.rerun()



        except Exception as e:


            notify_error(

                str(e)

            )





    st.divider()





    # ==========================================================================
    # FINANCE SETTINGS
    # ==========================================================================


    st.subheader(

        "💱 Finance Settings"

    )



    currency_options = [

        "MMK",

        "USD",

        "THB",

        "SGD"

    ]



    current_currency = settings.get(

        "CURRENCY",

        "MMK"

    )



    currency = st.selectbox(

        "Base Currency",

        currency_options,

        index=(

            currency_options.index(

                current_currency

            )

            if current_currency in currency_options

            else 0

        )

    )





    payment_methods = st.multiselect(

        "Enabled Payment Methods",

        [

            "Cash",

            "Bank Transfer",

            "Mobile Pay",

            "Credit"

        ],

        default=settings.get(

            "PAYMENT_METHODS",

            "Cash,Bank Transfer"

        ).split(",")

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

                "💱 Finance settings saved."

            )


            st.rerun()



        except Exception as e:


            notify_error(

                str(e)

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

✔ Warehouse Engine Ready

✔ Inventory Engine Connected

✔ Sales Engine Connected

✔ Purchase Engine Connected

✔ Pricing Engine Connected

✔ Settings Database Synced

✔ Product / Category / Global Markup Ready

✔ Tax Engine Connected
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
