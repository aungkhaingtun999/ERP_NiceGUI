# ==============================================================================
# erp_ui/settings/inventory_settings.py
# ERP INVENTORY SETTINGS COMPONENT v2.0
#
# Approval Workflow:
#
# Maker
#   |
#   ↓
# settings_change_requests
#   |
#   ↓
# Checker Approval
#   |
#   ↓
# settings table update
#
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





# ==============================================================================
# INVENTORY SETTINGS UI
# ==============================================================================


def render_inventory_settings(
    settings,
    user
):


    # --------------------------------------------------------------------------
    # SHOW SUCCESS MESSAGE AFTER RERUN
    # --------------------------------------------------------------------------

    if "inventory_setting_saved" in st.session_state:


        notify_success(

            st.session_state.inventory_setting_saved

        )


        del st.session_state.inventory_setting_saved





    st.subheader(
        "📦 Inventory Rules"
    )





    # ==========================================================================
    # MINIMUM STOCK ALERT
    # ==========================================================================


    minimum_stock_value = settings.get(

        "MIN_STOCK_ALERT",

        0

    )



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

        step=1.0,

        key="inventory_min_stock_alert"

    )





    # ==========================================================================
    # AUTO REORDER
    # ==========================================================================


    auto_reorder = st.toggle(

        "🔄 Enable Auto Reorder",

        value=get_bool(

            settings,

            "AUTO_REORDER",

            False

        ),

        key="inventory_auto_reorder"

    )





    st.divider()





    # ==========================================================================
    # SUBMIT CHANGE REQUEST
    # ==========================================================================


    if st.button(

        "📨 Submit Inventory Change Request",

        use_container_width=True,

        key="submit_inventory_settings_request"

    ):


        try:


            # --------------------------------------------------------------
            # MIN STOCK REQUEST
            # --------------------------------------------------------------


            SettingsService.request_change(

                "MIN_STOCK_ALERT",

                str(minimum_stock),

                "Change minimum stock alert level",

                user["id"]

            )





            # --------------------------------------------------------------
            # AUTO REORDER REQUEST
            # --------------------------------------------------------------


            SettingsService.request_change(

                "AUTO_REORDER",

                auto_reorder,

                "Change auto reorder setting",

                user["id"]

            )





            # --------------------------------------------------------------
            # HOLD MESSAGE
            # --------------------------------------------------------------


            st.session_state.inventory_setting_saved = (

                "📦 Inventory change request submitted for approval"

            )



            st.rerun()





        except Exception as e:


            notify_error(

                f"Inventory Request Failed : {e}"

            )
