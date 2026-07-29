# ==============================================================================
# erp_pages/12_Settings.py
# ERP ENTERPRISE CONTROL CENTER v5.0 FINAL
#
# Settings UI
#
# Connected:
#
# settings_loader
# SettingsService
# ERP Cache
#
# ==============================================================================


import streamlit as st


from erp_core.loaders.settings_loader import (

    get_setting,

    get_bool,

    get_float,

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
            "⛔ Admin permission required"
        )

        st.stop()



    return user






# ==============================================================================
# SAFE DISPLAY
# ==============================================================================


def display_value(value):


    if value is None:

        return "⚠ Not Configured"


    return value






# ==============================================================================
# SAVE WRAPPER
# ==============================================================================


def save_config(

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
Pricing Flow


Product Markup

        ↓

Category Markup

        ↓

Global Markup


Controlled completely by ERP Settings.
"""
    )



    st.divider()



    current_markup = get_float(

        "DEFAULT_MARKUP_PERCENT"

    )



    st.metric(

        "Current Global Markup",

        (

            f"{current_markup:.2f}%"

            if current_markup is not None

            else

            "Not Configured"

        )

    )



    markup_input = st.number_input(

        "Set Global Markup (%)",

        min_value=0.0,

        max_value=500.0,

        value=(

            float(current_markup)

            if current_markup is not None

            else 0.0

        )

    )



    priority = get_setting(

        "PRICING_PRIORITY"

    )



    priority_options = [

        "PRODUCT_FIRST",

        "CATEGORY_FIRST",

        "GLOBAL_FIRST"

    ]



    selected_priority = st.selectbox(

        "Pricing Priority",

        priority_options,

        index=(

            priority_options.index(priority)

            if priority in priority_options

            else 0

        )

    )

# ==============================================================================
# PART 2
# PRICING CONTROL
# ==============================================================================



    # ==========================================================================
    # MARKUP CONTROL
    # ==========================================================================


    col1, col2 = st.columns(2)



    product_markup_enabled = st.checkbox(

        "☑ Enable Product Markup Override",

        value=get_bool(

            "ENABLE_PRODUCT_MARKUP"

        )

    )



    category_markup_enabled = st.checkbox(

        "☑ Enable Category Markup",

        value=get_bool(

            "ENABLE_CATEGORY_MARKUP"

        )

    )





    # ==========================================================================
    # PRICING METHOD
    # ==========================================================================


    pricing_method = st.selectbox(

        "📊 Pricing Calculation Method",

        [

            "MARKUP",

            "MARGIN"

        ],

        index=(

            0

            if get_setting(

                "PRICING_METHOD"

            )

            != "MARGIN"

            else 1

        )

    )





    # ==========================================================================
    # PRICE CONTROL
    # ==========================================================================


    col3, col4 = st.columns(2)



    with col3:


        auto_update_price = st.checkbox(

            "🔄 Auto Update Selling Price",

            value=get_bool(

                "AUTO_UPDATE_SELLING_PRICE"

            )

        )



    with col4:


        manual_override = st.checkbox(

            "✏ Allow Manual Price Override",

            value=get_bool(

                "ALLOW_MANUAL_PRICE_OVERRIDE"

            )

        )






    # ==========================================================================
    # SAVE PRICING SETTINGS
    # ==========================================================================


    if st.button(

        "💾 Save Pricing Settings",

        use_container_width=True

    ):


        try:


            save_config(

                "DEFAULT_MARKUP_PERCENT",

                markup_input

            )


            save_config(

                "PRICING_PRIORITY",

                selected_priority

            )


            save_config(

                "ENABLE_PRODUCT_MARKUP",

                product_markup_enabled

            )


            save_config(

                "ENABLE_CATEGORY_MARKUP",

                category_markup_enabled

            )


            save_config(

                "PRICING_METHOD",

                pricing_method

            )


            save_config(

                "AUTO_UPDATE_SELLING_PRICE",

                auto_update_price

            )


            save_config(

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







    st.divider()



    # ==========================================================================
    # TAX SETTINGS
    # ==========================================================================


    st.subheader(

        "🧾 Accounting & Tax"

    )



    tax_rate = get_float(

        "DEFAULT_TAX_RATE"

    )



    if tax_rate is None:


        st.warning(

            "⚠ Tax Rate is not configured"

        )


    else:


        st.metric(

            "Current Active Tax Rate",

            f"{tax_rate:.2f}%"

        )





    new_tax_rate = st.number_input(

        "Set Tax Rate (%)",

        min_value=0.0,

        max_value=100.0,

        value=(

            float(tax_rate)

            if tax_rate is not None

            else 0.0

        ),

        step=0.1

    )





    discount_policy = st.selectbox(

        "Discount Policy",

        [

            "allowed",

            "restricted"

        ],

        index=(

            0

            if get_setting(

                "DISCOUNT_POLICY"

            )

            != "restricted"

            else 1

        )

    )





    if st.button(

        "💾 Save Tax Settings",

        use_container_width=True

    ):


        try:


            save_config(

                "DEFAULT_TAX_RATE",

                new_tax_rate

            )


            save_config(

                "DISCOUNT_POLICY",

                discount_policy

            )



            clear_settings_cache()



            notify_success(

                "🧾 Tax settings saved"

            )


            st.rerun()



        except Exception as e:


            notify_error(

                str(e)

            )

# ==============================================================================
# PART 3
# INVENTORY + FINANCE SETTINGS
# ==============================================================================



    st.divider()



    # ==========================================================================
    # INVENTORY RULES
    # ==========================================================================


    st.subheader(

        "📦 Inventory Rules"

    )



    minimum_stock = get_float(

        "MIN_STOCK_ALERT"

    )



    if minimum_stock is None:

        minimum_stock_value = 0.0


    else:

        minimum_stock_value = float(

            minimum_stock

        )





    stock_alert = st.number_input(

        "Minimum Stock Alert",

        min_value=0.0,

        value=minimum_stock_value,

        step=1.0

    )





    auto_reorder = st.checkbox(

        "🔄 Enable Auto Reorder",

        value=get_bool(

            "AUTO_REORDER"

        )

    )





    if st.button(

        "💾 Save Inventory Settings",

        use_container_width=True

    ):


        try:


            save_config(

                "MIN_STOCK_ALERT",

                stock_alert

            )


            save_config(

                "AUTO_REORDER",

                auto_reorder

            )



            clear_settings_cache()



            notify_success(

                "📦 Inventory settings saved"

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



    currency_list = [

        "MMK",

        "USD",

        "THB",

        "SGD"

    ]



    current_currency = get_setting(

        "CURRENCY"

    )




    currency = st.selectbox(

        "Base Currency",

        currency_list,

        index=(

            currency_list.index(

                current_currency

            )

            if current_currency in currency_list

            else 0

        )

    )






    payment_options = [

        "Cash",

        "Bank Transfer",

        "Mobile Pay",

        "Credit"

    ]



    current_payment = get_setting(

        "PAYMENT_METHODS"

    )



    if current_payment:


        default_payment = current_payment.split(",")


    else:


        default_payment = []





    payment_methods = st.multiselect(

        "Enabled Payment Methods",

        payment_options,

        default=default_payment

    )







    if st.button(

        "💾 Save Finance Settings",

        use_container_width=True

    ):


        try:


            save_config(

                "CURRENCY",

                currency

            )


            save_config(

                "PAYMENT_METHODS",

                ",".join(

                    payment_methods

                )

            )



            clear_settings_cache()



            notify_success(

                "💱 Finance settings saved"

            )


            st.rerun()



        except Exception as e:


            notify_error(

                str(e)

            )

# ==============================================================================
# PART 4
# SYSTEM STATUS + ENTRY POINT
# ==============================================================================



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

✔ Finance Module Connected

✔ POS Ready

✔ ERP Configuration Synced
"""
    )





    # ==========================================================================
    # SETTINGS HEALTH CHECK
    # ==========================================================================


    st.subheader(

        "❤️ Settings Health"

    )


    try:


        from erp_core.services.settings_service import (

            SettingsService

        )


        from erp_core.base_repo import db



        service = SettingsService(

            db()

        )


        health = service.health_check()



        if health.get(

            "status"

        ) == "PASS":


            st.success(

                f"""
Settings Service : PASS

Database : Connected

Rows : {health.get('rows',0)}
"""

            )


        else:


            st.error(

                str(health)

            )



    except Exception as e:


        st.error(

            f"Health Check Failed : {e}"

        )







    # ==========================================================================
    # FINAL MESSAGE
    # ==========================================================================


    st.success(

        "🚀 ERP Enterprise Control Center Fully Operational"

    )






# ==============================================================================
# ENTRY POINT
# ==============================================================================


if __name__ == "__main__":


    st.set_page_config(

        page_title=

        "ERP Control Center",

        page_icon=

        "⚙️",

        layout=

        "wide"

    )


    run()

