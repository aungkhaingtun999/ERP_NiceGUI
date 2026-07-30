# ==============================================================================
# erp_ui/settings/inventory_settings.py
# ERP INVENTORY SETTINGS COMPONENT
# ==============================================================================


import streamlit as st


from erp_core.loaders.settings_loader import (
    get_bool,
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
# INVENTORY SETTINGS UI
# ==============================================================================


def render_inventory_settings(settings,
    user):


    st.subheader(

        "📦 Inventory Rules"

    )



    # --------------------------------------------------------------------------
    # MINIMUM STOCK ALERT
    # --------------------------------------------------------------------------


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



    # --------------------------------------------------------------------------
    # AUTO REORDER
    # --------------------------------------------------------------------------


    auto_reorder = st.toggle(

        "🔄 Enable Auto Reorder",

        value=get_bool(

            settings,

            "AUTO_REORDER",

            False

        )

    )



    # --------------------------------------------------------------------------
    # SAVE
    # --------------------------------------------------------------------------


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
