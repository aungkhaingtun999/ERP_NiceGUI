# ==============================================================================
# erp_pages/12_Settings.py
# ERP ENTERPRISE CONTROL CENTER v5.0
#
# Settings Router Page
#
# UI Components:
#   Pricing
#   Accounting
#   Inventory
#   Finance
#   System Status
#
# Database Driven Architecture
#
# ==============================================================================


import streamlit as st



from erp_core.loaders.settings_loader import (
    get_all_settings_cached,
    clear_settings_cache,
)



from erp_ui.settings.pricing_settings import (
    render_pricing_settings,
)


from erp_ui.settings.accounting_settings import (
    render_accounting_settings,
)


from erp_ui.settings.inventory_settings import (
    render_inventory_settings,
)


from erp_ui.settings.finance_settings import (
    render_finance_settings,
)


from erp_ui.settings.system_status import (
    render_system_status,
)
from erp_core.repositories.settings_repository import (
    approve_setting_change
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
# PAGE
# ==============================================================================
def run():

    clear_settings_cache()

    user = require_admin()

    settings = load_settings()

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
    # SETTINGS COMPONENTS
    # ==========================================================================


    render_pricing_settings(
    settings,
    user
)


    st.divider()



    render_accounting_settings(
        settings,
    user
    )


    st.divider()



    render_inventory_settings(
        settings,
    user
    )


    st.divider()



    render_finance_settings(
        settings,
    user
    )


    st.divider()



    render_system_status()



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
